import uuid
from typing import Optional
from datetime import datetime

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(tags=["Billing"])

PLANS = [
    {"id": "plan_basic", "name": "Basic", "price": 0, "currency": "INR", "features": ["5 job posts/month", "Basic analytics"]},
    {"id": "plan_pro", "name": "Pro", "price": 4999, "currency": "INR", "features": ["Unlimited job posts", "Advanced analytics", "Priority support"]},
    {"id": "plan_enterprise", "name": "Enterprise", "price": 14999, "currency": "INR", "features": ["Everything in Pro", "Dedicated account manager", "Custom integrations"]},
]


class SubscribeRequest(BaseModel):
    plan_id: str
    payment_method: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    cancel: Optional[bool] = False


def _get_hospital(current_user):
    from apps.hospitals.models import HospitalUser
    try:
        return HospitalUser.objects.select_related('hospital').get(user=current_user)
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=403, detail="Not associated with a hospital")


@router.get("/api/v1/billing/plans/")
async def list_billing_plans(current_user=Depends(get_current_user)):
    # Billing is Hospital Admin only — HR/Recruiter/Doctor must not access
    if current_user.user_type not in ('HOSPITAL_ADMIN', 'ADMIN'):
        raise HTTPException(status_code=403, detail="Hospital Admin access required")
    return {"results": PLANS}


@router.get("/api/v1/billing/subscription/")
async def get_subscription(current_user=Depends(get_current_user)):
    def _get():
        hu = _get_hospital(current_user)
        sub = hu.hospital.metadata.get("subscription", {})
        return sub

    try:
        sub = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    if not sub:
        return {"plan_id": "plan_basic", "status": "ACTIVE", "started_at": None, "expires_at": None}
    return sub


@router.post("/api/v1/billing/subscription/", status_code=201)
async def subscribe(body: SubscribeRequest, current_user=Depends(get_current_user)):
    plan = next((p for p in PLANS if p["id"] == body.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    def _subscribe():
        hu = _get_hospital(current_user)
        h = hu.hospital
        h.metadata["subscription"] = {
            "id": str(uuid.uuid4()),
            "plan_id": body.plan_id,
            "plan_name": plan["name"],
            "status": "ACTIVE",
            "started_at": datetime.now().isoformat(),
            "expires_at": None,
        }
        h.save(update_fields=["metadata"])
        return h.metadata["subscription"]

    try:
        sub = await sync_to_async(_subscribe, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "subscription": sub}


@router.patch("/api/v1/billing/subscription/")
async def update_subscription(body: SubscriptionUpdate, current_user=Depends(get_current_user)):
    def _update():
        hu = _get_hospital(current_user)
        h = hu.hospital
        sub = h.metadata.get("subscription", {})
        if body.cancel:
            sub["status"] = "CANCELLED"
        if body.plan_id:
            plan = next((p for p in PLANS if p["id"] == body.plan_id), None)
            if plan:
                sub["plan_id"] = body.plan_id
                sub["plan_name"] = plan["name"]
        h.metadata["subscription"] = sub
        h.save(update_fields=["metadata"])
        return sub

    try:
        sub = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "subscription": sub}


@router.get("/api/v1/billing/invoices/")
async def list_invoices(current_user=Depends(get_current_user)):
    def _list():
        hu = _get_hospital(current_user)
        return hu.hospital.metadata.get("invoices", [])

    try:
        invoices = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"total": len(invoices), "invoices": invoices}


@router.get("/api/v1/billing/invoices/{invoice_id}/")
async def get_invoice(invoice_id: str, current_user=Depends(get_current_user)):
    def _get():
        hu = _get_hospital(current_user)
        for inv in hu.hospital.metadata.get("invoices", []):
            if inv["id"] == invoice_id:
                return inv
        return None

    try:
        inv = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.post("/api/v1/billing/webhooks/{provider}/", status_code=200)
async def payment_webhook(provider: str, request: Request):
    """Idempotent payment webhook handler for Razorpay/Stripe/etc."""
    payload = await request.json()
    # In production: verify signature, process event, update subscription/invoice
    return {"success": True, "provider": provider, "received": True}


@router.post("/api/v1/admin/billing/refunds/")
async def issue_refund(
    invoice_id: str,
    amount: Optional[float] = None,
    reason: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return {
        "success": True,
        "refund_id": str(uuid.uuid4()),
        "invoice_id": invoice_id,
        "amount": amount,
        "reason": reason,
        "status": "PROCESSED",
    }
