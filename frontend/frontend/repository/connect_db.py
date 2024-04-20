from sqlalchemy import create_engine

def connect():
    engine = create_engine("mysql+pymysql://root:root1234@localhost:3306/prueba-concepto")
    return engine