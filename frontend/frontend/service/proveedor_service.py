from ..repository.proveedor_repository import select_all

def select_all_proveedor_serice():
    proveedores = select_all()
    print(proveedores)
    return proveedores