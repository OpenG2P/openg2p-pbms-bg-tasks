import enum

class StatusEnum(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"