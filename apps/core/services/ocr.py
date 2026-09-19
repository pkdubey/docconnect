"""
Hospital document OCR verification service using AWS Textract.

Extracts text from uploaded hospital registration/license documents
and returns structured fields for admin review.

Usage:
    result = await ocr_extract_hospital_document(file_id, s3_key)
    # result: {"raw_text": "...", "extracted_fields": {...}, "confidence": 0.85}
"""
import re
from typing import Any, Dict, Optional


def _extract_fields_from_text(text: str) -> Dict[str, Any]:
    """
    Parse common fields from hospital registration document text.
    Returns best-effort extracted values — admin must confirm.
    """
    fields: Dict[str, Any] = {}
    text_upper = text.upper()

    # Registration / license number patterns
    reg_patterns = [
        r'REG(?:ISTRATION)?\s*(?:NO|NUMBER|#)[:\s.]*([A-Z0-9/\-]{4,30})',
        r'LICENSE\s*(?:NO|NUMBER|#)[:\s.]*([A-Z0-9/\-]{4,30})',
        r'CERT(?:IFICATE)?\s*(?:NO|NUMBER|#)[:\s.]*([A-Z0-9/\-]{4,30})',
    ]
    for pat in reg_patterns:
        m = re.search(pat, text_upper)
        if m:
            fields['registration_number'] = m.group(1).strip()
            break

    # Hospital name — look for lines with "HOSPITAL", "CLINIC", "NURSING HOME"
    name_match = re.search(
        r'([A-Z][A-Z\s&\'.]{3,60}(?:HOSPITAL|CLINIC|NURSING HOME|MEDICAL COLLEGE|HEALTH CARE))',
        text_upper
    )
    if name_match:
        fields['hospital_name'] = name_match.group(1).strip().title()

    # Date patterns (issue date / valid until)
    date_patterns = [
        r'(?:ISSUE|ISSUED|DATE OF ISSUE)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        r'(?:VALID\s*(?:UPTO|UNTIL|TILL))[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
    ]
    for pat in date_patterns:
        m = re.search(pat, text_upper)
        if m:
            fields.setdefault('document_date', m.group(1).strip())
            break

    # State / authority
    state_keywords = [
        'MAHARASHTRA', 'DELHI', 'KARNATAKA', 'TAMIL NADU', 'TELANGANA',
        'GUJARAT', 'RAJASTHAN', 'UTTAR PRADESH', 'WEST BENGAL', 'KERALA',
        'ANDHRA PRADESH', 'MADHYA PRADESH', 'PUNJAB', 'HARYANA', 'BIHAR',
    ]
    for state in state_keywords:
        if state in text_upper:
            fields['state'] = state.title()
            break

    return fields


async def ocr_extract_hospital_document(
    file_id: str,
    s3_key: str,
    bucket: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run AWS Textract on a hospital document stored in S3.
    Returns raw text + extracted fields + confidence score.

    Falls back to a stub response if Textract is unavailable (dev mode).
    """
    from django.conf import settings

    bucket = bucket or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'docconnect-media')
    aws_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
    aws_secret = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
    region = getattr(settings, 'AWS_S3_REGION_NAME', 'ap-south-1')

    if not aws_key or not aws_secret:
        # Dev mode — return stub
        return {
            "file_id": file_id,
            "raw_text": "[OCR unavailable — AWS credentials not configured]",
            "extracted_fields": {},
            "confidence": 0.0,
            "status": "UNAVAILABLE",
            "message": "Configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to enable OCR",
        }

    try:
        import boto3
        textract = boto3.client(
            'textract',
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=region,
        )
        response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': bucket, 'Name': s3_key}}
        )
        blocks = response.get('Blocks', [])
        lines = [
            b['Text'] for b in blocks
            if b['BlockType'] == 'LINE' and 'Text' in b
        ]
        raw_text = '\n'.join(lines)

        # Average confidence across all LINE blocks
        confidences = [
            b.get('Confidence', 0) for b in blocks if b['BlockType'] == 'LINE'
        ]
        avg_confidence = round(sum(confidences) / len(confidences) / 100, 3) if confidences else 0.0

        extracted = _extract_fields_from_text(raw_text)
        return {
            "file_id": file_id,
            "raw_text": raw_text,
            "extracted_fields": extracted,
            "confidence": avg_confidence,
            "status": "SUCCESS",
            "message": f"Extracted {len(lines)} lines, {len(extracted)} fields",
        }

    except Exception as e:
        return {
            "file_id": file_id,
            "raw_text": "",
            "extracted_fields": {},
            "confidence": 0.0,
            "status": "ERROR",
            "message": str(e),
        }
