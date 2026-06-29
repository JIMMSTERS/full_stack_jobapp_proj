"""Database access functions (CRUD) for applications."""

from sqlalchemy.orm import Session

from app import models, schemas


def get_applications(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> list[models.Application]:
    """Return a page of the user's applications, newest first."""
    return (
        db.query(models.Application)
        .filter(models.Application.user_id == user_id)
        .order_by(models.Application.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_application(
    db: Session, application_id: int, user_id: int
) -> models.Application | None:
    """Return a single application owned by the user, or None."""
    return (
        db.query(models.Application)
        .filter(
            models.Application.id == application_id,
            models.Application.user_id == user_id,
        )
        .one_or_none()
    )


def create_application(
    db: Session, application: schemas.ApplicationCreate, user_id: int
) -> models.Application:
    """Insert a new application owned by the user."""
    db_application = models.Application(**application.model_dump(), user_id=user_id)
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


def update_application(
    db: Session, db_application: models.Application, updates: schemas.ApplicationUpdate
) -> models.Application:
    """Apply partial updates to an existing application."""
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_application, field, value)
    db.commit()
    db.refresh(db_application)
    return db_application


def delete_application(db: Session, db_application: models.Application) -> None:
    """Delete an application."""
    db.delete(db_application)
    db.commit()
