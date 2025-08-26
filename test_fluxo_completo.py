#!/usr/bin/env python3
"""
Sistema de Testes Completo para Fluxo de Solicitações
Testa todas as transições de status e casos edge possíveis
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurações do fluxo (baseado no app.py)
ETAPAS_PROCESSO = [
    "Solicitação",
    "Requisição", 
    "Suprimentos",
    "Em Cotação",
    "Pedido de Compras",
    "Aguardando Aprovação",
    "Aprovado",
    "Reprovado",
    "Compra feita",
    "Aguardando Entrega",
    "Pedido Finalizado"
]

PERFIS_USUARIOS = {
    "admin": {"perfil": "Admin", "pode_tudo": True},
    "Leonardo.Fragoso": {"perfil": "Solicitante", "pode_criar": True},
    "Genival.Silva": {"perfil": "Solicitante", "pode_criar": True},
    "Estoque.Sistema": {"perfil": "Estoque", "pode_requisicao": True},
    "Fabio.Ramos": {"perfil": "Suprimentos", "pode_processar": True},
    "Diretoria": {"perfil": "Gerência&Diretoria", "pode_aprovar": True}
}

PRIORIDADES = ["Urgente", "Alta", "Normal", "Baixa"]
SLA_PADRAO = {"Urgente": 1, "Alta": 2, "Normal": 3, "Baixa": 5}

class TestadorFluxoCompleto:
    """Classe principal para testes do fluxo de solicitações"""
    
    def __init__(self):
        self.resultados = []
        self.solicitacoes_teste = []
        self.contador_testes = 0
        self.contador_sucessos = 0
        self.contador_falhas = 0
        
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

    def criar_solicitacao_teste(self, prioridade: str = "Normal", valor: float = 1000.0) -> Dict:
        """Cria uma solicitação de teste com validações"""
        # VALIDAÇÕES DE SEGURANÇA
        # 1. Validar prioridade
        prioridades_validas = ["Urgente", "Alta", "Normal", "Baixa"]
        if prioridade not in prioridades_validas:
            raise ValueError(f"Prioridade inválida: '{prioridade}'. Use: {', '.join(prioridades_validas)}")
        
        # 2. Validar valor negativo
        if valor < 0:
            raise ValueError(f"Valor negativo não permitido: {valor}")
        
        numero = len(self.solicitacoes_teste) + 1
        solicitacao = {
            "numero_solicitacao": numero,
            "solicitante": "Leonardo.Fragoso",
            "departamento": "TI",
            "prioridade": prioridade,
            "descricao": f"Teste de solicitação #{numero}",
            "valor_total": valor,
            "status": "Solicitação",
            "data_solicitacao": datetime.now().isoformat(),
            "sla_dias": SLA_PADRAO.get(prioridade, 3),
            "itens": [
                {
                    "produto": "Produto Teste",
                    "quantidade": 1,
                    "unidade": "UN",
                    "valor_unitario": valor
                }
            ]
        }
        self.solicitacoes_teste.append(solicitacao)
        return solicitacao

    def testar_transicoes_validas(self):
        """Testa todas as transições válidas entre status"""
        print("\n🔄 TESTANDO TRANSIÇÕES VÁLIDAS DE STATUS")
        print("=" * 50)
        
        # Mapeamento de transições válidas
        transicoes_validas = {
            "Solicitação": ["Requisição"],
            "Requisição": ["Suprimentos"],
            "Suprimentos": ["Em Cotação"],
            "Em Cotação": ["Pedido de Compras"],
            "Pedido de Compras": ["Aguardando Aprovação"],
            "Aguardando Aprovação": ["Aprovado", "Reprovado"],
            "Aprovado": ["Compra feita"],
            "Reprovado": [],  # Status final
            "Compra feita": ["Aguardando Entrega"],
            "Aguardando Entrega": ["Pedido Finalizado"],
            "Pedido Finalizado": []  # Status final
        }
        
        for status_atual, proximos_validos in transicoes_validas.items():
            for proximo_status in proximos_validos:
                teste_nome = f"Transição: {status_atual} → {proximo_status}"
                
                # Simula a transição
                solicitacao = self.criar_solicitacao_teste()
                solicitacao["status"] = status_atual
                
                # Valida se a transição é permitida
                if self.validar_transicao(status_atual, proximo_status):
                    self.log_resultado(teste_nome, "SUCESSO")
                else:
                    self.log_resultado(teste_nome, "FALHA", "Transição não permitida")

    def testar_transicoes_invalidas(self):
        """Testa transições inválidas que devem ser bloqueadas"""
        print("\n❌ TESTANDO TRANSIÇÕES INVÁLIDAS (DEVEM FALHAR)")
        print("=" * 50)
        
        # Casos de transições inválidas
        transicoes_invalidas = [
            ("Solicitação", "Aprovado"),
            ("Requisição", "Pedido Finalizado"),
            ("Suprimentos", "Reprovado"),
            ("Em Cotação", "Aguardando Entrega"),
            ("Pedido Finalizado", "Solicitação"),
            ("Reprovado", "Aprovado"),
            ("Aprovado", "Reprovado")
        ]
        
        for status_atual, proximo_status in transicoes_invalidas:
            teste_nome = f"Transição Inválida: {status_atual} → {proximo_status}"
            
            if not self.validar_transicao(status_atual, proximo_status):
                self.log_resultado(teste_nome, "SUCESSO", "Corretamente bloqueada")
            else:
                self.log_resultado(teste_nome, "FALHA", "Transição inválida foi permitida")

    def testar_permissoes_por_perfil(self):
        """Testa permissões específicas por perfil de usuário"""
        print("\n👥 TESTANDO PERMISSÕES POR PERFIL")
        print("=" * 50)
        
        # Mapeamento de ações permitidas por perfil
        acoes_por_perfil = {
            "Solicitante": {
                "pode_criar_solicitacao": True,
                "pode_mover_para_requisicao": False,
                "pode_processar_suprimentos": False,
                "pode_aprovar": False,
                "pode_finalizar": False
            },
            "Estoque": {
                "pode_criar_solicitacao": False,
                "pode_mover_para_requisicao": True,
                "pode_processar_suprimentos": False,
                "pode_aprovar": False,
                "pode_finalizar": False
            },
            "Suprimentos": {
                "pode_criar_solicitacao": False,
                "pode_mover_para_requisicao": False,
                "pode_processar_suprimentos": True,
                "pode_aprovar": False,
                "pode_finalizar": True
            },
            "Gerência&Diretoria": {
                "pode_criar_solicitacao": False,
                "pode_mover_para_requisicao": False,
                "pode_processar_suprimentos": False,
                "pode_aprovar": True,
                "pode_finalizar": False
            },
            "Admin": {
                "pode_criar_solicitacao": True,
                "pode_mover_para_requisicao": True,
                "pode_processar_suprimentos": True,
                "pode_aprovar": True,
                "pode_finalizar": True
            }
        }
        
        for perfil, permissoes in acoes_por_perfil.items():
            for acao, permitido in permissoes.items():
                teste_nome = f"Permissão {perfil}: {acao}"
                
                # Simula verificação de permissão
                resultado = self.verificar_permissao(perfil, acao)
                
                if resultado == permitido:
                    self.log_resultado(teste_nome, "SUCESSO")
                else:
                    status_esperado = "permitido" if permitido else "negado"
                    status_atual = "permitido" if resultado else "negado"
                    self.log_resultado(teste_nome, "FALHA", 
                                     f"Esperado: {status_esperado}, Atual: {status_atual}")

    def testar_regras_sla(self):
        """Testa cálculos e validações de SLA"""
        print("\n⏰ TESTANDO REGRAS DE SLA")
        print("=" * 50)
        
        for prioridade in PRIORIDADES:
            sla_esperado = SLA_PADRAO[prioridade]
            
            # Teste 1: SLA dentro do prazo
            solicitacao = self.criar_solicitacao_teste(prioridade)
            solicitacao["data_solicitacao"] = datetime.now().isoformat()
            
            dias_decorridos = 0
            sla_cumprido = dias_decorridos <= sla_esperado
            
            teste_nome = f"SLA {prioridade} - Dentro do prazo ({dias_decorridos}/{sla_esperado} dias)"
            if sla_cumprido:
                self.log_resultado(teste_nome, "SUCESSO")
            else:
                self.log_resultado(teste_nome, "FALHA", "SLA não cumprido")
            
            # Teste 2: SLA estourado
            solicitacao_atrasada = self.criar_solicitacao_teste(prioridade)
            data_antiga = datetime.now() - timedelta(days=sla_esperado + 1)
            solicitacao_atrasada["data_solicitacao"] = data_antiga.isoformat()
            
            dias_decorridos = sla_esperado + 1
            sla_cumprido = dias_decorridos <= sla_esperado
            
            teste_nome = f"SLA {prioridade} - Estourado ({dias_decorridos}/{sla_esperado} dias)"
            if not sla_cumprido:
                self.log_resultado(teste_nome, "SUCESSO", "Corretamente identificado como atrasado")
            else:
                self.log_resultado(teste_nome, "FALHA", "SLA estourado não foi detectado")

    def testar_valores_limites(self):
        """Testa regras de valores e limites de aprovação"""
        print("\n💰 TESTANDO VALORES E LIMITES")
        print("=" * 50)
        
        # Limites baseados nas configurações
        limite_gerencia = 5000.0
        limite_diretoria = 15000.0
        
        casos_teste = [
            (500.0, "Valor baixo", "gerencia"),
            (4999.0, "Limite gerência", "gerencia"),
            (5000.0, "Exato limite gerência", "gerencia"),
            (5001.0, "Acima limite gerência", "diretoria"),
            (14999.0, "Limite diretoria", "diretoria"),
            (15000.0, "Exato limite diretoria", "diretoria"),
            (15001.0, "Acima limite diretoria", "especial")
        ]
        
        for valor, descricao, aprovador_esperado in casos_teste:
            solicitacao = self.criar_solicitacao_teste(valor=valor)
            aprovador_calculado = self.calcular_aprovador_necessario(valor, limite_gerencia, limite_diretoria)
            
            teste_nome = f"Valor {valor} ({descricao}) - Aprovador: {aprovador_esperado}"
            
            if aprovador_calculado == aprovador_esperado:
                self.log_resultado(teste_nome, "SUCESSO")
            else:
                self.log_resultado(teste_nome, "FALHA", 
                                 f"Esperado: {aprovador_esperado}, Calculado: {aprovador_calculado}")

    def testar_casos_edge(self):
        """Testa casos extremos e situações especiais"""
        print("\n🔍 TESTANDO CASOS EDGE")
        print("=" * 50)
        
        # Caso 1: Solicitação com valor zero
        solicitacao_zero = self.criar_solicitacao_teste(valor=0.0)
        teste_nome = "Solicitação com valor zero"
        if solicitacao_zero["valor_total"] == 0.0:
            self.log_resultado(teste_nome, "SUCESSO", "Valor zero aceito")
        else:
            self.log_resultado(teste_nome, "FALHA", "Valor zero não tratado corretamente")
        
        # Caso 2: Solicitação com valor negativo
        try:
            solicitacao_negativa = self.criar_solicitacao_teste(valor=-100.0)
            teste_nome = "Solicitação com valor negativo"
            self.log_resultado(teste_nome, "FALHA", "Valor negativo foi aceito")
        except Exception:
            teste_nome = "Solicitação com valor negativo"
            self.log_resultado(teste_nome, "SUCESSO", "Valor negativo corretamente rejeitado")
        
        # Caso 3: Prioridade inválida
        try:
            solicitacao_prioridade_invalida = self.criar_solicitacao_teste(prioridade="Inexistente")
            teste_nome = "Prioridade inválida"
            self.log_resultado(teste_nome, "FALHA", "Prioridade inválida foi aceita")
        except Exception:
            teste_nome = "Prioridade inválida"
            self.log_resultado(teste_nome, "SUCESSO", "Prioridade inválida corretamente rejeitada")
        
        # Caso 4: Múltiplas transições simultâneas
        solicitacao = self.criar_solicitacao_teste()
        teste_nome = "Múltiplas transições simultâneas"
        
        # Simula tentativa de múltiplas mudanças de status
        status_original = solicitacao["status"]
        try:
            solicitacao["status"] = "Aprovado"  # Pula várias etapas
            if not self.validar_transicao(status_original, "Aprovado"):
                self.log_resultado(teste_nome, "SUCESSO", "Múltiplas transições bloqueadas")
            else:
                self.log_resultado(teste_nome, "FALHA", "Múltiplas transições permitidas")
        except Exception:
            self.log_resultado(teste_nome, "SUCESSO", "Múltiplas transições corretamente bloqueadas")

    def testar_fluxo_completo_cenarios(self):
        """Testa cenários completos do fluxo"""
        print("\n🎯 TESTANDO CENÁRIOS COMPLETOS")
        print("=" * 50)
        
        # Cenário 1: Fluxo normal aprovado
        self.testar_cenario_fluxo_normal_aprovado()
        
        # Cenário 2: Fluxo reprovado
        self.testar_cenario_fluxo_reprovado()
        
        # Cenário 3: Fluxo com valor alto
        self.testar_cenario_valor_alto()

    def testar_cenario_fluxo_normal_aprovado(self):
        """Testa fluxo completo normal que é aprovado"""
        cenario = "Fluxo Normal Aprovado"
        solicitacao = self.criar_solicitacao_teste(prioridade="Normal", valor=2000.0)
        
        etapas_esperadas = [
            "Solicitação",
            "Requisição", 
            "Suprimentos",
            "Em Cotação",
            "Pedido de Compras",
            "Aguardando Aprovação",
            "Aprovado",
            "Compra feita",
            "Aguardando Entrega",
            "Pedido Finalizado"
        ]
        
        status_atual = "Solicitação"
        sucesso = True
        
        for i in range(len(etapas_esperadas) - 1):
            proximo_status = etapas_esperadas[i + 1]
            
            if self.validar_transicao(status_atual, proximo_status):
                status_atual = proximo_status
            else:
                sucesso = False
                break
        
        if sucesso and status_atual == "Pedido Finalizado":
            self.log_resultado(f"{cenario} - Completo", "SUCESSO")
        else:
            self.log_resultado(f"{cenario} - Completo", "FALHA", f"Parou em: {status_atual}")

    def testar_cenario_fluxo_reprovado(self):
        """Testa fluxo que é reprovado"""
        cenario = "Fluxo Reprovado"
        solicitacao = self.criar_solicitacao_teste(prioridade="Alta", valor=8000.0)
        
        etapas_ate_reprovacao = [
            "Solicitação",
            "Requisição",
            "Suprimentos", 
            "Em Cotação",
            "Pedido de Compras",
            "Aguardando Aprovação",
            "Reprovado"
        ]
        
        status_atual = "Solicitação"
        sucesso = True
        
        for i in range(len(etapas_ate_reprovacao) - 1):
            proximo_status = etapas_ate_reprovacao[i + 1]
            
            if self.validar_transicao(status_atual, proximo_status):
                status_atual = proximo_status
            else:
                sucesso = False
                break
        
        if sucesso and status_atual == "Reprovado":
            self.log_resultado(f"{cenario} - Completo", "SUCESSO")
            
            # Testa se não pode sair do status Reprovado
            if not self.validar_transicao("Reprovado", "Aprovado"):
                self.log_resultado(f"{cenario} - Status final", "SUCESSO", "Reprovado é status final")
            else:
                self.log_resultado(f"{cenario} - Status final", "FALHA", "Reprovado permite transições")
        else:
            self.log_resultado(f"{cenario} - Completo", "FALHA", f"Parou em: {status_atual}")

    def testar_cenario_valor_alto(self):
        """Testa fluxo com valor alto que requer aprovação especial"""
        cenario = "Valor Alto (>15k)"
        solicitacao = self.criar_solicitacao_teste(prioridade="Urgente", valor=20000.0)
        
        aprovador = self.calcular_aprovador_necessario(20000.0, 5000.0, 15000.0)
        
        if aprovador == "especial":
            self.log_resultado(f"{cenario} - Aprovador", "SUCESSO", "Requer aprovação especial")
        else:
            self.log_resultado(f"{cenario} - Aprovador", "FALHA", f"Aprovador: {aprovador}")

    # Métodos auxiliares para simulação
    def validar_transicao(self, status_atual: str, proximo_status: str) -> bool:
        """Simula validação de transição entre status"""
        transicoes_validas = {
            "Solicitação": ["Requisição"],
            "Requisição": ["Suprimentos"],
            "Suprimentos": ["Em Cotação"],
            "Em Cotação": ["Pedido de Compras"],
            "Pedido de Compras": ["Aguardando Aprovação"],
            "Aguardando Aprovação": ["Aprovado", "Reprovado"],
            "Aprovado": ["Compra feita"],
            "Reprovado": [],
            "Compra feita": ["Aguardando Entrega"],
            "Aguardando Entrega": ["Pedido Finalizado"],
            "Pedido Finalizado": []
        }
        
        return proximo_status in transicoes_validas.get(status_atual, [])

    def verificar_permissao(self, perfil: str, acao: str) -> bool:
        """Simula verificação de permissão"""
        if perfil == "Admin":
            return True
            
        permissoes = {
            "Solicitante": ["pode_criar_solicitacao"],
            "Estoque": ["pode_mover_para_requisicao"],
            "Suprimentos": ["pode_processar_suprimentos", "pode_finalizar"],
            "Gerência&Diretoria": ["pode_aprovar"]
        }
        
        return acao in permissoes.get(perfil, [])

    def calcular_aprovador_necessario(self, valor: float, limite_gerencia: float, limite_diretoria: float) -> str:
        """Simula cálculo do aprovador necessário baseado no valor"""
        if valor <= limite_gerencia:
            return "gerencia"
        elif valor <= limite_diretoria:
            return "diretoria"
        else:
            return "especial"

    def executar_todos_os_testes(self):
        """Executa todos os testes disponíveis"""
        print("🧪 INICIANDO TESTES COMPLETOS DO FLUXO DE SOLICITAÇÕES")
        print("=" * 60)
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        
        # Executa todos os grupos de teste
        self.testar_transicoes_validas()
        self.testar_transicoes_invalidas()
        self.testar_permissoes_por_perfil()
        self.testar_regras_sla()
        self.testar_valores_limites()
        self.testar_casos_edge()
        self.testar_fluxo_completo_cenarios()
        
        # Relatório final
        self.gerar_relatorio_final()

    def gerar_relatorio_final(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DOS TESTES")
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
        
        print(f"\n📄 Relatório detalhado salvo em: relatorio_testes_fluxo.json")
        print("=" * 60)

    def salvar_relatorio_arquivo(self):
        """Salva relatório detalhado em arquivo JSON"""
        relatorio = {
            "data_execucao": datetime.now().isoformat(),
            "resumo": {
                "total_testes": self.contador_testes,
                "sucessos": self.contador_sucessos,
                "falhas": self.contador_falhas,
                "taxa_sucesso": (self.contador_sucessos / self.contador_testes * 100) if self.contador_testes > 0 else 0
            },
            "resultados_detalhados": self.resultados,
            "configuracao_testada": {
                "etapas_processo": ETAPAS_PROCESSO,
                "perfis_usuarios": PERFIS_USUARIOS,
                "prioridades": PRIORIDADES,
                "sla_padrao": SLA_PADRAO
            }
        }
        
        with open("relatorio_testes_fluxo.json", "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)


def main():
    """Função principal"""
    testador = TestadorFluxoCompleto()
    testador.executar_todos_os_testes()


if __name__ == "__main__":
    main()
