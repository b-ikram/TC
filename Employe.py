from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from database import SessionLocal
from models import EmployeeModel
from models import CongeModel, EmployeeModel
from models import TacheModel
from datetime import datetime , time
from datetime import date 
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

@router.put("/task/complete/{task_id}")
async def complete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Met à jour l'état d'une tâche en 'complete' et modifie la date de fin.
    
    :param task_id: ID de la tâche à mettre à jour
    :param db: Session de la base de données
    :return: Message de confirmation ou erreur
    """
    # Recherche de la tâche par son ID
    task = db.query(TacheModel).filter(TacheModel.id == task_id).first()

    # Si la tâche n'existe pas, lever une exception
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Mise à jour de l'état de la tâche et de la date de fin
    task.etat_tache = "complete"
    task.date_fin = datetime.now().date()  # Date actuelle

    # Sauvegarde des modifications dans la base de données
    db.commit()
    db.refresh(task)

    return {
        "message": "Task marked as complete successfully",
        "task_id": task.id,
        "title": task.title,
        "etat_tache": task.etat_tache,
        "date_fin": task.date_fin
    }


class CongeRequest(BaseModel):
    raison: str
    date_debut: date
    date_fin: date

@router.post("/conge/request/{employe_id}")
async def request_conge(employe_id: int, conge: CongeRequest, db: Session = Depends(get_db)):
    """
    Permet à un employé de demander un congé.
    
    :param employe_id: ID de l'employé faisant la demande
    :param conge: Détails de la demande de congé
    :param db: Session de la base de données
    :return: Message de confirmation ou erreur
    """
    # Vérification de l'employé dans la base de données
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employe_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Vérification des jours de congés disponibles
    if employee.Jour_Conge == 0:
        raise HTTPException(status_code=400, detail="No remaining vacation days")

    # Calcul de la durée du congé (en jours)
    conge_duration = (conge.date_fin - conge.date_debut).days + 1  # +1 pour inclure le jour de début

    if conge_duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range for the vacation")

    # Vérification si le congé dépasse le nombre de jours restants
    if conge_duration > employee.Jour_Conge:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient vacation days. You have only {employee.Jour_Conge} day(s) left."
        )

    # Création de la demande de congé
    new_conge = CongeModel(
        raison=conge.raison,
        etat_conge="en attente",  # Statut initial
        date_debut=conge.date_debut,
        date_fin=conge.date_fin,
        Employe_id=employe_id
    )

    # Mise à jour des jours de congés restants pour l'employé
    employee.Jour_Conge -= conge_duration

    # Sauvegarde dans la base de données
    db.add(new_conge)
    db.commit()
    db.refresh(new_conge)

    return {
        "message": "Vacation request submitted successfully",
        "etat_conge": new_conge.etat_conge,
        "remaining_days": employee.Jour_Conge
    }
