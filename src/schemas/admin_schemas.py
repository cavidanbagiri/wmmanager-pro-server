
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterSchema(BaseModel):

    first_name: str = Field(min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr()
    password: str = Field(min_length=8, max_length=50)
    project_id: int
    is_admin: Optional[bool] = False
    role_id: int = None

    @field_validator('first_name')
    @classmethod
    def validate_first_name(cls, v: str):
        v = v.strip()
        if ' ' in v:
            raise ValueError('Remove empty spaces (' ')')

        if len(v) < 3 or len(v)>30:
            raise ValueError("Value must be greater then 3 and less than 30")
        return v.lower()

    @field_validator('middle_name')
    @classmethod
    def validate_middle_name(cls, v: Optional[str]):
        if v is None:
            return None
        v = v.strip()
        if v == '':
            return None
        if ' ' in v:
            raise ValueError('Remove empty spaces (' ')')
        if len(v) < 3 or len(v)>30:
            raise ValueError('Value must be greater then 3 and less than 30')
        return v.lower()

    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v: str):
        v = v.strip()
        if ' ' in v:
            raise ValueError('Remove empty spaces (' ')')
        if len(v) < 3 or len(v)>30:
            raise ValueError('Value must be greater then 3 and less than 30')
        return v.lower()


    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Additional password checks"""

        if len(value.strip()) < 8:
            raise ValueError("Password too short (min 8 chars)")
        if value.lower() in ["password", "12345678"]:
            raise ValueError("Password too common")
        if ' ' in value:
            raise ValueError("Password can't contain space")

        return value



class UserResponseSchema(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime

    class Config:
        from_attributes = True



class ProjectCreateSchema(BaseModel):
    project_name: str = Field(min_length=2, max_length=40)
    project_code: str = Field(min_length=2, max_length=20)


    @field_validator('project_name')
    @classmethod
    def validate_project_name(cls, v:str) -> str:
        print('project name this code is work')
        if not " " in v:
            raise ValueError('Project name must be contain space ')
        return v.strip().upper()

    @field_validator('project_code')
    @classmethod
    def validate_project_code(cls, v: str) -> str:
        print('project code this code is work')
        return v.strip().upper()

class ProjectResponseSchema(BaseModel):
    id: int
    project_name: str = Field(min_length=2, max_length=40)
    project_code: str = Field(min_length=2, max_length=20)

    class Config:
        from_attributes = True



class GroupCreateSchema(BaseModel):

    group_name: str = Field(min_length=2, max_length=30)

    @field_validator('group_name')
    @classmethod
    def validate_group_name(cls, v: str):
        if len(v.strip()) < 2:
            raise ValueError('Group name must be at least two characters')
        return v.strip().lower()

class GroupResponseSchema(BaseModel):
    id: int
    group_name: str = Field(min_length=2, max_length=30)

    class Config:
        from_attributes = True


class CategoryCreateSchema(BaseModel):

    category_name: str = Field(min_length=2, max_length=30)

    @field_validator('category_name')
    @classmethod
    def validate_category_name(cls, v: str):
        if len(v.strip()) < 2:
            raise ValueError('Category name must be at least two characters')
        return v.strip().upper()

class CategoryResponseSchema(BaseModel):
    id: int
    category_name: str = Field(min_length=2, max_length=30)

    class Config:
        from_attributes = True

