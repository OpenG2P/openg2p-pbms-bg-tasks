import enum


class StatusEnum(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"


class ListWorkflowStatusEnum(enum.Enum):
    INITIATED = "initiated"
    PUBLISHED_TO_COMMUNITIES = "published_to_communities"
    APPROVED_FINAL_ENROLMENT = "approved_final_enrolment"
    APPROVED_FOR_DISBURSEMENT = "approved_for_disbursement"


class ListStageEnum(enum.Enum):
    ENROLLMENT = "enrollment"
    DISBURSEMENT = "disbursement"
