# 🔄 Novo Fluxo de Requisições - Sistema de Compras

## 📋 Visão Geral

O sistema foi atualizado para incluir uma nova etapa de **Requisição** no fluxo de compras, conforme solicitado. Agora o processo funciona com duas ferramentas integradas: o **Sistema Interno da Empresa** e o **Sistema de Gestão de Compras**.

## 🔄 Novo Fluxo Completo (11 Etapas)

### 1. **Solicitação** 
- Qualquer pessoa faz a solicitação de material
- Entrega para a pessoa de estoque
- **Sistema:** Gestão de Compras

### 2. **Requisição**
- Pessoa de estoque cria requisição no sistema interno da empresa
- Gera número de requisição oficial
- **Sistema:** Sistema Interno + Gestão de Compras

### 3. **Suprimentos**
- Suprimentos visualiza a requisição
- Processa e inicia análise
- **Sistema:** Gestão de Compras

### 4. **Em Cotação**
- Processo de cotação ativo
- Múltiplos fornecedores consultados
- **Sistema:** Gestão de Compras

### 5. **Pedido de Compras**
- Suprimentos cria pedido após cotação
- Avalia melhores preços e condições
- **Sistema:** Sistema Interno + Gestão de Compras

### 6. **Aguardando Aprovação**
- Diretoria analisa o pedido
- **Sistema:** Gestão de Compras

### 7. **Aprovado/Reprovado**
- Decisão da diretoria
- **Sistema:** Gestão de Compras

### 8. **Compra feita**
- Pedido executado
- **Sistema:** Gestão de Compras

### 9. **Aguardando Entrega**
- Produto em trânsito
- **Sistema:** Gestão de Compras

### 10. **Pedido Finalizado**
- Processo concluído
- **Sistema:** Gestão de Compras

## 👥 Novos Perfis e Responsabilidades

### **Perfil Estoque** (NOVO)
- **Usuário:** Estoque.Sistema / Teste123
- **Responsabilidades:**
  - Receber solicitações físicas
  - Criar requisições no sistema interno
  - Gerar números de requisição oficiais
  - Enviar para suprimentos

### **Perfil Suprimentos** (ATUALIZADO)
- **Funcionalidades Novas:**
  - 🏭 **Processar Requisições** - Nova interface principal
  - 💰 **Criar Pedido de Compras** - Após cotação
  - 📊 **Dashboard** - Métricas de requisições
- **Funcionalidades Mantidas:**
  - 📑 Requisição (Estoque) - Legado
  - 🔄 Mover para Próxima Etapa
  - 📚 Histórico por Etapa
  - 📦 Catálogo de Produtos

## 🔢 Numeração Automática

### **Números de Requisição**
- Gerados automaticamente pelo sistema
- Sequencial: 1, 2, 3, 4...
- Único por requisição no sistema interno

### **Números de Pedido de Compras**
- Gerados automaticamente após cotação
- Sequencial: 1, 2, 3, 4...
- Único por pedido de compras

### **Números de Solicitação** (Mantido)
- Continua funcionando como antes
- Sequencial por solicitação original

## 🏭 Como Usar o Novo Sistema

### **Para Pessoa de Estoque:**

1. **Login:** Estoque.Sistema / Teste123
2. **Acesse:** Interface principal do estoque
3. **Veja:** Solicitações pendentes de requisição
4. **Crie:** Nova requisição no sistema interno
5. **Preencha:** Dados da requisição
6. **Envie:** Para suprimentos

### **Para Suprimentos:**

1. **Login:** Fabio.Ramos / Teste123
2. **Acesse:** 🏭 Processar Requisições
3. **Veja:** Requisições aguardando processamento
4. **Processe:** Requisição → Suprimentos → Em Cotação
5. **Crie:** Pedido de Compras após cotação
6. **Envie:** Para aprovação da diretoria

## 📊 Benefícios do Novo Fluxo

### **Rastreabilidade Completa**
- Número de solicitação original
- Número de requisição no sistema interno
- Número de pedido de compras oficial
- Histórico completo de cada etapa

### **Integração Dupla**
- Sistema interno da empresa (requisições)
- Sistema de gestão de compras (controle)
- Dados sincronizados entre ambos

### **Controle Aprimorado**
- Responsável por cada etapa identificado
- Datas de cada movimentação
- Observações detalhadas
- Métricas de performance

### **Flexibilidade Futura**
- Preparado para múltiplos fornecedores por pedido
- Suporte a cotações complexas
- Expansível para novos requisitos

## 🔧 Configuração Técnica

### **Banco de Dados Atualizado**
- Novos campos: `numero_requisicao`, `data_requisicao`, `responsavel_estoque`
- Campos para pedido: `numero_pedido_compras`, `observacoes_pedido_compras`
- Histórico expandido com todas as etapas

### **Usuários Configurados**
```
- admin / admin123 (Administrador)
- Leonardo.Fragoso / Teste123 (Solicitante)
- Genival.Silva / Teste123 (Solicitante)
- Diretoria / Teste123 (Aprovador)
- Fabio.Ramos / Teste123 (Suprimentos)
- Estoque.Sistema / Teste123 (Estoque) ← NOVO
```

### **Configurações Automáticas**
- Numeração sequencial automática
- SLA por prioridade mantido
- Notificações entre etapas
- Backup e auditoria completos

## 🚀 Próximos Passos

### **Implementação Imediata**
1. ✅ Sistema atualizado e funcionando
2. ✅ Usuário de estoque criado
3. ✅ Interfaces novas implementadas
4. ✅ Fluxo completo testado

### **Treinamento Sugerido**
1. **Pessoa de Estoque:** Como criar requisições
2. **Suprimentos:** Nova interface de processamento
3. **Diretoria:** Fluxo atualizado de aprovação

### **Melhorias Futuras**
1. **Múltiplos Fornecedores:** Sistema preparado para compras com vários fornecedores
2. **Integração API:** Possível integração direta com sistema interno
3. **Relatórios Avançados:** Métricas específicas por etapa
4. **Mobile:** Interface mobile para aprovações

## 📞 Suporte

Para dúvidas ou ajustes no novo fluxo, entre em contato com a equipe de desenvolvimento.

**Sistema funcionando em:** http://18.222.147.19:8501

---

*Documentação criada em: 25/08/2024*  
*Versão do Sistema: 2.0 - Fluxo com Requisições*
