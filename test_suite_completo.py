#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite Completa de Testes - Sistema de Compras
Executa todos os tipos de teste: Backend, Frontend Streamlit e Selenium
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, List

# Importa os módulos de teste
try:
    from test_fluxo_completo import TestadorFluxoCompleto
    BACKEND_DISPONIVEL = True
except ImportError:
    BACKEND_DISPONIVEL = False

try:
    from test_frontend_streamlit import TestadorFrontendStreamlit
    FRONTEND_STREAMLIT_DISPONIVEL = True
except ImportError:
    FRONTEND_STREAMLIT_DISPONIVEL = False

try:
    from test_frontend_selenium import TestadorFrontendSelenium
    SELENIUM_DISPONIVEL = True
except ImportError:
    SELENIUM_DISPONIVEL = False

class SuiteTestesCompleta:
    """Suite completa de testes para o sistema"""
    
    def __init__(self):
        self.resultados_suite = {
            "backend": None,
            "frontend_streamlit": None,
            "frontend_selenium": None
        }
        self.inicio_execucao = datetime.now()
        
    def executar_testes_backend(self):
        """Executa testes de backend/lógica de negócio"""
        print("🔧 EXECUTANDO TESTES DE BACKEND")
        print("=" * 60)
        
        if not BACKEND_DISPONIVEL:
            print("❌ Módulo de testes de backend não disponível")
            return False
        
        try:
            testador = TestadorFluxoCompleto()
            testador.executar_todos_os_testes()
            
            self.resultados_suite["backend"] = {
                "executado": True,
                "total_testes": testador.contador_testes,
                "sucessos": testador.contador_sucessos,
                "falhas": testador.contador_falhas,
                "taxa_sucesso": (testador.contador_sucessos / testador.contador_testes * 100) if testador.contador_testes > 0 else 0,
                "resultados": testador.resultados
            }
            
            print(f"✅ Testes de backend concluídos: {testador.contador_sucessos}/{testador.contador_testes}")
            return True
            
        except Exception as e:
            print(f"❌ Erro nos testes de backend: {e}")
            self.resultados_suite["backend"] = {
                "executado": False,
                "erro": str(e)
            }
            return False
    
    def executar_testes_frontend_streamlit(self):
        """Executa testes de frontend Streamlit"""
        print("\n🎨 EXECUTANDO TESTES DE FRONTEND STREAMLIT")
        print("=" * 60)
        
        if not FRONTEND_STREAMLIT_DISPONIVEL:
            print("❌ Módulo de testes de frontend Streamlit não disponível")
            return False
        
        try:
            testador = TestadorFrontendStreamlit()
            testador.executar_todos_os_testes()
            
            self.resultados_suite["frontend_streamlit"] = {
                "executado": True,
                "total_testes": testador.contador_testes,
                "sucessos": testador.contador_sucessos,
                "falhas": testador.contador_falhas,
                "taxa_sucesso": (testador.contador_sucessos / testador.contador_testes * 100) if testador.contador_testes > 0 else 0,
                "resultados": testador.resultados
            }
            
            print(f"✅ Testes de frontend Streamlit concluídos: {testador.contador_sucessos}/{testador.contador_testes}")
            return True
            
        except Exception as e:
            print(f"❌ Erro nos testes de frontend Streamlit: {e}")
            self.resultados_suite["frontend_streamlit"] = {
                "executado": False,
                "erro": str(e)
            }
            return False
    
    def executar_testes_selenium(self):
        """Executa testes com Selenium"""
        print("\n🎭 EXECUTANDO TESTES SELENIUM")
        print("=" * 60)
        
        if not SELENIUM_DISPONIVEL:
            print("❌ Módulo de testes Selenium não disponível")
            print("💡 Para instalar: pip install selenium")
            return False
        
        try:
            testador = TestadorFrontendSelenium()
            testador.executar_todos_os_testes()
            
            self.resultados_suite["frontend_selenium"] = {
                "executado": True,
                "total_testes": testador.contador_testes,
                "sucessos": testador.contador_sucessos,
                "falhas": testador.contador_falhas,
                "taxa_sucesso": (testador.contador_sucessos / testador.contador_testes * 100) if testador.contador_testes > 0 else 0,
                "resultados": testador.resultados
            }
            
            print(f"✅ Testes Selenium concluídos: {testador.contador_sucessos}/{testador.contador_testes}")
            return True
            
        except Exception as e:
            print(f"❌ Erro nos testes Selenium: {e}")
            self.resultados_suite["frontend_selenium"] = {
                "executado": False,
                "erro": str(e)
            }
            return False
    
    def executar_suite_completa(self):
        """Executa toda a suite de testes"""
        print("🚀 INICIANDO SUITE COMPLETA DE TESTES")
        print("=" * 80)
        print(f"Data/Hora: {self.inicio_execucao.strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        
        # Executa cada tipo de teste
        backend_ok = self.executar_testes_backend()
        frontend_streamlit_ok = self.executar_testes_frontend_streamlit()
        selenium_ok = self.executar_testes_selenium()
        
        # Gera relatório consolidado
        self.gerar_relatorio_consolidado()
        
        return backend_ok and frontend_streamlit_ok and selenium_ok
    
    def gerar_relatorio_consolidado(self):
        """Gera relatório consolidado de todos os testes"""
        fim_execucao = datetime.now()
        duracao_total = fim_execucao - self.inicio_execucao
        
        print("\n" + "=" * 80)
        print("📊 RELATÓRIO CONSOLIDADO - SUITE COMPLETA DE TESTES")
        print("=" * 80)
        
        # Estatísticas gerais
        total_testes_geral = 0
        total_sucessos_geral = 0
        total_falhas_geral = 0
        suites_executadas = 0
        
        for tipo, resultado in self.resultados_suite.items():
            if resultado and resultado.get("executado"):
                suites_executadas += 1
                total_testes_geral += resultado.get("total_testes", 0)
                total_sucessos_geral += resultado.get("sucessos", 0)
                total_falhas_geral += resultado.get("falhas", 0)
        
        print(f"🕒 Duração total: {duracao_total.total_seconds():.1f} segundos")
        print(f"📦 Suites executadas: {suites_executadas}/3")
        print(f"🧪 Total de testes: {total_testes_geral}")
        print(f"✅ Total de sucessos: {total_sucessos_geral}")
        print(f"❌ Total de falhas: {total_falhas_geral}")
        
        if total_testes_geral > 0:
            taxa_geral = (total_sucessos_geral / total_testes_geral) * 100
            print(f"📈 Taxa de sucesso geral: {taxa_geral:.1f}%")
        
        # Detalhes por suite
        print(f"\n📋 DETALHES POR SUITE:")
        print("-" * 50)
        
        for tipo, resultado in self.resultados_suite.items():
            nome_suite = {
                "backend": "Backend (Lógica de Negócio)",
                "frontend_streamlit": "Frontend (Streamlit)",
                "frontend_selenium": "Frontend (Selenium)"
            }.get(tipo, tipo)
            
            if resultado and resultado.get("executado"):
                taxa = resultado.get("taxa_sucesso", 0)
                print(f"✅ {nome_suite}: {resultado.get('sucessos', 0)}/{resultado.get('total_testes', 0)} ({taxa:.1f}%)")
            else:
                erro = resultado.get("erro", "Não executado") if resultado else "Módulo não disponível"
                print(f"❌ {nome_suite}: {erro}")
        
        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        print("-" * 50)
        
        if total_falhas_geral == 0:
            print("🎉 Parabéns! Todos os testes passaram com sucesso!")
            print("✨ Sistema está pronto para produção")
        elif total_falhas_geral <= 5:
            print("⚠️  Poucas falhas detectadas - revisar e corrigir")
            print("🔧 Sistema está quase pronto para produção")
        else:
            print("🚨 Muitas falhas detectadas - revisão necessária")
            print("🛠️  Recomenda-se correções antes da produção")
        
        # Próximos passos
        if not self.resultados_suite["frontend_selenium"] or not self.resultados_suite["frontend_selenium"].get("executado"):
            print("📦 Para testes completos de UI, instale: pip install selenium")
            print("🌐 E baixe o ChromeDriver: https://chromedriver.chromium.org/")
        
        # Salva relatório consolidado
        self.salvar_relatorio_consolidado(duracao_total)
        
        print(f"\n📄 Relatório consolidado salvo em: relatorio_suite_completa.json")
        print("=" * 80)
    
    def salvar_relatorio_consolidado(self, duracao_total):
        """Salva relatório consolidado em arquivo"""
        relatorio = {
            "execucao": {
                "data_inicio": self.inicio_execucao.isoformat(),
                "data_fim": datetime.now().isoformat(),
                "duracao_segundos": duracao_total.total_seconds()
            },
            "resumo_geral": {
                "suites_disponiveis": 3,
                "suites_executadas": sum(1 for r in self.resultados_suite.values() if r and r.get("executado")),
                "total_testes": sum(r.get("total_testes", 0) for r in self.resultados_suite.values() if r and r.get("executado")),
                "total_sucessos": sum(r.get("sucessos", 0) for r in self.resultados_suite.values() if r and r.get("executado")),
                "total_falhas": sum(r.get("falhas", 0) for r in self.resultados_suite.values() if r and r.get("executado"))
            },
            "resultados_por_suite": self.resultados_suite,
            "configuracao": {
                "sistema_operacional": os.name,
                "python_version": sys.version,
                "diretorio_trabalho": os.getcwd()
            }
        }
        
        # Calcula taxa geral
        total_testes = relatorio["resumo_geral"]["total_testes"]
        total_sucessos = relatorio["resumo_geral"]["total_sucessos"]
        
        if total_testes > 0:
            relatorio["resumo_geral"]["taxa_sucesso_geral"] = (total_sucessos / total_testes) * 100
        else:
            relatorio["resumo_geral"]["taxa_sucesso_geral"] = 0
        
        with open("relatorio_suite_completa.json", "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)


def main():
    """Função principal"""
    suite = SuiteTestesCompleta()
    
    try:
        sucesso = suite.executar_suite_completa()
        
        if sucesso:
            print("\n🎉 Suite de testes concluída com sucesso!")
            return 0
        else:
            print("\n⚠️  Suite de testes concluída com algumas falhas")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Suite de testes interrompida pelo usuário")
        return 2
    except Exception as e:
        print(f"\n❌ Erro durante execução da suite: {e}")
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
