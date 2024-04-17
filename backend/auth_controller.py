import jwt
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext
import os

# Configuración de la base de datos
engine = create_engine('sqlite:///./users.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de usuario
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

# Crear la tabla de usuarios en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar FastAPI
app = FastAPI()

# Inicializar CryptContext, esto es para hashear y verificar las contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelo de Pydantic para el usuario
class UserIn(BaseModel):
    username: str
    password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ES UNA PESIMA PRACTICA HACER ESTO, pero lo hago para simplificar el ejemplo
SECRET_KEY = "41f45ce3d02c0798d1f68155163b18c038aaa6d6251866439a32dfeb556a9c1a"  

def get_user_from_token(token: str, db: Session):
    try:
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Aquí puedes obtener la información del usuario del payload.
        # Por ejemplo, si el payload tiene un campo 'username', puedes hacer:
        username = payload.get("username")
        
        # Luego, puedes buscar al usuario en tu base de datos y devolverlo.
        # Por ejemplo:
        db_user = db.query(User).filter(User.username == username).first()
        
        return db_user
    except jwt.PyJWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user_from_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.post("/login/")
async def login(user: UserIn, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Aquí debes implementar la lógica para generar y devolver un token de acceso
    token = jwt.encode({"username": db_user.username}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/create_user/")
async def create_user(user: UserIn, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    return {"status": "User created"}

@app.get("/estadisticas/")
async def estadisticas(current_user: User = Depends(get_current_user)):
    return {"message": "Estadísticas"}