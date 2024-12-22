from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime , timedelta , timezone
from typing import Annotated
from database import SessionLocal
from models import EmployeeModel,  CongeModel , TacheModel, AdminModel , Check_in_outModel
from passlib.context import CryptContext
from schema import Login, UpdateEmployee, CongeRequest
from .config import settings
import bcrypt
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


router = APIRouter()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def incrementer_absence(employe_id: int, db: Session):
    # Chercher le dernier enregistrement de Check_in_out pour cet employé
    check_in = db.query(Check_in_outModel).filter(Check_in_outModel.Employe_id == employe_id).order_by(Check_in_outModel.date.desc()).first()

    # Vérifier si le check-in est None (c'est-à-dire que l'employé n'a pas pointé son arrivée)
    if check_in and check_in.heur_arrive is None:
        # Trouver l'employé dans la base de données
        employee = db.query(EmployeeModel).filter(EmployeeModel.id == employe_id).first()
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Incrémenter le compteur d'absences de l'employé
        employee.absence += 1
        db.commit()
        db.refresh(employee)
        
        return {"message": f"Absence incremented for employee {employee.Nom} {employee.Prenom}. Current absences: {employee.absence}"}
    
    # Si l'employé a déjà pointé son arrivée, ne rien faire
    return {"message": "Employee has checked in, no absence incremented."}

@router.put("/absence/{employe_id}")
async def incrementer_absence_route(employe_id: int, db: Session = Depends(get_db)):
    return await incrementer_absence(employe_id, db)

def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def authenticate_employee(email: str, password: str, db: Session) -> EmployeeModel:
  
    employee = db.query(EmployeeModel).filter(EmployeeModel.email == email).first()
    if employee is None:
        return None
    if not bcrypt.checkpw(password.encode('utf-8'), employee.password_hash.encode('utf-8')):
        return None
    return employee



# Hashage du mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)




@router.post("/auth/login")
async def authenticate_employee(login: Login, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.Email == login.email).first()
    if not employee or not verify_password(login.password, employee.Password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Authentication successful", "employee_id": employee.id, "name": f"{employee.Prenom} {employee.Nom}"}



# Mise à jour des informations d'un employé
@router.put("/employee/{employee_id}")
async def update_employee(employee_id: int, updated_info: UpdateEmployee, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in updated_info.dict(exclude_unset=True).items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    return {"message": "Employee information updated successfully", "employee": employee}

# Obtenir les tâches d'un employé
@router.get("/employee/{employee_id}/tasks")
async def get_employee_tasks(employee_id: int, db: Session = Depends(get_db)):
    tasks = db.query(TacheModel).filter(TacheModel.Employe_id == employee_id).all()

    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found for this employee")

    return {"employee_id": employee_id, "tasks": tasks}

# Marquer une tâche comme complète
@router.put("/task/complete/{task_id}")
async def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TacheModel).filter(TacheModel.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.etat_tache = "complete"
    task.date_fin = datetime.now().date()  # Date actuelle

    db.commit()
    db.refresh(task)

    return {
        "message": "Task marked as complete successfully",
        "task_id": task.id,
        "title": task.title,
        "etat_tache": task.etat_tache,
        "date_fin": task.date_fin
    }


# Demander un congé
@router.post("/conge/request/{employe_id}")
async def request_conge(employe_id: int, conge: CongeRequest, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employe_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.Jour_Conge == 0:
        raise HTTPException(status_code=400, detail="No remaining vacation days")

    conge_duration = (conge.date_fin - conge.date_debut).days + 1  # +1 pour inclure le jour de début

    if conge_duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range for the vacation")

    if conge_duration > employee.Jour_Conge:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient vacation days. You have only {employee.Jour_Conge} day(s) left."
        )

    new_conge = CongeModel(
        raison=conge.raison,
        etat_conge="en attente",  # Statut initial
        date_debut=conge.date_debut,
        date_fin=conge.date_fin,
        Employe_id=employe_id
    )


    db.add(new_conge)
    db.commit()
    db.refresh(new_conge)

    return {
        "message": "Vacation request submitted successfully",
        "etat_conge": new_conge.etat_conge
    }

