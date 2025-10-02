# 🚀 Executar Teste Completo na EC2

## 📋 Pré-requisitos
- Sistema rodando na EC2 (IP: 18.222.147.19)
- PostgreSQL local configurado
- Chave SSH `Compras.pem` disponível

## 📤 1. Upload do Script para EC2

```bash
# Fazer upload do script de teste
scp -i "chavepem\Compras.pem" test_fluxo_completo_ec2.py ubuntu@18.222.147.19:~/sistema_compras/
```

## 🔐 2. Conectar à EC2

```bash
# Conectar via SSH
ssh -i "chavepem\Compras.pem" ubuntu@18.222.147.19
```

## 🏃 3. Executar o Teste

```bash
# Navegar para o diretório
cd ~/sistema_compras

# Executar o teste completo
python3 test_fluxo_completo_ec2.py
```

## 📊 O que o Script Testa

### **Fluxo Completo (8 Etapas):**
1. **Conexão DB** - Testa conexão PostgreSQL
2. **Autenticação** - Valida todos os usuários:
   - Leonardo.Fragoso (Solicitante)
   - Fabio.Ramos (Suprimentos) 
   - Diretoria (Aprovador)
   - Estoque.Sistema (Estoque)
   - admin (Administrador)

3. **Criar Solicitação** - Simula solicitante criando pedido
4. **Processar Suprimentos** - Move para cotação
5. **Enviar Aprovação** - Envia para diretoria
6. **Aprovar Solicitação** - Diretoria aprova
7. **Realizar Compra** - Suprimentos efetua compra
8. **Processar Entrega** - Estoque recebe produto
9. **Finalizar** - Completa o processo
10. **Verificar Estado** - Valida resultado final

### **Dados de Teste:**
- **Produto:** Notebook Dell Inspiron 15
- **Valor:** R$ 2.350,00
- **Prioridade:** Alta
- **Justificativa:** Equipamento com falhas
- **Centro de Custo:** TI-001

## 📈 Resultado Esperado

```
📊 RELATÓRIO FINAL DO TESTE DE FLUXO COMPLETO
================================================================================
🕐 Duração total: X.XX segundos
📈 Testes executados: 10
✅ Sucessos: 10
❌ Erros: 0
📊 Taxa de sucesso: 100.0%
🆔 ID da solicitação criada: XXX

🎉 TODOS OS TESTES PASSARAM! Sistema funcionando perfeitamente.
```

## 🔍 Verificação Manual

Após o teste, você pode verificar no sistema web:

1. **Acesse:** http://18.222.147.19:8501
2. **Login como admin:** admin / admin123
3. **Vá em:** Histórico → Verificar solicitação criada
4. **Status deve estar:** "Pedido Finalizado"

## 🐛 Troubleshooting

### Erro de Conexão DB:
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Reiniciar se necessário
sudo systemctl restart postgresql
```

### Erro de Autenticação:
```bash
# Executar fix de autenticação
python3 fix_authentication_ec2.py
```

### Erro de Schema:
```bash
# Executar fix de schema
python3 fix_schema_ec2.py
```

## 📝 Logs Detalhados

O script gera logs detalhados de cada etapa:
- ✅ Sucesso com detalhes
- ❌ Erro com causa específica
- ⚠️ Avisos importantes

Cada teste mostra:
- Status da operação
- Dados inseridos/atualizados
- Timestamps das transições
- Valores e responsáveis

## 🎯 Objetivo

Este teste valida que **TODA** a cadeia de compras funciona corretamente:
- Todos os perfis conseguem autenticar
- Transições de status funcionam
- Dados são persistidos corretamente
- Fluxo completo sem erros

**Tempo estimado:** 30-60 segundos para execução completa.
