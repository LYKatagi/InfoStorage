from pydantic import BaseModel, ConfigDict, Field, field_validator


class CredentialsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    username: str = Field(default="", max_length=254)
    password: str = Field(min_length=1, max_length=4096)
    notes: str = Field(default="", max_length=4000)


class Credential(CredentialsInput):
    id: str


class NoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50000)


class Note(NoteInput):
    id: str


class AuthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=1024)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Nome de usuário inválido.")
        normalized = value.strip().casefold()
        if not normalized:
            raise ValueError("Nome de usuário inválido.")
        return normalized


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str


class MessageResponse(BaseModel):
    message: str
