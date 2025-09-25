import logging
from datetime import datetime
from typing import List

from openg2p_bg_task_models.schemas import (
    BenefitProgramRequest,
    BenefitProgram,
    BenefitProgramResponse,
    BenefitProgramResponseBody,
    BenefitProgramDetailResponse,
    BenefitProgramDetailResponseBody,
)
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..engine import get_engine
from openg2p_pbms_models.models.beneficiary_list import G2PBeneficiaryList
from openg2p_pbms_models.models.enrollment_cycle import G2PEnrollmentCycle
from openg2p_pbms_models.models.program_definiton import G2PProgramDefinition
from openg2p_pbms_models.models.program_benefit_codes import (
    G2PProgramBenefitCodes,
)
from openg2p_pbms_models.models.benefit_codes import G2PBenefitCodes
from openg2p_bg_task_models.models.beneficiary_list_details import (
    BeneficiaryListDetails,
)

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


class BenefitProgramService(BaseService):
    async def get_my_programs(
        self, benefit_program_request: BenefitProgramRequest
    ) -> BenefitProgramResponse:
        pagination = (
            benefit_program_request.g2p_request_body.g2p_pagination_request
            if benefit_program_request.g2p_request_body
            else None
        )
        payload = (
            benefit_program_request.g2p_request_body.g2p_request_payload
            if benefit_program_request.g2p_request_body
            else None
        )

        # TODO: Extract beneficiary_id from auth context; temporary header-based fallback possible in controller
        beneficiary_id = None

        session_maker_pbms = async_sessionmaker(
            bind=_engine.get("db_engine_sr"), expire_on_commit=False
        )
        session_maker_bg = async_sessionmaker(
            bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
        )

        benefit_programs: List[BenefitProgram] = []

        async with session_maker_pbms() as session_pbms:
            # Latest approved cycle per program
            sub_latest_cycle = (
                select(
                    G2PEnrollmentCycle.program_id,
                    func.max(G2PEnrollmentCycle.cycle_number).label("max_cycle"),
                )
                .where(G2PEnrollmentCycle.approved_for_enrollment.is_(True))
                .group_by(G2PEnrollmentCycle.program_id)
                .subquery()
            )

            selected_cycles = (
                select(G2PEnrollmentCycle.id, G2PEnrollmentCycle.program_id)
                .join(
                    sub_latest_cycle,
                    (G2PEnrollmentCycle.program_id == sub_latest_cycle.c.program_id)
                    & (G2PEnrollmentCycle.cycle_number == sub_latest_cycle.c.max_cycle),
                )
            )

            # Approved lists for selected cycles
            approved_lists_stmt = (
                select(
                    G2PBeneficiaryList.id.label("list_pk"),
                    G2PBeneficiaryList.beneficiary_list_id,
                    G2PBeneficiaryList.program_id,
                    G2PBeneficiaryList.approval_date,
                )
                .join(selected_cycles.subquery(), G2PBeneficiaryList.enrollment_cycle_id == selected_cycles.subquery().c.id)
                .where(G2PBeneficiaryList.approval_date.is_not(None))
            )

            approved_lists = (await session_pbms.execute(approved_lists_stmt)).all()

        # Membership check in bg-task DB via BeneficiaryListDetails
        async with session_maker_bg() as session_bg:
            list_ids_for_beneficiary = set()
            for benefit_code in approved_lists:
                beneficiary_list_id = benefit_code.beneficiary_list_id
                beneficiary_list_details = await session_bg.get(BeneficiaryListDetails, {"beneficiary_list_id": beneficiary_list_id})
                # Fallback when get by PK won't work: query by beneficiary_list_id
                if not beneficiary_list_details:
                    beneficiary_list_details = (
                        await session_bg.execute(
                            select(BeneficiaryListDetails).where(
                                BeneficiaryListDetails.beneficiary_list_id
                                == beneficiary_list_id
                            )
                        )
                    ).scalars().first()
                if not beneficiary_list_details:
                    continue

                registrants = beneficiary_list_details.registrant_details or []
                if any(
                    isinstance(registrant, dict)
                    and registrant.get("registrant_id") == beneficiary_id
                    for registrant in registrants
                ):
                    list_ids_for_beneficiary.add(beneficiary_list_id)

        matching_program_ids = {
            row.program_id for row in approved_lists if row.beneficiary_list_id in list_ids_for_beneficiary
        }

        if not matching_program_ids:
            return await self.construct_benefit_program_success_response(
                benefit_program_request, []
            )

        async with session_maker_pbms() as session_pbms:
            # Fetch program definitions
            programs = (
                await session_pbms.execute(
                    select(G2PProgramDefinition).where(
                        G2PProgramDefinition.id.in_(matching_program_ids)
                    )
                )
            ).scalars().all()

            # Fetch latest enrolment date per program from the approved lists we had
            program_id_to_enrolment_date = {}
            for benefit_code in approved_lists:
                if benefit_code.beneficiary_list_id in list_ids_for_beneficiary:
                    current = program_id_to_enrolment_date.get(benefit_code.program_id)
                    if not current or (benefit_code.approval_date and benefit_code.approval_date > current):
                        program_id_to_enrolment_date[benefit_code.program_id] = benefit_code.approval_date

            # Fetch benefit codes via mapping
            benefit_codes = (
                await session_pbms.execute(
                    select(
                        G2PProgramBenefitCodes.program_id,
                        G2PBenefitCodes.id,
                        G2PBenefitCodes.benefit_mnemonic,
                        G2PBenefitCodes.benefit_type,
                        G2PBenefitCodes.benefit_description,
                        G2PBenefitCodes.measurement_unit,
                        G2PProgramBenefitCodes.max_quantity,
                    )
                    .join(
                        G2PBenefitCodes,
                        G2PProgramBenefitCodes.benefit_code_id == G2PBenefitCodes.id,
                    )
                    .where(G2PProgramBenefitCodes.program_id.in_(matching_program_ids))
                )
            ).all()

            program_id_to_benefit_codes = {}
            for benefit_code in benefit_codes:
                program_id_to_benefit_codes.setdefault(benefit_code.program_id, []).append(
                    {
                        "id": benefit_code.id,
                        "benefit_code_mnemonic": benefit_code.benefit_mnemonic,
                        "benefit_type": benefit_code.benefit_type,
                        "benefit_code_description": benefit_code.benefit_description,
                        "benefit_code_max_quantity": benefit_code.max_quantity,
                        "measurement_unit": benefit_code.measurement_unit,
                    }
                )

            for program in programs:
                benefit_programs.append(
                    BenefitProgram(
                        id=program.id,
                        program_name=program.description,
                        program_mnemonic=program.program_mnemonic,
                        program_description=program.description,
                        application_id=None,
                        application_status=None,
                        enrolment_date=program_id_to_enrolment_date.get(program.id),
                        benefit_codes=program_id_to_benefit_codes.get(program.id, []),
                    )
                )

        return await self.construct_benefit_program_success_response(
            benefit_program_request, benefit_programs
        )

    async def construct_benefit_program_success_response(
        self,
        benefit_program_request: BenefitProgramRequest,
        benefit_programs: List[BenefitProgram],
    ) -> BenefitProgramResponse:
        benefit_programs_response = BenefitProgramResponse(
            g2p_response_header={
                "request_id": benefit_program_request.g2p_request_header.request_id,
                "response_status": "SUCCESS",
                "response_timestamp": datetime.now(),
            },
            g2p_response_body=BenefitProgramResponseBody(
                g2p_pagination_response={
                    "number_of_items": len(benefit_programs),
                    "number_of_pages": 1,
                },
                g2p_response_payload=benefit_programs,
            ),
        )
        return benefit_programs_response

    async def construct_benefit_program_failure_response(
        self,
        benefit_program_request: BenefitProgramRequest,
        error_code: str,
        error_message: str | None = None,
    ) -> BenefitProgramResponse:
        benefit_programs_response = BenefitProgramResponse(
            g2p_response_header={
                "request_id": benefit_program_request.g2p_request_header.request_id,
                "response_status": "ERROR",
                "response_error_code": error_code,
                "response_error_message": error_message,
                "response_timestamp": datetime.now(),
            },
            g2p_response_body=BenefitProgramResponseBody(
                g2p_pagination_response={
                    "number_of_items": 0,
                    "number_of_pages": 0,
                },
                g2p_response_payload=[],
            ),
        )
        return benefit_programs_response

    async def get_all_programs(
        self, benefit_program_request: BenefitProgramRequest
    ) -> BenefitProgramResponse:
        # Reuse the same PBMS queries but skip membership filtering
        session_maker_pbms = async_sessionmaker(
            bind=_engine.get("db_engine_sr"), expire_on_commit=False
        )

        async with session_maker_pbms() as session_pbms:
            programs = (
                await session_pbms.execute(select(G2PProgramDefinition))
            ).scalars().all()

            # Benefit codes
            benefit_codes = (
                await session_pbms.execute(
                    select(
                        G2PProgramBenefitCodes.program_id,
                        G2PBenefitCodes.id,
                        G2PBenefitCodes.benefit_mnemonic,
                        G2PBenefitCodes.benefit_type,
                        G2PBenefitCodes.benefit_description,
                        G2PBenefitCodes.measurement_unit,
                        G2PProgramBenefitCodes.max_quantity,
                    ).join(
                        G2PBenefitCodes,
                        G2PProgramBenefitCodes.benefit_code_id == G2PBenefitCodes.id,
                    )
                )
            ).all()

            program_id_to_benefit_codes = {}
            for benefit_code in benefit_codes:
                program_id_to_benefit_codes.setdefault(benefit_code.program_id, []).append(
                    {
                        "id": benefit_code.id,
                        "benefit_code_mnemonic": benefit_code.benefit_mnemonic,
                        "benefit_type": benefit_code.benefit_type,
                        "benefit_code_description": benefit_code.benefit_description,
                        "benefit_code_max_quantity": benefit_code.max_quantity,
                        "measurement_unit": benefit_code.measurement_unit,
                    }
                )

            benefit_programs: List[BenefitProgram] = []
            for program in programs:
                benefit_programs.append(
                    BenefitProgram(
                        id=program.id,
                        program_name=program.description,
                        program_mnemonic=program.program_mnemonic,
                        program_description=program.description,
                        application_id=None,
                        application_status=None,
                        enrolment_date=None,
                        benefit_codes=program_id_to_benefit_codes.get(program.id, []),
                    )
                )

        return await self.construct_benefit_program_success_response(
            benefit_program_request, benefit_programs
        )

    async def get_program(
        self, benefit_program_request: BenefitProgramRequest
    ) -> BenefitProgramDetailResponse:
        program_id = (
            benefit_program_request.g2p_request_body.g2p_request_payload.program_id
            if benefit_program_request.g2p_request_body
            and benefit_program_request.g2p_request_body.g2p_request_payload
            else None
        )
        if not program_id:
            return await self.construct_benefit_program_detail_failure_response(
                benefit_program_request,
                "INVALID_REQUEST",
                "program_id is required",
            )

        session_maker_pbms = async_sessionmaker(
            bind=_engine.get("db_engine_sr"), expire_on_commit=False
        )
        async with session_maker_pbms() as session_pbms:
            program = (
                await session_pbms.execute(
                    select(G2PProgramDefinition).where(G2PProgramDefinition.id == int(program_id))
                )
            ).scalars().first()
            if not program:
                return await self.construct_benefit_program_detail_failure_response(
                    benefit_program_request,
                    "NOT_FOUND",
                    "Program not found",
                )

            join_codes = (
                await session_pbms.execute(
                    select(
                        G2PBenefitCodes.id,
                        G2PBenefitCodes.benefit_mnemonic,
                        G2PBenefitCodes.benefit_type,
                        G2PBenefitCodes.benefit_description,
                        G2PBenefitCodes.measurement_unit,
                        G2PProgramBenefitCodes.max_quantity,
                    )
                    .join(
                        G2PProgramBenefitCodes,
                        G2PProgramBenefitCodes.benefit_code_id == G2PBenefitCodes.id,
                    )
                    .where(G2PProgramBenefitCodes.program_id == program.id)
                )
            ).all()

            benefit_codes = [
                {
                    "id": row.id,
                    "benefit_code_mnemonic": row.benefit_mnemonic,
                    "benefit_type": row.benefit_type,
                    "benefit_code_description": row.benefit_description,
                    "benefit_code_max_quantity": row.max_quantity,
                    "measurement_unit": row.measurement_unit,
                }
                for row in join_codes
            ]

            benefit_program = BenefitProgram(
                id=program.id,
                program_name=program.description,
                program_mnemonic=program.program_mnemonic,
                program_description=program.description,
                application_id=None,
                application_status=None,
                enrolment_date=None,
                benefit_codes=benefit_codes,
            )

        return await self.construct_benefit_program_detail_success_response(
            benefit_program_request, benefit_program
        )

    async def construct_benefit_program_detail_success_response(
        self,
        benefit_program_request: BenefitProgramRequest,
        benefit_program: BenefitProgram,
    ) -> BenefitProgramDetailResponse:
        return BenefitProgramDetailResponse(
            g2p_response_header={
                "request_id": benefit_program_request.g2p_request_header.request_id,
                "response_status": G2PBenefitCodes.SUCCESS.value,
                "response_timestamp": datetime.now(),
            },
            g2p_response_body=BenefitProgramDetailResponseBody(
                g2p_response_payload=benefit_program
            ),
        )

    async def construct_benefit_program_detail_failure_response(
        self,
        benefit_program_request: BenefitProgramRequest,
        error_code: str,
        error_message: str | None = None,
    ) -> BenefitProgramDetailResponse:
        return BenefitProgramDetailResponse(
            g2p_response_header={
                "request_id": benefit_program_request.g2p_request_header.request_id,
                "response_status": G2PBenefitCodes.ERROR.value,
                "response_error_code": error_code,
                "response_error_message": error_message,
                "response_timestamp": datetime.now(),
            },
            g2p_response_body=BenefitProgramDetailResponseBody(
                g2p_response_payload=None
            ),
        )

