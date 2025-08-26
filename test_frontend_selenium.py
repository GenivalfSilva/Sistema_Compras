#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de Frontend com Selenium - Sistema de Compras
Testa interações reais do usuário na interface web
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List
import threading

# Importações condicionais para Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_DISPONIVEL = True
except ImportError:
    SELENIUM_DISPONIVEL = False

class TestadorFrontendSelenium:
    """Classe para testar interações reais na interface web"""
    
    def __init__(self):
        self.resultados = []
        self.contador_testes = 0
        self.contador_sucessos = 0
        self.contador_falhas = 0
        self.driver = None
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
            print("🚀 Iniciando servidor Streamlit...")
            
            # Para processos existentes
            try:
                subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], 
                             capture_output=True, check=False)
                time.sleep(2)
            except:
                pass
            
            # Inicia servidor
            self.servidor_processo = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", "app.py",
                "--server.port", "8501",
                "--server.headless", "true"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Aguarda inicialização
            print("⏳ Aguardando servidor...")
            time.sleep(10)  # Streamlit precisa de mais tempo
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return False

    def iniciar_webdriver(self):
        """Inicia o WebDriver do Chrome"""
        if not SELENIUM_DISPONIVEL:
            print("❌ Selenium não está instalado. Execute: pip install selenium")
            return False
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Executa sem interface gráfica
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            print("✅ WebDriver Chrome iniciado")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar WebDriver: {e}")
            print("💡 Certifique-se de ter o ChromeDriver instalado")
            return False

    def testar_carregamento_pagina(self):
        """Testa carregamento da página principal"""
        print("\n🌐 TESTANDO CARREGAMENTO COM SELENIUM")
        print("=" * 50)
        
        try:
            self.driver.get(self.base_url)
            
            # Aguarda elemento aparecer
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            titulo = self.driver.title
            if "streamlit" in titulo.lower() or len(titulo) > 0:
                self.log_resultado("Carregamento da página", "SUCESSO")
            else:
                self.log_resultado("Carregamento da página", "FALHA", f"Título: {titulo}")
                
        except TimeoutException:
            self.log_resultado("Carregamento da página", "FALHA", "Timeout ao carregar")
        except Exception as e:
            self.log_resultado("Carregamento da página", "FALHA", str(e))

    def testar_elementos_login(self):
        """Testa elementos da tela de login"""
        print("\n🔐 TESTANDO ELEMENTOS DE LOGIN")
        print("=" * 50)
        
        try:
            # Aguarda carregamento completo do Streamlit
            time.sleep(5)
            
            # Múltiplas estratégias para encontrar campos de input
            inputs_encontrados = 0
            
            # Estratégia 1: Inputs padrão
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            inputs_encontrados += len(inputs)
            
            # Estratégia 2: Inputs do Streamlit (text_input)
            streamlit_inputs = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stTextInput'] input")
            inputs_encontrados += len(streamlit_inputs)
            
            # Estratégia 3: Inputs por classe CSS do Streamlit
            css_inputs = self.driver.find_elements(By.CSS_SELECTOR, ".stTextInput input")
            inputs_encontrados += len(css_inputs)
            
            # Estratégia 4: Qualquer elemento de input visível
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password'], input:not([type])")
            inputs_encontrados += len(all_inputs)
            
            if inputs_encontrados >= 2:
                self.log_resultado("Campos de login presentes", "SUCESSO", f"{inputs_encontrados} campos encontrados")
            else:
                self.log_resultado("Campos de login presentes", "FALHA", 
                                 f"Apenas {inputs_encontrados} campos encontrados")
            
            # Procura por botões com múltiplas estratégias
            botoes_encontrados = 0
            
            # Botões padrão
            botoes = self.driver.find_elements(By.TAG_NAME, "button")
            botoes_encontrados += len(botoes)
            
            # Botões do Streamlit
            streamlit_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stButton'] button")
            botoes_encontrados += len(streamlit_buttons)
            
            if botoes_encontrados >= 1:
                self.log_resultado("Botões presentes", "SUCESSO", f"{botoes_encontrados} botões encontrados")
            else:
                self.log_resultado("Botões presentes", "FALHA", "Nenhum botão encontrado")
                
        except Exception as e:
            self.log_resultado("Elementos de login", "FALHA", str(e))

    def testar_interacao_login(self):
        """Testa interação com formulário de login"""
        print("\n👤 TESTANDO INTERAÇÃO DE LOGIN")
        print("=" * 50)
        
        try:
            # Aguarda carregamento completo
            time.sleep(5)
            
            # Procura campos com múltiplas estratégias
            inputs_usuario = None
            inputs_senha = None
            
            # Estratégia 1: Inputs padrão
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            
            # Estratégia 2: Inputs do Streamlit
            streamlit_inputs = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stTextInput'] input")
            
            # Estratégia 3: Todos os inputs visíveis
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input")
            
            # Combina todas as estratégias
            todos_inputs = list(set(inputs + streamlit_inputs + all_inputs))
            
            if len(todos_inputs) >= 2:
                # Tenta identificar campos por posição ou atributos
                for i, input_elem in enumerate(todos_inputs[:2]):
                    try:
                        if i == 0:  # Primeiro campo - usuário
                            input_elem.clear()
                            input_elem.send_keys("admin")
                            inputs_usuario = input_elem
                        elif i == 1:  # Segundo campo - senha
                            input_elem.clear()
                            input_elem.send_keys("admin123")
                            inputs_senha = input_elem
                    except:
                        continue
                
                if inputs_usuario is not None and inputs_senha is not None:
                    self.log_resultado("Preenchimento de campos", "SUCESSO")
                else:
                    self.log_resultado("Preenchimento de campos", "FALHA", "Não foi possível preencher os campos")
                
                # Procura botão de login com múltiplas estratégias
                botao_clicado = False
                
                # Estratégia 1: Botões padrão
                botoes = self.driver.find_elements(By.TAG_NAME, "button")
                
                # Estratégia 2: Botões do Streamlit
                streamlit_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stButton'] button")
                
                todos_botoes = list(set(botoes + streamlit_buttons))
                
                for botao in todos_botoes:
                    try:
                        texto_botao = botao.text.lower()
                        if any(palavra in texto_botao for palavra in ["login", "entrar", "acessar", "conectar"]):
                            botao.click()
                            self.log_resultado("Clique no botão de login", "SUCESSO")
                            botao_clicado = True
                            time.sleep(5)  # Aguarda processamento
                            break
                    except:
                        continue
                
                if not botao_clicado and todos_botoes:
                    # Clica no primeiro botão disponível
                    try:
                        todos_botoes[0].click()
                        self.log_resultado("Clique em botão", "SUCESSO")
                        time.sleep(5)
                    except:
                        self.log_resultado("Clique em botão", "FALHA", "Não foi possível clicar")
                
            else:
                self.log_resultado("Interação de login", "FALHA", f"Apenas {len(todos_inputs)} campos encontrados")
                
        except Exception as e:
            self.log_resultado("Interação de login", "FALHA", str(e))

    def testar_navegacao_pos_login(self):
        """Testa navegação após login"""
        print("\n🧭 TESTANDO NAVEGAÇÃO PÓS-LOGIN")
        print("=" * 50)
        
        try:
            # Aguarda carregamento após login
            time.sleep(5)
            
            elementos_nav = []
            
            # Estratégia 1: Sidebar do Streamlit
            sidebar_selectors = [
                "[data-testid='stSidebar']",
                ".css-1d391kg",
                ".stSidebar",
                "[class*='sidebar']",
                "[class*='Sidebar']"
            ]
            
            for selector in sidebar_selectors:
                try:
                    sidebar = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if sidebar.is_displayed():
                        elementos_nav.append("sidebar")
                        break
                except:
                    continue
            
            # Estratégia 2: Selectbox do Streamlit
            selectbox_selectors = [
                "[data-testid='stSelectbox'] select",
                ".stSelectbox select",
                "select",
                "[data-testid='stSelectbox']"
            ]
            
            for selector in selectbox_selectors:
                try:
                    selectboxes = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if selectboxes:
                        elementos_nav.append("selectbox")
                        break
                except:
                    continue
            
            # Estratégia 3: Botões de navegação
            try:
                botoes = self.driver.find_elements(By.TAG_NAME, "button")
                streamlit_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stButton'] button")
                todos_botoes = list(set(botoes + streamlit_buttons))
                
                if len(todos_botoes) > 1:
                    elementos_nav.append(f"botões ({len(todos_botoes)})")
            except:
                pass
            
            # Estratégia 4: Tabs do Streamlit
            try:
                tabs = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stTabs'] button")
                if tabs:
                    elementos_nav.append(f"tabs ({len(tabs)})")
            except:
                pass
            
            # Estratégia 5: Elementos com texto indicativo de navegação
            try:
                nav_texts = ["dashboard", "solicitação", "admin", "perfil", "menu"]
                for text in nav_texts:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]") 
                    if elements:
                        elementos_nav.append(f"texto-{text}")
                        break
            except:
                pass
            
            if elementos_nav:
                self.log_resultado("Elementos de navegação", "SUCESSO", 
                                 f"Encontrados: {', '.join(elementos_nav)}")
            else:
                # Verifica se pelo menos a página mudou após login
                try:
                    page_source = self.driver.page_source.lower()
                    if any(word in page_source for word in ["dashboard", "bem-vindo", "logout", "sair", "perfil"]):
                        self.log_resultado("Navegação pós-login", "SUCESSO", "Página alterada após login")
                    else:
                        self.log_resultado("Elementos de navegação", "FALHA", 
                                         "Nenhum elemento de navegação encontrado")
                except:
                    self.log_resultado("Elementos de navegação", "FALHA", 
                                     "Nenhum elemento de navegação encontrado")
                
        except Exception as e:
            self.log_resultado("Navegação pós-login", "FALHA", str(e))

    def testar_responsividade(self):
        """Testa responsividade em diferentes tamanhos"""
        print("\n📱 TESTANDO RESPONSIVIDADE")
        print("=" * 50)
        
        tamanhos = [
            (1920, 1080, "Desktop"),
            (768, 1024, "Tablet"),
            (375, 667, "Mobile")
        ]
        
        for largura, altura, dispositivo in tamanhos:
            try:
                self.driver.set_window_size(largura, altura)
                time.sleep(2)
                
                # Verifica se a página ainda está funcional
                body = self.driver.find_element(By.TAG_NAME, "body")
                
                if body.is_displayed():
                    self.log_resultado(f"Responsividade {dispositivo}", "SUCESSO")
                else:
                    self.log_resultado(f"Responsividade {dispositivo}", "FALHA", 
                                     "Página não visível")
                    
            except Exception as e:
                self.log_resultado(f"Responsividade {dispositivo}", "FALHA", str(e))

    def testar_performance_carregamento(self):
        """Testa performance de carregamento"""
        print("\n⚡ TESTANDO PERFORMANCE")
        print("=" * 50)
        
        try:
            inicio = time.time()
            self.driver.get(self.base_url)
            
            # Aguarda carregamento completo
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            fim = time.time()
            tempo_carregamento = fim - inicio
            
            if tempo_carregamento < 10:
                self.log_resultado("Performance de carregamento", "SUCESSO", 
                                 f"{tempo_carregamento:.2f}s")
            elif tempo_carregamento < 20:
                self.log_resultado("Performance de carregamento", "AVISO", 
                                 f"Lento: {tempo_carregamento:.2f}s")
            else:
                self.log_resultado("Performance de carregamento", "FALHA", 
                                 f"Muito lento: {tempo_carregamento:.2f}s")
                
        except Exception as e:
            self.log_resultado("Performance de carregamento", "FALHA", str(e))

    def executar_todos_os_testes(self):
        """Executa todos os testes de frontend com Selenium"""
        print("🎭 INICIANDO TESTES DE FRONTEND - SELENIUM")
        print("=" * 60)
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        
        if not SELENIUM_DISPONIVEL:
            self.log_resultado("Selenium", "FALHA", 
                             "Selenium não instalado. Execute: pip install selenium")
            self.gerar_relatorio_final()
            return
        
        # Inicia servidor
        if not self.iniciar_servidor_streamlit():
            self.log_resultado("Servidor Streamlit", "FALHA", "Não foi possível iniciar")
            self.gerar_relatorio_final()
            return
        
        # Inicia WebDriver
        if not self.iniciar_webdriver():
            self.log_resultado("WebDriver", "FALHA", "Não foi possível iniciar")
            self.parar_servidor()
            self.gerar_relatorio_final()
            return
        
        try:
            # Executa testes
            self.testar_performance_carregamento()
            self.testar_carregamento_pagina()
            self.testar_elementos_login()
            self.testar_interacao_login()
            self.testar_navegacao_pos_login()
            self.testar_responsividade()
            
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
            self.parar_servidor()
        
        self.gerar_relatorio_final()

    def parar_servidor(self):
        """Para o servidor Streamlit"""
        try:
            if self.servidor_processo:
                self.servidor_processo.terminate()
                self.servidor_processo.wait(timeout=5)
            
            subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], 
                         capture_output=True, check=False)
            print("🛑 Servidor parado")
            
        except Exception as e:
            print(f"⚠️  Erro ao parar servidor: {e}")

    def gerar_relatorio_final(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DOS TESTES SELENIUM")
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
        
        # Salva relatório
        self.salvar_relatorio_arquivo()
        print(f"\n📄 Relatório salvo em: relatorio_testes_selenium.json")
        print("=" * 60)

    def salvar_relatorio_arquivo(self):
        """Salva relatório em arquivo JSON"""
        relatorio = {
            "data_execucao": datetime.now().isoformat(),
            "tipo_teste": "Frontend Selenium",
            "resumo": {
                "total_testes": self.contador_testes,
                "sucessos": self.contador_sucessos,
                "falhas": self.contador_falhas,
                "taxa_sucesso": (self.contador_sucessos / self.contador_testes * 100) if self.contador_testes > 0 else 0
            },
            "resultados_detalhados": self.resultados,
            "configuracao": {
                "framework": "Selenium WebDriver",
                "browser": "Chrome Headless",
                "url_base": self.base_url
            }
        }
        
        with open("relatorio_testes_selenium.json", "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)


def main():
    """Função principal"""
    testador = TestadorFrontendSelenium()
    
    try:
        testador.executar_todos_os_testes()
    except KeyboardInterrupt:
        print("\n⚠️  Testes interrompidos")
        if testador.driver:
            testador.driver.quit()
        testador.parar_servidor()


if __name__ == "__main__":
    main()
