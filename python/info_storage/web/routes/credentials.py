from fastapi import APIRouter, HTTPException, Request, Response, status

from info_storage.web.schemas import Credential, CredentialsInput
from info_storage.web.sessions import SessionDependency

router = APIRouter(prefix="/credentials", tags=["Credenciais"])


@router.get("", response_model=list[Credential])
def list_credentials(
    request: Request,
    session: SessionDependency,
) -> list[dict]:
    with session.lock:
        return request.app.state.account_store.list_items(session, "credentials")


@router.post("", response_model=Credential, status_code=status.HTTP_201_CREATED)
def create_credential(
    request: Request,
    body: CredentialsInput,
    session: SessionDependency,
) -> dict:
    with session.lock:
        return request.app.state.account_store.create_item(
            session, "credentials", body.model_dump()
        )


@router.get("/{credential_id}", response_model=Credential)
def get_credential(
    request: Request,
    credential_id: str,
    session: SessionDependency,
) -> dict:
    with session.lock:
        item = request.app.state.account_store.get_item(
            session, "credentials", credential_id
        )
    if item is None:
        raise HTTPException(status_code=404, detail="Credencial não encontrada.")
    return item


@router.put("/{credential_id}", response_model=Credential)
def update_credential(
    request: Request,
    credential_id: str,
    body: CredentialsInput,
    session: SessionDependency,
) -> dict:
    with session.lock:
        item = request.app.state.account_store.update_item(
            session, "credentials", credential_id, body.model_dump()
        )
    if item is None:
        raise HTTPException(status_code=404, detail="Credencial não encontrada.")
    return item


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credential(
    request: Request,
    credential_id: str,
    session: SessionDependency,
) -> Response:
    with session.lock:
        deleted = request.app.state.account_store.delete_item(
            session, "credentials", credential_id
        )
    if not deleted:
        raise HTTPException(status_code=404, detail="Credencial não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
