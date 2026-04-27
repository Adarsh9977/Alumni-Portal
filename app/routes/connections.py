# app/routes/connections.py - API routes for networking connections

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Connection
from ..schemas import ConnectionCreate, ConnectionUpdate, ConnectionResponse
from ..dependencies import get_current_user
from ..cache import get_or_set, invalidate_namespaces, make_cache_key

router = APIRouter(prefix="/api/connections", tags=["connections"])


@router.post("/", response_model=ConnectionResponse)
def send_connection_request(
    connection: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a connection request to another user."""
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == connection.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")

    if receiver.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot connect with yourself")

    # Check if a connection already exists
    existing = db.query(Connection).filter(
        ((Connection.sender_id == current_user.id) & (Connection.receiver_id == connection.receiver_id)) |
        ((Connection.sender_id == connection.receiver_id) & (Connection.receiver_id == current_user.id))
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Connection/Request already exists")

    new_connection = Connection(sender_id=current_user.id, receiver_id=connection.receiver_id)
    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)
    invalidate_namespaces("users", "connections", "messages")

    # Attach names for response
    new_connection.sender_name = current_user.name
    new_connection.receiver_name = receiver.name
    return new_connection


@router.get("/pending", response_model=List[ConnectionResponse])
def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pending connection requests for the current user."""
    cache_key = make_cache_key("connections", "pending", current_user.id)

    def load_pending():
        requests = db.query(Connection).filter(
            Connection.receiver_id == current_user.id,
            Connection.status == "pending"
        ).all()
        sender_ids = [request.sender_id for request in requests]
        senders = db.query(User).filter(User.id.in_(sender_ids)).all() if sender_ids else []
        senders_by_id = {sender.id: sender for sender in senders}
        return [
            {
                "id": r.id,
                "sender_id": r.sender_id,
                "receiver_id": r.receiver_id,
                "status": r.status,
                "created_at": r.created_at,
                "sender_name": senders_by_id[r.sender_id].name if r.sender_id in senders_by_id else None,
                "receiver_name": current_user.name
            }
            for r in requests
        ]

    return get_or_set(cache_key, load_pending)


@router.put("/{connection_id}/status", response_model=ConnectionResponse)
def update_connection_status(
    connection_id: int,
    update: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept or reject a connection request."""
    conn = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.receiver_id == current_user.id
    ).first()

    if not conn:
        raise HTTPException(status_code=404, detail="Connection request not found")

    if conn.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    conn.status = update.status
    db.commit()
    db.refresh(conn)
    invalidate_namespaces("users", "connections", "messages")

    # Attach names for response
    conn.sender_name = db.query(User.name).filter(User.id == conn.sender_id).scalar()
    conn.receiver_name = current_user.name
    return conn


@router.get("/my", response_model=List[ConnectionResponse])
def get_my_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accepted connections for the current user."""
    cache_key = make_cache_key("connections", "my", current_user.id)

    def load_connections():
        connections = db.query(Connection).filter(
            ((Connection.sender_id == current_user.id) | (Connection.receiver_id == current_user.id)),
            Connection.status == "accepted"
        ).all()
        user_ids = {c.sender_id for c in connections} | {c.receiver_id for c in connections}
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        users_by_id = {user.id: user for user in users}
        return [
            {
                "id": c.id,
                "sender_id": c.sender_id,
                "receiver_id": c.receiver_id,
                "status": c.status,
                "created_at": c.created_at,
                "sender_name": users_by_id[c.sender_id].name if c.sender_id in users_by_id else None,
                "receiver_name": users_by_id[c.receiver_id].name if c.receiver_id in users_by_id else None
            }
            for c in connections
        ]

    return get_or_set(cache_key, load_connections)


@router.get("/count", response_model=dict)
def get_connection_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the total number of accepted connections for the current user."""
    cache_key = make_cache_key("connections", "count", current_user.id)
    return get_or_set(
        cache_key,
        lambda: {
            "count": db.query(Connection).filter(
                ((Connection.sender_id == current_user.id) | (Connection.receiver_id == current_user.id)),
                Connection.status == "accepted"
            ).count()
        }
    )


@router.get("/status/{other_user_id}")
def get_connection_status(
    other_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the connection status between current user and another user."""
    cache_key = make_cache_key("connections", "status", current_user.id, other_user_id)

    def load_status():
        conn = db.query(Connection).filter(
            ((Connection.sender_id == current_user.id) & (Connection.receiver_id == other_user_id)) |
            ((Connection.sender_id == other_user_id) & (Connection.receiver_id == current_user.id))
        ).first()
        if not conn:
            return {"status": "none"}
        return {
            "status": conn.status,
            "is_sender": conn.sender_id == current_user.id,
            "connection_id": conn.id
        }

    return get_or_set(cache_key, load_status)
