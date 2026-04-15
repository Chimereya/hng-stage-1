from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from uuid6 import uuid7
from . import models, schemas, services, database

# Initialize DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Profile Intelligence Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": str(exc.detail)},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    status_code = 422
    message = "Invalid type"

    for error in errors:
        error_type = error.get("type", "")
        error_loc = error.get("loc", [])
        error_msg = error.get("msg", "")

        if error_loc and error_loc[-1] == "name":
            if error_type == "value_error.missing" or error_msg == "Missing or empty name":
                status_code = 400
                message = "Missing or empty name"
                break
            if error_type.startswith("value_error.any_str.min_length"):
                status_code = 400
                message = "Missing or empty name"
                break

    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"},
    )


@app.post("/api/profiles", status_code=201, response_model=schemas.SuccessResponse)
async def create_profile(request: schemas.ProfileCreate, db: Session = Depends(database.get_db)):
    name_clean = request.name.lower().strip()

    # Check for existing profile
    existing = db.query(models.Profile).filter(models.Profile.name == name_clean).first()
    
    if existing:
        # Convert SQLAlchemy model to Pydantic, then to a JSON-compatible dict
        pydantic_data = schemas.ProfileResponse.model_validate(existing)
        
        # jsonable_encoder handles the datetime/UUID serialization issue
        safe_data = jsonable_encoder(pydantic_data)
        
        return JSONResponse(
            status_code=200, 
            content={
                "status": "success", 
                "message": "Profile already exists", 
                "data": safe_data
            }
        )

    # If no existing profile, proceed with creation
    intel = await services.get_profile_intelligence(name_clean)

    new_profile = models.Profile(
        id=str(uuid7()),
        name=name_clean,
        **intel,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    # FastAPI's response_model handles the serialization automatically for the 201 return
    return {
        "status": "success", 
        "data": schemas.ProfileResponse.model_validate(new_profile)
    }

@app.get("/api/profiles", response_model=schemas.ListResponse)
def get_profiles(
    gender: str = None,
    country_id: str = None,
    age_group: str = None,
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Profile)
    if gender:
        query = query.filter(models.Profile.gender == gender.lower())
    if country_id:
        query = query.filter(models.Profile.country_id == country_id.upper())
    if age_group:
        query = query.filter(models.Profile.age_group == age_group.lower())

    results = query.all()
    return {
        "status": "success",
        "count": len(results),
        "data": [schemas.ProfileListItem.from_orm(profile) for profile in results],
    }

@app.get("/api/profiles/{profile_id}", response_model=schemas.SuccessResponse)
def get_single_profile(profile_id: str, db: Session = Depends(database.get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success", "data": schemas.ProfileResponse.from_orm(profile)}

@app.delete("/api/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: str, db: Session = Depends(database.get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()
    return None