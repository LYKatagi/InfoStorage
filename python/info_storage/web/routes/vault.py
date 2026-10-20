from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from info_storage.web.sessions import SessionDependency

router = APIRouter(tags=["Cofre"])


@router.get("/vault/summary")
def vault_summary(
    request: Request,
    session: SessionDependency,
) -> dict[str, int | str]:
    with session.lock:
        store = request.app.state.account_store
        credentials = store.list_items(session, "credentials")
        notes = store.list_items(session, "notes")
    return {
        "username": session.username,
        "credential_count": len(credentials),
        "note_count": len(notes),
    }


@router.get("/search")
def search_vault(
    request: Request,
    session: SessionDependency,
    q: str = Query(min_length=2, max_length=120),
    collection: Literal["all", "credentials", "notes"] = "all",
) -> list[dict[str, str | list[str]]]:
    query = q.casefold().strip()
    if len(query) < 2:
        raise HTTPException(status_code=422, detail="Informe ao menos dois caracteres, difícil em")
    collections = ("credentials", "notes") if collection == "all" else (collection,)

    matches = []
    with session.lock:
        store = request.app.state.account_store
        for name in collections:
            for item in store.list_items(session, name):
                searchable_fields = (
                    {
                        "title": item.get("title", ""),
                        "username": item.get("username", ""),
                        "notes": item.get("notes", ""),
                    }
                    if name == "credentials"
                    else {
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                    }
                )
                matched_fields = [
                    field
                    for field, value in searchable_fields.items()
                    if isinstance(value, str) and query in value.casefold()
                ]
                if matched_fields:
                    matches.append(
                        {
                            "id": item["id"],
                            "collection": name,
                            "title": item.get("title", "Sem título"),
                            "matched_fields": matched_fields,
                        }
                    )
    return matches
