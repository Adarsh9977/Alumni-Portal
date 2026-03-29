# routes/events.py - Event management routes

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Event, EventParticipant
from ..schemas import EventCreate, EventResponse
from ..dependencies import get_current_user, require_alumni_or_admin

router = APIRouter(prefix="/api/events", tags=["Events"])


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
    events = db.query(Event).filter(Event.is_active == True).order_by(Event.date.desc()).all()
    
    result = []
    for event in events:
        organizer = db.query(User).filter(User.id == event.organized_by).first()
        participant_count = db.query(EventParticipant).filter(EventParticipant.event_id == event.id).count()
        is_registered = db.query(EventParticipant).filter(
            EventParticipant.event_id == event.id, EventParticipant.user_id == current_user.id
        ).first() is not None
        
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date,
            "time": event.time,
            "location": event.location,
            "event_type": event.event_type,
            "organized_by": event.organized_by,
            "organizer_name": organizer.name if organizer else "Unknown",
            "is_active": event.is_active,
            "participant_count": participant_count,
            "is_registered": is_registered,
            "created_at": str(event.created_at) if event.created_at else None
        })
    
    return result


@router.get("/{event_id}", response_model=dict)
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific event by ID with participants."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    organizer = db.query(User).filter(User.id == event.organized_by).first()
    is_registered = db.query(EventParticipant).filter(
        EventParticipant.event_id == event.id, EventParticipant.user_id == current_user.id
    ).first() is not None
    
    participants = db.query(EventParticipant).filter(EventParticipant.event_id == event.id).all()
    participant_list = []
    for p in participants:
        u = db.query(User).filter(User.id == p.user_id).first()
        if u:
            participant_list.append({
                "id": u.id,
                "name": u.name,
                "role": u.role,
                "company": u.company,
                "batch": u.batch
            })
    
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date,
        "time": event.time,
        "location": event.location,
        "event_type": event.event_type,
        "organized_by": event.organized_by,
        "organizer_name": organizer.name if organizer else "Unknown",
        "is_registered": is_registered,
        "participant_count": len(participant_list),
        "participants": participant_list,
        "is_active": event.is_active,
        "created_at": str(event.created_at) if event.created_at else None
    }


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
        return {"message": "unregistered", "is_registered": False}
    else:
        new_p = EventParticipant(event_id=event_id, user_id=current_user.id)
        db.add(new_p)
        db.commit()
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
    
    return {"message": "Event deleted successfully"}
