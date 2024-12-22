from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import SessionLocal
from models import EmployeeModel,  CongeModel , TacheModel, Check_in_outModel
from passlib.context import CryptContext
from schema import TacheCreate , CheckInOutResponse
from typing import List
from datetime import date
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


"""
Validation des conges
"""

@router.put("/conge/validate/{conge_id}")   
async def validate_conge(conge_id: int, validation: bool, db: Session = Depends(get_db)):
   
    conge_request = db.query(CongeModel).filter(CongeModel.id == conge_id).first()
    
    if not conge_request:
        raise HTTPException(status_code=404, detail="Vacation request not found")

    status = "Validée" if validation else "Refusée"
    conge_request.etat_conge = status

    if status == "Validée":
        employee = db.query(EmployeeModel).filter(EmployeeModel.id == conge_request.Employe_id).first()

        conge_duration = (conge_request.date_fin - conge_request.date_debut).days + 1

        if conge_duration > employee.Jour_Conge:
            status = "Rejetée"
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient vacation days. Employee has only {employee.Jour_Conge} day(s) left."
            )
        employee.Jour_Conge -= conge_duration
        db.commit()
        db.refresh(employee)
    db.commit()
    db.refresh(conge_request)
    return {"message": f"Vacation request {status} successfully", "conge_id": conge_request.id}


"""
visualisation des conges a valide
"""


@router.get("/conges/demandes")
async def get_demanded_conges(db: Session = Depends(get_db)):
   
    # Récupérer les congés avec un état spécifique
    demandes = db.query(CongeModel).filter(CongeModel.etat_conge == "en attente").all()

    # Vérification si aucun congé trouvé
    if not demandes:
        return {"message": "Aucun congé en attente trouvé."}

    # Retourner les résultats
    return {"demandes": demandes}


@router.post("/tache/create")
async def create_tache(tache: TacheCreate, db: Session = Depends(get_db)):
   
    # Vérifier si l'employé existe
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == tache.Employe_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employé non trouvé")
    
    # Créer une instance de TacheModel
    new_tache = TacheModel(
        title=tache.title,
        description=tache.description,
        etat_tache=tache.etat_tache,
        date_debut=tache.date_debut,
        date_fin=None,
        deadline=tache.deadline,
        Employe_id=tache.Employe_id
    )
    
    # Ajouter et valider la tâche dans la base de données
    db.add(new_tache)
    db.commit()
    db.refresh(new_tache)
    
    return {"message": "Tâche créée avec succès", "tache_id": new_tache.id}

@router.get("/check_in_out/{query_date}", response_model=List[CheckInOutResponse])
async def get_check_in_out(query_date: date, db: Session = Depends(get_db)):
   
    # Récupérer les données pour la date donnée
    check_ins_outs = db.query(Check_in_outModel).filter(Check_in_outModel.date == query_date).all()

    if not check_ins_outs:
        raise HTTPException(status_code=404, detail="Aucun enregistrement trouvé pour cette date")

    # Formater les résultats pour l'API
    result = []
    for record in check_ins_outs:
        result.append(
            CheckInOutResponse(
                employe_id=record.Employe_id,
                heur_arrive=str(record.heur_arrive),
                heur_sortie=str(record.heur_sortie) if record.heur_sortie else "None",
                date=record.date,
            )
        )

    return result

@router.get("/check-in-out/{employee_id}")
async def get_check_in_out_records(
    employee_id: int,
    db: Session = Depends(get_db),
):
    
    records = (
        db.query(Check_in_outModel)
        .filter(Check_in_outModel.Employe_id == employee_id)
        .order_by(Check_in_outModel.date.desc())
        .all()
    )

    if not records:
        raise HTTPException(status_code=404, detail="No check-in/out records found for this employee")

    # Format the records for better readability
    formatted_records = [
        {
            "date": record.date,
            "heur_arrive": str(record.heur_arrive),
            "heur_sortie": str(record.heur_sortie) if record.heur_sortie else "Not recorded",
            "duree_retard": str(record.duree_retard),
        }
        for record in records
    ]

    return {"employee_id": employee_id, "check_in_out_records": formatted_records} 

@router.get("/employees/{employe_id}/absences")
async def get_employee_absences(employe_id: int, db: Session = Depends(get_db)):
    # Chercher l'employé par son ID
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employe_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Renvoyer le nombre d'absences de l'employé
    return {"employee_id": employee.id, "name": f"{employee.Prenom} {employee.Nom}", "absences": employee.absence}

@router.get("/employees/absences")
async def get_all_employees_absences(db: Session = Depends(get_db)):
    # Récupérer tous les employés avec leurs absences
    employees = db.query(EmployeeModel).all()
    
    if not employees:
        raise HTTPException(status_code=404, detail="No employees found")
    
    # Renvoyer une liste d'employés avec leurs absences
    return [{"employee_id": employee.id, "name": f"{employee.Prenom} {employee.Nom}", "absences": employee.absence} for employee in employees]

# Endpoint pour obtenir les retards d'un employé spécifique
@router.get("/employees/{employe_id}/delays")
async def get_employee_delays(employe_id: int, db: Session = Depends(get_db)):
    # Récupérer les enregistrements de check-in de l'employé
    check_in_records = db.query(Check_in_outModel).filter(Check_in_outModel.Employe_id == employe_id).all()
    
    if not check_in_records:
        raise HTTPException(status_code=404, detail="No check-in records found for this employee")

    # Compter le nombre de retards
    delay_count = 0
    for record in check_in_records:
        # Vérifier si l'heure d'arrivée est plus tard que l'heure prévue
        if record.heur_arrive > record.date:  # Ceci est une hypothèse, vous pouvez adapter en fonction de votre logique métier
            delay_count += 1

    return {"employee_id": employe_id, "delays": delay_count}

@router.get("/employees/delays")
async def get_all_employees_delays(db: Session = Depends(get_db)):
    # Récupérer tous les employés
    employees = db.query(EmployeeModel).all()

    if not employees:
        raise HTTPException(status_code=404, detail="No employees found")

    # Compter les retards pour chaque employé
    employee_delays = []
    for employee in employees:
        check_in_records = db.query(Check_in_outModel).filter(Check_in_outModel.Employe_id == employee.id).all()
        delay_count = 0
        for record in check_in_records:
            # Logique pour vérifier si l'employé est en retard
            if record.heur_arrive > record.date:  # Ajustez cette logique
                delay_count += 1
        employee_delays.append({
            "employee_id": employee.id,
            "name": f"{employee.Prenom} {employee.Nom}",
            "delays": delay_count
        })

    return employee_delays