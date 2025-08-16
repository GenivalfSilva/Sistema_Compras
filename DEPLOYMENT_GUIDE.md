# 🚀 Guia de Deploy - Sistema de Gestão de Compras Ziran

## 📋 Resumo dos Problemas Resolvidos

### ❌ **Problemas Identificados:**
1. **Usuários não salvos**: Sistema JSON funcionava, mas sem persistência robusta
2. **Logout ao refresh**: `st.session_state` é volátil no Streamlit
3. **Incompatibilidade Streamlit Cloud**: Filesystem efêmero não suporta JSON local

### ✅ **Soluções Implementadas:**
1. **Sistema de banco híbrido**: SQLite local + PostgreSQL para cloud
2. **Sessões persistentes**: Sistema de tokens com expiração
3. **Migração automática**: Script para converter JSON → Database
4. **Compatibilidade**: Fallback para JSON se banco não disponível

## 🛠️ Arquivos Criados

### **1. `database.py`**
- Gerenciador de banco de dados híbrido
- Suporte SQLite (local) e PostgreSQL (cloud)
- Migração automática de dados JSON
- Sessões persistentes com expiração

### **2. `session_manager.py`**
- Gerenciamento de sessões persistentes
- Login/logout com tokens
- Restauração automática de sessão
- Integração com banco de dados

### **3. `migrate_to_db.py`**
- Script de migração JSON → Database
- Backup automático dos dados originais
- Testes de integridade
- Interface interativa

### **4. `secrets.toml.example`**
- Template para configurações do Streamlit Cloud
- Exemplos para PostgreSQL, MongoDB, MySQL
- Instruções de configuração

## 🔧 Como Usar Localmente

### **1. Instalar Dependências**
```bash
pip install -r requirements.txt
```

### **2. Migrar Dados (Opcional)**
```bash
python migrate_to_db.py migrate
```

### **3. Executar Aplicação**
```bash
streamlit run app.py
```

## ☁️ Deploy no Streamlit Cloud

### **1. Configurar Banco de Dados**

#### **Opção A: PostgreSQL (Recomendado)**
- Criar conta no [Supabase](https://supabase.com) ou [Railway](https://railway.app)
- Obter credenciais de conexão
- Criar arquivo `.streamlit/secrets.toml`:

```toml
[database]
host = "your-host.supabase.co"
name = "postgres"
user = "postgres"
password = "your-password"
port = "5432"
```

#### **Opção B: MongoDB Atlas**
```toml
[mongodb]
connection_string = "mongodb+srv://user:pass@cluster.mongodb.net/db"
```

### **2. Deploy no Streamlit Cloud**
1. Fazer push do código para GitHub
2. Conectar repositório no [Streamlit Cloud](https://share.streamlit.io)
3. Adicionar secrets via interface web
4. Deploy automático

### **3. Migração de Dados**
- Dados JSON serão migrados automaticamente na primeira execução
- Usuário admin criado automaticamente: `admin` / `admin123`

## 🔒 Funcionalidades de Sessão

### **Sessões Persistentes**
- ✅ Login mantido após refresh da página
- ✅ Expiração automática (24h por padrão)
- ✅ Logout seguro com limpeza de tokens
- ✅ Múltiplas sessões simultâneas

### **Segurança**
- ✅ Senhas hasheadas com salt
- ✅ Tokens UUID únicos
- ✅ Validação de expiração
- ✅ Limpeza automática de sessões expiradas

## 📊 Estrutura do Banco

### **Tabelas Criadas:**
- `usuarios`: Dados de usuários e autenticação
- `solicitacoes`: Solicitações de compra (futuro)
- `configuracoes`: Configurações do sistema
- `notificacoes`: Sistema de notificações
- `sessoes`: Sessões persistentes

## 🔄 Compatibilidade

### **Modo Híbrido**
- Se banco disponível: Usa database + sessões persistentes
- Se banco indisponível: Fallback para JSON + session_state
- Migração transparente entre modos

### **Dados Existentes**
- JSON mantido para compatibilidade
- Migração não destrutiva
- Backup automático criado

## 🧪 Testes

### **Testar Localmente:**
```bash
python migrate_to_db.py test
```

### **Verificar Funcionalidades:**
1. ✅ Criação de usuários
2. ✅ Login/logout
3. ✅ Persistência de sessão
4. ✅ Refresh da página
5. ✅ Múltiplos usuários

## 🚨 Troubleshooting

### **Erro: "Módulos de banco não encontrados"**
- Instalar dependências: `pip install psycopg2-binary`
- Verificar imports em `database.py`

### **Erro: "Conexão com banco falhou"**
- Verificar credenciais em `secrets.toml`
- Testar conectividade de rede
- Verificar firewall/VPN

### **Logout automático**
- Verificar se sessões estão sendo criadas
- Checar logs de erro no console
- Validar expiração de tokens

## 📈 Próximos Passos

1. **Migrar solicitações**: Mover dados de solicitações para banco
2. **Dashboard avançado**: Relatórios com dados do banco
3. **API REST**: Endpoints para integração externa
4. **Backup automático**: Rotinas de backup agendadas
5. **Auditoria**: Log de ações dos usuários

## 🎯 Benefícios Alcançados

- ✅ **Persistência robusta**: Dados salvos permanentemente
- ✅ **Sessões estáveis**: Sem logout ao refresh
- ✅ **Cloud-ready**: Compatível com Streamlit Cloud
- ✅ **Escalabilidade**: Suporte a múltiplos usuários
- ✅ **Segurança**: Autenticação e sessões seguras
- ✅ **Flexibilidade**: Funciona local e cloud
