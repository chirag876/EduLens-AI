from enum import Enum

class SourceType(str, Enum):
    PDF = 'pdf'
    VIDEO = 'video'

class IngestionStatus(str, Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

class GradeLevel(str, Enum):
    PRIMARY = 'primary'
    MIDDLE = 'middle'
    HIGH = 'high'
    COLLEGE = 'college'