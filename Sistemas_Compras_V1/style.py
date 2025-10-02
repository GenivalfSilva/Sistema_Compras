"""
Módulo de estilos CSS para o Sistema de Gestão de Compras - SLA
Contém toda a estilização customizada com as cores da marca Ziran
"""

def get_custom_css() -> str:
    """
    Retorna o CSS customizado completo para o Sistema de Gestão de Compras.
    Inclui todas as cores da marca Ziran e estilos personalizados.
    """
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
    
    :root {
        --ziran-red: #E53E3E;
        --ziran-red-light: #FC8181;
        --ziran-red-dark: #C53030;
        --ziran-gray: #2D3748;
        --ziran-gray-light: #4A5568;
        --ziran-white: #FFFFFF;
        --ziran-bg-light: #F7FAFC;
        --ziran-bg-gray: #EDF2F7;
    }
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: linear-gradient(rgba(247, 250, 252, 0.95), rgba(247, 250, 252, 0.95)), 
                    url('./assets/img/ziran fundo.jpg') center/cover no-repeat fixed;
        min-height: 100vh;
    }
    
    .background-overlay {
        background: linear-gradient(135deg, rgba(229, 62, 62, 0.05) 0%, rgba(197, 48, 48, 0.05) 100%);
        backdrop-filter: blur(1px);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .main-header {
        background: linear-gradient(135deg, var(--ziran-red) 0%, var(--ziran-red-dark) 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(229, 62, 62, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .title-text {
        color: black !important;
        margin: 0;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 1.8rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .subtitle-text {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 0.95rem;
        font-weight: 400;
        opacity: 0.9;
    }
    .brand-text {
        color: var(--ziran-gray);
        font-weight: 600;
        font-size: 1rem;
        text-shadow: none;
        background: rgba(255, 255, 255, 0.9);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        display: inline-block;
        border: 1px solid rgba(45, 55, 72, 0.1);
    }
    .section-header {
        background: linear-gradient(135deg, var(--ziran-red) 0%, var(--ziran-red-dark) 100%);
        color: var(--ziran-white);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin: 2rem 0 1.5rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.1rem;
        font-family: 'Poppins', sans-serif;
        box-shadow: 0 4px 16px rgba(229, 62, 62, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .info-box {
        background: linear-gradient(135deg, var(--ziran-bg-light) 0%, var(--ziran-bg-gray) 100%);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 4px solid var(--ziran-red);
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        color: var(--ziran-gray);
    }
    .success-box {
        background: linear-gradient(135deg, #F0FFF4 0%, #C6F6D5 100%);
        border: 1px solid #9AE6B4;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 4px solid #38A169;
        color: #22543D;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(56, 161, 105, 0.1);
    }
    .warning-box {
        background: linear-gradient(135deg, #FFFAF0 0%, #FED7AA 100%);
        border: 1px solid #F6AD55;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 4px solid #ED8936;
        color: #C05621;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(237, 137, 54, 0.1);
    }
    .form-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 1rem 0;
    }
    .form-section {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--ziran-bg-gray);
    }
    .form-section:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }
    .form-section h3 {
        color: var(--ziran-gray);
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--ziran-red);
        display: inline-block;
    }
    .stats-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(8px);
        padding: 1.1rem;
        border-radius: 12px;
        border-left: 4px solid var(--ziran-red);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        margin: 0.5rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .stats-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(229, 62, 62, 0.12);
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--ziran-red);
        margin: 0;
        font-family: 'Poppins', sans-serif;
    }
    .metric-label {
        color: var(--ziran-gray-light);
        font-size: 0.9rem;
        margin: 0;
        font-weight: 500;
    }
    .stButton > button {
        background: linear-gradient(135deg, var(--ziran-red) 0%, var(--ziran-red-dark) 100%) !important;
        color: var(--ziran-white) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 16px rgba(229, 62, 62, 0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(229, 62, 62, 0.4) !important;
        background: linear-gradient(135deg, var(--ziran-red-light) 0%, var(--ziran-red) 100%) !important;
    }
    .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label {
        font-weight: 500 !important;
        color: var(--ziran-gray) !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
    }
    .stFileUploader {
        border: 2px dashed var(--ziran-red-light) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        background: var(--ziran-bg-light) !important;
        transition: all 0.3s ease !important;
    }
    .stFileUploader:hover {
        border-color: var(--ziran-red) !important;
        background: var(--ziran-white) !important;
    }
    .sidebar .stSelectbox {
        margin-bottom: 1rem;
    }
    /* Sidebar customization */
    .css-1d391kg {
        background-color: var(--ziran-white) !important;
    }
    .css-1d391kg .stSelectbox > div > div {
        background-color: var(--ziran-bg-light) !important;
        border: 1px solid var(--ziran-red-light) !important;
    }
    /* Metrics styling */
    .css-1xarl3l {
        color: var(--ziran-red) !important;
        font-weight: 600 !important;
    }
    </style>
    """

def get_sidebar_css() -> str:
    """
    Retorna o CSS específico para a sidebar com design da marca Ziran.
    """
    return """
    <div style="background: linear-gradient(135deg, var(--ziran-red) 0%, var(--ziran-red-dark) 100%); 
                padding: 1rem; border-radius: 12px; margin-bottom: 1rem; text-align: center;">
        <h3 style="color: white; margin: 0; font-family: 'Poppins', sans-serif;">🏢 ZIRAN</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">Sistema de Compras</p>
    </div>
    """

def get_header_html(logo_path: str = "assets/img/logo_ziran.jpg") -> str:
    """
    Retorna o HTML do cabeçalho principal com logo e título.
    
    Args:
        logo_path: Caminho para o arquivo de logo
    """
    return f"""
    <div class="main-header">
        <div style="display: flex; align-items: center; gap: 2rem;">
            <div style="flex-shrink: 0;">
                <!-- Logo será inserido via st.image() -->
            </div>
            <div style="flex: 1;">
                <h1 class="title-text">📋 Sistema de Gestão de Compras - SLA</h1>
                <p class="subtitle-text">Controle de Solicitações e Medição de SLA</p>
                <p class="brand-text">✨ Ziran - Gestão Inteligente</p>
            </div>
        </div>
    </div>
    """

def get_stats_card_html(value: str, label: str) -> str:
    """
    Retorna o HTML de um card de estatísticas personalizado.
    
    Args:
        value: Valor a ser exibido
        label: Rótulo do card
    """
    return f"""
    <div class="stats-card">
        <p class="metric-value">{value}</p>
        <p class="metric-label">{label}</p>
    </div>
    """

def get_section_header_html(title: str) -> str:
    """
    Retorna o HTML de um cabeçalho de seção estilizado.
    
    Args:
        title: Título da seção
    """
    return f'<div class="section-header">{title}</div>'

def get_info_box_html(content: str, box_type: str = "info") -> str:
    """
    Retorna o HTML de uma caixa de informação estilizada.
    
    Args:
        content: Conteúdo da caixa
        box_type: Tipo da caixa ('info', 'success', 'warning')
    """
    css_class = f"{box_type}-box"
    return f'<div class="{css_class}">{content}</div>'

def get_form_container_start() -> str:
    """Retorna o HTML de abertura do container de formulário."""
    return '<div class="form-container">'

def get_form_container_end() -> str:
    """Retorna o HTML de fechamento do container de formulário."""
    return '</div>'

def get_form_section_start() -> str:
    """Retorna o HTML de abertura de uma seção de formulário."""
    return '<div class="form-section">'

def get_form_section_end() -> str:
    """Retorna o HTML de fechamento de uma seção de formulário."""
    return '</div>'

def get_form_section_title(title: str) -> str:
    """
    Retorna o HTML de um título de seção de formulário.
    
    Args:
        title: Título da seção
    """
    return f'<h3>{title}</h3>'
