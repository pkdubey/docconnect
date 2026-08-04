import uuid
import boto3
from django.conf import settings


async def upload_file_to_s3(file, folder: str = "uploads") -> uuid.UUID:
    file_id = uuid.uuid4()
    ext = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'bin'
    key = f"{folder}/{file_id}.{ext}"

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    content = await file.read()
    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Body=content,
        ContentType=file.content_type,
    )
    return file_id


def get_presigned_url(file_id: uuid.UUID, folder: str = "uploads", ext: str = "jpg", expires: int = 3600) -> str:
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    key = f"{folder}/{file_id}.{ext}"
    return s3.generate_presigned_url('get_object', Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key}, ExpiresIn=expires)
