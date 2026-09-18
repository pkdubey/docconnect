import uuid
from typing import Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/files", tags=["Files"])


class FileMetaOut(BaseModel):
    id: str
    filename: str
    content_type: str
    size: Optional[int]
    folder: str
    uploaded_by: str
    created_at: str


class SignedUrlOut(BaseModel):
    id: str
    signed_url: str
    expires_in: int


@router.post("/upload/", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """Upload a file (photo/CV/credential) — returns file_id for use in profile/job fields."""
    from apps.core.services.storage import upload_file_to_s3

    ALLOWED = (
        "image/jpeg", "image/png", "image/webp",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    await file.seek(0)

    file_id = await upload_file_to_s3(file, folder="uploads")

    def _store_meta():
        meta = current_user.metadata.get("uploaded_files", [])
        meta.append({
            "id": str(file_id),
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(data),
            "folder": "uploads",
        })
        current_user.metadata["uploaded_files"] = meta
        current_user.save(update_fields=["metadata"])

    await sync_to_async(_store_meta, thread_sensitive=True)()
    return {"success": True, "file_id": str(file_id), "filename": file.filename}


@router.get("/{file_id}/", response_model=FileMetaOut)
async def get_file_metadata(file_id: str, current_user=Depends(get_current_user)):
    """Get file metadata by ID."""
    def _get():
        for f in current_user.metadata.get("uploaded_files", []):
            if f["id"] == file_id:
                return f
        return None

    meta = await sync_to_async(_get, thread_sensitive=True)()
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    return FileMetaOut(
        id=meta["id"], filename=meta["filename"],
        content_type=meta["content_type"], size=meta.get("size"),
        folder=meta.get("folder", "uploads"),
        uploaded_by=str(current_user.id),
        created_at="",
    )


@router.get("/{file_id}/signed-url/", response_model=SignedUrlOut)
async def get_signed_url(file_id: str, current_user=Depends(get_current_user)):
    """Get a short-lived signed URL for a private file."""
    from django.conf import settings
    import boto3
    from botocore.exceptions import ClientError

    def _check():
        for f in current_user.metadata.get("uploaded_files", []):
            if f["id"] == file_id:
                return f
        return None

    meta = await sync_to_async(_check, thread_sensitive=True)()
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", ""),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", ""),
            region_name=getattr(settings, "AWS_S3_REGION_NAME", "ap-south-1"),
        )
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "docconnect-media")
        key = f"uploads/{file_id}"
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )
    except Exception:
        url = f"/media/uploads/{file_id}"

    return SignedUrlOut(id=file_id, signed_url=url, expires_in=3600)


@router.delete("/{file_id}/", status_code=204)
async def delete_file(file_id: str, current_user=Depends(get_current_user)):
    """Delete a file by ID."""
    def _delete():
        files = current_user.metadata.get("uploaded_files", [])
        new_files = [f for f in files if f["id"] != file_id]
        if len(new_files) == len(files):
            raise HTTPException(status_code=404, detail="File not found")
        current_user.metadata["uploaded_files"] = new_files
        current_user.save(update_fields=["metadata"])

    try:
        await sync_to_async(_delete, thread_sensitive=True)()
    except HTTPException:
        raise
