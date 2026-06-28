"""Routes for managing job applications."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[schemas.Application])
def list_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List tracked applications."""
    return crud.get_applications(db, skip=skip, limit=limit)


@router.post("", response_model=schemas.Application, status_code=status.HTTP_201_CREATED)
def create_application(payload: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    """Create a new application."""
    return crud.create_application(db, payload)


@router.get("/{application_id}", response_model=schemas.Application)
def get_application(application_id: int, db: Session = Depends(get_db)):
    """Fetch a single application by id."""
    application = crud.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


@router.patch("/{application_id}", response_model=schemas.Application)
def update_application(
    application_id: int, payload: schemas.ApplicationUpdate, db: Session = Depends(get_db)
):
    """Partially update an application."""
    application = crud.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return crud.update_application(db, application, payload)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    """Delete an application."""
    application = crud.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    crud.delete_application(db, application)
