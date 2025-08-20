"""
Implementação da funcionalidade Nova Solicitação para o perfil Solicitante
"""

import streamlit as st
import pandas as pd
import datetime
import os
from typing import Dict, List

def nova_solicitacao(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Renderiza a página de Nova Solicitação"""
    from style import (get_section_header_html, get_info_box_html, get_form_container_start, 
                      get_form_container_end, get_form_section_start, get_form_section_end, 
                      get_form_section_title)
    
    # Importações condicionais
    if USE_DATABASE:
        try:
            from database import get_database
        except ImportError:
            USE_DATABASE = False
    
    # Constantes
    DEPARTAMENTOS = ["Manutenção", "TI", "RH", "Financeiro", "Marketing", "Operações", "Outro"]
    PRIORIDADES = ["Normal", "Urgente", "Baixa", "Alta"]
    ALLOWED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"]
    
    # Funções auxiliares
    def obter_sla_por_prioridade(prioridade: str, departamento: str = None) -> int:
        SLA_PADRAO = {"Urgente": 1, "Alta": 2, "Normal": 3, "Baixa": 5}
        return SLA_PADRAO.get(prioridade, 3)
    
    def ensure_upload_dir(data: Dict):
        upload_dir = data.get("configuracoes", {}).get("upload_dir", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir
    
    def save_uploaded_files(files: List, base_dir: str) -> List[Dict]:
        saved = []
        if not files:
            return saved
        os.makedirs(base_dir, exist_ok=True)
        for f in files:
            try:
                filename = f.name
                ext = filename.split('.')[-1].lower()
                dest_path = os.path.join(base_dir, filename)
                with open(dest_path, 'wb') as out:
                    out.write(f.getbuffer())
                saved.append({
                    "nome_arquivo": filename,
                    "caminho": dest_path.replace('\\', '/'),
                    "tipo": ext,
                    "data_upload": datetime.datetime.now().isoformat()
                })
            except Exception:
                pass
        return saved
    
    def render_data_editor(df: pd.DataFrame, key: str = None, **kwargs) -> pd.DataFrame:
        try:
            return st.data_editor(df, key=key, **kwargs)
        except Exception:
            try:
                return st.experimental_data_editor(df, key=key, **kwargs)
            except Exception:
                st.dataframe(df, use_container_width=True)
                return df
    
    def save_data(data: Dict):
        if USE_DATABASE:
            try:
                db = get_database()
                if db.db_available:
                    config = data.get("configuracoes", {})
                    for key, value in config.items():
                        if key != "catalogo_produtos":
                            db.set_config(key, str(value))
                    catalogo = config.get("catalogo_produtos", [])
                    if catalogo:
                        db.update_catalogo_produtos(catalogo)
                    return
            except Exception:
                pass
        
        import json
        with open("compras_sla_data.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # Interface principal
    st.markdown(get_section_header_html('📝 Nova Solicitação de Compra'), unsafe_allow_html=True)
    st.markdown(get_info_box_html('💡 <strong>Baseado na estrutura da planilha Excel - Aba \'Solicitação\'</strong>'), unsafe_allow_html=True)
    
    st.markdown(get_form_container_start(), unsafe_allow_html=True)
    
    with st.form("nova_solicitacao"):
        # Seção 1: Dados do Solicitante
        st.markdown(get_form_section_start(), unsafe_allow_html=True)
        st.markdown(get_form_section_title('👤 Dados do Solicitante'), unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            solicitante = st.text_input("Solicitante (Nome e Sobrenome)*", 
                                      help="Campo obrigatório conforme planilha",
                                      placeholder="Digite o nome completo do solicitante")
            departamento = st.selectbox("Departamento*", DEPARTAMENTOS, help="Departamento do solicitante")
        
        with col2:
            prioridade = st.selectbox("Prioridade*", PRIORIDADES, help="Define o SLA automaticamente")
            sla_dias = obter_sla_por_prioridade(prioridade)
            st.info(f"📅 **SLA:** {sla_dias} dias úteis para prioridade '{prioridade}'")
        
        st.markdown(get_form_section_end(), unsafe_allow_html=True)
        
        # Seção 2: Dados da Solicitação
        st.markdown(get_form_section_start(), unsafe_allow_html=True)
        st.markdown(get_form_section_title('📋 Dados da Solicitação'), unsafe_allow_html=True)
        
        descricao = st.text_area("Descrição*", height=120,
                                help="Descrição detalhada da solicitação",
                                placeholder="Descreva detalhadamente o que está sendo solicitado...")
        
        local_aplicacao = st.text_input("Local de Aplicação*",
                                       help="Onde o material será aplicado",
                                       placeholder="Ex: Sala de Servidores, Linha de Produção 1...")

        # Itens da Solicitação
        st.markdown(get_form_section_title('🧾 Itens da Solicitação'), unsafe_allow_html=True)
        catalogo = data.get("configuracoes", {}).get("catalogo_produtos", [])
        
        if not catalogo:
            st.warning("Catálogo de produtos vazio. Configure em '📦 Catálogo de Produtos'.")
            itens_editados = pd.DataFrame([{"codigo": "", "quantidade": 1}])
        else:
            itens_df_init = pd.DataFrame([{"codigo": "", "quantidade": 1}])
            try:
                if hasattr(st, "column_config"):
                    col_cfg = {
                        "codigo": st.column_config.SelectboxColumn(
                            "Código do Produto",
                            options=[c.get("codigo") for c in catalogo if c.get("ativo", True)],
                            help="Selecione um código válido do catálogo"
                        ),
                        "quantidade": st.column_config.NumberColumn(
                            "Quantidade", min_value=1, step=1, help="Informe a quantidade desejada"
                        )
                    }
                    itens_editados = render_data_editor(itens_df_init, key="itens_editor",
                                                       use_container_width=True, num_rows="dynamic",
                                                       column_config=col_cfg, hide_index=True)
                else:
                    itens_editados = render_data_editor(itens_df_init, key="itens_editor",
                                                       use_container_width=True, num_rows="dynamic")
            except Exception:
                itens_editados = render_data_editor(itens_df_init, key="itens_editor",
                                                   use_container_width=True, num_rows="dynamic")
            
            st.info("Adicione linhas e selecione o código do produto e a quantidade. Linhas vazias serão ignoradas.")
        
        st.markdown(get_form_section_end(), unsafe_allow_html=True)
        
        # Seção 3: Anexos
        st.markdown(get_form_section_start(), unsafe_allow_html=True)
        st.markdown(get_form_section_title('📎 Anexos da Solicitação'), unsafe_allow_html=True)
        
        anexos_files = st.file_uploader("Faça upload dos arquivos relacionados à solicitação (opcional)",
                                       type=ALLOWED_FILE_TYPES, accept_multiple_files=True,
                                       help="Tipos permitidos: PDF, PNG, JPG, JPEG, DOC, DOCX, XLS, XLSX")
        
        if anexos_files:
            st.success(f"✅ {len(anexos_files)} arquivo(s) selecionado(s)")
        
        st.markdown(get_form_section_end(), unsafe_allow_html=True)
        
        # Seção 4: Informações Automáticas
        st.markdown(get_form_section_start(), unsafe_allow_html=True)
        st.markdown(get_form_section_title('⚙️ Informações de Controle'), unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-style: italic; margin-bottom: 1rem;">Os campos abaixo são preenchidos automaticamente pelo sistema</p>', unsafe_allow_html=True)
        
        col5, col6 = st.columns(2)
        with col5:
            st.text_input("Nº Solicitação (Estoque)", value="Será gerado automaticamente", disabled=True)
            st.text_input("Status Inicial", value="Solicitação", disabled=True)
        with col6:
            st.text_input("Data/Hora de Criação", 
                         value=datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S'), disabled=True)
            st.text_input("SLA Aplicado", value=f"{sla_dias} dias úteis", disabled=True)
        
        st.markdown(get_form_section_end(), unsafe_allow_html=True)
        
        # Botão de submissão
        st.markdown('<br>', unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Criar Solicitação", use_container_width=True)
    
    st.markdown(get_form_container_end(), unsafe_allow_html=True)
    
    # Processamento do formulário
    if submitted:
        # Previne dupla submissão
        if 'form_submitted' not in st.session_state:
            st.session_state.form_submitted = False
        
        if st.session_state.form_submitted:
            st.warning("⚠️ Solicitação já foi enviada. Aguarde o processamento.")
            return
        
        # Prepara itens estruturados
        itens_struct = []
        try:
            catalog_map = {c.get("codigo"): c for c in data.get("configuracoes", {}).get("catalogo_produtos", [])}
            if 'itens_editados' in locals() and isinstance(itens_editados, pd.DataFrame):
                for r in itens_editados.to_dict(orient="records"):
                    cod = (r.get("codigo") or "").strip()
                    if not cod:
                        continue
                    prod = catalog_map.get(cod)
                    qtd = r.get("quantidade")
                    try:
                        qtd_val = int(qtd) if float(qtd) == int(qtd) else float(qtd)
                    except Exception:
                        qtd_val = None
                    if prod and qtd_val and qtd_val > 0:
                        itens_struct.append({
                            "codigo": cod,
                            "nome": prod.get("nome"),
                            "unidade": prod.get("unidade"),
                            "quantidade": qtd_val
                        })
        except Exception:
            itens_struct = []

        if solicitante and departamento and descricao and local_aplicacao and len(itens_struct) > 0:
            # Gera números automáticos
            numero_solicitacao = data["configuracoes"]["proximo_numero_solicitacao"]
            data["configuracoes"]["proximo_numero_solicitacao"] += 1
            
            # Salva anexos da solicitação
            upload_root = ensure_upload_dir(data)
            sol_dir = os.path.join(upload_root, f"solicitacao_{numero_solicitacao}", "requisicao")
            anexos_meta = save_uploaded_files(anexos_files, sol_dir)
            
            nova_solicitacao = {
                "carimbo_data_hora": datetime.datetime.now().isoformat(),
                "solicitante": solicitante,
                "departamento": departamento,
                "prioridade": prioridade,
                "descricao": descricao,
                "local_aplicacao": local_aplicacao,
                "status": "Solicitação",
                "numero_solicitacao_estoque": numero_solicitacao,
                "numero_pedido_compras": None,
                "data_numero_pedido": None,
                "data_cotacao": None,
                "data_entrega": None,
                "sla_dias": sla_dias,
                "dias_atendimento": None,
                "sla_cumprido": None,
                "observacoes": None,
                "numero_requisicao_interno": None,
                "data_requisicao_interna": None,
                "responsavel_suprimentos": None,
                "itens": itens_struct,
                "anexos_requisicao": anexos_meta,
                "cotacoes": [],
                "aprovacoes": [],
                "valor_estimado": None,
                "valor_final": None,
                "fornecedor_recomendado": None,
                "fornecedor_final": None,
                "id": len(data["solicitacoes"]) + 1,
                "etapa_atual": "Solicitação",
                "historico_etapas": [{
                    "etapa": "Solicitação",
                    "data_entrada": datetime.datetime.now().isoformat(),
                    "usuario": "Sistema"
                }]
            }
            
            # Salva no banco ou JSON
            if USE_DATABASE:
                db = get_database()
                if db.db_available:
                    success = db.add_solicitacao(nova_solicitacao)
                    if success:
                        db.set_config('proximo_numero_solicitacao', str(data["configuracoes"]["proximo_numero_solicitacao"]))
                        st.success(f"✅ Solicitação #{numero_solicitacao} salva no banco Neon com sucesso!")
                    else:
                        st.error("❌ Erro ao salvar solicitação no banco de dados.")
                        return
                else:
                    data["solicitacoes"].append(nova_solicitacao)
                    save_data(data)
            else:
                data["solicitacoes"].append(nova_solicitacao)
                save_data(data)
            
            # Marca como submetido para prevenir duplicatas
            st.session_state.form_submitted = True
            
            # Mensagem de sucesso
            success_content = f'<h3 style="color: #065f46; margin: 0 0 1rem 0;">🎉 Solicitação #{numero_solicitacao} Criada com Sucesso!</h3>'
            st.markdown(get_info_box_html(success_content, "success"), unsafe_allow_html=True)
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown(f"**📅 Data/Hora:** {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
                st.markdown(f"**⏱️ SLA:** {sla_dias} dias úteis")
            with col_info2:
                st.markdown(f"**📊 Status:** Solicitação (Etapa 1 de 7)")
                st.markdown(f"**📎 Anexos:** {len(anexos_meta)} arquivo(s)")
            st.markdown(f"**🧾 Itens:** {len(itens_struct)} item(ns)")
            
            # Próximos passos
            proximos_passos = '<h4 style="color: #1e40af; margin: 0 0 1rem 0;">🔄 Próximos Passos</h4>**1.** A solicitação será analisada pela área de **Suprimentos**<br>**2.** Use a opção **\'🔄 Mover para Próxima Etapa\'** para avançar o processo<br>**3.** Acompanhe o progresso no **Dashboard SLA** ou **Histórico por Etapa**'
            st.markdown(get_info_box_html(proximos_passos), unsafe_allow_html=True)
            
            # Botão para criar nova solicitação (limpa o formulário)
            if st.button("🆕 Criar Nova Solicitação", type="primary", use_container_width=True):
                # Limpa o estado do formulário
                for key in list(st.session_state.keys()):
                    if key.startswith('nova_solicitacao') or key in ['form_submitted', 'itens_editor']:
                        del st.session_state[key]
                st.rerun()
            
        else:
            warning_content = '<h4 style="color: #92400e; margin: 0 0 0.5rem 0;">⚠️ Campos Obrigatórios</h4>Por favor, preencha todos os campos marcados com **asterisco (*)** e adicione ao menos 1 item válido antes de continuar.'
            st.markdown(get_info_box_html(warning_content, "warning"), unsafe_allow_html=True)
