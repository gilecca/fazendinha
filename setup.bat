@echo off
chcp 65001 >nul
echo.
echo  ==========================================
echo   FEIRA DIGITAL --- Setup da Fazendinha
echo  ==========================================
echo.

cd /d "%~dp0"

echo [1/5] Criando ambiente virtual...
python -m venv venv
if errorlevel 1 ( echo ERRO: Python nao encontrado. Instale em python.org & pause & exit /b 1 )

echo [2/5] Instalando dependencias...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if errorlevel 1 ( echo ERRO ao instalar dependencias & pause & exit /b 1 )

echo [3/5] Criando banco de dados...
python manage.py migrate
if errorlevel 1 ( echo ERRO nas migrations & pause & exit /b 1 )

echo [4/5] Populando dados de exemplo...
python manage.py seed_data

echo [5/5] Criando superusuario admin...
python manage.py shell -c "from core.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@feira.com','admin123')"

echo.
echo  ==========================================
echo   PRONTO! Servidor iniciando com WebSocket
echo  ==========================================
echo.
echo  Acesse: http://127.0.0.1:8000
echo  Admin:  http://127.0.0.1:8000/admin
echo.
echo  Logins:
echo    Produtor 1:  fazenda_bela  / fazenda123
echo    Produtor 2:  sitio_verde   / fazenda123
echo    Consumidor:  ana_consumidora / teste123
echo    Admin:       admin / admin123
echo.

venv\Scripts\daphne.exe -b 127.0.0.1 -p 8000 feira_digital.asgi:application
pause
