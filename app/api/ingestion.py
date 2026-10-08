import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.security.dependencies import get_current_user
from app.security.models import User
from app.security.access_control import AccessController
from app.services.web_ingestion_service import WebIngestionService
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile
from app.services.spreadsheet_ingestion_service import (
    SpreadsheetIngestionService,
)
from app.services.pdf_ingestion_service import PDFIngestionService
from app.retrieval.vector_store import VectorStore
from app.security.permissions import validate_role_assignment


router = APIRouter(
    prefix="/ingest",
    tags=["Ingestion"],
)

access_controller = AccessController()
web_ingestion_service = WebIngestionService()
spreadsheet_ingestion_service = SpreadsheetIngestionService()
pdf_ingestion_service = PDFIngestionService()
vector_store = VectorStore()


class WebsiteIngestionRequest(BaseModel):
    url: str
    allowed_roles: list[str] | None = None


class WebsiteIngestionResponse(BaseModel):
    source: str
    document_type: str
    chunks_ingested: int


class SpreadsheetIngestionResponse(BaseModel):
    source: str
    document_type: str
    chunks_ingested: int


class PDFIngestionResponse(BaseModel):
    source: str
    document_type: str
    chunks_ingested: int
    allowed_roles: list[str] | None = None


class DocumentDeletionResponse(BaseModel):
    source: str
    deleted_chunks: int


@router.post(
    "/website",
    response_model=WebsiteIngestionResponse,
)
def ingest_website(
    request: WebsiteIngestionRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        access_controller.require_action(
            current_user,
            "ingest",
        )

        roles = validate_role_assignment(
            current_user.role,
            request.allowed_roles,
        )

        return web_ingestion_service.ingest(
            request.url,
            allowed_roles=roles,
)

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

@router.post(
    "/pdf",
    response_model=PDFIngestionResponse,
)
def ingest_pdf(
    file: UploadFile = File(...),
    allowed_roles: str | None = None,
    current_user: User = Depends(get_current_user),
):
    try:
        access_controller.require_action(
            current_user,
            "ingest",
        )

        if not file.filename:
            raise ValueError("A file must be provided.")

        extension = Path(file.filename).suffix.lower()

        if extension != ".pdf":
            raise ValueError(
                "Only PDF files are supported."
            )

        roles = validate_role_assignment(
            current_user.role,
            None,
        )

        if allowed_roles:

            try:
                roles = json.loads(allowed_roles)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "allowed_roles must be a valid JSON array."
                ) from exc

            if not isinstance(roles, list) or not all(
                isinstance(role, str) for role in roles
            ):
                raise ValueError(
                    "allowed_roles must be a JSON array of role names."
                )

            roles = validate_role_assignment(
                current_user.role,
                roles,
            )

            if not roles:
                raise ValueError(
                    "allowed_roles must contain at least one role."
                )

            valid_roles = {
                "employee",
                "manager",
                "hr",
                "admin",
            }

            invalid_roles = set(roles) - valid_roles

            if invalid_roles:
                raise ValueError(
                    f"Invalid roles: {sorted(invalid_roles)}"
                )

        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temporary_file:

            shutil.copyfileobj(
                file.file,
                temporary_file,
            )

            temporary_path = temporary_file.name

        try:
            result = pdf_ingestion_service.ingest(
                temporary_path,
                allowed_roles=roles,
                source_name=file.filename,
            )

            result["source"] = file.filename

            return result

        finally:
            Path(temporary_path).unlink(
                missing_ok=True
            )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

@router.post(
    "/spreadsheet",
    response_model=SpreadsheetIngestionResponse,
)
def ingest_spreadsheet(
    file: UploadFile = File(...),
    allowed_roles: str | None = None,
    current_user: User = Depends(get_current_user),
):
    try:
        access_controller.require_action(
            current_user,
            "ingest",
        )

        if not file.filename:
            raise ValueError("A file must be provided.")

        extension = Path(file.filename).suffix.lower()

        if extension not in {".csv", ".xlsx"}:
            raise ValueError(
                "Supported spreadsheet formats are CSV and XLSX."
            )

        roles = None

        if allowed_roles:
            try:
                roles = json.loads(allowed_roles)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "allowed_roles must be a valid JSON array."
                ) from exc

            if not isinstance(roles, list) or not all(
                isinstance(role, str) for role in roles
            ):
                raise ValueError(
                    "allowed_roles must be a JSON array of role names."
                )

            roles = [
                role.strip().lower()
                for role in roles
                if role.strip()
            ]

            roles = validate_role_assignment(
                current_user.role,
                roles,
            )

        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temporary_file:

            shutil.copyfileobj(
                file.file,
                temporary_file,
            )

            temporary_path = temporary_file.name

        try:
            result = spreadsheet_ingestion_service.ingest(
                temporary_path,
                allowed_roles=roles,
                source_name=file.filename,
            )

            result["source"] = file.filename

            return result

        finally:
            Path(temporary_path).unlink(
                missing_ok=True
            )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.delete(
    "/document/{source}",
    response_model=DocumentDeletionResponse,
)
def delete_document(
    source: str,
    current_user: User = Depends(get_current_user),
):
    try:
        access_controller.require_action(
            current_user,
            "delete",
        )

        source = source.strip()

        if not source:
            raise ValueError(
                "Source cannot be empty."
            )

        result = vector_store.delete_by_source(
            source
        )

        return result

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
