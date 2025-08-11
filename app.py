import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta, date
import json
import os
from typing import Dict, List
import math

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão de Compras - SLA",
    page_icon="📋",
    layout="wide"
)

# Arquivo para armazenar os dados
DATA_FILE = "compras_sla_data.json"

# Configurações baseadas na planilha Excel
ETAPAS_PROCESSO = [
    "Solicitação",
    "Suprimentos", 
    "Em Cotação",
    "Pedido Finalizado"
]

DEPARTAMENTOS = [
    "Manutenção",
    "TI", 
    "RH",
    "Financeiro",
    "Marketing",
    "Operações",
    "Outro"
]

PRIORIDADES = [
    "Normal",
    "Urgente",
    "Baixa",
    "Alta"
]

# SLA padrão por prioridade (em dias)
SLA_PADRAO = {
    "Urgente": 1,
    "Alta": 2,
    "Normal": 3,
    "Baixa": 5
}

def load_data() -> Dict:
    """Carrega os dados do arquivo JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return init_empty_data()
    return init_empty_data()

def init_empty_data() -> Dict:
    """Inicializa estrutura de dados vazia baseada na planilha"""
    return {
        "solicitacoes": [],
        "movimentacoes": [],  # Histórico de mudanças de etapa
        "configuracoes": {
            "sla_por_departamento": {},
            "proximo_numero_solicitacao": 1,
            "proximo_numero_pedido": 1
        }
    }

def save_data(data: Dict):
    """Salva os dados no arquivo JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def calcular_dias_uteis(data_inicio: datetime.datetime, data_fim: datetime.datetime = None) -> int:
    """Calcula dias úteis entre duas datas (excluindo fins de semana)"""
    if data_fim is None:
        data_fim = datetime.datetime.now()
    
    try:
        # Converte para date se necessário
        if isinstance(data_inicio, str):
            data_inicio = datetime.datetime.fromisoformat(data_inicio)
        if isinstance(data_fim, str):
            data_fim = datetime.datetime.fromisoformat(data_fim)
            
        data_atual = data_inicio.date()
        data_final = data_fim.date()
        
        dias_uteis = 0
        while data_atual <= data_final:
            # 0-6 onde 0=segunda, 6=domingo
            if data_atual.weekday() < 5:  # Segunda a sexta
                dias_uteis += 1
            data_atual += timedelta(days=1)
            
        return max(0, dias_uteis - 1)  # Subtrai 1 para não contar o dia inicial
    except:
        return 0

def verificar_sla_cumprido(dias_atendimento: int, sla_dias: int) -> str:
    """Verifica se o SLA foi cumprido"""
    if dias_atendimento <= sla_dias:
        return "Sim"
    else:
        return "Não"

def obter_sla_por_prioridade(prioridade: str, departamento: str = None) -> int:
    """Obtém SLA baseado na prioridade e departamento"""
    # Por enquanto usa SLA padrão, mas pode ser customizado por departamento
    return SLA_PADRAO.get(prioridade, 3)

def main():
    st.title("📋 Sistema de Gestão de Compras - SLA")
    st.markdown("### Controle de Solicitações e Medição de SLA baseado na Planilha Excel")
    
    # Carrega os dados
    data = load_data()
    
    # Sidebar para navegação
    st.sidebar.title("🔧 Navegação")
    opcao = st.sidebar.selectbox(
        "Escolha uma opção:",
        [
            "📝 Nova Solicitação", 
            "🔄 Mover para Próxima Etapa",
            "📊 Dashboard SLA", 
            "📚 Histórico por Etapa",
            "⚙️ Configurações SLA"
        ]
    )
    
    # Mostra estatísticas rápidas na sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Estatísticas Rápidas")
    
    total_solicitacoes = len(data["solicitacoes"])
    solicitacoes_pendentes = len([s for s in data["solicitacoes"] if s["status"] != "Pedido Finalizado"])
    
    st.sidebar.metric("Total de Solicitações", total_solicitacoes)
    st.sidebar.metric("Em Andamento", solicitacoes_pendentes)
    
    if total_solicitacoes > 0:
        # Calcula SLA médio
        slas_cumpridos = 0
        total_com_sla = 0
        for sol in data["solicitacoes"]:
            if sol.get("dias_atendimento") is not None and sol.get("sla_cumprido"):
                total_com_sla += 1
                if sol["sla_cumprido"] == "Sim":
                    slas_cumpridos += 1
        
        if total_com_sla > 0:
            taxa_sla = (slas_cumpridos / total_com_sla) * 100
            st.sidebar.metric("Taxa SLA Cumprido", f"{taxa_sla:.1f}%")
    
    if opcao == "📝 Nova Solicitação":
        st.header("📝 Nova Solicitação de Compra")
        st.markdown("*Baseado na estrutura da planilha Excel - Aba 'Solicitação'*")
        
        with st.form("nova_solicitacao"):
            # Campos principais baseados na planilha
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Dados do Solicitante**")
                solicitante = st.text_input("Solicitante (Nome e Sobrenome)*", 
                                          help="Campo obrigatório conforme planilha")
                departamento = st.selectbox(
                    "Departamento*",
                    DEPARTAMENTOS,
                    help="Departamento do solicitante"
                )
                prioridade = st.selectbox(
                    "Prioridade*",
                    PRIORIDADES,
                    help="Define o SLA automaticamente"
                )
                
            with col2:
                st.markdown("**Dados da Solicitação**")
                descricao = st.text_area("Descrição*", height=100,
                                        help="Descrição detalhada da solicitação")
                aplicacao = st.number_input("Aplicação (Código)*", 
                                          min_value=1, step=1,
                                          help="Código numérico da aplicação")
                
                # Mostra SLA que será aplicado
                sla_dias = obter_sla_por_prioridade(prioridade if 'prioridade' in locals() else "Normal")
                st.info(f"📅 SLA para prioridade '{prioridade if 'prioridade' in locals() else 'Normal'}': {sla_dias} dias úteis")
            
            # Campos opcionais/futuros
            st.markdown("---")
            st.markdown("**Campos de Controle (preenchidos automaticamente)**")
            
            col3, col4 = st.columns(2)
            with col3:
                st.text_input("Nº Solicitação (Estoque)", 
                            value="Será gerado automaticamente", 
                            disabled=True)
                st.text_input("Status", 
                            value="Solicitação", 
                            disabled=True)
            
            with col4:
                st.text_input("Carimbo de data/hora", 
                            value=datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'), 
                            disabled=True)
                st.text_input("SLA (dias)", 
                            value=f"{sla_dias} dias úteis", 
                            disabled=True)
            
            submitted = st.form_submit_button("🚀 Criar Solicitação", use_container_width=True)
            
            if submitted:
                if solicitante and departamento and descricao and aplicacao:
                    # Gera números automáticos
                    numero_solicitacao = data["configuracoes"]["proximo_numero_solicitacao"]
                    data["configuracoes"]["proximo_numero_solicitacao"] += 1
                    
                    # Calcula SLA baseado na prioridade
                    sla_dias = obter_sla_por_prioridade(prioridade, departamento)
                    
                    nova_solicitacao = {
                        # Campos da planilha Excel
                        "carimbo_data_hora": datetime.datetime.now().isoformat(),
                        "solicitante": solicitante,
                        "departamento": departamento,
                        "prioridade": prioridade,
                        "descricao": descricao,
                        "aplicacao": aplicacao,
                        "status": "Solicitação",  # Primeira etapa
                        "numero_solicitacao_estoque": numero_solicitacao,
                        "numero_pedido_compras": None,
                        "data_numero_pedido": None,
                        "data_cotacao": None,
                        "data_entrega": None,
                        "sla_dias": sla_dias,
                        "dias_atendimento": None,
                        "sla_cumprido": None,
                        "observacoes": None,
                        
                        # Campos de controle interno
                        "id": len(data["solicitacoes"]) + 1,
                        "etapa_atual": "Solicitação",
                        "historico_etapas": [{
                            "etapa": "Solicitação",
                            "data_entrada": datetime.datetime.now().isoformat(),
                            "usuario": "Sistema"
                        }]
                    }
                    
                    data["solicitacoes"].append(nova_solicitacao)
                    save_data(data)
                    
                    st.success(f"✅ Solicitação #{numero_solicitacao} criada com sucesso!")
                    st.info(f"📅 Data/Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                    st.info(f"⏱️ SLA: {sla_dias} dias úteis")
                    st.info(f"📊 Status: Solicitação (Etapa 1 de 4)")
                    
                    # Mostra próximos passos
                    st.markdown("### 🔄 Próximos Passos")
                    st.markdown("1. A solicitação será analisada pela área de Suprimentos")
                    st.markdown("2. Use a opção '🔄 Mover para Próxima Etapa' para avançar o processo")
                    
                else:
                    st.error("❌ Por favor, preencha todos os campos obrigatórios (*)")
    
    elif opcao == "🔄 Mover para Próxima Etapa":
        st.header("🔄 Mover Solicitação para Próxima Etapa")
        st.markdown("*Fluxo baseado na planilha Excel: Solicitação → Suprimentos → Em Cotação → Pedido Finalizado*")
        
        # Filtra solicitações que não estão finalizadas
        solicitacoes_ativas = [s for s in data["solicitacoes"] if s["status"] != "Pedido Finalizado"]
        
        if not solicitacoes_ativas:
            st.warning("📋 Não há solicitações ativas para mover.")
            st.info("💡 Crie uma nova solicitação primeiro!")
            return
        
        # Seleção da solicitação
        st.subheader("1️⃣ Selecione a Solicitação")
        
        opcoes_solicitacoes = []
        for s in solicitacoes_ativas:
            data_criacao = datetime.datetime.fromisoformat(s["carimbo_data_hora"]).strftime('%d/%m/%Y %H:%M')
            opcoes_solicitacoes.append(
                f"#{s['numero_solicitacao_estoque']} - {s['solicitante']} - {s['status']} ({data_criacao})"
            )
        
        solicitacao_selecionada = st.selectbox("Escolha a solicitação:", opcoes_solicitacoes)
        
        if solicitacao_selecionada:
            # Extrai o número da solicitação
            numero_solicitacao = int(solicitacao_selecionada.split('#')[1].split(' -')[0])
            solicitacao = next(s for s in solicitacoes_ativas if s['numero_solicitacao_estoque'] == numero_solicitacao)
            
            # Mostra detalhes da solicitação
            st.subheader("2️⃣ Detalhes da Solicitação Atual")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Número", f"#{solicitacao['numero_solicitacao_estoque']}")
                st.metric("Solicitante", solicitacao['solicitante'])
                st.metric("Departamento", solicitacao['departamento'])
            
            with col2:
                st.metric("Status Atual", solicitacao['status'])
                st.metric("Prioridade", solicitacao['prioridade'])
                st.metric("SLA (dias)", solicitacao['sla_dias'])
            
            with col3:
                data_criacao = datetime.datetime.fromisoformat(solicitacao["carimbo_data_hora"])
                dias_decorridos = calcular_dias_uteis(data_criacao)
                st.metric("Dias Decorridos", dias_decorridos)
                
                # Calcula status do SLA
                if dias_decorridos <= solicitacao['sla_dias']:
                    st.success("✅ Dentro do SLA")
                else:
                    st.error("❌ SLA Estourado")
            
            st.markdown(f"**Descrição:** {solicitacao['descricao']}")
            
            # Determina próxima etapa
            etapa_atual = solicitacao['status']
            proxima_etapa = None
            
            if etapa_atual == "Solicitação":
                proxima_etapa = "Suprimentos"
            elif etapa_atual == "Suprimentos":
                proxima_etapa = "Em Cotação"
            elif etapa_atual == "Em Cotação":
                proxima_etapa = "Pedido Finalizado"
            
            if proxima_etapa:
                st.subheader(f"3️⃣ Mover para: {proxima_etapa}")
                
                with st.form("mover_etapa"):
                    # Campos específicos por etapa
                    if proxima_etapa == "Suprimentos":
                        st.markdown("**📦 Dados para Suprimentos**")
                        col1, col2 = st.columns(2)
                        with col1:
                            responsavel = st.text_input("Responsável Suprimentos*")
                        with col2:
                            observacoes = st.text_area("Observações", height=100)
                    
                    elif proxima_etapa == "Em Cotação":
                        st.markdown("**💰 Dados para Cotação**")
                        col1, col2 = st.columns(2)
                        with col1:
                            numero_pedido = st.number_input("Nº Pedido (Compras)*", min_value=1, step=1)
                            data_pedido = st.date_input("Data Nº Pedido*", value=date.today())
                        with col2:
                            data_cotacao = st.date_input("Data Cotação", value=date.today())
                            observacoes = st.text_area("Observações", height=100)
                    
                    elif proxima_etapa == "Pedido Finalizado":
                        st.markdown("**✅ Finalização do Pedido**")
                        col1, col2 = st.columns(2)
                        with col1:
                            data_entrega = st.date_input("Data Entrega*", value=date.today())
                            valor_final = st.number_input("Valor Final (R$)", min_value=0.0, step=0.01)
                        with col2:
                            fornecedor_final = st.text_input("Fornecedor Final")
                            observacoes = st.text_area("Observações Finais", height=100)
                    
                    submitted = st.form_submit_button(f"🚀 Mover para {proxima_etapa}", use_container_width=True)
                    
                    if submitted:
                        # Atualiza a solicitação
                        for i, s in enumerate(data["solicitacoes"]):
                            if s["numero_solicitacao_estoque"] == numero_solicitacao:
                                # Atualiza status
                                data["solicitacoes"][i]["status"] = proxima_etapa
                                data["solicitacoes"][i]["etapa_atual"] = proxima_etapa
                                
                                # Adiciona ao histórico
                                data["solicitacoes"][i]["historico_etapas"].append({
                                    "etapa": proxima_etapa,
                                    "data_entrada": datetime.datetime.now().isoformat(),
                                    "usuario": responsavel if 'responsavel' in locals() else "Sistema"
                                })
                                
                                # Atualiza campos específicos
                                if proxima_etapa == "Em Cotação" and 'numero_pedido' in locals():
                                    data["solicitacoes"][i]["numero_pedido_compras"] = numero_pedido
                                    data["solicitacoes"][i]["data_numero_pedido"] = data_pedido.isoformat()
                                    if 'data_cotacao' in locals():
                                        data["solicitacoes"][i]["data_cotacao"] = data_cotacao.isoformat()
                                
                                elif proxima_etapa == "Pedido Finalizado":
                                    data["solicitacoes"][i]["data_entrega"] = data_entrega.isoformat()
                                    
                                    # Calcula dias de atendimento e SLA
                                    data_inicio = datetime.datetime.fromisoformat(s["carimbo_data_hora"])
                                    data_fim = datetime.datetime.combine(data_entrega, datetime.time())
                                    dias_atendimento = calcular_dias_uteis(data_inicio, data_fim)
                                    
                                    data["solicitacoes"][i]["dias_atendimento"] = dias_atendimento
                                    data["solicitacoes"][i]["sla_cumprido"] = verificar_sla_cumprido(
                                        dias_atendimento, s["sla_dias"]
                                    )
                                
                                # Atualiza observações
                                if 'observacoes' in locals() and observacoes:
                                    data["solicitacoes"][i]["observacoes"] = observacoes
                                
                                break
                        
                        save_data(data)
                        
                        st.success(f"✅ Solicitação #{numero_solicitacao} movida para '{proxima_etapa}' com sucesso!")
                        
                        if proxima_etapa == "Pedido Finalizado":
                            # Mostra resultado final do SLA
                            solicitacao_atualizada = next(s for s in data["solicitacoes"] if s['numero_solicitacao_estoque'] == numero_solicitacao)
                            st.info(f"⏱️ Dias de atendimento: {solicitacao_atualizada['dias_atendimento']}")
                            
                            if solicitacao_atualizada['sla_cumprido'] == "Sim":
                                st.success(f"🎯 SLA CUMPRIDO! (Limite: {solicitacao_atualizada['sla_dias']} dias)")
                            else:
                                st.error(f"⚠️ SLA NÃO CUMPRIDO! (Limite: {solicitacao_atualizada['sla_dias']} dias)")
                        
                        st.rerun()
            else:
                st.info("✅ Esta solicitação já está finalizada!")
    
    elif opcao == "📊 Dashboard SLA":
        st.header("📊 Dashboard SLA - Análise de Performance")
        st.markdown("*Métricas baseadas na estrutura da planilha Excel*")
        
        if not data["solicitacoes"]:
            st.warning("📋 Não há dados para exibir no dashboard.")
            st.info("💡 Crie algumas solicitações primeiro!")
            return
        
        # Métricas principais
        st.subheader("📈 Métricas Gerais")
        col1, col2, col3, col4 = st.columns(4)
        
        total_solicitacoes = len(data["solicitacoes"])
        finalizadas = len([s for s in data["solicitacoes"] if s["status"] == "Pedido Finalizado"])
        em_andamento = total_solicitacoes - finalizadas
        
        # Calcula SLA
        slas_cumpridos = len([s for s in data["solicitacoes"] if s.get("sla_cumprido") == "Sim"])
        slas_nao_cumpridos = len([s for s in data["solicitacoes"] if s.get("sla_cumprido") == "Não"])
        
        with col1:
            st.metric("Total Solicitações", total_solicitacoes)
        with col2:
            st.metric("Finalizadas", finalizadas)
        with col3:
            st.metric("Em Andamento", em_andamento)
        with col4:
            if finalizadas > 0:
                taxa_sla = (slas_cumpridos / finalizadas) * 100
                st.metric("Taxa SLA", f"{taxa_sla:.1f}%")
            else:
                st.metric("Taxa SLA", "N/A")
        
        # Distribuição por etapa
        st.subheader("🔄 Distribuição por Etapa")
        etapas_count = {}
        for etapa in ETAPAS_PROCESSO:
            etapas_count[etapa] = len([s for s in data["solicitacoes"] if s["status"] == etapa])
        
        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]
        
        for i, (etapa, count) in enumerate(etapas_count.items()):
            with cols[i]:
                st.metric(etapa, count)
        
        # Análise por departamento
        st.subheader("🏢 Performance por Departamento")
        
        dept_stats = {}
        for sol in data["solicitacoes"]:
            dept = sol["departamento"]
            if dept not in dept_stats:
                dept_stats[dept] = {
                    "total": 0,
                    "finalizadas": 0,
                    "sla_cumprido": 0,
                    "sla_nao_cumprido": 0,
                    "dias_medio": []
                }
            
            dept_stats[dept]["total"] += 1
            
            if sol["status"] == "Pedido Finalizado":
                dept_stats[dept]["finalizadas"] += 1
                
                if sol.get("sla_cumprido") == "Sim":
                    dept_stats[dept]["sla_cumprido"] += 1
                elif sol.get("sla_cumprido") == "Não":
                    dept_stats[dept]["sla_nao_cumprido"] += 1
                
                if sol.get("dias_atendimento") is not None:
                    dept_stats[dept]["dias_medio"].append(sol["dias_atendimento"])
        
        if dept_stats:
            dept_df = []
            for dept, stats in dept_stats.items():
                taxa_finalizacao = (stats["finalizadas"] / stats["total"]) * 100 if stats["total"] > 0 else 0
                taxa_sla = (stats["sla_cumprido"] / stats["finalizadas"]) * 100 if stats["finalizadas"] > 0 else 0
                dias_medio = sum(stats["dias_medio"]) / len(stats["dias_medio"]) if stats["dias_medio"] else 0
                
                dept_df.append({
                    "Departamento": dept,
                    "Total": stats["total"],
                    "Finalizadas": stats["finalizadas"],
                    "Taxa Finalização": f"{taxa_finalizacao:.1f}%",
                    "SLA Cumprido": stats["sla_cumprido"],
                    "Taxa SLA": f"{taxa_sla:.1f}%",
                    "Dias Médio": f"{dias_medio:.1f}"
                })
            
            df_dept = pd.DataFrame(dept_df)
            st.dataframe(df_dept, use_container_width=True)
        
        # Análise por prioridade
        st.subheader("⚡ Performance por Prioridade")
        
        prio_stats = {}
        for sol in data["solicitacoes"]:
            prio = sol["prioridade"]
            if prio not in prio_stats:
                prio_stats[prio] = {
                    "total": 0,
                    "finalizadas": 0,
                    "sla_cumprido": 0,
                    "dias_medio": []
                }
            
            prio_stats[prio]["total"] += 1
            
            if sol["status"] == "Pedido Finalizado":
                prio_stats[prio]["finalizadas"] += 1
                
                if sol.get("sla_cumprido") == "Sim":
                    prio_stats[prio]["sla_cumprido"] += 1
                
                if sol.get("dias_atendimento") is not None:
                    prio_stats[prio]["dias_medio"].append(sol["dias_atendimento"])
        
        if prio_stats:
            prio_df = []
            for prio, stats in prio_stats.items():
                taxa_sla = (stats["sla_cumprido"] / stats["finalizadas"]) * 100 if stats["finalizadas"] > 0 else 0
                dias_medio = sum(stats["dias_medio"]) / len(stats["dias_medio"]) if stats["dias_medio"] else 0
                sla_definido = SLA_PADRAO.get(prio, 3)
                
                prio_df.append({
                    "Prioridade": prio,
                    "SLA Definido": f"{sla_definido} dias",
                    "Total": stats["total"],
                    "Finalizadas": stats["finalizadas"],
                    "SLA Cumprido": stats["sla_cumprido"],
                    "Taxa SLA": f"{taxa_sla:.1f}%",
                    "Dias Médio": f"{dias_medio:.1f}"
                })
            
            df_prio = pd.DataFrame(prio_df)
            st.dataframe(df_prio, use_container_width=True)
        
        # Solicitações com SLA em risco
        st.subheader("⚠️ Solicitações com SLA em Risco")
        
        solicitacoes_risco = []
        for sol in data["solicitacoes"]:
            if sol["status"] != "Pedido Finalizado":
                data_criacao = datetime.datetime.fromisoformat(sol["carimbo_data_hora"])
                dias_decorridos = calcular_dias_uteis(data_criacao)
                
                if dias_decorridos >= sol["sla_dias"]:
                    solicitacoes_risco.append({
                        "Número": f"#{sol['numero_solicitacao_estoque']}",
                        "Solicitante": sol["solicitante"],
                        "Departamento": sol["departamento"],
                        "Prioridade": sol["prioridade"],
                        "Status": sol["status"],
                        "SLA (dias)": sol["sla_dias"],
                        "Dias Decorridos": dias_decorridos,
                        "Atraso": dias_decorridos - sol["sla_dias"]
                    })
        
        if solicitacoes_risco:
            df_risco = pd.DataFrame(solicitacoes_risco)
            st.dataframe(df_risco, use_container_width=True)
        else:
            st.success("✅ Nenhuma solicitação com SLA em risco!")
    
    elif opcao == "📚 Histórico por Etapa":
        st.header("📚 Histórico por Etapa")
        st.markdown("*Visualização baseada nas abas da planilha Excel*")
        
        if not data["solicitacoes"]:
            st.warning("📋 Não há dados para exibir.")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            etapa_filtro = st.selectbox(
                "Filtrar por Etapa:",
                ["Todas"] + ETAPAS_PROCESSO
            )
        
        with col2:
            departamento_filtro = st.selectbox(
                "Filtrar por Departamento:",
                ["Todos"] + DEPARTAMENTOS
            )
        
        with col3:
            prioridade_filtro = st.selectbox(
                "Filtrar por Prioridade:",
                ["Todas"] + PRIORIDADES
            )
        
        # Aplica filtros
        solicitacoes_filtradas = data["solicitacoes"]
        
        if etapa_filtro != "Todas":
            solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["status"] == etapa_filtro]
        
        if departamento_filtro != "Todos":
            solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["departamento"] == departamento_filtro]
        
        if prioridade_filtro != "Todas":
            solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["prioridade"] == prioridade_filtro]
        
        # Cria DataFrame para exibição
        if solicitacoes_filtradas:
            historico_df = []
            for sol in solicitacoes_filtradas:
                data_criacao = datetime.datetime.fromisoformat(sol["carimbo_data_hora"]).strftime('%d/%m/%Y %H:%M')
                
                historico_df.append({
                    "Nº Solicitação": f"#{sol['numero_solicitacao_estoque']}",
                    "Data/Hora": data_criacao,
                    "Solicitante": sol["solicitante"],
                    "Departamento": sol["departamento"],
                    "Prioridade": sol["prioridade"],
                    "Descrição": sol["descricao"][:50] + "..." if len(sol["descricao"]) > 50 else sol["descricao"],
                    "Status": sol["status"],
                    "SLA (dias)": sol["sla_dias"],
                    "Dias Atendimento": sol.get("dias_atendimento", "N/A"),
                    "SLA Cumprido": sol.get("sla_cumprido", "N/A"),
                    "Nº Pedido": sol.get("numero_pedido_compras", "N/A"),
                    "Data Entrega": datetime.datetime.fromisoformat(sol["data_entrega"]).strftime('%d/%m/%Y') if sol.get("data_entrega") else "N/A"
                })
            
            df_historico = pd.DataFrame(historico_df)
            st.dataframe(df_historico, use_container_width=True)
            
            # Botão para download
            csv = df_historico.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"historico_compras_sla_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📋 Nenhuma solicitação encontrada com os filtros aplicados.")
    
    elif opcao == "⚙️ Configurações SLA":
        st.header("⚙️ Configurações SLA")
        st.markdown("*Personalize os SLAs por prioridade e departamento*")
        
        st.subheader("📋 SLA Atual por Prioridade")
        
        # Mostra SLA atual
        sla_df = []
        for prio, dias in SLA_PADRAO.items():
            sla_df.append({
                "Prioridade": prio,
                "SLA (dias úteis)": dias
            })
        
        df_sla = pd.DataFrame(sla_df)
        st.dataframe(df_sla, use_container_width=True)
        
        st.info("💡 Os SLAs são aplicados automaticamente baseados na prioridade da solicitação.")
        st.info("📊 Use o Dashboard SLA para monitorar a performance e ajustar os SLAs conforme necessário.")
    
    else:
        st.error("❌ Opção não implementada ainda.")

if __name__ == "__main__":
    main()
