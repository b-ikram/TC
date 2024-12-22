from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import SessionLocal
from models import EmployeeModel, Check_in_outModel 
from passlib.context import CryptContext
from schema import Employee 

router = APIRouter()

# Dépendance pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hashage du mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Endpoint pour ajouter un employé
@router.post("/add_user")
async def add_user(emp: Employee, db: Session = Depends(get_db)):
    hashed_password = hash_password(emp.Password)

    db_employee = EmployeeModel(
        Nom=emp.Nom,
        Prenom=emp.Prenom,
        Date_naiss=emp.Date_naiss,
        Lieu_naiss=emp.Lieu_naiss,
        Password=hashed_password,
        Email=emp.Email,
        Jour_Conge=emp.Jour_Conge,
        Departement_id=emp.Departement_id,
        RH=emp.RH  
    )

    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    return {"message": "Employee added successfully", "employee_id": db_employee.id}

# Endpoint pour récupérer tous les employés
@router.get("/employees")
async def get_employees(db: Session = Depends(get_db)):
    employees = db.query(EmployeeModel).all()
    return {"employees": employees}

@router.get("/recogrize")
async def recognize_face():
    return {}

# Endpoint pour récupérer un employé spécifique
@router.get("/employee/{employee_id}")
async def get_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"employee": employee}

# Endpoint pour effectuer un check-in
@router.post("/check_in/{employee_id}")
async def check_in(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

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

    return {"message": "Check-in registered successfully", "check_in_id": check_in_record.id}

# Endpoint pour effectuer un check-out
@router.post("/check_out/{employee_id}")
async def check_out(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

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

    return {"message": "Check-out registered successfully", "check_out_id": check_in_record.id}