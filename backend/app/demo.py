"""Public demo login: throwaway sandbox accounts seeded with sample data.

Each demo login creates an isolated ``demo-*`` user so visitors can freely add,
drag, and edit without touching real data or each other's sandbox — and without
Google sign-in (which needs OAuth verification for the Gmail scope).
"""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app import models

# (company, position, final_status, created_days_ago, follow_up_in_days | None)
_DEMO_APPLICATIONS = [
    ("Stripe", "Software Engineer Intern", "interview", 21, 2),
    ("Datadog", "Backend Engineer Intern", "screening", 12, 5),
    ("Airbnb", "Full-Stack Intern", "applied", 5, 10),
    ("Notion", "Frontend Engineer Intern", "offer", 34, None),
    ("Figma", "Product Engineer Intern", "rejected", 40, None),
    ("Ramp", "Software Engineer Intern", "interview", 17, 1),
    ("Vercel", "Developer Experience Intern", "applied", 3, 7),
    ("Linear", "Software Engineer Intern", "screening", 9, 4),
]

# The status path each application walks, so its activity timeline looks real.
_PROGRESSION = {
    "applied": ["applied"],
    "screening": ["applied", "screening"],
    "interview": ["applied", "screening", "interview"],
    "offer": ["applied", "screening", "interview", "offer"],
    "rejected": ["applied", "screening", "rejected"],
}


def create_demo_user(db: Session) -> models.User:
    """Create a fresh demo user seeded with sample applications."""
    suffix = secrets.token_hex(6)
    user = models.User(
        google_sub=f"demo-{suffix}",
        email=f"demo+{suffix}@offerflow.app",
        name="Demo User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _seed_applications(db, user.id)
    return user


def _seed_applications(db: Session, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    for company, position, status, created_days_ago, follow_up_in in _DEMO_APPLICATIONS:
        created_at = now - timedelta(days=created_days_ago)
        follow_up = (
            (now + timedelta(days=follow_up_in)).date()
            if follow_up_in is not None
            else None
        )
        application = models.Application(
            user_id=user_id,
            company=company,
            position=position,
            status=status,
            source="manual",
            follow_up_date=follow_up,
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(application)
        db.flush()  # assign application.id for the status events below

        path = _PROGRESSION[status]
        previous = None
        for index, stage in enumerate(path):
            # Spread events evenly between the created date and now.
            offset = int(index * created_days_ago / max(len(path), 1))
            event_at = min(created_at + timedelta(days=offset), now)
            db.add(
                models.StatusEvent(
                    application_id=application.id,
                    from_status=previous,
                    to_status=stage,
                    created_at=event_at,
                )
            )
            previous = stage
    db.commit()
