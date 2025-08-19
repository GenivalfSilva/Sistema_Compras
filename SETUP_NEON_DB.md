# Setup do Banco Neon DB - Sistema de Compras

Este documento explica como configurar e executar o script `setup_neon_db.py` para criar e atualizar todas as tabelas do sistema no banco Neon DB.

## 📋 Pré-requisitos

1. **Python 3.7+** instalado
2. **Dependências Python**:
   ```bash
   pip install psycopg2-binary toml
   ```
3. **Conta no Neon DB** com banco criado
4. **Credenciais de acesso** configuradas

## 🔧 Configuração das Credenciais

O script suporta três métodos de configuração:

### Método 1: Arquivo secrets.toml (Recomendado)
Crie um arquivo `secrets.toml` na raiz do projeto:

```toml
[postgres]
host = "seu-host.neon.tech"
database = "nome-do-banco"
user = "seu-usuario"
password = "sua-senha"
port = 5432
sslmode = "require"
```

### Método 2: Variáveis de Ambiente
Configure as seguintes variáveis:

```bash
# Opção 1: URL completa
export DATABASE_URL="postgresql://usuario:senha@host:5432/database?sslmode=require"

# Opção 2: Variáveis individuais
export POSTGRES_HOST="seu-host.neon.tech"
export POSTGRES_DATABASE="nome-do-banco"
export POSTGRES_USER="seu-usuario"
export POSTGRES_PASSWORD="sua-senha"
export POSTGRES_PORT="5432"
export POSTGRES_SSLMODE="require"
```

### Método 3: Streamlit Secrets (Para deploy)
No Streamlit Cloud, configure em `Settings > Secrets`:

```toml
[postgres]
host = "seu-host.neon.tech"
database = "nome-do-banco"
user = "seu-usuario"
password = "sua-senha"
port = 5432
sslmode = "require"
```

## 🚀 Execução do Script

### Execução Simples
```bash
python setup_neon_db.py
```

### Execução com Logs Detalhados
```bash
python -u setup_neon_db.py
```

## 📊 O que o Script Faz

### 1. **Criação de Tabelas**
- `usuarios` - Gerenciamento de usuários do sistema
- `solicitacoes` - Solicitações de compras com todos os campos
- `configuracoes` - Configurações do sistema
- `catalogo_produtos` - Catálogo de produtos
- `movimentacoes` - Histórico de mudanças de etapa
- `notificacoes` - Sistema de notificações
- `sessoes` - Gerenciamento de sessões de usuário

### 2. **Migração de Schema**
- Adiciona colunas faltantes em tabelas existentes
- Garante compatibilidade com versões anteriores
- Inclui campo `numero_pedido_compras` mencionado no histórico

### 3. **Criação de Índices**
- Índices para melhorar performance das consultas
- Otimização para buscas por número, status, etapa, etc.

### 4. **Dados Padrão**
- Usuário admin inicial (login: `admin`, senha: `admin123`)
- Catálogo básico de produtos
- Configurações padrão do sistema

### 5. **Verificação Final**
- Testa todas as tabelas criadas
- Conta registros inseridos
- Confirma integridade do setup

## ✅ Saída Esperada

```
🚀 Iniciando setup do Neon DB para Sistema de Compras
============================================================
Tentando conectar ao Neon DB...
✅ Conexão estabelecida com sucesso!

🔧 Criando tabelas...
✅ Tabela 'usuarios' criada/atualizada
✅ Tabela 'solicitacoes' criada/atualizada
✅ Tabela 'configuracoes' criada/atualizada
✅ Tabela 'catalogo_produtos' criada/atualizada
✅ Tabela 'movimentacoes' criada/atualizada
✅ Tabela 'notificacoes' criada/atualizada
✅ Tabela 'sessoes' criada/atualizada
✅ Todas as tabelas foram criadas com sucesso!

🔧 Verificando e adicionando colunas faltantes...
  ➕ Adicionada coluna 'numero_pedido_compras' na tabela 'solicitacoes'
✅ Verificação de colunas concluída!

🔧 Criando índices...
  ✅ Índice criado
✅ Índices criados!

🔧 Inserindo dados padrão...
  ➕ Usuário admin criado (login: admin, senha: admin123)
  ➕ Catálogo padrão de produtos inserido
✅ Dados padrão inseridos!

🔍 Verificando setup...
  ✅ Tabela 'usuarios': 1 registros
  ✅ Tabela 'solicitacoes': 0 registros
  ✅ Tabela 'configuracoes': 7 registros
  ✅ Tabela 'catalogo_produtos': 5 registros
  ✅ Tabela 'movimentacoes': 0 registros
  ✅ Tabela 'notificacoes': 0 registros
  ✅ Tabela 'sessoes': 0 registros
✅ Verificação concluída com sucesso!

============================================================
🎉 Setup do Neon DB concluído com sucesso!
📋 O sistema está pronto para uso.

📝 Próximos passos:
   1. Execute o app.py para testar a conexão
   2. Faça login com: admin / admin123
   3. Configure usuários adicionais se necessário
🔌 Conexão fechada
```

## 🔄 Re-execução

O script é **idempotente**, ou seja, pode ser executado múltiplas vezes sem problemas:
- Tabelas existentes não são recriadas
- Colunas faltantes são adicionadas automaticamente
- Dados padrão não são duplicados
- Índices são criados apenas se não existirem

## ❌ Solução de Problemas

### Erro de Conexão
- Verifique as credenciais do Neon DB
- Confirme se o banco está ativo
- Teste conectividade de rede

### Erro de Permissões
- Verifique se o usuário tem permissões de CREATE TABLE
- Confirme se pode criar índices

### Dependências Faltando
```bash
pip install psycopg2-binary toml
```

### Erro de SSL
Adicione `sslmode = "require"` na configuração.

## 🔗 Integração com o Sistema

Após executar o script:

1. **Configure o app.py** para usar o banco:
   - Certifique-se que `USE_DATABASE = True`
   - Configure as mesmas credenciais

2. **Teste a aplicação**:
   ```bash
   streamlit run app.py
   ```

3. **Faça login inicial**:
   - Usuário: `admin`
   - Senha: `admin123`

4. **Configure usuários adicionais** através da interface admin.

## 📚 Referências

- [Documentação Neon DB](https://neon.tech/docs)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
