from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

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

# Inicializar CryptContext
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

@app.post("/login/")
async def login(user: UserIn, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"status": "Logged in"}

#Crear usuario mtiendose en la direccion, automaticamente lo mete en la base de datos
@app.post("/create_user/")
async def create_user(user: UserIn, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    return {"status": "User created"}