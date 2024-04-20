from pydantic import BaseModel

class VendedorBase(BaseModel):
    primer_nombre: str
    segundo_nombre: str
    dni: str
    telefono_vendedor: str
    correo_vendedor: str

class VendedorCreate(VendedorBase):
    pass

class Vendedor(VendedorBase):
    id: int
    proveedor_id: int

    class Config:
        orm_mode = True

class ProveedorBase(BaseModel):
    direccion: str
    nombre_proveedor: str
    rtn: str
    telefono_proveedor: str
    correo_proveedor: str

class ProveedorCreate(ProveedorBase):
    pass

class Proveedor(ProveedorBase):
    id: int
    vendedores: List[Vendedor] = []

    class Config:
        orm_mode = True