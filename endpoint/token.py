from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime , timedelta , timezone
from typing import Annotated
from database import SessionLocal
from models import EmployeeModel,  CongeModel , TacheModel, AdminModel
from passlib.context import CryptContext
from schema import Login, UpdateEmployee, CongeRequest
from .config import settings
import bcrypt
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Configuration OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Clés pour JWT
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

def is_admin(email: str, db: Session) -> bool:
    """Vérifie si un employé est un administrateur."""
    admin = db.query(AdminModel).filter(AdminModel.email == email).first()
    return admin is not None

def create_access_token(data: dict) -> str:
    """Crée un token d'accès JWT."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str, db: Session) -> EmployeeModel:
    """Décode un token JWT et retourne l'employé correspondant."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        employee = db.query(EmployeeModel).filter(EmployeeModel.email == email).first()
        if employee is None:
            raise HTTPException(status_code=401, detail="User not found")

        # Ajout des rôles RH et Admin à l'objet employé
        employee.isRH = employee.RH
        employee.isAdmin = is_admin(email, db)

        return employee
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_employee(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> EmployeeModel:
    """Retourne l'employé authentifié basé sur le token JWT."""
    return decode_token(token, db)

# Endpoint de connexion pour obtenir un token
@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    employee = await authenticate_employee(form_data.Email, form_data.Password, db)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Créez un token d'accès avec l'email et les rôles
    access_token = create_access_token(
        data={"sub": employee.Email}
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint pour récupérer le profil de l'employé authentifié
@router.get("/employees/me")
async def get_my_profile(
    current_employee: EmployeeModel = Depends(get_current_employee),
):
    return {
        "id": current_employee.id,
        "email": current_employee.email,
        "name": current_employee.name,
        "isRH": current_employee.isRH,
        "isAdmin": current_employee.isAdmin,
    }


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
