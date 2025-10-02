@echo off
echo 🔧 CORRIGINDO AUTENTICACAO POSTGRESQL
echo =====================================

set PG_DATA="C:\Program Files\PostgreSQL\17\data"
set PG_HBA=%PG_DATA%\pg_hba.conf
set PG_HBA_BACKUP=%PG_DATA%\pg_hba.conf.backup

echo Fazendo backup do pg_hba.conf...
copy %PG_HBA% %PG_HBA_BACKUP%

echo Parando PostgreSQL...
net stop postgresql-x64-17

echo Modificando pg_hba.conf para trust...
powershell -Command "(Get-Content '%PG_HBA%') -replace 'local\s+all\s+postgres\s+peer', 'local   all             postgres                                trust' | Set-Content '%PG_HBA%'"
powershell -Command "(Get-Content '%PG_HBA%') -replace 'host\s+all\s+all\s+127\.0\.0\.1/32\s+scram-sha-256', 'host    all             all             127.0.0.1/32            trust' | Set-Content '%PG_HBA%'"
powershell -Command "(Get-Content '%PG_HBA%') -replace 'host\s+all\s+all\s+::1/128\s+scram-sha-256', 'host    all             all             ::1/128                 trust' | Set-Content '%PG_HBA%'"

echo Iniciando PostgreSQL...
net start postgresql-x64-17

echo Aguardando PostgreSQL iniciar...
timeout /t 5 /nobreak > nul

echo Resetando senha do postgres...
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -p 5432 -d postgres -c "ALTER USER postgres PASSWORD 'postgres123';"

echo Restaurando pg_hba.conf original...
copy %PG_HBA_BACKUP% %PG_HBA%

echo Reiniciando PostgreSQL com configuracao original...
net stop postgresql-x64-17
net start postgresql-x64-17

echo Aguardando PostgreSQL reiniciar...
timeout /t 3 /nobreak > nul

echo ✅ Testando conexao com nova senha...
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', database='postgres', user='postgres', password='postgres123', port=5432); print('✅ SUCESSO! Conexao PostgreSQL OK!'); conn.close()"

echo.
echo ✅ Senha do PostgreSQL alterada para: postgres123
echo ✅ Agora execute: python setup_postgres_windows.py
pause
