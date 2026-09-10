from typing import Optional

from pydantic import BaseModel, root_validator


class EscalationLevel(BaseModel):
    level: int
    role_id: list[str]
    user_id: Optional[list[str]] = None


class CreateCategoryRequest(BaseModel):
    name: str
    description: Optional[str] = None
    escalation_levels: int

    role_responsible: list[EscalationLevel]

    @root_validator
    def validate_escalation_levels(cls, values):
        escalation_levels = values.get('escalation_levels')
        role_responsible = values.get('role_responsible')

        if escalation_levels <= 0:
            raise ValueError('Escalation levels must be greater than 0')

        if escalation_levels != len(role_responsible):
            raise ValueError(f'Please complete all {escalation_levels} escalation levels')

        expected_levels = set(range(1, escalation_levels + 1))
        provided_levels = {item.level for item in role_responsible}

        if expected_levels != provided_levels:
            raise ValueError(f'Escalation levels must be sequential from 1 to {escalation_levels}')

        return values


class CategoryUpdate(BaseModel):
    category_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    escalation_levels: Optional[int] = None
    role_responsible: Optional[list[EscalationLevel]] = None


class RoleUsersRequest(BaseModel):
    role_ids: list[str]
