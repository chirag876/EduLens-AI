from typing import Any, Optional

from pydantic import Field

from app.server.models.generic import BaseModel, DateTimeModelMixin, DictWithObjectIdStr


class CreateData(DictWithObjectIdStr, DateTimeModelMixin):
    """Model class to accept any arbitrary field types for document creation with auto ObjectId generation

    Args:
        DictWithObjectIdStr (class): Model to extend from
    """

    is_deleted: bool = False

    class Config:
        extra = 'allow'


class QueryData(BaseModel):
    """Model class to accept filter and options dict which can be directly used to query database

    Args:
        BaseModel (class): Model to extend from
    """

    filter: Optional[dict[str, Any]] = {}
    options: Optional[dict[str, Any]] = None
    pageSize: Optional[int] = None
    lastId: Optional[str] = None


class UpdateData(BaseModel):
    """Model class to accept filter, update and options dict which can be directly used to updated database

    Args:
        BaseModel (class): Model to extend from
    """

    filter: Optional[dict[str, Any]] = {}
    update: dict[str, Any] = Field(...)
    options: Optional[dict[str, Any]] = {}
