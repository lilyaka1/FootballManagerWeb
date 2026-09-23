from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserAdminUpdate(BaseModel):
    role: str = Field(pattern="^(user|admin)$")


class UserAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str
