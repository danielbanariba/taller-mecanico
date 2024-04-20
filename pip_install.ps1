python -m venv /path/to/new/virtual/environment

# Crear un entorno virtual
python -m venv env

# Activar el entorno virtual
Set-Location env/Scripts
.\activate.ps1

Set-Location ..
Set-Location ..

# Ahora instalar los paquetes
pip install fastapi
pip install "uvicorn[standard]"
pip install reflex
pip install pydantic
pip install pandas
pip install sqlalchemy
pip install passlib
pip install typing
pip install requests
pip install bcrypt
pip install pyjwt
pip install pydantic[email]