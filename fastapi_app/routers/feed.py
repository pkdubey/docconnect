from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/feed", tags=["Feed & Posts"])


# ── Helpers ───────────────────────────────────────────────────

AVATAR_COLORS = ['#0a66c2', '#e16b00', '#057642', '#cc1016', '#915907', '#6b46c1', '#0891b2', '#be185d']


def _color(pk):
    return AVATAR_COLORS[hash(str(pk)) % len(AVATAR_COLORS)]


def _initials(name: str) -> str:
    parts = name.strip().split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()


def _resolve_author(user):
    name, photo = '', ''
    if user.user_type == 'DOCTOR':
        try:
            dp = user.doctor_profile
            name = f'Dr. {dp.first_name} {dp.last_name}'
            photo = dp.photo_base64 or ''
        except Exception:
            pass
    if not name:
        meta = user.metadata or {}
        first = meta.get('first_name', '').strip()
        last = meta.get('last_name', '').strip()
        name = f'{first} {last}'.strip() or user.get_user_type_display()
    return name, photo


# ── Schemas ───────────────────────────────────────────────────

class StatsOut(BaseModel):
    doctors: int
    hospitals: int
    jobs: int


class UrgentJobOut(BaseModel):
    id: str
    title: str
    hospital_name: str
    hospital_logo: Optional[str]
    job_type: str
    job_type_display: str
    location: Dict[str, Any]
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_visibility: str
    experience_min_years: float
    is_urgent: bool
    posted_at: Optional[str]


class SuggestedDoctorOut(BaseModel):
    id: str
    full_name: str
    headline: Optional[str]
    photo: Optional[str]
    initials: str
    color: str
    location: Optional[Dict[str, Any]]
    experience_years: float
    verification_status: str
    connection_status: Optional[str]    # PENDING / ACCEPTED / DECLINED / WITHDRAWN / null
    connection_id: Optional[str]
    connection_direction: Optional[str]  # sent / received


class HomeSummaryResponse(BaseModel):
    stats: StatsOut
    urgent_jobs: List[UrgentJobOut]
    suggested_doctors: List[SuggestedDoctorOut]
    unread_messages: int
    unread_notifications: int
    pending_connections: int


class ReplyOut(BaseModel):
    id: str
    author: str
    initials: str
    color: str
    photo: Optional[str]
    content: str
    created_at: str
    is_mine: bool


class CommentOut(BaseModel):
    id: str
    author: str
    initials: str
    color: str
    photo: Optional[str]
    content: str
    created_at: str
    is_mine: bool
    replies: List[ReplyOut]


class PostOut(BaseModel):
    id: str
    author: str
    author_id: Optional[str]
    headline: Optional[str]
    initials: str
    color: str
    photo: Optional[str]
    post_type: str
    post_type_display: str
    content: str
    image: Optional[str]
    like_count: int
    comment_count: int
    liked: bool
    is_mine: bool
    created_at: str


class FeedResponse(BaseModel):
    posts: List[PostOut]
    page: int
    page_size: int
    has_more: bool


class CreatePostResponse(BaseModel):
    success: bool
    post_id: str
    author: str
    post_type: str
    content: str
    image: Optional[str]
    created_at: str


class LikeResponse(BaseModel):
    liked: bool
    count: int


class CommentListResponse(BaseModel):
    comments: List[CommentOut]


class CommentCreateResponse(BaseModel):
    id: str
    author: str
    initials: str
    color: str
    photo: Optional[str]
    content: str
    created_at: str
    count: int


class ReplyCreateResponse(BaseModel):
    id: str
    author: str
    initials: str
    color: str
    photo: Optional[str]
    content: str
    created_at: str
    is_mine: bool


class EditPostResponse(BaseModel):
    success: bool
    content: str
    image: Optional[str]


class EditCommentResponse(BaseModel):
    success: bool
    content: str


class DeleteResponse(BaseModel):
    success: bool


# ── 1. Home Summary ───────────────────────────────────────────

@router.get(
    "/home/",
    response_model=HomeSummaryResponse,
    summary="Home page summary",
)
async def home_summary(current_user=Depends(get_current_user)):
    """
    Single API for the mobile home screen — equivalent to LinkedIn's home feed bootstrap.

    Returns in one call:
    - **stats**: total verified doctors, hospitals, published jobs
    - **urgent_jobs**: top 3 urgent published jobs
    - **suggested_doctors**: top 4 verified doctors to connect with
    - **unread_messages**: count of conversations with unread messages
    - **unread_notifications**: count of unread notifications
    - **pending_connections**: incoming pending connection requests (doctors only)
    """
    def _fetch():
        from apps.doctors.models import DoctorProfile, Connection
        from apps.hospitals.models import Hospital
        from apps.jobs.models import JobPost
        from apps.notifications.models import Notification
        from apps.messaging.models import ConversationParticipant
        from django.db.models import Q

        # Stats
        stats = StatsOut(
            doctors=DoctorProfile.objects.filter(verification_status='VERIFIED').count(),
            hospitals=Hospital.objects.filter(verification_status='VERIFIED').count(),
            jobs=JobPost.objects.filter(status='PUBLISHED').count(),
        )

        # Urgent jobs — top 3
        urgent_raw = list(
            JobPost.objects.filter(status='PUBLISHED', is_urgent=True)
            .select_related('hospital')
            .order_by('-published_at')[:3]
        )
        urgent_jobs = [
            UrgentJobOut(
                id=str(j.id),
                title=j.title,
                hospital_name=j.hospital.name,
                hospital_logo=getattr(j.hospital, 'logo_base64', None) or None,
                job_type=j.job_type,
                job_type_display=j.get_job_type_display(),
                location=j.location or {},
                salary_min=float(j.salary_min) if j.salary_min else None,
                salary_max=float(j.salary_max) if j.salary_max else None,
                salary_visibility=j.salary_visibility,
                experience_min_years=float(j.experience_min_years or 0),
                is_urgent=j.is_urgent,
                posted_at=j.published_at.strftime('%b %d') if j.published_at else None,
            )
            for j in urgent_raw
        ]

        # Suggested doctors — top 4 verified, exclude self
        suggested_raw = list(
            DoctorProfile.objects.filter(verification_status='VERIFIED')
            .exclude(user=current_user)
            .order_by('-created_at')[:4]
        )

        # Connection map for suggested doctors
        conn_map = {}
        if current_user.user_type == 'DOCTOR':
            try:
                my_profile = current_user.doctor_profile
                doc_ids = [d.id for d in suggested_raw]
                for c in Connection.objects.filter(
                    Q(sender=my_profile, receiver__in=doc_ids) |
                    Q(receiver=my_profile, sender__in=doc_ids)
                ):
                    other_id = c.receiver_id if c.sender_id == my_profile.id else c.sender_id
                    conn_map[str(other_id)] = {
                        'status': c.status,
                        'id': str(c.id),
                        'direction': 'sent' if c.sender_id == my_profile.id else 'received',
                    }
            except Exception:
                pass

        suggested_doctors = [
            SuggestedDoctorOut(
                id=str(d.id),
                full_name=f'Dr. {d.full_name}',
                headline=d.headline or None,
                photo=d.photo_base64 or None,
                initials=_initials(d.full_name),
                color=_color(d.id),
                location=d.professional_location or None,
                experience_years=float(d.experience_years or 0),
                verification_status=d.verification_status,
                connection_status=conn_map.get(str(d.id), {}).get('status'),
                connection_id=conn_map.get(str(d.id), {}).get('id'),
                connection_direction=conn_map.get(str(d.id), {}).get('direction'),
            )
            for d in suggested_raw
        ]

        # Unread messages
        unread_messages = 0
        try:
            for p in ConversationParticipant.objects.filter(user=current_user, is_active=True).select_related('conversation'):
                last = p.conversation.messages.order_by('-created_at').first()
                if last and last.sender_id != current_user.id:
                    if p.last_read_at is None or last.created_at > p.last_read_at:
                        unread_messages += 1
        except Exception:
            pass

        # Unread notifications
        unread_notifications = 0
        try:
            unread_notifications = Notification.objects.filter(user=current_user, is_read=False).count()
        except Exception:
            pass

        # Pending connection requests (doctor only)
        pending_connections = 0
        if current_user.user_type == 'DOCTOR':
            try:
                pending_connections = Connection.objects.filter(
                    receiver=current_user.doctor_profile, status='PENDING'
                ).count()
            except Exception:
                pass

        return stats, urgent_jobs, suggested_doctors, unread_messages, unread_notifications, pending_connections

    stats, urgent_jobs, suggested_doctors, unread_messages, unread_notifications, pending_connections = \
        await sync_to_async(_fetch, thread_sensitive=True)()

    return HomeSummaryResponse(
        stats=stats,
        urgent_jobs=urgent_jobs,
        suggested_doctors=suggested_doctors,
        unread_messages=unread_messages,
        unread_notifications=unread_notifications,
        pending_connections=pending_connections,
    )


# ── 2. Feed (paginated posts) ─────────────────────────────────

@router.get(
    "/",
    response_model=FeedResponse,
    summary="Get feed posts",
)
async def get_feed(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Posts per page"),
    current_user=Depends(get_current_user),
):
    """
    Paginated feed posts — call after home_summary to populate the post list.

    Each post includes author info, content, image, like/comment counts,
    `liked` (whether current user liked it), and `is_mine` for edit/delete controls.
    """
    from apps.doctors.models import Post, PostLike

    def _fetch():
        offset = (page - 1) * page_size
        posts = list(
            Post.objects.select_related('author', 'posted_by')
            .order_by('-created_at')[offset: offset + page_size]
        )
        liked_ids = set()
        try:
            liked_ids = set(
                str(pl.post_id) for pl in PostLike.objects.filter(liked_by=current_user, post__in=posts)
            )
        except Exception:
            pass
        return posts, liked_ids

    posts, liked_ids = await sync_to_async(_fetch, thread_sensitive=True)()

    result = []
    for p in posts:
        author_id, photo, headline = '', '', ''
        if not p.is_anonymous and p.author:
            author_id = str(p.author.id)
            photo = p.author.photo_base64 or ''
            headline = p.author.headline or ''
        display = p.display_name
        result.append(PostOut(
            id=str(p.id),
            author=display,
            author_id=author_id or None,
            headline=headline or None,
            initials='AN' if p.is_anonymous else _initials(display),
            color='#666' if p.is_anonymous else _color(p.posted_by_id or p.author_id or 0),
            photo=photo or None,
            post_type=p.post_type,
            post_type_display=p.get_post_type_display(),
            content=p.content,
            image=p.image_base64 or None,
            like_count=p.likes.count(),
            comment_count=p.comments.filter(parent__isnull=True).count(),
            liked=str(p.id) in liked_ids,
            is_mine=p.posted_by_id == current_user.id,
            created_at=p.created_at.strftime('%b %d'),
        ))

    return FeedResponse(posts=result, page=page, page_size=page_size, has_more=len(result) == page_size)


# ── 3. Create Post ────────────────────────────────────────────

@router.post(
    "/posts/",
    response_model=CreatePostResponse,
    status_code=201,
    summary="Create a new post",
)
async def create_post(
    content: str = Form(..., description="Post text content"),
    post_type: str = Form("UPDATE", description="UPDATE | CASE | ARTICLE | PHOTO"),
    is_anonymous: bool = Form(False, description="Post anonymously — doctors only, CASE type"),
    image: Optional[UploadFile] = File(None, description="Optional image (JPEG/PNG/WEBP, max 5MB)"),
    current_user=Depends(get_current_user),
):
    """
    Create a new feed post with optional image.

    - **post_type**: `UPDATE` (default) | `CASE` | `ARTICLE` | `PHOTO`
    - **is_anonymous**: only for `CASE` posts by doctors
    """
    import base64
    from apps.doctors.models import Post

    if not content.strip():
        raise HTTPException(status_code=400, detail="Content is required")
    if post_type not in ('UPDATE', 'CASE', 'ARTICLE', 'PHOTO'):
        post_type = 'UPDATE'
    if is_anonymous and current_user.user_type != 'DOCTOR':
        is_anonymous = False

    image_base64 = None
    if image:
        data = await image.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image max 5MB")
        if image.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
            raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP allowed")
        image_base64 = f"data:{image.content_type};base64,{base64.b64encode(data).decode()}"

    def _create():
        doctor_profile = None
        if current_user.user_type == 'DOCTOR':
            try:
                doctor_profile = current_user.doctor_profile
            except Exception:
                raise HTTPException(status_code=400, detail="Doctor profile not found")
        return Post.objects.create(
            author=doctor_profile,
            posted_by=current_user,
            post_type=post_type,
            content=content.strip(),
            image_base64=image_base64,
            is_anonymous=is_anonymous,
        )

    try:
        post = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise

    return CreatePostResponse(
        success=True,
        post_id=str(post.id),
        author=post.display_name,
        post_type=post.get_post_type_display(),
        content=post.content,
        image=post.image_base64 or None,
        created_at='Just now',
    )


# ── 4. Like / Unlike ──────────────────────────────────────────

@router.post(
    "/posts/{post_id}/like/",
    response_model=LikeResponse,
    summary="Like or unlike a post",
)
async def like_post(post_id: str, current_user=Depends(get_current_user)):
    """
    Toggle like on a post.
    - Returns `liked: true` if now liked, `false` if unliked.
    - Returns updated `count`.
    """
    from apps.doctors.models import Post, PostLike

    def _toggle():
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise HTTPException(status_code=404, detail="Post not found")
        like, created = PostLike.objects.get_or_create(
            post=post, liked_by=current_user,
            defaults={'doctor': getattr(current_user, 'doctor_profile', None)},
        )
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        return liked, post.likes.count()

    try:
        liked, count = await sync_to_async(_toggle, thread_sensitive=True)()
    except HTTPException:
        raise
    return LikeResponse(liked=liked, count=count)


# ── 5. Get Comments ───────────────────────────────────────────

@router.get(
    "/posts/{post_id}/comments/",
    response_model=CommentListResponse,
    summary="Get comments for a post",
)
async def get_comments(post_id: str, current_user=Depends(get_current_user)):
    """Returns all top-level comments with nested replies for a post."""
    from apps.doctors.models import Post, PostComment

    def _fetch():
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise HTTPException(status_code=404, detail="Post not found")
        return list(
            PostComment.objects.filter(post=post, parent__isnull=True)
            .select_related('author')
            .prefetch_related('replies__author')
            .order_by('created_at')
        )

    try:
        top_comments = await sync_to_async(_fetch, thread_sensitive=True)()
    except HTTPException:
        raise

    def _build(c) -> CommentOut:
        name, photo = _resolve_author(c.author)
        replies = [
            ReplyOut(
                id=str(r.id),
                author=_resolve_author(r.author)[0],
                initials=_initials(_resolve_author(r.author)[0]),
                color=_color(r.author.id),
                photo=_resolve_author(r.author)[1] or None,
                content=r.content,
                created_at=r.created_at.strftime('%b %d'),
                is_mine=r.author_id == current_user.id,
            ) for r in c.replies.all()
        ]
        return CommentOut(
            id=str(c.id), author=name,
            initials=_initials(name), color=_color(c.author.id),
            photo=photo or None, content=c.content,
            created_at=c.created_at.strftime('%b %d'),
            is_mine=c.author_id == current_user.id,
            replies=replies,
        )

    return CommentListResponse(comments=[_build(c) for c in top_comments])


# ── 6. Add Comment ────────────────────────────────────────────

@router.post(
    "/posts/{post_id}/comments/",
    response_model=CommentCreateResponse,
    status_code=201,
    summary="Add a comment to a post",
)
async def add_comment(
    post_id: str,
    content: str = Form(..., description="Comment text"),
    current_user=Depends(get_current_user),
):
    """Adds a top-level comment. Returns the new comment and updated top-level comment count."""
    from apps.doctors.models import Post, PostComment

    def _create():
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise HTTPException(status_code=404, detail="Post not found")
        if not content.strip():
            raise HTTPException(status_code=400, detail="Comment cannot be empty")
        comment = PostComment.objects.create(post=post, author=current_user, content=content.strip())
        count = post.comments.filter(parent__isnull=True).count()
        return comment, count

    try:
        comment, count = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise

    name, photo = _resolve_author(current_user)
    return CommentCreateResponse(
        id=str(comment.id), author=name,
        initials=_initials(name), color=_color(current_user.id),
        photo=photo or None, content=comment.content,
        created_at='Just now', count=count,
    )


# ── 7. Reply to Comment ───────────────────────────────────────

@router.post(
    "/comments/{comment_id}/reply/",
    response_model=ReplyCreateResponse,
    status_code=201,
    summary="Reply to a comment",
)
async def reply_to_comment(
    comment_id: str,
    content: str = Form(..., description="Reply text"),
    current_user=Depends(get_current_user),
):
    """Adds a threaded reply to an existing top-level comment."""
    from apps.doctors.models import PostComment

    def _create():
        try:
            parent = PostComment.objects.get(id=comment_id)
        except PostComment.DoesNotExist:
            raise HTTPException(status_code=404, detail="Comment not found")
        if not content.strip():
            raise HTTPException(status_code=400, detail="Reply cannot be empty")
        return PostComment.objects.create(
            post=parent.post, author=current_user, parent=parent, content=content.strip()
        )

    try:
        reply = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise

    name, photo = _resolve_author(current_user)
    return ReplyCreateResponse(
        id=str(reply.id), author=name,
        initials=_initials(name), color=_color(current_user.id),
        photo=photo or None, content=reply.content,
        created_at='Just now', is_mine=True,
    )


# ── 8. Edit Post ──────────────────────────────────────────────

@router.patch(
    "/posts/{post_id}/",
    response_model=EditPostResponse,
    summary="Edit a post",
)
async def edit_post(
    post_id: str,
    content: str = Form(..., description="Updated post content"),
    remove_image: bool = Form(False, description="Set true to remove existing image"),
    image: Optional[UploadFile] = File(None, description="New image to replace existing"),
    current_user=Depends(get_current_user),
):
    """Edit your own post. Optionally replace or remove the image."""
    import base64
    from apps.doctors.models import Post

    image_base64 = None
    if image:
        data = await image.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image max 5MB")
        image_base64 = f"data:{image.content_type};base64,{base64.b64encode(data).decode()}"

    def _edit():
        try:
            post = Post.objects.get(id=post_id, posted_by=current_user)
        except Post.DoesNotExist:
            raise HTTPException(status_code=404, detail="Post not found or not yours")
        if not content.strip():
            raise HTTPException(status_code=400, detail="Content is required")
        post.content = content.strip()
        if remove_image:
            post.image_base64 = None
        elif image_base64:
            post.image_base64 = image_base64
        post.save(update_fields=['content', 'image_base64', 'updated_at'])
        return post

    try:
        post = await sync_to_async(_edit, thread_sensitive=True)()
    except HTTPException:
        raise
    return EditPostResponse(success=True, content=post.content, image=post.image_base64 or None)


# ── 9. Delete Post ────────────────────────────────────────────

@router.delete(
    "/posts/{post_id}/",
    response_model=DeleteResponse,
    summary="Delete a post",
)
async def delete_post(post_id: str, current_user=Depends(get_current_user)):
    """Deletes your own post along with all its comments and likes."""
    from apps.doctors.models import Post

    deleted = await sync_to_async(
        lambda: Post.objects.filter(id=post_id, posted_by=current_user).delete()[0],
        thread_sensitive=True,
    )()
    if not deleted:
        raise HTTPException(status_code=404, detail="Post not found or not yours")
    return DeleteResponse(success=True)


# ── 10. Edit Comment / Reply ──────────────────────────────────

@router.patch(
    "/comments/{comment_id}/",
    response_model=EditCommentResponse,
    summary="Edit a comment or reply",
)
async def edit_comment(
    comment_id: str,
    content: str = Form(..., description="Updated comment text"),
    current_user=Depends(get_current_user),
):
    """Edit your own comment or reply."""
    from apps.doctors.models import PostComment

    def _edit():
        try:
            comment = PostComment.objects.get(id=comment_id, author=current_user)
        except PostComment.DoesNotExist:
            raise HTTPException(status_code=404, detail="Comment not found or not yours")
        if not content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        comment.content = content.strip()
        comment.save(update_fields=['content'])
        return comment

    try:
        comment = await sync_to_async(_edit, thread_sensitive=True)()
    except HTTPException:
        raise
    return EditCommentResponse(success=True, content=comment.content)


# ── 11. Delete Comment / Reply ────────────────────────────────

@router.delete(
    "/comments/{comment_id}/",
    response_model=DeleteResponse,
    summary="Delete a comment or reply",
)
async def delete_comment(comment_id: str, current_user=Depends(get_current_user)):
    """Deletes your own comment or reply (and all its child replies)."""
    from apps.doctors.models import PostComment

    deleted = await sync_to_async(
        lambda: PostComment.objects.filter(id=comment_id, author=current_user).delete()[0],
        thread_sensitive=True,
    )()
    if not deleted:
        raise HTTPException(status_code=404, detail="Comment not found or not yours")
    return DeleteResponse(success=True)
