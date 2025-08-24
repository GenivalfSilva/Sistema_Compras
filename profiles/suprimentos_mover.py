"""
Módulo para mover solicitações para próxima etapa do perfil Suprimentos
Contém: Visualizar solicitações em diferentes etapas, mover entre etapas, controle de fluxo
"""

import streamlit as st
import pandas as pd
import datetime
from typing import Dict

def mover_etapa(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Página para mover solicitações entre etapas"""
    st.markdown("## 🔄 Mover para Próxima Etapa")
    
    # Importa funções necessárias
    from app import save_data, add_notification, format_brl
    from database_local import get_local_database as get_database
    
    # Define etapas do processo - Fluxo completo de 8 etapas
    etapas_processo = [
        "Solicitação",
        "Suprimentos", 
        "Em Cotação",
        "Aguardando Aprovação",
        "Aprovado",
        "Reprovado",
        "Compra feita",
        "Aguardando Entrega",
        "Pedido Finalizado"
    ]
    
    # Filtra solicitações que podem ser movidas pelo Suprimentos
    solicitacoes_moveveis = []
    for sol in data.get("solicitacoes", []):
        etapa_atual = sol.get("etapa_atual", sol.get("status", ""))
        # Suprimentos pode mover de: Compra feita -> Aguardando Entrega -> Pedido Finalizado
        if etapa_atual in ["Compra feita", "Aguardando Entrega"]:
            solicitacoes_moveveis.append(sol)
    
    if not solicitacoes_moveveis:
        st.info("📋 Não há solicitações disponíveis para movimentação no momento.")
        
        # Mostra resumo de todas as etapas
        st.markdown("### 📊 Resumo por Etapas")
        resumo_etapas = {}
        for sol in data.get("solicitacoes", []):
            etapa = sol.get("etapa_atual", sol.get("status", "Indefinido"))
            resumo_etapas[etapa] = resumo_etapas.get(etapa, 0) + 1
        
        if resumo_etapas:
            resumo_df = pd.DataFrame([
                {"Etapa": etapa, "Quantidade": qtd}
                for etapa, qtd in resumo_etapas.items()
            ]).sort_values("Quantidade", ascending=False)
            st.dataframe(resumo_df, use_container_width=True)
        
        return
    
    st.success(f"🔄 {len(solicitacoes_moveveis)} solicitação(ões) disponível(eis) para movimentação")
    
    # Tabs para organizar funcionalidades
    tab1, tab2 = st.tabs(["🔄 Controlar Entregas", "📊 Controle de Etapas"])
    
    with tab1:
        st.markdown("### 🔄 Controlar Entregas e Finalizações")
        st.info("💡 Mova solicitações entre as etapas: Compra feita → Aguardando Entrega → Pedido Finalizado")
        
        for sol in solicitacoes_moveveis:
            numero_solicitacao = sol.get("numero_solicitacao_estoque")
            
            with st.expander(f"📦 Pedido #{numero_solicitacao} - {sol.get('solicitante', 'N/A')}", 
                           expanded=len(solicitacoes_moveveis) <= 3):
                
                # Informações da solicitação
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Solicitante:** {sol.get('solicitante', 'N/A')}")
                    st.markdown(f"**Departamento:** {sol.get('departamento', 'N/A')}")
                    st.markdown(f"**Data:** {sol.get('data_solicitacao', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Prioridade:** {sol.get('prioridade', 'N/A')}")
                    st.markdown(f"**Etapa Atual:** {sol.get('etapa_atual', 'N/A')}")
                    req_interno = sol.get('numero_requisicao_interno')
                    st.markdown(f"**Req. Interna:** {req_interno if req_interno else 'N/A'}")
                
                with col3:
                    valor_final = sol.get('valor_final') or sol.get('valor_estimado')
                    st.markdown(f"**Valor Final:** {format_brl(valor_final) if valor_final else 'N/A'}")
                    fornecedor = sol.get('fornecedor_final') or sol.get('fornecedor_recomendado')
                    st.markdown(f"**Fornecedor:** {fornecedor if fornecedor else 'N/A'}")
                    st.markdown(f"**Status:** ✅ Aprovado")
                
                # Descrição
                if sol.get('descricao'):
                    st.markdown("**Descrição:**")
                    st.info(sol.get('descricao'))
                
                # Itens (resumo)
                if sol.get('itens'):
                    st.markdown("**📦 Itens:**")
                    total_itens = len(sol['itens'])
                    valor_total_itens = sum(item.get('valor_total', 0) or 0 for item in sol['itens'])
                    st.write(f"• {total_itens} item(ns) - Valor total: {format_brl(valor_total_itens)}")
                
                # Aprovação (se houver)
                aprovacoes = sol.get('aprovacoes', [])
                if aprovacoes:
                    ultima_aprovacao = aprovacoes[-1]
                    st.markdown("**✅ Última Aprovação:**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"• **Aprovador:** {ultima_aprovacao.get('nome_aprovador', 'N/A')}")
                        data_aprov = ultima_aprovacao.get('data_aprovacao', '')
                        if data_aprov:
                            try:
                                data_formatada = datetime.datetime.fromisoformat(data_aprov).strftime("%d/%m/%Y %H:%M")
                            except:
                                data_formatada = data_aprov
                            st.write(f"• **Data:** {data_formatada}")
                    with col_b:
                        if ultima_aprovacao.get('observacoes'):
                            st.write(f"• **Observações:** {ultima_aprovacao.get('observacoes')}")
                
                st.markdown("---")
                
                # Formulário para mover etapa
                etapa_atual = sol.get('etapa_atual', 'N/A')
                
                if etapa_atual == "Compra feita":
                    st.markdown("### 🚚 Registrar Entrega")
                    
                    with st.form(f"registrar_entrega_form_{numero_solicitacao}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            numero_pedido = st.text_input(
                                "Número do Pedido*",
                                placeholder="Ex: PED-2024-001",
                                help="Número do pedido de compra"
                            )
                            
                            data_entrega_prevista = st.date_input(
                                "Data de Entrega Prevista",
                                value=datetime.date.today() + datetime.timedelta(days=7)
                            )
                        
                        with col2:
                            fornecedor_final = st.text_input(
                                "Fornecedor Final",
                                value=fornecedor if fornecedor else "",
                                help="Fornecedor que executará o pedido"
                            )
                            
                            valor_final_input = st.number_input(
                                "Valor Final (R$)",
                                min_value=0.0,
                                value=float(valor_final) if valor_final else 0.0,
                                step=0.01
                            )
                        
                        observacoes_entrega = st.text_area(
                            "Observações da Entrega",
                            height=100,
                            placeholder="Observações sobre a entrega..."
                        )
                        
                        registrar_entrega = st.form_submit_button(
                            "🚚 Registrar Aguardando Entrega",
                            type="primary"
                        )
                        
                elif etapa_atual == "Aguardando Entrega":
                    st.markdown("### ✅ Finalizar Pedido")
                    
                    with st.form(f"finalizar_pedido_form_{numero_solicitacao}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            data_entrega_real = st.date_input(
                                "Data de Entrega Real",
                                value=datetime.date.today()
                            )
                            
                            entrega_conforme = st.selectbox(
                                "Entrega Conforme?",
                                ["Sim", "Não", "Parcial"]
                            )
                        
                        with col2:
                            responsavel_recebimento = st.text_input(
                                "Responsável pelo Recebimento",
                                value=usuario.get('nome', usuario.get('username', ''))
                            )
                            
                            nota_fiscal = st.text_input(
                                "Número da Nota Fiscal",
                                placeholder="Ex: NF-123456"
                            )
                        
                        observacoes_finalizacao = st.text_area(
                            "Observações da Finalização",
                            height=100,
                            placeholder="Observações sobre o recebimento e finalização..."
                        )
                        
                        finalizar_pedido = st.form_submit_button(
                            "✅ Finalizar Pedido",
                            type="primary"
                        )
                
                if etapa_atual == "Compra feita" and 'registrar_entrega' in locals() and registrar_entrega:
                    if numero_pedido.strip():
                        # Atualiza para Aguardando Entrega
                        for i, s in enumerate(data["solicitacoes"]):
                            if s["numero_solicitacao_estoque"] == numero_solicitacao:
                                data["solicitacoes"][i]["numero_pedido_compras"] = numero_pedido.strip()
                                data["solicitacoes"][i]["data_entrega_prevista"] = data_entrega_prevista.isoformat()
                                data["solicitacoes"][i]["status"] = "Aguardando Entrega"
                                data["solicitacoes"][i]["etapa_atual"] = "Aguardando Entrega"
                                
                                if fornecedor_final:
                                    data["solicitacoes"][i]["fornecedor_final"] = fornecedor_final
                                if valor_final_input > 0:
                                    data["solicitacoes"][i]["valor_final"] = valor_final_input
                                if observacoes_entrega:
                                    data["solicitacoes"][i]["observacoes_entrega"] = observacoes_entrega
                                
                                # Adiciona ao histórico
                                data["solicitacoes"][i]["historico_etapas"].append({
                                    "etapa": "Aguardando Entrega",
                                    "data_entrada": datetime.datetime.now().isoformat(),
                                    "usuario": usuario.get('nome', usuario.get('username')),
                                    "observacoes": f"Pedido #{numero_pedido} - Aguardando entrega prevista para {data_entrega_prevista.strftime('%d/%m/%Y')}"
                                })
                                
                                # Notifica solicitante
                                try:
                                    add_notification(data, "Solicitante", numero_solicitacao,
                                                   f"Pedido #{numero_pedido} em andamento - Aguardando entrega")
                                except:
                                    pass
                                
                                # Salva no banco se disponível
                                if USE_DATABASE:
                                    try:
                                        db = get_database()
                                        if db.db_available:
                                            updates = {
                                                "numero_pedido_compras": numero_pedido.strip(),
                                                "data_entrega_prevista": data_entrega_prevista.isoformat(),
                                                "status": "Aguardando Entrega",
                                                "etapa_atual": "Aguardando Entrega",
                                                "historico_etapas": data["solicitacoes"][i]["historico_etapas"]
                                            }
                                            if fornecedor_final:
                                                updates["fornecedor_final"] = fornecedor_final
                                            if valor_final_input > 0:
                                                updates["valor_final"] = valor_final_input
                                            if observacoes_entrega:
                                                updates["observacoes_entrega"] = observacoes_entrega
                                            
                                            db.update_solicitacao(numero_solicitacao, updates)
                                    except Exception as e:
                                        st.error(f"Erro ao salvar no banco: {e}")
                                
                                break
                        
                        save_data(data)
                        st.success(f"🚚 Pedido #{numero_pedido} registrado como 'Aguardando Entrega'!")
                        st.rerun()
                    else:
                        st.error("❌ Digite o número do pedido.")
                        
                elif etapa_atual == "Aguardando Entrega" and 'finalizar_pedido' in locals() and finalizar_pedido:
                    # Finaliza o pedido
                    for i, s in enumerate(data["solicitacoes"]):
                        if s["numero_solicitacao_estoque"] == numero_solicitacao:
                            data["solicitacoes"][i]["data_entrega_real"] = data_entrega_real.isoformat()
                            data["solicitacoes"][i]["entrega_conforme"] = entrega_conforme
                            data["solicitacoes"][i]["responsavel_recebimento"] = responsavel_recebimento
                            data["solicitacoes"][i]["nota_fiscal"] = nota_fiscal
                            data["solicitacoes"][i]["status"] = "Pedido Finalizado"
                            data["solicitacoes"][i]["etapa_atual"] = "Pedido Finalizado"
                            
                            if observacoes_finalizacao:
                                data["solicitacoes"][i]["observacoes_finalizacao"] = observacoes_finalizacao
                            
                            # Adiciona ao histórico
                            data["solicitacoes"][i]["historico_etapas"].append({
                                "etapa": "Pedido Finalizado",
                                "data_entrada": datetime.datetime.now().isoformat(),
                                "usuario": usuario.get('nome', usuario.get('username')),
                                "observacoes": f"Pedido finalizado - Entrega: {entrega_conforme} - NF: {nota_fiscal}"
                            })
                            
                            # Calcula SLA final
                            try:
                                from app import calcular_dias_uteis, obter_sla_por_prioridade, verificar_sla_cumprido
                                
                                data_inicio = datetime.datetime.fromisoformat(s.get('carimbo_data_hora', datetime.datetime.now().isoformat()))
                                data_fim = datetime.datetime.now()
                                dias_atendimento = calcular_dias_uteis(data_inicio, data_fim)
                                
                                sla_dias = obter_sla_por_prioridade(s.get('prioridade', 'Normal'), s.get('departamento'))
                                sla_cumprido = verificar_sla_cumprido(dias_atendimento, sla_dias)
                                
                                data["solicitacoes"][i]["dias_atendimento"] = dias_atendimento
                                data["solicitacoes"][i]["sla_dias"] = sla_dias
                                data["solicitacoes"][i]["sla_cumprido"] = sla_cumprido
                            except:
                                pass
                            
                            # Notifica solicitante
                            try:
                                add_notification(data, "Solicitante", numero_solicitacao,
                                               f"Pedido finalizado com sucesso! NF: {nota_fiscal}")
                            except:
                                pass
                            
                            # Salva no banco se disponível
                            if USE_DATABASE:
                                try:
                                    db = get_database()
                                    if db.db_available:
                                        updates = {
                                            "data_entrega_real": data_entrega_real.isoformat(),
                                            "entrega_conforme": entrega_conforme,
                                            "responsavel_recebimento": responsavel_recebimento,
                                            "nota_fiscal": nota_fiscal,
                                            "status": "Pedido Finalizado",
                                            "etapa_atual": "Pedido Finalizado",
                                            "historico_etapas": data["solicitacoes"][i]["historico_etapas"]
                                        }
                                        if observacoes_finalizacao:
                                            updates["observacoes_finalizacao"] = observacoes_finalizacao
                                        
                                        # Adiciona métricas SLA se calculadas
                                        if data["solicitacoes"][i].get("dias_atendimento") is not None:
                                            updates["dias_atendimento"] = data["solicitacoes"][i]["dias_atendimento"]
                                            updates["sla_dias"] = data["solicitacoes"][i]["sla_dias"]
                                            updates["sla_cumprido"] = data["solicitacoes"][i]["sla_cumprido"]
                                        
                                        db.update_solicitacao(numero_solicitacao, updates)
                                except Exception as e:
                                    st.error(f"Erro ao salvar no banco: {e}")
                            
                            break
                    
                    save_data(data)
                    st.success(f"✅ Pedido finalizado com sucesso!")
                    st.rerun()
    
    with tab2:
        st.markdown("### 📊 Controle de Etapas")
        
        # Resumo geral por etapas
        resumo_completo = {}
        valores_por_etapa = {}
        
        for sol in data.get("solicitacoes", []):
            etapa = sol.get("etapa_atual", sol.get("status", "Indefinido"))
            resumo_completo[etapa] = resumo_completo.get(etapa, 0) + 1
            
            valor = sol.get("valor_final") or sol.get("valor_estimado") or 0
            valores_por_etapa[etapa] = valores_por_etapa.get(etapa, 0) + valor
        
        if resumo_completo:
            st.markdown("#### 📈 Distribuição por Etapas")
            
            # Cria DataFrame para visualização
            resumo_df = pd.DataFrame([
                {
                    "Etapa": etapa,
                    "Quantidade": qtd,
                    "Valor Total": format_brl(valores_por_etapa.get(etapa, 0)),
                    "Valor_Num": valores_por_etapa.get(etapa, 0)
                }
                for etapa, qtd in resumo_completo.items()
            ]).sort_values("Quantidade", ascending=False)
            
            # Exibe tabela
            st.dataframe(resumo_df[["Etapa", "Quantidade", "Valor Total"]], use_container_width=True)
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_solicitacoes = sum(resumo_completo.values())
                st.metric("Total Solicitações", total_solicitacoes)
            
            with col2:
                finalizadas = resumo_completo.get("Pedido Finalizado", 0)
                st.metric("Finalizadas", finalizadas)
            
            with col3:
                pendentes = total_solicitacoes - finalizadas
                st.metric("Em Andamento", pendentes)
            
            with col4:
                if total_solicitacoes > 0:
                    taxa_finalizacao = (finalizadas / total_solicitacoes) * 100
                    st.metric("Taxa Finalização", f"{taxa_finalizacao:.1f}%")
                else:
                    st.metric("Taxa Finalização", "0%")
            
            # Gráfico de barras
            if len(resumo_df) > 1:
                st.markdown("#### 📊 Gráfico por Etapas")
                st.bar_chart(resumo_df.set_index("Etapa")["Quantidade"])
        
        # Solicitações com atraso de SLA
        st.markdown("#### ⚠️ Atenção - Possíveis Atrasos")
        
        solicitacoes_atrasadas = []
        for sol in data.get("solicitacoes", []):
            if sol.get("etapa_atual") not in ["Pedido Finalizado", "Reprovado"]:
                try:
                    from app import calcular_dias_uteis, obter_sla_por_prioridade
                    
                    data_inicio = datetime.datetime.fromisoformat(sol.get('carimbo_data_hora', datetime.datetime.now().isoformat()))
                    dias_decorridos = calcular_dias_uteis(data_inicio)
                    sla_dias = obter_sla_por_prioridade(sol.get('prioridade', 'Normal'), sol.get('departamento'))
                    
                    if dias_decorridos > sla_dias:
                        solicitacoes_atrasadas.append({
                            "Solicitação": sol.get("numero_solicitacao_estoque"),
                            "Solicitante": sol.get("solicitante", "N/A"),
                            "Etapa": sol.get("etapa_atual", "N/A"),
                            "Prioridade": sol.get("prioridade", "N/A"),
                            "Dias Decorridos": dias_decorridos,
                            "SLA (dias)": sla_dias,
                            "Atraso": dias_decorridos - sla_dias
                        })
                except:
                    pass
        
        if solicitacoes_atrasadas:
            st.warning(f"⚠️ {len(solicitacoes_atrasadas)} solicitação(ões) com possível atraso de SLA")
            atraso_df = pd.DataFrame(solicitacoes_atrasadas).sort_values("Atraso", ascending=False)
            st.dataframe(atraso_df, use_container_width=True)
        else:
            st.success("✅ Nenhuma solicitação com atraso de SLA identificada.")
