# Sistema de Gestão de Compras - SLA

Sistema completo de gestão de solicitações de compras com controle de SLA, desenvolvido em Streamlit para deploy em EC2 com PostgreSQL local.

## 🚀 Funcionalidades

- **Gestão de Solicitações**: Criação, acompanhamento e aprovação de solicitações
- **Controle de SLA**: Monitoramento automático de prazos por prioridade
- **Fluxo de Aprovação**: Sistema hierárquico de aprovações (Gerência/Diretoria)
- **Gestão de Suprimentos**: Cotações, requisições e controle de estoque
- **Dashboard Administrativo**: Relatórios e métricas completas
- **Sistema de Usuários**: Perfis diferenciados (Admin, Solicitante, Suprimentos, Diretoria)

## 📋 Perfis de Usuário

### Solicitante
- Criar novas solicitações
- Acompanhar status das próprias solicitações
- Visualizar histórico pessoal

### Suprimentos
- Gerenciar requisições
- Fazer cotações
- Controlar catálogo de produtos
- Movimentar solicitações no fluxo

### Gerência & Diretoria
- Aprovar/reprovar solicitações
- Visualizar solicitações pendentes
- Acompanhar métricas gerenciais

### Administrador
- Gestão completa de usuários
- Configurações do sistema
- Relatórios e dashboards
- Controle de limites e SLAs

## 🔧 Deploy na EC2

### Pré-requisitos
- EC2 Ubuntu 24.04 LTS
- PostgreSQL 16+ instalado
- Python 3.8+
- Chave SSH configurada

### Instalação na EC2

1. **Conecte-se à EC2:**
```bash
ssh -i chavepem/Compras.pem ubuntu@SEU_IP_EC2
```

2. **Clone o repositório:**
```bash
git clone <url-do-repositorio>
cd Sistema_Compras
```

3. **Instale dependências:**
```bash
sudo apt update
sudo apt install python3-pip python3-venv postgresql postgresql-contrib
pip3 install -r requirements_ec2.txt
```

4. **Configure PostgreSQL:**
```bash
sudo -u postgres psql
CREATE DATABASE sistema_compras;
CREATE USER postgres WITH PASSWORD 'postgres123';
GRANT ALL PRIVILEGES ON DATABASE sistema_compras TO postgres;
\q
```

5. **Configure variáveis de ambiente para o banco (sem secrets_local.toml):**
Defina uma das opções abaixo no serviço que executa o Streamlit:

Opção A — única string:
```
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/sistema_compras
```

Opção B — variáveis PG*:
```
PGHOST=localhost
PGDATABASE=sistema_compras
PGUSER=postgres
PGPASSWORD=postgres123
PGPORT=5432
```

6. **Inicialize usuários padrão:**
```bash
python3 setup_users_local.py
```

7. **Execute a aplicação:**
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Acesso ao Sistema

- **URL**: http://SEU_IP_EC2:8501
- **Porta**: 8501 (configure security group da EC2)

## 👥 Usuários Padrão

Após executar `setup_users_local.py`:

- **admin** / admin123 (Administrador)
- **Leonardo.Fragoso** / Teste123 (Solicitante)
- **Genival.Silva** / Teste123 (Solicitante)
- **Diretoria** / Teste123 (Aprovador)
- **Fabio.Ramos** / Teste123 (Suprimentos)

## 📊 Fluxo de Processo (8 Etapas)

1. **Solicitação** - Criada pelo solicitante
2. **Suprimentos** - Análise técnica e cotações
3. **Em Cotação** - Processo de cotação ativo
4. **Aguardando Aprovação** - Pendente de aprovação gerencial
5. **Aprovado/Reprovado** - Decisão da gerência/diretoria
6. **Compra Feita** - Pedido realizado
7. **Aguardando Entrega** - Produto em trânsito
8. **Pedido Finalizado** - Processo concluído

## 📈 Métricas e SLA

### SLA por Prioridade
- **Urgente**: 1 dia útil
- **Alta**: 2 dias úteis
- **Normal**: 3 dias úteis
- **Baixa**: 5 dias úteis

### Relatórios Disponíveis
- Taxa de cumprimento de SLA
- Tempo médio de atendimento
- Solicitações por departamento
- Performance por colaborador
- Histórico completo de movimentações
- Exportação Excel/CSV com formatação PT-BR

## 🗄️ Arquitetura do Sistema

### Banco de Dados PostgreSQL Local
- **Conexão**: Via `database_local.py`
- **Tabelas**: usuarios, solicitacoes, configuracoes, catalogo_produtos, movimentacoes, notificacoes, sessoes
- **Índices**: Otimizados para performance
- **Backup**: Dados locais na EC2

### Estrutura do Projeto
```
Sistema_Compras/
├── app.py                    # Aplicação principal
├── database_local.py         # Gerenciador PostgreSQL local
├── session_manager.py        # Gestão de sessões
├── setup_users_local.py      # Setup inicial de usuários
├── style.py                  # Estilos CSS customizados
├── (variáveis de ambiente)    # Configuração PostgreSQL (DATABASE_URL ou PG*)
├── requirements_ec2.txt      # Dependências para EC2
├── profiles/                 # Módulos por perfil de usuário
│   ├── admin.py
│   ├── solicitante.py
│   ├── suprimentos.py
│   └── diretoria.py
├── assets/                   # Recursos estáticos
├── uploads/                  # Arquivos enviados
└── chavepem/                 # Chave SSH da EC2
    └── Compras.pem
```

## 🔒 Segurança

- Autenticação SHA256
- Sessões persistentes no PostgreSQL
- Dados locais (sem dependência cloud)
- Controle de acesso por perfil
- Backup local na EC2

## 🚀 Produção

### Para ambiente de produção, configure:

1. **Nginx como proxy reverso**
2. **Supervisor para auto-restart**
3. **SSL/HTTPS**
4. **Firewall adequado**
5. **Backup automático**

### Comandos úteis:

```bash
# Verificar status do PostgreSQL
sudo systemctl status postgresql

# Reiniciar aplicação
pkill -f streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Backup do banco
pg_dump -U postgres sistema_compras > backup_$(date +%Y%m%d).sql
```

## 📞 Suporte

Sistema otimizado para EC2 + PostgreSQL local, sem dependências de serviços cloud externos.

---

**Desenvolvido com ❤️ para otimizar processos de compras na EC2**