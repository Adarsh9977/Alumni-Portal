from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List

from ..database import get_db
from ..models import User, Message, Connection
from ..schemas import MessageCreate, MessageResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/messages", tags=["Messages"])

@router.post("/", response_model=dict)
def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a direct message to another user."""
    # Ensure receiver exists
    receiver = db.query(User).filter(User.id == message_data.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_msg = Message(
        sender_id=current_user.id,
        receiver_id=message_data.receiver_id,
        content=message_data.content
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    return {
        "message": "Message sent",
        "data": {
            "id": new_msg.id,
            "sender_id": new_msg.sender_id,
            "receiver_id": new_msg.receiver_id,
            "content": new_msg.content,
            "created_at": str(new_msg.created_at) if new_msg.created_at else None
        }
    }


# IMPORTANT: /conversations must come BEFORE /{other_user_id} so FastAPI
# doesn't try to parse "conversations" as an integer user ID.
@router.get("/conversations", response_model=List[dict])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users whom the current user has chatted with, plus all accepted connections."""
    # Find all unique user IDs that the current user has sent messages to or received from
    sent_to = db.query(Message.receiver_id).filter(Message.sender_id == current_user.id).distinct().all()
    received_from = db.query(Message.sender_id).filter(Message.receiver_id == current_user.id).distinct().all()
    
    chat_user_ids = set([u[0] for u in sent_to] + [u[0] for u in received_from])
    
    # Also include all accepted connections so users have someone to message
    accepted_conns = db.query(Connection).filter(
        or_(
            Connection.sender_id == current_user.id,
            Connection.receiver_id == current_user.id
        ),
        Connection.status == "accepted"
    ).all()
    for c in accepted_conns:
        peer_id = c.receiver_id if c.sender_id == current_user.id else c.sender_id
        chat_user_ids.add(peer_id)
    
    results = []
    for uid in chat_user_ids:
        peer = db.query(User).filter(User.id == uid).first()
        if peer:
            # Get last message for this conversation
            last_msg = db.query(Message).filter(
                or_(
                    and_(Message.sender_id == current_user.id, Message.receiver_id == uid),
                    and_(Message.sender_id == uid, Message.receiver_id == current_user.id)
                )
            ).order_by(Message.created_at.desc()).first()
            
            unread = db.query(Message).filter(
                Message.sender_id == uid, 
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).count()
            
            results.append({
                "user_id": peer.id,
                "user_name": peer.name,
                "user_role": peer.role,
                "profile_picture": peer.profile_picture,
                "last_message": last_msg.content if last_msg else "",
                "last_message_time": str(last_msg.created_at) if last_msg and last_msg.created_at else None,
                "unread_count": unread
            })
            
    # Sort: conversations with messages first (by time), then connections with no messages
    results.sort(key=lambda x: x['last_message_time'] if x['last_message_time'] else "", reverse=True)
    return results


@router.get("/{other_user_id}", response_model=List[MessageResponse])
def get_messages(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation between current user and another user."""
    msgs = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Mark messages as read
    for m in msgs:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.commit()
    
    return msgs
