from fastapi import FastAPI ,APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, datetime, timedelta
import random
import string
from database import SessionLocal 
from models import EmployeeModel, Check_in_outModel
from passlib.context import CryptContext

router = APIRouter()


class Employee(BaseModel):
    nom: str
    prenom: str
    email:str
    pwd:str
    BirthDate: date
    BirthPlace: str
    joursConges: int
    depId: str
    RH: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/add_user")
async def add_user(emp: Employee, db: Session = Depends(get_db)):
        
    hashed_password = hash_password(emp.pwd)

    db_employee = EmployeeModel(
        Nom=emp.nom,
        Prenom=emp.prenom,
        Date_naiss=emp.BirthDate,
        Lieu_naiss=emp.BirthPlace,
        Password=hashed_password,
        Email=emp.email,
        Jour_Conge=emp.joursConges,
        Departement_id=emp.depId,
        RH=emp.RH  
    )

    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)


@router.get("/employees")
async def get_employees(db: Session = Depends(get_db)):
    employees = db.query(EmployeeModel).all()
    return {"employees": employees}

@router.get("/employee/{employee_id}")
async def get_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"employee": employee}

@router.post("/check_in/{employee_id}")
async def check_in(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee non trouvé")

    now = datetime.now()
    check_in_record = Check_in_outModel(
        heur_arrive=now.time(),
        heur_sortie=None,  # Check-out not yet recorded
        date=now.date(),
        duree_retard=(now - datetime.combine(now.date(), datetime.min.time())) if now.time() > datetime.strptime("09:00", "%H:%M").time() else timedelta(seconds=0),
        Employe_id=employee_id,
    )

    db.add(check_in_record)
    db.commit()
    db.refresh(check_in_record)

    return {"message": "Check-in enregistré avec succès!", "check_in_id": check_in_record.id}

@router.post("/check_out/{employee_id}")
async def check_out(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee non trouve")

    now = datetime.now()
    check_in_record = db.query(Check_in_outModel).filter(
        Check_in_outModel.Employe_id == employee_id,
        Check_in_outModel.date == now.date(),
        Check_in_outModel.heur_sortie == None
    ).first()

    if not check_in_record:
        raise HTTPException(status_code=404, detail="No active check-in record found for today.")

    check_in_record.heur_sortie = now.time()
    db.commit()
    db.refresh(check_in_record)

    return {"message": "Check-out enregistré avec succès!", "check_out_id": check_in_record.id}

 