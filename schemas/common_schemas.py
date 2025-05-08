from typing import Optional

from pydantic import BaseModel, Field, EmailStr, field_validator

class CompanyCreteSchema(BaseModel):
    company_name: str = Field(min_length=2, max_length=100)
    country: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

    # Validator for company_name
    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Company name cannot be empty or whitespace")
        if len(stripped) < 2:
            raise ValueError("Company name must be at least 2 characters after removing whitespace")
        if len(stripped) > 100:
            raise ValueError("Company name cannot exceed 100 characters")
        return stripped.upper()

    # Validator for country
    @field_validator('country')
    @classmethod
    def uppercase_country(cls, v):
        stripped = v.strip()
        if not stripped:  # Catches empty strings after stripping
            raise ValueError("Country cannot be empty or whitespace")
        return stripped.upper()

    # Validator for phone_number
    @field_validator('phone_number')
    @classmethod
    def uppercase_phone_number(cls, v):
        stripped = v.strip()
        if not stripped:  # Catches empty strings after stripping
            raise ValueError("Phone number cannot be empty or whitespace")
        return stripped.upper()


class CompanyResponseSchema(BaseModel):
    id: int
    company_name: str = Field(min_length=2, max_length=100)

    class Config:
        from_attributes = True


class OrderedCreateSchema(BaseModel):
    f_name: str
    l_name: str
    email: EmailStr | None = None
    group_id: int
    project_id: int

    @field_validator('f_name')
    @classmethod
    def validate_f_name(cls, v: str):
        v = v.strip()
        if ' ' in v:
            raise ValueError('Remove empty spaces (' ')')

        if len(v) < 2 or len(v) > 30:
            raise ValueError("Value must be greater then 3 and less than 30")
        return v.lower()

    @field_validator('l_name')
    @classmethod
    def validate_l_name(cls, v: str):
        v = v.strip()
        if ' ' in v:
            raise ValueError('Remove empty spaces (' ')')

        if len(v) < 2 or len(v) > 30:
            raise ValueError("Value must be greater then 3 and less than 30")
        return v.lower()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str):
        if v:
            v = v.strip()
            if ' ' in v:
                raise ValueError('Remove empty spaces (' ')')

            if len(v) < 3 or len(v) > 30:
                raise ValueError("Value must be greater then 3 and less than 30")
            return v.lower()
        return None


class OrderedResponseSchema(BaseModel):
    id: int
    f_name: str = Field(min_length=2, max_length=30)
    l_name: str = Field(min_length=2, max_length=30)

    class Config:
        from_attributes = True


class OrderedFetchResponseSchema(BaseModel):
    id: int
    f_name: str
    l_name: str
    group_name: str



class MaterialCodeCreateSchema(BaseModel):

    description: str = Field(min_length=2, max_length=30)

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str):
        if len(v.strip()) < 2:
            raise ValueError('Description name must be at least two characters')
        return v.strip().upper()

class MaterialCodeResponseSchema(BaseModel):
    id: int
    code_num: str
    description: str = Field(min_length=2, max_length=30)

    class Config:
        from_attributes = True