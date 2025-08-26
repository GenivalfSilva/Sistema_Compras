@echo off
echo 🔧 RESETANDO SENHA POSTGRESQL
echo ================================

echo Parando serviço PostgreSQL...
net stop postgresql-x64-17

echo Iniciando PostgreSQL em modo single-user...
"C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" -D "C:\Program Files\PostgreSQL\17\data" -l "C:\Program Files\PostgreSQL\17\data\logfile" start -o "-F -p 5433"

echo Aguarde 3 segundos...
timeout /t 3 /nobreak > nul

echo Resetando senha do usuário postgres...
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -p 5433 -c "ALTER USER postgres PASSWORD 'postgres123';"

echo Parando PostgreSQL temporário...
"C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" -D "C:\Program Files\PostgreSQL\17\data" stop

echo Reiniciando serviço PostgreSQL normal...
net start postgresql-x64-17

echo ✅ Senha resetada para: postgres123
echo Testando conexão...
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', database='postgres', user='postgres', password='postgres123', port=5432); print('✅ Conexão OK!'); conn.close()"

pause
