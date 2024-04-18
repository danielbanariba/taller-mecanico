<div align="center">
  <h1 align="center">Taller Mecanico</a></h1>
</div>

<div align="center">
  <img align="center" src="frontend/assets/logo2.jpg" alt="soundcloud" width="50%">
</div>
<br>

## Ir a la documentacion para la creacion de un entorno virtual
https://docs.python.org/3/library/venv.html

## 👨‍💻 Crear un entorno virtual
 ```sh
python -m venv /path/to/new/virtual/environment
```
 ```sh
python -m venv env
```

Acceder a la carpeta env, scripts 
```sh
cd env/Scripts
```

y por ultimo activarlo, y ya estaremos en el entorno virtual
```sh
.\activate.ps1
```
<!-- Installation -->
### :gear: Instalacion
  
Librerias que se tienen que instalar:
```sh
pip install fastapi
```
```sh
pip install "uvicorn[standard]"
```
```sh
pip install reflex
```
```sh
pip install pydantic
```
```sh
pip install pandas
```
```sh
pip install sqlalchemy
```
```sh
pip install passlib
```
```sh
pip install typing
```
```sh
pip install requests
```
```sh
pip install bcrypt
```
```sh
pip install pyjwt
```

## Aqui esta la estructura de carpetas del TallerMecanico
```bash
TALLER-MECANICO/
|- backend/
  |-- db/
    |--- TALLER_MECANICO.db
  |-- models/
    |--- client.py
  |-- routers/
|- env/

|- frontend/
  |-- assets/
  |-- frontend/
    |-- components/
    |-- styles/
    |-- view/
    |-- frontend.py/
    |-- login.py/
    |-- URL.py/
```

<!-- TENGO QUE DEJAR PASO A PASO QUE TIENE QUE HACER! -->
## Instruciones antes de probar el proyecto: 

Despues de a ver cloneado e instalado todas la dependencia y la estructura de carpetas quede exactamente igual que en el ejemplo de arriba lo que sigue es lo siquiente:

#### Paso 1:
Abrimos dos terminamles una para levantar Reflex(frontend) y la otra para FastAPI(backend)

#### Paso 2:
Nos vamos a la terminal del backend y ponemos:
```sh
cd backend
```
```sh
uvicorn auth_controller:app --reload
```

#### Paso 3:
Una vez levantado el backend ahora tenemos que levantar el frontend, nos dirigimos a la otra terminal y ponemos:
```sh
cd frontend/
```
```sh
cd reflex init
```
```sh
cd reflex run
```

#### Paso 4:
> [!WARNING] 
> ESTO SOLO ES PARA FIN DE EJEMPLO
>

Nos vamos a la herramienta Thunder Client, Postman o cualquier otra, y hacemos una nueva peticion de tipo POST para poder crear un nuevo usuario
Ponemos la direccion "localhost:8000/create_user/" 

<!-- Run Locally -->
## :running: Correr el servidor

Abrir dos terminames donde uno se dirija al backend y el otro al frontend

```sh
python -m uvicorn main:app –reload
```
  
Si va a levatar el servidor desde visual studio code
```sh
uvicorn main:app
```
<!-- TechStack -->
## 👀 Ir a la documentación

### Swagger:
```sh
127.0.0.1:8000/docs
```
### Redocly:
```sh
127.0.0.1:8000/redoc
```
<!-- TechStack -->
## :space_invader: Tecnologias utilizadas
<p align="left">
<a href="https://www.python.org/" target="_blank"><img src="https://img.icons8.com/color/144/000000/python--v1.png" alt="Python" width="50" height="50"/> </a>
<a href="https://www.oracle.com/database/" target="_blank"> <img src="https://img.icons8.com/color/144/000000/oracle-logo.png" alt="Oracle SQL" width="50" height="50"/> </a>
<a href="https://fastapi.tiangolo.com/" target="_blank"> <img src="/assets/fastapi-logo.svg" alt="FastAPI" width="50" height="50"/> </a> 
</p>