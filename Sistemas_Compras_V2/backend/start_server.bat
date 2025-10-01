@echo off
echo 🚀 Iniciando Django V2 Backend Server...
echo ==========================================

cd /d "%~dp0"

echo 📋 Verificando ambiente...
if exist "venv\Scripts\activate.bat" (
    echo ✅ Virtual environment encontrado
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment não encontrado, usando Python global
)

echo 📦 Verificando dependências...
python -c "import django; print(f'✅ Django {django.get_version()} instalado')" 2>nul || (
    echo ❌ Django não encontrado! Instalando...
    pip install -r requirements.txt
)

echo 🗄️  Verificando banco de dados...
if exist "db\sistema_compras_v1.db" (
    echo ✅ Banco V1 encontrado
) else (
    echo ❌ Banco V1 não encontrado! Execute copy_v1_database.py primeiro
    pause
    exit /b 1
)

echo 🔧 Aplicando migrações...
python manage.py migrate --run-syncdb

echo 🌐 Iniciando servidor Django...
echo.
echo 📡 API Endpoints disponíveis:
echo    - http://127.0.0.1:8000/api/usuarios/test/
echo    - http://127.0.0.1:8000/api/usuarios/
echo    - http://127.0.0.1:8000/api/solicitacoes/
echo    - http://127.0.0.1:8000/api/catalogo/
echo    - http://127.0.0.1:8000/api/configuracoes/
echo    - http://127.0.0.1:8000/api/auditoria/
echo.
echo ⚡ Pressione Ctrl+C para parar o servidor
echo ==========================================

python manage.py runserver
