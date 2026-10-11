from fastapi import APIRouter, HTTPException, Request, Response, status

from info_storage.web.schemas import Note, NoteInput
from info_storage.web.sessions import SessionDependency

router = APIRouter(prefix="/notes", tags=["Notas"])


@router.get("", response_model=list[Note])
def list_notes(
    request: Request,
    session: SessionDependency,
) -> list[dict]:
    with session.lock:
        return request.app.state.account_store.list_items(session, "notes")


@router.post("", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(
    request: Request,
    body: NoteInput,
    session: SessionDependency,
) -> dict:
    with session.lock:
        return request.app.state.account_store.create_item(
            session, "notes", body.model_dump()
        )


@router.get("/{note_id}", response_model=Note)
def get_note(
    request: Request,
    note_id: str,
    session: SessionDependency,
) -> dict:
    with session.lock:
        item = request.app.state.account_store.get_item(session, "notes", note_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada.")
    return item


@router.put("/{note_id}", response_model=Note)
def update_note(
    request: Request,
    note_id: str,
    body: NoteInput,
    session: SessionDependency,
) -> dict:
    with session.lock:
        item = request.app.state.account_store.update_item(
            session, "notes", note_id, body.model_dump()
        )
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada.")
    return item


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    request: Request,
    note_id: str,
    session: SessionDependency,
) -> Response:
    with session.lock:
        deleted = request.app.state.account_store.delete_item(session, "notes", note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Nota não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
