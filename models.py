from sqlalchemy import Column, String, Integer, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class EmployeeModel(Base):
    __tablename__ = 'Employe'

    id = Column(String, primary_key=True, index=True)
    Email = Column(String, nullable=False)
    Password = Column(String, nullable=False)
    Nom = Column(String, nullable=False)
    Prenom = Column(String, nullable=False)
    Departement_id = Column(String, nullable=False)
    Jour_Conge = Column(Integer, nullable=False)
    Date_naiss = Column(Date, nullable=False)
    Lieu_naiss = Column(String, nullable=False)
    RH = Column(Boolean, nullable=False) 
    
    
  
    
