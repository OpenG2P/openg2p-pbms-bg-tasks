from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel
from .status_enum import StatusEnum


class G2PBeneficiaryList(BaseORMModel):
    __tablename__ = "g2p_beneficiary_list"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_list_id = mapped_column(String, index=True, unique=True, nullable=False)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    enrollment_cycle_id = mapped_column(
        Integer, ForeignKey("g2p_enrollment_cycle.id"), nullable=True
    )
    disbursement_cycle_id = mapped_column(
        Integer, ForeignKey("g2p_disbursement_cycle.id"), nullable=True
    )
    brief = mapped_column(Text, nullable=True)
    eligibility_process_status = mapped_column(
        String, nullable=False, default=StatusEnum.PENDING.value
    )
    entitlement_process_status = mapped_column(
        String, nullable=False, default=StatusEnum.NOT_APPLICABLE.value
    )
    disbursement_envelope_status = mapped_column(
        String, nullable=False, default=StatusEnum.NOT_APPLICABLE.value
    )
    disbursement_batch_creation_status = mapped_column(
        String, nullable=False, default=StatusEnum.NOT_APPLICABLE.value
    )
    creation_date = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_date = mapped_column(DateTime, default=None, nullable=True)
    mnemonic = mapped_column(String, nullable=False)
    list_stage = mapped_column(String, nullable=True)  # ENROLLMENT or DISBURSEMENT
    list_workflow_status = mapped_column(
        String, nullable=True
    )  # INITIATED, PUBLISHED TO COMMUNITIES, APPROVED FINAL ENROLMENT, APPROVED FOR DISBURSEMENT

    # add field for disb envelope preprocessing
    # add field for disb envelope creation status

    # feedback_ids = relationship(
    #     "G2PBeneficiaryListFeedback",
    #     back_populates="beneficiary_list",
    #     cascade="all, delete-orphan",
    #     primaryjoin="G2PBeneficiaryList.id==G2PBeneficiaryListFeedback.beneficiary_list_id"
    # )
    # verification_ids = relationship(
    #     "G2PBeneficiaryListVerification",
    #     back_populates="beneficiary_list",
    #     cascade="all, delete-orphan",
    #     primaryjoin="G2PBeneficiaryList.id==G2PBeneficiaryListVerification.beneficiary_list_id"
    # )
