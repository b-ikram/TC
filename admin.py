# app.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from database import SessionLocal  # Import the session from database.py
from models import EmployeeModel  # Import the EmployeeModel from models.py

app = FastAPI()

# Pydantic model for the input data (request body)
class Employee(BaseModel):
    email: str
    id: str
    nom: str
    prenom: str
    BirthDate: date
    BirthPlace: str
    pwd: str
    joursConges: int
    depId: str

# Function to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint to add a user (Employee) to the database
@app.post("/add_user")
async def add_user(emp: Employee, db: Session = Depends(get_db)):
    # Create a new employee record from the Pydantic model data
    db_employee = EmployeeModel(
        id=emp.id,
        Nom=emp.nom,
        Prenom=emp.prenom,
        Date_naiss=emp.BirthDate,
        Lieu_naiss=emp.BirthPlace,
        Password=emp.pwd,
        Email=emp.email,
        Jour_Conge=emp.joursConges,
        Departement_id=emp.depId,
        RH=True  # Defaulting to True, adjust as needed
    )

    # Add and commit the new employee to the database
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    return {"message": "Utilisateur ajouté avec succès!", "id": db_employee.id}

# Endpoint to get a list of all employees
@app.get("/employees")
async def get_employees(db: Session = Depends(get_db)):
    employees = db.query(EmployeeModel).all()
    return {"employees": employees}

# Endpoint to get a single employee by ID
@app.get("/employee/{employee_id}")
async def get_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"employee": employee}
