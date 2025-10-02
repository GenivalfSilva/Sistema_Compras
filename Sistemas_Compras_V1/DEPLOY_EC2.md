# Deploy do Sistema de Compras na AWS EC2

Este guia detalha como fazer o deploy do Sistema de Compras em uma instância EC2 da Amazon com PostgreSQL local.

## 📋 Pré-requisitos

- Instância EC2 Ubuntu 20.04 LTS ou superior
- Acesso SSH à instância
- Domínio ou IP público configurado
- Pelo menos 2GB de RAM e 20GB de storage

## 🚀 Passo a Passo

### 1. Preparar a Instância EC2

```bash
# Conectar via SSH
ssh -i sua-chave.pem ubuntu@seu-ip-ec2

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y python3 python3-pip python3-venv git nginx supervisor
```

### 2. Instalar PostgreSQL

```bash
# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Iniciar serviço
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configurar usuário postgres
sudo -u postgres psql
```

No prompt do PostgreSQL:
```sql
ALTER USER postgres PASSWORD 'postgres123';
CREATE DATABASE sistema_compras;
\q
```

### 3. Configurar PostgreSQL

```bash
# Editar configuração do PostgreSQL
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Alterar:
```
listen_addresses = 'localhost'
port = 5432
```

```bash
# Editar autenticação
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Alterar linha local:
```
local   all             all                                     md5
```

```bash
# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

### 4. Preparar Aplicação

```bash
# Criar usuário para aplicação
sudo useradd -m -s /bin/bash compras
sudo su - compras

# Clonar/copiar projeto
git clone <seu-repositorio> sistema_compras
# OU
# scp -r sistema_compras ubuntu@ip:/home/compras/

cd sistema_compras

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements_ec2.txt
```

### 5. Configurar Banco de Dados

```bash
# Ainda como usuário compras
cd sistema_compras

# Executar setup do banco
python setup_postgres_local.py

# Verificar se tudo funcionou
python -c "from database_local import get_local_database; db = get_local_database(); print('✅ Banco OK' if db.db_available else '❌ Erro no banco')"
```

### 6. Configurar Nginx

```bash
# Voltar para usuário ubuntu/root
exit
sudo nano /etc/nginx/sites-available/sistema_compras
```

Conteúdo do arquivo:
```nginx
server {
    listen 80;
    server_name seu-dominio.com;  # ou IP público

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/sistema_compras /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Configurar Supervisor

```bash
sudo nano /etc/supervisor/conf.d/sistema_compras.conf
```

Conteúdo:
```ini
[program:sistema_compras]
command=/home/compras/sistema_compras/venv/bin/streamlit run app_local.py --server.port=8501 --server.address=127.0.0.1 --server.headless=true
directory=/home/compras/sistema_compras
user=compras
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/sistema_compras.log
environment=PATH="/home/compras/sistema_compras/venv/bin"
```

```bash
# Atualizar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start sistema_compras
```

### 8. Configurar Firewall

```bash
# Configurar UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### 9. Verificar Deploy

```bash
# Verificar status dos serviços
sudo systemctl status postgresql
sudo systemctl status nginx
sudo supervisorctl status sistema_compras

# Verificar logs
sudo tail -f /var/log/sistema_compras.log
sudo tail -f /var/log/nginx/access.log
```

Acesse: `http://seu-ip-ou-dominio`

## 🔧 Configurações Adicionais

### SSL/HTTPS com Let's Encrypt

```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Renovação automática
sudo crontab -e
```

Adicionar linha:
```
0 12 * * * /usr/bin/certbot renew --quiet
```

### Backup Automático

```bash
# Criar script de backup
sudo nano /home/compras/backup_db.sh
```

Conteúdo:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/compras/backups"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -U postgres -h localhost sistema_compras > $BACKUP_DIR/sistema_compras_$DATE.sql

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "sistema_compras_*.sql" -mtime +7 -delete

echo "Backup concluído: sistema_compras_$DATE.sql"
```

```bash
# Tornar executável
chmod +x /home/compras/backup_db.sh

# Agendar backup diário
sudo crontab -e
```

Adicionar:
```
0 2 * * * /home/compras/backup_db.sh
```

### Monitoramento

```bash
# Instalar htop para monitoramento
sudo apt install -y htop

# Script de monitoramento
nano /home/compras/monitor.sh
```

Conteúdo:
```bash
#!/bin/bash
echo "=== Status dos Serviços ==="
sudo systemctl status postgresql --no-pager -l
sudo systemctl status nginx --no-pager -l
sudo supervisorctl status sistema_compras

echo "=== Uso de Recursos ==="
free -h
df -h
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Aplicação não inicia:**
   ```bash
   sudo supervisorctl tail -f sistema_compras
   ```

2. **Erro de conexão com banco:**
   ```bash
   sudo -u postgres psql -c "SELECT version();"
   ```

3. **Nginx não funciona:**
   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

4. **Porta 8501 ocupada:**
   ```bash
   sudo netstat -tulpn | grep 8501
   sudo kill -9 <PID>
   ```

### Logs Importantes

- Aplicação: `/var/log/sistema_compras.log`
- Nginx: `/var/log/nginx/access.log` e `/var/log/nginx/error.log`
- PostgreSQL: `/var/log/postgresql/postgresql-*-main.log`
- Supervisor: `/var/log/supervisor/supervisord.log`

## 📊 Monitoramento de Performance

### Métricas Importantes

1. **CPU e Memória:**
   ```bash
   htop
   ```

2. **Espaço em Disco:**
   ```bash
   df -h
   ```

3. **Conexões PostgreSQL:**
   ```bash
   sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
   ```

4. **Status da Aplicação:**
   ```bash
   curl -I http://localhost:8501
   ```

## 🚨 Segurança

### Recomendações

1. **Firewall configurado** (UFW ativado)
2. **PostgreSQL apenas local** (não exposto externamente)
3. **Nginx como proxy reverso**
4. **SSL/HTTPS configurado**
5. **Backups automáticos**
6. **Logs monitorados**
7. **Usuário dedicado** (não root)

### Atualizações

```bash
# Atualizar sistema mensalmente
sudo apt update && sudo apt upgrade -y

# Atualizar aplicação
cd /home/compras/sistema_compras
git pull
sudo supervisorctl restart sistema_compras
```

## ✅ Checklist de Deploy

- [ ] Instância EC2 configurada
- [ ] PostgreSQL instalado e configurado
- [ ] Banco de dados criado com setup_postgres_local.py
- [ ] Aplicação instalada com requirements_ec2.txt
- [ ] Nginx configurado como proxy reverso
- [ ] Supervisor configurado para auto-restart
- [ ] Firewall configurado (UFW)
- [ ] SSL/HTTPS configurado (opcional)
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] Teste de acesso realizado

## 📞 Suporte

Em caso de problemas:

1. Verificar logs da aplicação
2. Verificar status dos serviços
3. Verificar conectividade de rede
4. Verificar recursos do sistema (CPU/RAM/Disk)
5. Consultar documentação do PostgreSQL/Nginx/Streamlit
