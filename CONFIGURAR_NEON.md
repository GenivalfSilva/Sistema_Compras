# 🔧 Como Configurar o Neon DB

## 📋 Passo 1: Obter Credenciais do Neon Console

1. **Acesse seu projeto no Neon Console** (como mostrado na imagem)
2. **Clique em "Connect"** no dashboard
3. **Copie a connection string** que aparece no formato:
   ```
   postgresql://neondb_owner:password@ep-xxx-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

## 📝 Passo 2: Criar Arquivo de Configuração

Crie um arquivo chamado `secrets.toml` na pasta do projeto com o seguinte conteúdo:

```toml
[postgres]
host = "ep-xxx-xxx.us-east-1.aws.neon.tech"  # Seu endpoint
database = "neondb"                           # Nome do banco
user = "neondb_owner"                        # Seu usuário
password = "sua-senha-aqui"                  # Sua senha
port = 5432
sslmode = "require"
```

### Exemplo Real:
Se sua connection string for:
```
postgresql://neondb_owner:abc123xyz@ep-aged-cloud-12345.us-east-1.aws.neon.tech/neondb?sslmode=require
```

Seu `secrets.toml` deve ficar:
```toml
[postgres]
host = "ep-aged-cloud-12345.us-east-1.aws.neon.tech"
database = "neondb"
user = "neondb_owner"
password = "abc123xyz"
port = 5432
sslmode = "require"
```

## 🚀 Passo 3: Executar o Setup

Depois de criar o arquivo `secrets.toml`, execute:

```bash
python setup_neon_db.py
```

## ⚡ Alternativa Rápida: Variável de Ambiente

Se preferir, você pode definir a variável de ambiente:

```bash
# Windows (PowerShell)
$env:DATABASE_URL="postgresql://neondb_owner:password@ep-xxx-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Windows (CMD)
set DATABASE_URL=postgresql://neondb_owner:password@ep-xxx-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require

# Depois execute o setup
python setup_neon_db.py
```

## 🔍 Como Encontrar suas Credenciais no Neon Console

### Método 1: Connection String Completa
1. No dashboard do Neon, clique em **"Connect"**
2. Selecione **"Connection string"**
3. Copie a string completa que aparece

### Método 2: Parâmetros Individuais
1. No dashboard do Neon, clique em **"Connect"**
2. Selecione **"Parameters"**
3. Copie cada campo individualmente:
   - **Host**: ep-xxx-xxx.region.aws.neon.tech
   - **Database**: neondb (ou o nome que você definiu)
   - **Username**: neondb_owner (ou seu usuário)
   - **Password**: sua senha

## 🛠️ Instalação de Dependências

Antes de executar o setup, instale as dependências:

```bash
pip install psycopg2-binary toml
```

## ✅ Verificação

Para testar se a configuração está correta, execute:

```bash
python configure_neon.py
```

Este script irá:
- ✅ Verificar se as credenciais estão configuradas
- ✅ Testar a conexão com o banco
- ✅ Criar o arquivo `secrets.toml` se necessário

## 🎯 Resumo dos Arquivos

Após a configuração, você terá:

- `secrets.toml` - Credenciais do banco
- `setup_neon_db.py` - Script principal de setup
- `configure_neon.py` - Script para testar conexão
- `SETUP_NEON_DB.md` - Documentação completa

## 🔧 Solução de Problemas

### Erro: "Não foi possível conectar ao banco"
1. Verifique se o arquivo `secrets.toml` existe
2. Confirme se as credenciais estão corretas
3. Teste a conexão com `python configure_neon.py`

### Erro: "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Erro: "toml not found"
```bash
pip install toml
```

### Erro de SSL
Certifique-se que `sslmode = "require"` está no `secrets.toml`