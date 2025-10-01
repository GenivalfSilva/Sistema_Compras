# Sistema de Compras V2 - Backend Django

Backend do Sistema de Gestão de Compras V2 desenvolvido em Django REST Framework com SQLite.

## 🚀 Funcionalidades

### ✅ **APIs REST Completas**
- **Usuários:** Autenticação JWT, CRUD, perfis de usuário
- **Solicitações:** Fluxo completo de 11 etapas, aprovações, dashboard
- **Configurações:** Sistema de configurações, SLA, limites de aprovação
- **Auditoria:** Logs completos, relatórios, alertas de segurança

### 🔐 **Autenticação e Segurança**
- JWT tokens com refresh
- Compatibilidade com senhas V1 (SHA256)
- Permissões granulares por perfil
- Auditoria automática de todas as ações
- Rate limiting e validação de entrada

### 📊 **Perfis de Usuário**
- **Solicitante:** Criar e acompanhar solicitações
- **Estoque:** Gerenciar requisições
- **Suprimentos:** Processar cotações e pedidos
- **Diretoria:** Aprovar/reprovar solicitações
- **Admin:** Acesso total ao sistema

## 🛠️ Instalação

### 1. Pré-requisitos
```bash
Python 3.9+
pip
```

### 2. Configuração do Ambiente
```bash
# Clone o repositório
cd Sistemas_Compras_V2/backend

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

### 3. Configuração do Banco de Dados
```bash
# Execute migrações
python manage.py makemigrations
python manage.py migrate

# Crie superusuário (opcional)
python manage.py createsuperuser
```

### 4. Migração de Dados V1 → V2
```bash
# Migre dados do sistema V1
python migrate_v1_to_v2.py --v1-db /caminho/para/sistema_compras.db

# Exemplo:
python migrate_v1_to_v2.py --v1-db ../Sistemas_Compras_V1/sistema_compras.db
```

### 5. Executar o Servidor
```bash
python manage.py runserver
```

O servidor estará disponível em `http://localhost:8000`

## 📡 Endpoints da API

### **Autenticação**
```
POST /api/usuarios/auth/login/          # Login
POST /api/usuarios/auth/logout/         # Logout
GET  /api/usuarios/auth/profile/        # Perfil do usuário
PUT  /api/usuarios/auth/change-password/ # Alterar senha
```

### **Usuários**
```
GET    /api/usuarios/                   # Listar usuários
POST   /api/usuarios/                   # Criar usuário
GET    /api/usuarios/{id}/              # Detalhes do usuário
PUT    /api/usuarios/{id}/              # Atualizar usuário
DELETE /api/usuarios/{id}/              # Excluir usuário
```

### **Solicitações**
```
GET    /api/solicitacoes/               # Listar solicitações
POST   /api/solicitacoes/               # Criar solicitação
GET    /api/solicitacoes/{id}/          # Detalhes da solicitação
PUT    /api/solicitacoes/{id}/          # Atualizar solicitação
DELETE /api/solicitacoes/{id}/          # Excluir solicitação
PUT    /api/solicitacoes/{id}/update-status/  # Atualizar status
POST   /api/solicitacoes/{id}/approval/ # Aprovar/reprovar
GET    /api/solicitacoes/dashboard/     # Dashboard com métricas
```

### **Catálogo de Produtos**
```
GET    /api/solicitacoes/catalogo/      # Listar produtos
POST   /api/solicitacoes/catalogo/      # Criar produto
PUT    /api/solicitacoes/catalogo/{id}/ # Atualizar produto
DELETE /api/solicitacoes/catalogo/{id}/ # Excluir produto
```

### **Configurações**
```
GET    /api/configuracoes/              # Configurações gerais
POST   /api/configuracoes/              # Criar configuração
GET    /api/configuracoes/sla/          # Configurações SLA
GET    /api/configuracoes/limites/      # Limites de aprovação
POST   /api/configuracoes/bulk-update/  # Atualização em lote
```

### **Auditoria**
```
GET    /api/auditoria/admin/            # Logs administrativos
GET    /api/auditoria/logs/             # Logs do sistema
GET    /api/auditoria/login/            # Histórico de login
GET    /api/auditoria/statistics/       # Estatísticas
GET    /api/auditoria/security-alerts/  # Alertas de segurança
```

## 🔧 Configuração

### **Variáveis de Ambiente**
Crie um arquivo `.env` na raiz do projeto:

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# Sistema
SISTEMA_NOME=Sistema de Gestão de Compras V2
EMPRESA_NOME=Empresa Ziran
```

### **Configurações do Sistema**
As configurações podem ser gerenciadas via API ou Django Admin:

- **SLA por Departamento:** Prazos de atendimento
- **Limites de Aprovação:** Alçadas por valor
- **Configurações Gerais:** Parâmetros do sistema

## 📋 Fluxo de Solicitações

### **Estados da Solicitação**
1. **Solicitação** → Criada pelo solicitante
2. **Requisição** → Processada pelo estoque
3. **Suprimentos** → Em análise pelos suprimentos
4. **Em Cotação** → Buscando fornecedores
5. **Pedido de Compras** → Pedido criado
6. **Aguardando Aprovação** → Pendente de aprovação
7. **Aprovado** → Aprovado pela diretoria
8. **Reprovado** → Reprovado pela diretoria
9. **Compra feita** → Compra realizada
10. **Aguardando Entrega** → Aguardando fornecedor
11. **Pedido Finalizado** → Processo concluído

### **Permissões por Perfil**
- **Solicitante:** Criar e visualizar próprias solicitações
- **Estoque:** Processar requisições (etapas 1-3)
- **Suprimentos:** Gerenciar cotações e pedidos (etapas 3-6, 9-11)
- **Diretoria:** Aprovar/reprovar solicitações (etapas 6-8)
- **Admin:** Acesso completo a todas as funcionalidades

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Executar testes de uma app específica
python manage.py test apps.usuarios
python manage.py test apps.solicitacoes
```

## 📊 Monitoramento

### **Logs**
- Logs de aplicação: `logs/django.log`
- Logs de auditoria: Via API `/api/auditoria/`
- Logs de segurança: Alertas automáticos

### **Métricas**
- Dashboard por perfil de usuário
- Estatísticas de SLA
- Relatórios de auditoria
- Alertas de segurança

## 🔒 Segurança

### **Implementado**
- ✅ Autenticação JWT
- ✅ Permissões granulares
- ✅ Rate limiting
- ✅ Validação de entrada
- ✅ Auditoria completa
- ✅ Logs de segurança
- ✅ CORS configurado

### **Alertas de Segurança**
- Múltiplas tentativas de login falhadas
- Login de novos IPs
- Ações administrativas fora do horário comercial
- Alterações em configurações críticas

## 🚀 Deploy

### **Desenvolvimento**
```bash
python manage.py runserver
```

### **Produção**
```bash
# Colete arquivos estáticos
python manage.py collectstatic

# Execute com Gunicorn
gunicorn compras_project.wsgi:application
```

## 📚 Estrutura do Projeto

```
backend/
├── compras_project/          # Configurações do Django
│   ├── settings.py          # Configurações principais
│   ├── urls.py              # URLs principais
│   └── wsgi.py              # WSGI para deploy
├── apps/                    # Aplicações Django
│   ├── usuarios/            # Autenticação e usuários
│   ├── solicitacoes/        # Solicitações e fluxo
│   ├── configuracoes/       # Configurações do sistema
│   ├── auditoria/           # Logs e auditoria
│   └── dashboard/           # Métricas e relatórios
├── db/                      # Banco de dados SQLite
├── media/                   # Arquivos de upload
├── static/                  # Arquivos estáticos
├── migrate_v1_to_v2.py     # Script de migração
├── requirements.txt         # Dependências Python
└── README.md               # Este arquivo
```

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é propriedade da Empresa Ziran. Todos os direitos reservados.

## 📞 Suporte

Para suporte técnico, entre em contato com a equipe de TI.

---

**Sistema de Gestão de Compras V2** - Desenvolvido com Django REST Framework
