from ..repository.inventario_repository import select_all, select_inventario_by_id, create_inventario, delete_inventario
from ..model.iventario_model import Inventario
import cx_Oracle

def select_all_inventario_service():
    inventarios = select_all()
    print(inventarios)
    return inventarios

def select_inventario_by_id_service(id_inventario: int):
    if id_inventario:
        return select_inventario_by_id(id_inventario)
    else:
        return select_all()

def create_inventario_service(id_inventario: int, cantidad_productos: int, fecha_entrada: str, fecha_salida: str, id_repuesto: int):
    inventario = select_inventario_by_id(id_inventario)
    if not inventario:
        inventario_save = Inventario(id_inventario=id_inventario, cantidad_productos=cantidad_productos, fecha_entrada=fecha_entrada, fecha_salida=fecha_salida, id_repuesto=id_repuesto)
        try:
            return create_inventario(inventario_save)
        except cx_Oracle.IntegrityError as e:
            if 'ORA-00001' in str(e):
                print("An inventory with this ID already exists.")
                raise
            else:
                raise
    else:
        print("An inventory with this ID already exists.")
        raise BaseException("An inventory with this ID already exists.")

def delete_inventario_service(id_inventario: int):
    return delete_inventario(id_inventario)
