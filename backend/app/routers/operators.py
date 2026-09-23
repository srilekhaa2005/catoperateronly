from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Operator
from ..schemas.api import OperatorLanguageUpdate, SUPPORTED_LANGUAGES

router = APIRouter(tags=["operators"])

def out(op):
    return {"id": op.id, "name": op.name, "employee_code": op.employee_code,
            "preferred_language": op.preferred_language, "role": op.role}

@router.get("/operators/{operator_id}")
def get_operator(operator_id: int, db: Session = Depends(get_db)):
    op = db.get(Operator, operator_id)
    if not op: raise HTTPException(404, detail=f"Operator with id {operator_id} was not found")
    return out(op)

@router.patch("/operators/{operator_id}")
def update_operator(operator_id: int, payload: OperatorLanguageUpdate, db: Session = Depends(get_db)):
    if payload.preferred_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(422, detail="Unsupported language code")
    op = db.get(Operator, operator_id)
    if not op: raise HTTPException(404, detail=f"Operator with id {operator_id} was not found")
    op.preferred_language = payload.preferred_language
    db.commit(); db.refresh(op)
    return out(op)
