import httpx
from django.conf import settings


async def send_otp_sms(phone: str, otp: str) -> bool:
    provider = getattr(settings, 'SMS_PROVIDER', 'msg91')
    if provider == 'msg91':
        return await _send_msg91(phone, otp)
    return await _send_twilio(phone, otp)


async def _send_msg91(phone: str, otp: str) -> bool:
    url = "https://api.msg91.com/api/v5/otp"
    params = {
        "template_id": settings.SMS_OTP_TEMPLATE_ID,
        "mobile": f"91{phone}",
        "authkey": settings.SMS_API_KEY,
        "otp": otp,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=params, timeout=10)
        return resp.status_code == 200


async def _send_twilio(phone: str, otp: str) -> bool:
    from twilio.rest import Client
    client = Client(settings.SMS_API_KEY, getattr(settings, 'SMS_AUTH_TOKEN', ''))
    client.messages.create(
        body=f"Your DocConnect OTP is {otp}. Valid for 5 minutes.",
        from_=getattr(settings, 'TWILIO_FROM_NUMBER', ''),
        to=f"+91{phone}",
    )
    return True
