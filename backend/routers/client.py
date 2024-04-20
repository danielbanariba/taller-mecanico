from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.sql import select, insert, update, delete

# Crear la base de datos si no existe
engine = create_engine("sqlite:///cliente.db")
metadata = MetaData()

# Definir la tabla de clientes
clientes = Table(
    'clientes', metadata, 
    Column('id', Integer, primary_key=True), 
    Column('nombre', String), 
    Column('email', String),
)

metadata.create_all(engine)

app = FastAPI()

# Modelo para recibir datos del cliente desde el frontend
class Cliente(BaseModel):
    nombre: str
    email: str

# Ruta para obtener todos los clientes
@app.get("/clientes", response_model=List[Cliente])
async def get_clientes():
    conn = engine.connect()
    query = select([clientes])
    result = conn.execute(query)
    return [Cliente(nombre=row['nombre'], email=row['email']) for row in result]

# Ruta para obtener un cliente por id
@app.get("/clientes/{cliente_id}", response_model=Cliente)
async def get_cliente(cliente_id: int):
    conn = engine.connect()
    query = select([clientes]).where(clientes.c.id == cliente_id)
    result = conn.execute(query).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return Cliente(nombre=result['nombre'], email=result['email'])

# Ruta para agregar un nuevo cliente
@app.post("/clientes", response_model=Cliente)
async def create_cliente(cliente: Cliente):
    conn = engine.connect()
    query = insert(clientes).values(nombre=cliente.nombre, email=cliente.email)
    result = conn.execute(query)
    return Cliente(nombre=cliente.nombre, email=cliente.email)

# Ruta para actualizar un cliente
@app.put("/clientes/{cliente_id}", response_model=Cliente)
async def update_cliente(cliente_id: int, cliente: Cliente):
    conn = engine.connect()
    query = update(clientes).where(clientes.c.id == cliente_id).values(nombre=cliente.nombre, email=cliente.email)
    result = conn.execute(query)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# Ruta para eliminar un cliente
@app.delete("/clientes/{cliente_id}")
async def delete_cliente(cliente_id: int):
    conn = engine.connect()
    query = delete(clientes).where(clientes.c.id == cliente_id)
    result = conn.execute(query)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado con éxito"}