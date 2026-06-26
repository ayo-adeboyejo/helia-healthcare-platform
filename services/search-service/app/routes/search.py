from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel

from app.core.elasticsearch import get_es
from app.core.logger import logger

router = APIRouter()

DOCTORS_INDEX = "helia_doctors"


# ── Schemas ───────────────────────────────────────────────────────────────────
class DoctorIndex(BaseModel):
    id:               str
    first_name:       str
    last_name:        str
    specialty:        Optional[str] = None
    qualification:    Optional[str] = None
    experience_years: int = 0
    bio:              Optional[str] = None
    consultation_fee: float = 0.0
    languages:        Optional[str] = None
    clinic_address:   Optional[str] = None
    rating:           float = 0.0
    total_reviews:    int = 0
    is_available:     bool = True
    is_approved:      bool = True


# ── Index a doctor (called by user-service when doctor is approved) ────────────
@router.post("/search/doctors/index", status_code=201)
async def index_doctor(
    payload: DoctorIndex,
    es: AsyncElasticsearch = Depends(get_es),
):
    doc = payload.model_dump()
    await es.index(index=DOCTORS_INDEX, id=payload.id, document=doc)
    logger.info(f"doctor_indexed id={payload.id}")
    return {"message": "Doctor indexed successfully"}


# ── Update doctor in index ────────────────────────────────────────────────────
@router.put("/search/doctors/{doctor_id}")
async def update_doctor_index(
    doctor_id: str,
    payload: DoctorIndex,
    es: AsyncElasticsearch = Depends(get_es),
):
    doc = payload.model_dump()
    await es.update(index=DOCTORS_INDEX, id=doctor_id, doc=doc)
    logger.info(f"doctor_index_updated id={doctor_id}")
    return {"message": "Doctor index updated"}


# ── Remove doctor from index ──────────────────────────────────────────────────
@router.delete("/search/doctors/{doctor_id}")
async def remove_doctor_index(
    doctor_id: str,
    es: AsyncElasticsearch = Depends(get_es),
):
    await es.delete(index=DOCTORS_INDEX, id=doctor_id, ignore=[404])
    logger.info(f"doctor_removed_from_index id={doctor_id}")
    return {"message": "Doctor removed from index"}


# ── Search doctors ────────────────────────────────────────────────────────────
@router.get("/search/doctors")
async def search_doctors(
    q:            Optional[str]   = Query(None, description="Search by name, specialty or bio"),
    specialty:    Optional[str]   = Query(None),
    min_fee:      Optional[float] = Query(None),
    max_fee:      Optional[float] = Query(None),
    min_rating:   Optional[float] = Query(None),
    is_available: Optional[bool]  = Query(None),
    language:     Optional[str]   = Query(None),
    limit:        int             = Query(20, le=100),
    offset:       int             = Query(0),
    es: AsyncElasticsearch = Depends(get_es),
):
    must_clauses    = []
    filter_clauses  = [{"term": {"is_approved": True}}]

    # Full-text search across name, specialty, bio
    if q:
        must_clauses.append({
            "multi_match": {
                "query":  q,
                "fields": ["first_name^2", "last_name^2", "specialty^1.5", "bio", "qualification"],
                "fuzziness": "AUTO",
            }
        })

    if specialty:
        filter_clauses.append({"match": {"specialty": specialty}})

    if is_available is not None:
        filter_clauses.append({"term": {"is_available": is_available}})

    if language:
        filter_clauses.append({"match": {"languages": language}})

    if min_fee is not None or max_fee is not None:
        fee_range = {}
        if min_fee is not None: fee_range["gte"] = min_fee
        if max_fee is not None: fee_range["lte"] = max_fee
        filter_clauses.append({"range": {"consultation_fee": fee_range}})

    if min_rating is not None:
        filter_clauses.append({"range": {"rating": {"gte": min_rating}}})

    query = {
        "bool": {
            "must":   must_clauses if must_clauses else [{"match_all": {}}],
            "filter": filter_clauses,
        }
    }

    try:
        response = await es.search(
            index=DOCTORS_INDEX,
            query=query,
            sort=[{"rating": {"order": "desc"}}, {"total_reviews": {"order": "desc"}}],
            from_=offset,
            size=limit,
        )
    except Exception as e:
        logger.error(f"elasticsearch_search_failed: {e}")
        raise HTTPException(status_code=503, detail="Search service temporarily unavailable")

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    return {
        "total":   total,
        "results": [hit["_source"] for hit in hits],
        "limit":   limit,
        "offset":  offset,
    }


# ── Autocomplete doctor names ─────────────────────────────────────────────────
@router.get("/search/doctors/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=2),
    es: AsyncElasticsearch = Depends(get_es),
):
    try:
        response = await es.search(
            index=DOCTORS_INDEX,
            query={
                "bool": {
                    "must": [{"match_phrase_prefix": {"first_name": q}}],
                    "filter": [{"term": {"is_approved": True}}],
                }
            },
            size=5,
            source=["id", "first_name", "last_name", "specialty", "rating"],
        )
        suggestions = [hit["_source"] for hit in response["hits"]["hits"]]
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"autocomplete_failed: {e}")
        return {"suggestions": []}
