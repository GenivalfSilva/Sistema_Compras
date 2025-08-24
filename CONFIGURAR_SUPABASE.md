# 🚀 Configuração do Supabase para Sistema de Compras

## 📋 Passo a Passo - Configuração Completa

### 1️⃣ **Criar Conta no Supabase**
1. Acesse: https://supabase.com
2. Clique em "Start your project"
3. Faça login com GitHub (recomendado) ou email
4. É **100% gratuito** - não precisa cartão de crédito

### 2️⃣ **Criar Novo Projeto**
1. Clique em "New Project"
2. **Nome do projeto**: `sistema-compras-sla`
3. **Database Password**: Crie uma senha forte (anote!)
4. **Region**: `South America (São Paulo)` (mais próximo)
5. Clique em "Create new project"
6. ⏳ Aguarde 2-3 minutos para provisionar

### 3️⃣ **Obter Credenciais de Conexão**
1. No dashboard do projeto, vá em **Settings** → **Database**
2. Na seção **Connection string**, copie a **URI**
3. Exemplo: `postgresql://postgres:[YOUR-PASSWORD]@db.abc123xyz.supabase.co:5432/postgres`
4. **Substitua `[YOUR-PASSWORD]`** pela senha que você criou

### 4️⃣ **Configurar no Sistema**
1. Abra o arquivo `secrets_supabase.toml` (será criado automaticamente)
2. Cole suas credenciais:

```toml
[postgres]
host = "db.abc123xyz.supabase.co"
port = 5432
database = "postgres"
username = "postgres"
password = "SUA_SENHA_AQUI"

[database]
url = "postgresql://postgres:SUA_SENHA_AQUI@db.abc123xyz.supabase.co:5432/postgres"
```

### 5️⃣ **Executar Migração**
```bash
# No terminal, execute:
python setup_supabase_db.py
```

## ✅ **Vantagens do Supabase vs Neon**

| Recurso | Neon (Problema) | Supabase (Solução) |
|---------|-----------------|-------------------|
| **Limite de Tempo** | ❌ 100h/mês | ✅ Sem limite |
| **Storage** | 512MB | ✅ 500MB + 2GB transfer |
| **Uptime** | ❌ Suspende projeto | ✅ 24/7 disponível |
| **Backup** | Limitado | ✅ Backup automático |
| **Dashboard** | Básico | ✅ Interface avançada |
| **Compatibilidade** | PostgreSQL | ✅ PostgreSQL 100% |

## 🔧 **Recursos Extras do Supabase**
- **Dashboard SQL**: Execute queries direto no browser
- **Table Editor**: Edite dados visualmente
- **API REST**: Acesso automático via API
- **Real-time**: Atualizações em tempo real
- **Storage**: Para uploads de arquivos
- **Auth**: Sistema de autenticação integrado

## 🚨 **Solução Definitiva**
- ✅ **Zero alterações no código** (mesmo PostgreSQL)
- ✅ **Sem mais erros de quota**
- ✅ **Performance superior**
- ✅ **Gratuito permanente**
- ✅ **Backup automático**

## 📞 **Suporte**
- Documentação: https://supabase.com/docs
- Dashboard: https://app.supabase.com
- Status: https://status.supabase.com
