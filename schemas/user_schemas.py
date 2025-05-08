
from pydantic import BaseModel, EmailStr, field_validator



class UserLoginSchema(BaseModel):

    email: EmailStr()
    password: str

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


class UserTokenSchema(BaseModel):
    sub: str
    email: EmailStr()
    project_id: int