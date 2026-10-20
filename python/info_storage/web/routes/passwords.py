import secrets
import string

from fastapi import APIRouter

from info_storage.web.schemas import GeneratedPassword, PasswordGenerationInput
from info_storage.web.sessions import SessionDependency

router = APIRouter(prefix="/passwords", tags=["Senhas"])


@router.post("/generate", response_model=GeneratedPassword)
def generate_password(
    body: PasswordGenerationInput,
    session: SessionDependency,
) -> dict[str, str]:
    """Gera uma senha aleatória usando o gerador criptográfico do Python."""
    groups = []
    if body.lowercase:
        groups.append(string.ascii_lowercase)
    if body.uppercase:
        groups.append(string.ascii_uppercase)
    if body.digits:
        groups.append(string.digits)
    if body.symbols:
        groups.append("!@#$%^&*()-_=+[]{}:,.?")

    # Include one character from each selected group, then fill and shuffle.
    password = [secrets.choice(group) for group in groups]
    alphabet = "".join(groups)
    password.extend(secrets.choice(alphabet) for _ in range(body.length - len(password)))
    secrets.SystemRandom().shuffle(password)
    return {"password": "".join(password)}
