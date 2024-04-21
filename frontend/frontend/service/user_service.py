from ..repository.user_repository import select_all, select_user_by_email, create_user, delete_user
from ..model.user_model import User
import cx_Oracle  # Importamos el módulo cx_Oracle para manejar errores de Oracle

# Esta función obtiene todos los usuarios
def select_all_user_serice():
    users = select_all()  
    print(users) 
    return users 


def selec_user_by_email_service(email: str):
    if(len(email) != 0):  # Si el email no está vacío
        return select_user_by_email(email)  # Devolvemos el usuario con ese email
    else:
        return select_all()  # Si el email está vacío, devolvemos todos los usuarios

# Esta función crea un nuevo usuario
def create_user_service(username: str, password: str, phone: str, name: str):
    user = select_user_by_email(username)  # Buscamos si ya existe un usuario con ese email
    if not user:  # Si no existe
        user_save = User(username=username, password=password, phone=phone, name=name)  # Creamos un nuevo usuario
        try:
            return create_user(user_save)  # Intentamos guardar el nuevo usuario
        except cx_Oracle.IntegrityError as e:  # Si hay un error de integridad de Oracle
            if 'ORA-00001' in str(e):  # Si el error es de violación de restricción única
                print("A user with this email already exists.")  # Imprimimos un mensaje de error
                raise  # Relevamos el error
            else:
                raise  # Si el error es de otro tipo, también lo relevamos
    else:  # Si ya existe un usuario con ese email
        print("A user with this email already exists.")  # Imprimimos un mensaje de error
        raise BaseException("A user with this email already exists.")  # Lanzamos una excepción
    
def delete_user_service(email: str):
    return delete_user(email=email)  # Eliminamos el usuario con ese email