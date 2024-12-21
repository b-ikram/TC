from sqlalchemy import Column, String, Integer, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import INTERVAL
Base = declarative_base()

class EmployeeModel(Base):
    __tablename__ = 'Employe'

    id = Column(Integer, primary_key=True, index=True)
    Email = Column(String, nullable=False)
    Password = Column(String, nullable=False)
    Nom = Column(String, nullable=False)
    Prenom = Column(String, nullable=False)
    Departement_id = Column(String, nullable=False)
    Jour_Conge = Column(Integer, nullable=False)
    Date_naiss = Column(Date, nullable=False)
    Lieu_naiss = Column(String, nullable=False)
    RH = Column(Boolean, nullable=False) 
    
    
class TacheModel (Base):
    __tablename__ = 'tache'   
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    etat_tache = Column(String, nullable=False)
    date_fin = Column(Date, nullable=False)
    date_debut = Column(Date, nullable=False)
    deadline = Column(String, nullable=False)
    Employe_id = Column(Integer, nullable=False) 

class DepartementModel (Base):
    __tablename__ = 'departement'   
    id = Column(Integer, primary_key=True, index=True)
    manager = Column(String, nullable=False)
    absence = Column(String, nullable=False)
    retard = Column(String, nullable=False)
    presence = Column(Date, nullable=False)
   
class CongeModel (Base):
    __tablename__ = 'conge'   
    id = Column(Integer, primary_key=True, index=True)
    raison = Column(String, nullable=False)
    etat_conge = Column(String, nullable=False)
    date_fin = Column(Date, nullable=False)
    date_debut = Column(Date, nullable=False)
    Employe_id = Column(Integer, nullable=False)

class Check_in_outModel (Base):
    __tablename__ = 'check_in_out'   
    id = Column(Integer, primary_key=True, index=True,autoincrement="auto")
    heur_arrive = Column(INTERVAL, nullable=False)
    heur_sortie = Column(INTERVAL, nullable=True)
    date = Column(Date, nullable=False)
    duree_retard = Column(INTERVAL, nullable=False)
    Employe_id = Column(Integer, nullable=False) 

