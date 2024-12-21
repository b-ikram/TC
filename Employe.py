from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from database import SessionLocal
from models import EmployeeModel
from models import TacheModel
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

class Login(BaseModel):
    email: str
    password: str

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()

@router.post("/auth/login")
async def authenticate_employee(login: Login, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.Email == login.email).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(login.password, employee.Password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Authentication successful", "employee_id": employee.id, "name": f"{employee.Prenom} {employee.Nom}"}

@router.post("/auth/create")
async def create_employee(emp: Login, db: Session = Depends(get_db)):
    hashed_password = hash_password(emp.password)

    new_employee = EmployeeModel(
        Email=emp.email,
        Password=hashed_password
    )


    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)


    return {"message": "Employee created successfully", "employee_id": new_employee.id}

class UpdateEmployee(BaseModel):
    nom: str = None
    prenom: str = None
    BirthDate: str = None
    BirthPlace: str = None
    email: str = None
    RH: bool = None
    joursConges: int = None
    depId: int = None

# Endpoint to update employee information
@router.put("/employee/{employee_id}")
async def update_employee(employee_id: int, updated_info: UpdateEmployee, db: Session = Depends(get_db)):
    # Fetch the employee by ID
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Update the employee's fields with the provided data
    if updated_info.nom is not None:
        employee.Nom = updated_info.nom
    if updated_info.prenom is not None:
        employee.Prenom = updated_info.prenom
    if updated_info.BirthDate is not None:
        employee.Date_naiss = updated_info.BirthDate
    if updated_info.BirthPlace is not None:
        employee.Lieu_naiss = updated_info.BirthPlace
    if updated_info.email is not None:
        employee.Email = updated_info.email
    if updated_info.RH is not None:
        employee.RH = updated_info.RH
    if updated_info.joursConges is not None:
        employee.Jour_Conge = updated_info.joursConges
    if updated_info.depId is not None:
        employee.Departement_id = updated_info.depId

    # Commit the changes to the database
    db.commit()
    db.refresh(employee)

    return {"message": "Employee information updated successfully", "employee": employee}

@router.get("/employee/{employee_id}/tasks")
async def get_employee_tasks(employee_id: int, db: Session = Depends(get_db)):
    
    tasks = db.query(TacheModel).filter(TacheModel.Employe_id == employee_id).all()
    
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found for this employee")

    
    return {"employee_id": employee_id, "tasks": tasks}
