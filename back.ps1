Set-Location env/Scripts
.\activate.ps1
Set-Location ..
Set-Location ..
Set-Location .\backend
uvicorn main:app --reload