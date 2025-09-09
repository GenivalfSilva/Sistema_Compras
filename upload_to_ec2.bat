@echo off
echo 🚀 Enviando arquivos atualizados para EC2...
echo.

set EC2_HOST=ubuntu@ec2-18-222-147-19.us-east-2.compute.amazonaws.com
set KEY_PATH=chavepem\Compras.pem
set REMOTE_PATH=/home/ubuntu/Sistema_Compras

echo 📁 Criando backup na EC2...
ssh -i "%KEY_PATH%" %EC2_HOST% "cd %REMOTE_PATH% && cp -r . ../Sistema_Compras_backup_$(date +%%Y%%m%%d_%%H%%M%%S) 2>/dev/null || echo 'Backup nao necessario - primeira instalacao'"

echo.
echo 📤 Enviando arquivos principais...
scp -i "%KEY_PATH%" app.py %EC2_HOST%:%REMOTE_PATH%/
scp -i "%KEY_PATH%" database_local.py %EC2_HOST%:%REMOTE_PATH%/
scp -i "%KEY_PATH%" session_manager.py %EC2_HOST%:%REMOTE_PATH%/
scp -i "%KEY_PATH%" setup_users_local.py %EC2_HOST%:%REMOTE_PATH%/
scp -i "%KEY_PATH%" style.py %EC2_HOST%:%REMOTE_PATH%/
scp -i "%KEY_PATH%" requirements_ec2.txt %EC2_HOST%:%REMOTE_PATH%/
scp -i "%KEY_PATH%" README.md %EC2_HOST%:%REMOTE_PATH%/

echo.
echo 📂 Enviando pasta profiles...
scp -i "%KEY_PATH%" -r profiles/ %EC2_HOST%:%REMOTE_PATH%/

echo.
echo 🎨 Enviando assets...
scp -i "%KEY_PATH%" -r assets/ %EC2_HOST%:%REMOTE_PATH%/

echo.
echo ✅ Upload concluído!
echo.
echo 🔧 Próximos passos na EC2:
echo 1. ssh -i "%KEY_PATH%" %EC2_HOST%
echo 2. cd %REMOTE_PATH%
echo 3. python3 setup_users_local.py
echo 4. streamlit run app.py --server.port 8501 --server.address 0.0.0.0
echo.
pause
