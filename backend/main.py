from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

app = FastAPI(title="OfferFlow API")


class JobApplicationCreate(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    job_url: Optional[str] = None
    status: str = "Saved"
    deadline: Optional[date] = None
    notes: Optional[str] = None
    date_applied: Optional[date] = None


class JobApplication(JobApplicationCreate):
    id: int
    created_at: datetime
    updated_at: datetime


applications: List[JobApplication] = []
next_id = 1


@app.get("/")
def root():
    return {"message": "OfferFlow backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/applications", response_model=JobApplication)
def create_application(application: JobApplicationCreate):
    global next_id

    new_application = JobApplication(
        id=next_id,
        company=application.company,
        role=application.role,
        location=application.location,
        job_url=application.job_url,
        status=application.status,
        deadline=application.deadline,
        notes=application.notes,
        date_applied=application.date_applied,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    applications.append(new_application)
    next_id += 1

    return new_application


@app.get("/applications", response_model=List[JobApplication])
def get_applications():
    return applications


@app.get("/applications/{application_id}", response_model=JobApplication)
def get_application(application_id: int):
    for application in applications:
        if application.id == application_id:
            return application

    raise HTTPException(status_code=404, detail="Application not found")


@app.patch("/applications/{application_id}", response_model=JobApplication)
def update_application(application_id: int, updated_application: JobApplicationCreate):
    for index, application in enumerate(applications):
        if application.id == application_id:
            new_application = JobApplication(
                id=application.id,
                company=updated_application.company,
                role=updated_application.role,
                location=updated_application.location,
                job_url=updated_application.job_url,
                status=updated_application.status,
                deadline=updated_application.deadline,
                notes=updated_application.notes,
                date_applied=updated_application.date_applied,
                created_at=application.created_at,
                updated_at=datetime.now(),
            )

            applications[index] = new_application
            return new_application

    raise HTTPException(status_code=404, detail="Application not found")


@app.delete("/applications/{application_id}")
def delete_application(application_id: int):
    for index, application in enumerate(applications):
        if application.id == application_id:
            deleted_application = applications.pop(index)
            return {
                "message": "Application deleted",
                "application": deleted_application
            }

    raise HTTPException(status_code=404, detail="Application not found")