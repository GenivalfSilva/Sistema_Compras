#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de Frontend para Sistema de Compras - Streamlit
Testa componentes da interface, navegação e interações do usuário
"""

import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Any
import threading
import signal

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestadorFrontendStreamlit:
    """Classe para testar a interface Streamlit"""
    
    def __init__(self):
        self.resultados = []
        self.contador_testes = 0
        self.contador_sucessos = 0
        self.contador_falhas = 0
        self.servidor_processo = None
        self.base_url = "http://localhost:8501"
        
    def log_resultado(self, teste: str, status: str, detalhes: str = ""):
        """Registra resultado de um teste"""
        resultado = {
            "teste": teste,
            "status": status,
            "detalhes": detalhes,
            "timestamp": datetime.now().isoformat()
        }
        self.resultados.append(resultado)
        
        if status == "SUCESSO":
            self.contador_sucessos += 1
            print(f"✅ {teste}")
        elif status == "FALHA":
            self.contador_falhas += 1
            print(f"❌ {teste} - {detalhes}")
        else:
            print(f"⚠️  {teste} - {detalhes}")
            
        self.contador_testes += 1

    def iniciar_servidor_streamlit(self):
        """Inicia o servidor Streamlit para testes"""
        try:
            print("🚀 Iniciando servidor Streamlit para testes...")
            
            # Mata processos existentes na porta 8501
            try:
                subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], 
                             capture_output=True, check=False)
                time.sleep(2)
            except:
                pass
            
            # Inicia novo servidor
            self.servidor_processo = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", "app.py",
                "--server.port", "8501",
                "--server.headless", "true",
                "--server.enableCORS", "false",
                "--server.enableXsrfProtection", "false"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Aguarda servidor inicializar
            print("⏳ Aguardando servidor inicializar...")
            for i in range(30):  # 30 segundos timeout
                try:
                    response = requests.get(f"{self.base_url}/healthz", timeout=2)
                    if response.status_code == 200:
                        print("✅ Servidor Streamlit iniciado com sucesso!")
                        return True
                except:
                    time.sleep(1)
            
            print("❌ Timeout ao iniciar servidor Streamlit")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return False

    def parar_servidor_streamlit(self):
        """Para o servidor Streamlit"""
        try:
            if self.servidor_processo:
                self.servidor_processo.terminate()
                self.servidor_processo.wait(timeout=5)
            
            # Força parada se necessário
            subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], 
                         capture_output=True, check=False)
            print("🛑 Servidor Streamlit parado")
            
        except Exception as e:
            print(f"⚠️  Erro ao parar servidor: {e}")

    def testar_carregamento_pagina_principal(self):
        """Testa se a página principal carrega corretamente"""
        print("\n🌐 TESTANDO CARREGAMENTO DA INTERFACE")
        print("=" * 50)
        
        try:
            response = requests.get(self.base_url, timeout=10)
            
            if response.status_code == 200:
                self.log_resultado("Carregamento da página principal", "SUCESSO")
                
                # Verifica se contém elementos essenciais
                content = response.text.lower()
                
                elementos_essenciais = [
                    "gestão de compras",
                    "streamlit",
                    "ziran",
                    "sistema"
                ]
                
                for elemento in elementos_essenciais:
                    if elemento in content:
                        self.log_resultado(f"Elemento '{elemento}' presente", "SUCESSO")
                    else:
                        self.log_resultado(f"Elemento '{elemento}' ausente", "FALHA", 
                                         "Elemento não encontrado na página")
            else:
                self.log_resultado("Carregamento da página principal", "FALHA", 
                                 f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_resultado("Carregamento da página principal", "FALHA", str(e))

    def testar_estrutura_arquivos_interface(self):
        """Testa se todos os arquivos de interface existem"""
        print("\n📁 TESTANDO ESTRUTURA DE ARQUIVOS DA INTERFACE")
        print("=" * 50)
        
        arquivos_interface = [
            "app.py",
            "style.py",
            "session_manager.py",
            "profiles/admin.py",
            "profiles/solicitante_nova.py",
            "profiles/suprimentos_mover.py",
            "profiles/estoque_requisicoes.py",
            "profiles/diretoria_aprovacoes.py"
        ]
        
        for arquivo in arquivos_interface:
            caminho = os.path.join(os.getcwd(), arquivo)
            if os.path.exists(caminho):
                self.log_resultado(f"Arquivo {arquivo}", "SUCESSO")
            else:
                self.log_resultado(f"Arquivo {arquivo}", "FALHA", "Arquivo não encontrado")

    def testar_componentes_streamlit(self):
        """Testa componentes específicos do Streamlit"""
        print("\n🧩 TESTANDO COMPONENTES STREAMLIT")
        print("=" * 50)
        
        # Testa importações de módulos
        try:
            import streamlit as st
            self.log_resultado("Importação Streamlit", "SUCESSO")
        except ImportError as e:
            self.log_resultado("Importação Streamlit", "FALHA", str(e))
            return
        
        # Testa módulos personalizados
        modulos_teste = [
            ("style", "get_custom_css"),
            ("session_manager", "SessionManager"),
            ("database_local", "DatabaseLocal"),
            ("audit_logger", "AuditLogger")
        ]
        
        for modulo, funcao in modulos_teste:
            try:
                mod = __import__(modulo)
                if hasattr(mod, funcao):
                    self.log_resultado(f"Módulo {modulo}.{funcao}", "SUCESSO")
                else:
                    self.log_resultado(f"Módulo {modulo}.{funcao}", "FALHA", 
                                     f"Função {funcao} não encontrada")
            except ImportError as e:
                self.log_resultado(f"Módulo {modulo}", "FALHA", str(e))

    def testar_perfis_usuario(self):
        """Testa se todos os perfis de usuário estão implementados"""
        print("\n👥 TESTANDO PERFIS DE USUÁRIO")
        print("=" * 50)
        
        perfis = [
            ("admin.py", "def show_admin"),
            ("solicitante_nova.py", "def criar_nova_solicitacao"),
            ("suprimentos_mover.py", "def mover_solicitacao"),
            ("estoque_requisicoes.py", "def criar_requisicao"),
            ("diretoria_aprovacoes.py", "def aprovar_solicitacoes")
        ]
        
        for arquivo, funcao_esperada in perfis:
            caminho = os.path.join("profiles", arquivo)
            
            if os.path.exists(caminho):
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    if funcao_esperada in conteudo:
                        self.log_resultado(f"Perfil {arquivo}", "SUCESSO")
                    else:
                        self.log_resultado(f"Perfil {arquivo}", "FALHA", 
                                         f"Função {funcao_esperada} não encontrada")
                except Exception as e:
                    self.log_resultado(f"Perfil {arquivo}", "FALHA", str(e))
            else:
                self.log_resultado(f"Perfil {arquivo}", "FALHA", "Arquivo não encontrado")

    def testar_navegacao_interface(self):
        """Testa navegação entre páginas"""
        print("\n🧭 TESTANDO NAVEGAÇÃO DA INTERFACE")
        print("=" * 50)
        
        # Simula teste de navegação verificando estrutura do app.py
        try:
            with open("app.py", 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            elementos_navegacao = [
                "st.sidebar",
                "st.selectbox",
                "if usuario_logado",
                "session_state",
                "login"
            ]
            
            for elemento in elementos_navegacao:
                if elemento in conteudo:
                    self.log_resultado(f"Navegação - {elemento}", "SUCESSO")
                else:
                    self.log_resultado(f"Navegação - {elemento}", "FALHA", 
                                     "Elemento de navegação não encontrado")
                    
        except Exception as e:
            self.log_resultado("Navegação - Estrutura", "FALHA", str(e))

    def testar_formularios_interface(self):
        """Testa formulários da interface"""
        print("\n📝 TESTANDO FORMULÁRIOS DA INTERFACE")
        print("=" * 50)
        
        # Verifica formulários nos arquivos de perfil
        formularios_teste = [
            ("solicitante_nova.py", ["st.form", "st.text_input", "st.selectbox", "st.text_area"]),
            ("estoque_requisicoes.py", ["st.form", "st.number_input", "st.date_input"]),
            ("suprimentos_mover.py", ["st.form", "st.multiselect", "st.file_uploader"]),
            ("diretoria_aprovacoes.py", ["st.form", "st.radio", "st.button"])
        ]
        
        for arquivo, elementos in formularios_teste:
            caminho = os.path.join("profiles", arquivo)
            
            if os.path.exists(caminho):
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    elementos_encontrados = 0
                    for elemento in elementos:
                        if elemento in conteudo:
                            elementos_encontrados += 1
                    
                    if elementos_encontrados >= len(elementos) // 2:  # Pelo menos 50%
                        self.log_resultado(f"Formulário {arquivo}", "SUCESSO")
                    else:
                        self.log_resultado(f"Formulário {arquivo}", "FALHA", 
                                         f"Poucos elementos encontrados: {elementos_encontrados}/{len(elementos)}")
                        
                except Exception as e:
                    self.log_resultado(f"Formulário {arquivo}", "FALHA", str(e))

    def testar_responsividade_interface(self):
        """Testa responsividade da interface"""
        print("\n📱 TESTANDO RESPONSIVIDADE DA INTERFACE")
        print("=" * 50)
        
        # Verifica uso de colunas e containers responsivos
        arquivos_responsivos = ["app.py", "style.py"]
        
        for arquivo in arquivos_responsivos:
            if os.path.exists(arquivo):
                try:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    elementos_responsivos = [
                        "st.columns",
                        "st.container",
                        "use_container_width",
                        "@media",
                        "flex"
                    ]
                    
                    elementos_encontrados = sum(1 for elem in elementos_responsivos if elem in conteudo)
                    
                    if elementos_encontrados >= 2:
                        self.log_resultado(f"Responsividade {arquivo}", "SUCESSO")
                    else:
                        self.log_resultado(f"Responsividade {arquivo}", "FALHA", 
                                         "Poucos elementos responsivos encontrados")
                        
                except Exception as e:
                    self.log_resultado(f"Responsividade {arquivo}", "FALHA", str(e))

    def testar_validacoes_frontend(self):
        """Testa validações no frontend"""
        print("\n✅ TESTANDO VALIDAÇÕES DO FRONTEND")
        print("=" * 50)
        
        # Verifica validações nos formulários
        arquivos_validacao = [
            "profiles/solicitante_nova.py",
            "profiles/estoque_requisicoes.py",
            "profiles/suprimentos_mover.py"
        ]
        
        for arquivo in arquivos_validacao:
            if os.path.exists(arquivo):
                try:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    validacoes = [
                        "st.error",
                        "st.warning",
                        "st.success",
                        "if not",
                        "len(",
                        "strip()"
                    ]
                    
                    validacoes_encontradas = sum(1 for val in validacoes if val in conteudo)
                    
                    if validacoes_encontradas >= 3:
                        self.log_resultado(f"Validações {os.path.basename(arquivo)}", "SUCESSO")
                    else:
                        self.log_resultado(f"Validações {os.path.basename(arquivo)}", "FALHA", 
                                         "Poucas validações encontradas")
                        
                except Exception as e:
                    self.log_resultado(f"Validações {arquivo}", "FALHA", str(e))

    def executar_todos_os_testes(self):
        """Executa todos os testes de frontend"""
        print("🎨 INICIANDO TESTES DE FRONTEND - STREAMLIT")
        print("=" * 60)
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        
        # Testes que não precisam do servidor
        self.testar_estrutura_arquivos_interface()
        self.testar_componentes_streamlit()
        self.testar_perfis_usuario()
        self.testar_navegacao_interface()
        self.testar_formularios_interface()
        self.testar_responsividade_interface()
        self.testar_validacoes_frontend()
        
        # Testes que precisam do servidor
        servidor_iniciado = self.iniciar_servidor_streamlit()
        
        if servidor_iniciado:
            try:
                self.testar_carregamento_pagina_principal()
            finally:
                self.parar_servidor_streamlit()
        else:
            self.log_resultado("Testes com servidor", "FALHA", 
                             "Não foi possível iniciar o servidor Streamlit")
        
        # Relatório final
        self.gerar_relatorio_final()

    def gerar_relatorio_final(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DOS TESTES DE FRONTEND")
        print("=" * 60)
        
        print(f"Total de testes executados: {self.contador_testes}")
        print(f"✅ Sucessos: {self.contador_sucessos}")
        print(f"❌ Falhas: {self.contador_falhas}")
        
        if self.contador_testes > 0:
            taxa_sucesso = (self.contador_sucessos / self.contador_testes) * 100
            print(f"📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        if self.contador_falhas > 0:
            print(f"\n⚠️  TESTES QUE FALHARAM:")
            for resultado in self.resultados:
                if resultado["status"] == "FALHA":
                    print(f"   • {resultado['teste']}: {resultado['detalhes']}")
        
        # Salva relatório em arquivo
        self.salvar_relatorio_arquivo()
        
        print(f"\n📄 Relatório detalhado salvo em: relatorio_testes_frontend.json")
        print("=" * 60)

    def salvar_relatorio_arquivo(self):
        """Salva relatório detalhado em arquivo JSON"""
        relatorio = {
            "data_execucao": datetime.now().isoformat(),
            "tipo_teste": "Frontend Streamlit",
            "resumo": {
                "total_testes": self.contador_testes,
                "sucessos": self.contador_sucessos,
                "falhas": self.contador_falhas,
                "taxa_sucesso": (self.contador_sucessos / self.contador_testes * 100) if self.contador_testes > 0 else 0
            },
            "resultados_detalhados": self.resultados,
            "configuracao_testada": {
                "framework": "Streamlit",
                "url_base": self.base_url,
                "arquivos_testados": [
                    "app.py", "style.py", "session_manager.py",
                    "profiles/*.py"
                ]
            }
        }
        
        with open("relatorio_testes_frontend.json", "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)


def main():
    """Função principal"""
    testador = TestadorFrontendStreamlit()
    
    try:
        testador.executar_todos_os_testes()
    except KeyboardInterrupt:
        print("\n⚠️  Testes interrompidos pelo usuário")
        testador.parar_servidor_streamlit()
    except Exception as e:
        print(f"\n❌ Erro durante execução dos testes: {e}")
        testador.parar_servidor_streamlit()


if __name__ == "__main__":
    main()
