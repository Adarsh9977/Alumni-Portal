# routes/posts.py - News feed / post routes with likes and comments

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from ..models import User, Post, Comment, Like
from ..schemas import PostCreate, PostResponse, CommentCreate, CommentResponse
from ..dependencies import get_current_user, require_admin
from ..cache import get_or_set, invalidate_namespace, make_cache_key

router = APIRouter(prefix="/api/posts", tags=["Posts"])


def _serialize_posts(posts: list[Post], current_user_id: int, db: Session) -> list[dict]:
    post_ids = [post.id for post in posts]
    author_ids = {post.author_id for post in posts}

    comments = []
    if post_ids:
        comments = db.query(Comment).filter(
            Comment.post_id.in_(post_ids)
        ).order_by(Comment.created_at.asc()).all()
        author_ids.update(comment.author_id for comment in comments)

    users = db.query(User).filter(User.id.in_(author_ids)).all() if author_ids else []
    users_by_id = {user.id: user for user in users}

    like_counts = dict(
        db.query(Like.post_id, func.count(Like.id)).filter(
            Like.post_id.in_(post_ids)
        ).group_by(Like.post_id).all()
    ) if post_ids else {}

    liked_post_ids = {
        post_id for (post_id,) in db.query(Like.post_id).filter(
            Like.post_id.in_(post_ids),
            Like.user_id == current_user_id
        ).all()
    } if post_ids else set()

    comments_by_post: dict[int, list[dict]] = {post_id: [] for post_id in post_ids}
    for comment in comments:
        comment_author = users_by_id.get(comment.author_id)
        comments_by_post.setdefault(comment.post_id, []).append({
            "id": comment.id,
            "content": comment.content,
            "author_id": comment.author_id,
            "author_name": comment_author.name if comment_author else "Unknown",
            "created_at": str(comment.created_at) if comment.created_at else None
        })

    result = []
    for post in posts:
        author = users_by_id.get(post.author_id)
        result.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author_id": post.author_id,
            "author_name": author.name if author else "Unknown",
            "author_role": author.role if author else "unknown",
            "author_pic": author.profile_picture if author else None,
            "is_active": post.is_active,
            "created_at": str(post.created_at) if post.created_at else None,
            "like_count": like_counts.get(post.id, 0),
            "is_liked": post.id in liked_post_ids,
            "comments": comments_by_post.get(post.id, [])
        })
    return result


@router.post("/", response_model=dict)
def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new post in the news feed."""
    new_post = Post(
        title=post_data.title,
        content=post_data.content,
        author_id=current_user.id
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    invalidate_namespace("posts")
    
    return {
        "message": "Post created successfully",
        "post": {
            "id": new_post.id,
            "title": new_post.title,
            "content": new_post.content
        }
    }


@router.get("/", response_model=List[dict])
def get_all_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active posts with like counts and comments."""
    cache_key = make_cache_key("posts", "all", current_user.id)
    return get_or_set(
        cache_key,
        lambda: _serialize_posts(
            db.query(Post).filter(Post.is_active == True).order_by(Post.created_at.desc()).all(),
            current_user.id,
            db
        )
    )


@router.get("/{post_id}", response_model=dict)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific post by ID."""
    cache_key = make_cache_key("posts", "one", post_id, current_user.id)

    def load_post():
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        serialized = _serialize_posts([post], current_user.id, db)[0]
        serialized.pop("author_role", None)
        return serialized

    return get_or_set(cache_key, load_post)


@router.delete("/{post_id}", response_model=dict)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post - only the author or admin can delete."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )
    
    db.delete(post)
    db.commit()
    invalidate_namespace("posts")
    
    return {"message": "Post deleted successfully"}


# ==================== LIKES ====================

@router.post("/{post_id}/like", response_model=dict)
def toggle_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle like on a post (like/unlike)."""
    post = db.query(Post).filter(Post.id == post_id, Post.is_active == True).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    existing_like = db.query(Like).filter(
        Like.post_id == post_id, Like.user_id == current_user.id
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        db.commit()
        liked = False
    else:
        new_like = Like(post_id=post_id, user_id=current_user.id)
        db.add(new_like)
        db.commit()
        liked = True
    invalidate_namespace("posts")
    
    like_count = db.query(Like).filter(Like.post_id == post_id).count()
    
    return {
        "liked": liked,
        "like_count": like_count
    }


# ==================== COMMENTS ====================

@router.post("/{post_id}/comment", response_model=dict)
def add_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a post."""
    post = db.query(Post).filter(Post.id == post_id, Post.is_active == True).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    new_comment = Comment(
        content=comment_data.content,
        post_id=post_id,
        author_id=current_user.id
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    invalidate_namespace("posts")
    
    return {
        "message": "Comment added successfully",
        "comment": {
            "id": new_comment.id,
            "content": new_comment.content,
            "author_name": current_user.name,
            "created_at": str(new_comment.created_at) if new_comment.created_at else None
        }
    }


@router.delete("/comment/{comment_id}", response_model=dict)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a comment - only the author or admin can delete."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Find the post this comment belongs to
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    
    # Authorized if: comment author OR post author OR admin
    is_authorized = (
        comment.author_id == current_user.id or 
        (post and post.author_id == current_user.id) or 
        current_user.role == "admin"
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    db.delete(comment)
    db.commit()
    invalidate_namespace("posts")
    
    return {"message": "Comment deleted successfully"}
