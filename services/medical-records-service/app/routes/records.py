import uuid
import boto3
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.mongodb import get_db
from app.core.dependencies import get_current_user
from app.core.logger import logger
from app.config import settings

router = APIRouter()


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def get_s3_client():
    """
    Returns an S3 client.
    Development: points to MinIO (local S3-compatible storage)
    Production:  points to real AWS S3, authenticated via IAM role
    """
    if settings.using_minio:
        return boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name="us-east-1",
        )
    return boto3.client("s3", region_name=settings.aws_region)


# ── Schemas ───────────────────────────────────────────────────────────────────
class MedicalHistoryCreate(BaseModel):
    conditions:  Optional[List[str]] = []
    allergies:   Optional[List[str]] = []
    medications: Optional[List[str]] = []
    notes:       Optional[str]       = None


class PrescriptionCreate(BaseModel):
    appointment_id: str
    patient_id:     str
    medications:    List[dict]  # [{name, dosage, frequency, duration}]
    notes:          Optional[str] = None


class ConsultationNoteCreate(BaseModel):
    appointment_id: str
    patient_id:     str
    subjective:     Optional[str] = None  # what patient reports
    objective:      Optional[str] = None  # what doctor observes
    assessment:     Optional[str] = None  # diagnosis
    plan:           Optional[str] = None  # treatment plan


# ── Medical history ───────────────────────────────────────────────────────────
@router.get("/medical-records/history/{patient_id}")
async def get_patient_history(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["user_id"] != patient_id and current_user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    record = await db.patients_history.find_one({"patient_id": patient_id})
    if not record:
        return {"patient_id": patient_id, "conditions": [], "allergies": [], "medications": [], "notes": None}

    record["_id"] = str(record["_id"])
    return record


@router.put("/medical-records/history/{patient_id}")
async def update_patient_history(
    patient_id: str,
    payload: MedicalHistoryCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    doc = {
        "patient_id":  patient_id,
        "conditions":  payload.conditions,
        "allergies":   payload.allergies,
        "medications": payload.medications,
        "notes":       payload.notes,
        "updated_at":  utcnow(),
        "updated_by":  current_user["user_id"],
    }
    await db.patients_history.update_one(
        {"patient_id": patient_id},
        {"$set": doc},
        upsert=True,
    )
    logger.info(f"medical_history_updated patient={patient_id}")
    return {"message": "Medical history updated"}


# ── Prescriptions ─────────────────────────────────────────────────────────────
@router.post("/medical-records/prescriptions", status_code=201)
async def create_prescription(
    payload: PrescriptionCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Only doctors can create prescriptions")

    doc = {
        "id":             str(uuid.uuid4()),
        "appointment_id": payload.appointment_id,
        "patient_id":     payload.patient_id,
        "doctor_id":      current_user["user_id"],
        "medications":    payload.medications,
        "notes":          payload.notes,
        "created_at":     utcnow(),
    }
    await db.prescriptions.insert_one(doc)
    doc.pop("_id", None)

    logger.info(f"prescription_created patient={payload.patient_id} doctor={current_user['user_id']}")
    return doc


@router.get("/medical-records/prescriptions/{patient_id}")
async def get_patient_prescriptions(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["user_id"] != patient_id and current_user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    cursor = db.prescriptions.find({"patient_id": patient_id}).sort("created_at", -1)
    prescriptions = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        prescriptions.append(doc)
    return {"prescriptions": prescriptions}


# ── Consultation notes ────────────────────────────────────────────────────────
@router.post("/medical-records/notes", status_code=201)
async def create_consultation_note(
    payload: ConsultationNoteCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Only doctors can create consultation notes")

    doc = {
        "id":             str(uuid.uuid4()),
        "appointment_id": payload.appointment_id,
        "patient_id":     payload.patient_id,
        "doctor_id":      current_user["user_id"],
        "subjective":     payload.subjective,
        "objective":      payload.objective,
        "assessment":     payload.assessment,
        "plan":           payload.plan,
        "created_at":     utcnow(),
    }
    await db.consultation_notes.insert_one(doc)
    doc.pop("_id", None)

    logger.info(f"consultation_note_created appointment={payload.appointment_id}")
    return doc


@router.get("/medical-records/notes/{patient_id}")
async def get_consultation_notes(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["user_id"] != patient_id and current_user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    cursor = db.consultation_notes.find({"patient_id": patient_id}).sort("created_at", -1)
    notes = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        notes.append(doc)
    return {"notes": notes}


# ── File upload to S3 ─────────────────────────────────────────────────────────
@router.post("/medical-records/documents/upload")
async def upload_document(
    patient_id: str,
    document_type: str,  # lab-results | prescriptions | consultation-notes | profile-images
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    allowed_types = {"lab-results", "prescriptions", "consultation-notes", "profile-images"}
    if document_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"document_type must be one of: {allowed_types}")

    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
    import os
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File type not allowed")

    # Max 10MB
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB allowed")

    # Upload to S3
    file_key = f"{document_type}/{patient_id}/{str(uuid.uuid4())}{ext}"
    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=file_key,
            Body=content,
            ContentType=file.content_type,
            ServerSideEncryption="AES256",
        )
    except Exception as e:
        logger.error(f"s3_upload_failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

    # Record in MongoDB
    doc = {
        "id":            str(uuid.uuid4()),
        "patient_id":    patient_id,
        "uploaded_by":   current_user["user_id"],
        "document_type": document_type,
        "filename":      file.filename,
        "s3_key":        file_key,
        "size_bytes":    len(content),
        "created_at":    utcnow(),
    }
    await db.documents.insert_one(doc)
    doc.pop("_id", None)

    logger.info(f"document_uploaded patient={patient_id} type={document_type} key={file_key}")
    return {**doc, "message": "Document uploaded successfully"}


# ── Get pre-signed download URL ───────────────────────────────────────────────
@router.get("/medical-records/documents/{document_id}/download")
async def get_download_url(
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    doc = await db.documents.find_one({"id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc["patient_id"] != current_user["user_id"] and current_user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": doc["s3_key"]},
            ExpiresIn=3600,  # URL valid for 1 hour
        )
    except Exception as e:
        logger.error(f"presigned_url_failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download URL")

    return {"download_url": url, "expires_in": 3600, "filename": doc["filename"]}


# ── List patient documents ────────────────────────────────────────────────────
@router.get("/medical-records/documents/{patient_id}")
async def list_documents(
    patient_id: str,
    document_type: Optional[str] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["user_id"] != patient_id and current_user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    query = {"patient_id": patient_id}
    if document_type:
        query["document_type"] = document_type

    cursor = db.documents.find(query).sort("created_at", -1)
    documents = []
    async for doc in cursor:
        doc.pop("s3_key", None)  # Never expose S3 keys directly
        doc["_id"] = str(doc["_id"])
        documents.append(doc)

    return {"documents": documents}
