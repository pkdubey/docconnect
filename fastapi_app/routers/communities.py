from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, Form, HTTPException, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/communities", tags=["Communities"])


class CommunityOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    specialty_id: Optional[str]
    member_count: int
    is_member: bool
    created_at: str


class CommunityPostOut(BaseModel):
    id: str
    author: str
    content: str
    post_type: str
    like_count: int
    comment_count: int
    created_at: str


class SuccessOut(BaseModel):
    success: bool
    message: str


@router.get("/", response_model=List[CommunityOut])
async def list_communities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.core.models import Community, CommunityMember

    def _list():
        qs = Community.objects.filter(is_active=True).order_by('name')
        total = qs.count()
        communities = list(qs[(page - 1) * page_size: page * page_size])
        member_ids = set(
            CommunityMember.objects.filter(user=current_user, community__in=communities)
            .values_list('community_id', flat=True)
        )
        return communities, member_ids

    try:
        communities, member_ids = await sync_to_async(_list, thread_sensitive=True)()
    except Exception:
        return []

    return [CommunityOut(
        id=str(c.id), name=c.name, description=c.description,
        specialty_id=str(c.specialty_id) if getattr(c, 'specialty_id', None) else None,
        member_count=getattr(c, 'member_count', 0),
        is_member=c.id in member_ids,
        created_at=c.created_at.isoformat(),
    ) for c in communities]


@router.get("/{community_id}/", response_model=CommunityOut)
async def get_community(community_id: str, current_user=Depends(get_current_user)):
    from apps.core.models import Community, CommunityMember

    def _get():
        try:
            c = Community.objects.get(id=community_id, is_active=True)
        except Community.DoesNotExist:
            raise HTTPException(status_code=404, detail="Community not found")
        is_member = CommunityMember.objects.filter(user=current_user, community=c).exists()
        return c, is_member

    try:
        c, is_member = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return CommunityOut(
        id=str(c.id), name=c.name, description=c.description,
        specialty_id=str(c.specialty_id) if getattr(c, 'specialty_id', None) else None,
        member_count=getattr(c, 'member_count', 0),
        is_member=is_member,
        created_at=c.created_at.isoformat(),
    )


@router.post("/{community_id}/join/", response_model=SuccessOut, status_code=201)
async def join_community(community_id: str, current_user=Depends(get_current_user)):
    from apps.core.models import Community, CommunityMember

    def _join():
        try:
            c = Community.objects.get(id=community_id, is_active=True)
        except Community.DoesNotExist:
            raise HTTPException(status_code=404, detail="Community not found")
        CommunityMember.objects.get_or_create(user=current_user, community=c)

    try:
        await sync_to_async(_join, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Joined community")


@router.delete("/{community_id}/leave/", response_model=SuccessOut)
async def leave_community(community_id: str, current_user=Depends(get_current_user)):
    from apps.core.models import Community, CommunityMember

    def _leave():
        try:
            c = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            raise HTTPException(status_code=404, detail="Community not found")
        CommunityMember.objects.filter(user=current_user, community=c).delete()

    try:
        await sync_to_async(_leave, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Left community")


@router.get("/{community_id}/posts/", response_model=List[CommunityPostOut])
async def community_posts(
    community_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.doctors.models import Post

    def _list():
        qs = Post.objects.filter(
            metadata__community_id=community_id
        ).select_related('author', 'posted_by').order_by('-created_at')
        return list(qs[(page - 1) * page_size: page * page_size])

    try:
        posts = await sync_to_async(_list, thread_sensitive=True)()
    except Exception:
        posts = []

    return [CommunityPostOut(
        id=str(p.id), author=p.display_name,
        content=p.content, post_type=p.post_type,
        like_count=p.likes.count(), comment_count=p.comments.count(),
        created_at=p.created_at.isoformat(),
    ) for p in posts]


@router.post("/{community_id}/posts/", status_code=201)
async def post_in_community(
    community_id: str,
    content: str = Form(...),
    post_type: str = Form("UPDATE"),
    current_user=Depends(get_current_user),
):
    from apps.core.models import Community, CommunityMember
    from apps.doctors.models import Post

    def _create():
        try:
            c = Community.objects.get(id=community_id, is_active=True)
        except Community.DoesNotExist:
            raise HTTPException(status_code=404, detail="Community not found")
        if not CommunityMember.objects.filter(user=current_user, community=c).exists():
            raise HTTPException(status_code=403, detail="Join the community first")
        doctor_profile = None
        if current_user.user_type == 'DOCTOR':
            try:
                doctor_profile = current_user.doctor_profile
            except Exception:
                pass
        post = Post.objects.create(
            author=doctor_profile, posted_by=current_user,
            post_type=post_type, content=content.strip(),
            metadata={"community_id": community_id},
        )
        return post

    try:
        post = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "post_id": str(post.id)}
