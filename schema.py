from pydantic import BaseModel
from datetime import date

class Employee(BaseModel):
    Nom: str
    Prenom: str
    Email: str
    Password: str
    Date_naiss: date
    Lieu_naiss: str
    Jour_Conge: int
    depId: str
    RH: bool
    Departement_id: str

class Login(BaseModel):
    Email: str
    Password: str

class UpdateEmployee(BaseModel):
    Nom: str = None
    Prenom: str = None
    Date_naiss: date = None
    Lieu_naiss: str = None
    Email: str = None
    Departement_id: str = None

class CongeRequest(BaseModel):
    raison: str
    date_debut: date
    date_fin: date


class TacheCreate(BaseModel):
    title: str
    description: str
    etat_tache: str  # Exemple : "En cours", "Terminée", etc.
    date_debut: date
    deadline: date
    Employe_id: int

class CheckInOutResponse(BaseModel):
    employe_id: int
    heur_arrive: str  # Format HH:MM:SS
    heur_sortie: str  # Format HH:MM:SS ou "None" si absent
    date: date
