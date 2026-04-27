# routes/events.py - Event management routes

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from ..models import User, Event, EventParticipant
from ..schemas import EventCreate, EventResponse
from ..dependencies import get_current_user, require_alumni_or_admin
from ..cache import get_or_set, invalidate_namespace, make_cache_key

router = APIRouter(prefix="/api/events", tags=["Events"])


def _serialize_events(db: Session, events: list[Event], current_user_id: int) -> list[dict]:
    event_ids = [event.id for event in events]
    organizer_ids = {event.organized_by for event in events}
    organizers = db.query(User).filter(User.id.in_(organizer_ids)).all() if organizer_ids else []
    organizers_by_id = {organizer.id: organizer for organizer in organizers}
    participant_counts = dict(
        db.query(EventParticipant.event_id, func.count(EventParticipant.id)).filter(
            EventParticipant.event_id.in_(event_ids)
        ).group_by(EventParticipant.event_id).all()
    ) if event_ids else {}
    registered_event_ids = {
        event_id for (event_id,) in db.query(EventParticipant.event_id).filter(
            EventParticipant.event_id.in_(event_ids),
            EventParticipant.user_id == current_user_id
        ).all()
    } if event_ids else set()

    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date,
            "time": event.time,
            "location": event.location,
            "event_type": event.event_type,
            "organized_by": event.organized_by,
            "organizer_name": organizers_by_id[event.organized_by].name if event.organized_by in organizers_by_id else "Unknown",
            "is_active": event.is_active,
            "participant_count": participant_counts.get(event.id, 0),
            "is_registered": event.id in registered_event_ids,
            "created_at": str(event.created_at) if event.created_at else None
        }
        for event in events
    ]


@router.post("/", response_model=dict)
def create_event(
    event_data: EventCreate,
    current_user: User = Depends(require_alumni_or_admin),
    db: Session = Depends(get_db)
):
    """Create a new event - Alumni and Admin only."""
    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        date=event_data.date,
        time=event_data.time,
        location=event_data.location,
        event_type=event_data.event_type,
        organized_by=current_user.id
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    invalidate_namespace("events")
    
    return {
        "message": "Event created successfully",
        "event": {
            "id": new_event.id,
            "title": new_event.title,
            "date": new_event.date
        }
    }


@router.get("/", response_model=List[dict])
def get_all_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active events, ordered by date."""
    cache_key = make_cache_key("events", "all", current_user.id)
    return get_or_set(
        cache_key,
        lambda: _serialize_events(
            db,
            db.query(Event).filter(Event.is_active == True).order_by(Event.date.desc()).all(),
            current_user.id
        )
    )


@router.get("/{event_id}", response_model=dict)
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific event by ID with participants."""
    cache_key = make_cache_key("events", "one", event_id, current_user.id)

    def load_event():
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        event_data = _serialize_events(db, [event], current_user.id)[0]
        participants = db.query(EventParticipant).filter(EventParticipant.event_id == event.id).all()
        user_ids = [participant.user_id for participant in participants]
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        event_data["participants"] = [
            {
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "company": user.company,
                "batch": user.batch
            }
            for user in users
        ]
        event_data["participant_count"] = len(event_data["participants"])
        return event_data

    return get_or_set(cache_key, load_event)


@router.post("/{event_id}/rsvp", response_model=dict)
def rsvp_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register for an event (Toggle RSVP)."""
    event = db.query(Event).filter(Event.id == event_id, Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    existing = db.query(EventParticipant).filter(
        EventParticipant.event_id == event_id, 
        EventParticipant.user_id == current_user.id
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
        invalidate_namespace("events")
        return {"message": "unregistered", "is_registered": False}
    else:
        new_p = EventParticipant(event_id=event_id, user_id=current_user.id)
        db.add(new_p)
        db.commit()
        invalidate_namespace("events")
        return {"message": "registered", "is_registered": True}


@router.put("/{event_id}", response_model=dict)
def update_event(
    event_id: int,
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an event - only the organizer or admin can update."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.organized_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this event"
        )
    
    event.title = event_data.title
    event.description = event_data.description
    event.date = event_data.date
    event.time = event_data.time
    event.location = event_data.location
    event.event_type = event_data.event_type
    
    db.commit()
    db.refresh(event)
    invalidate_namespace("events")
    
    return {"message": "Event updated successfully"}


@router.delete("/{event_id}", response_model=dict)
def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an event - only the organizer or admin can delete."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.organized_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this event"
        )
    
    db.delete(event)
    db.commit()
    invalidate_namespace("events")
    
    return {"message": "Event deleted successfully"}
