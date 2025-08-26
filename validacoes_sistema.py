#!/usr/bin/env python3
"""
Módulo de Validações para o Sistema de Gestão de Compras
Implementa todas as validações identificadas nos testes
"""

from typing import Dict, List, Tuple, Optional
import re

# Configurações do sistema
PRIORIDADES_VALIDAS = ["Urgente", "Alta", "Normal", "Baixa"]
DEPARTAMENTOS_VALIDOS = [
    "Manutenção", "TI", "RH", "Financeiro", 
    "Marketing", "Operações", "Outro"
]
UNIDADES_VALIDAS = ["UN", "PC", "CX", "KG", "L", "M", "M2"]

class ValidadorSistema:
    """Classe para validações do sistema"""
    
    @staticmethod
    def validar_valor_monetario(valor: float) -> Tuple[bool, str]:
        """
        Valida valores monetários
        
        Args:
            valor: Valor a ser validado
            
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        if valor is None:
            return False, "Valor não pode ser nulo"
        
        if not isinstance(valor, (int, float)):
            return False, "Valor deve ser numérico"
        
        if valor < 0:
            return False, "Valor não pode ser negativo"
        
        if valor == 0:
            return True, "Atenção: Valor zero detectado"
        
        if valor > 1000000:  # Limite máximo de 1 milhão
            return False, "Valor excede limite máximo permitido (R$ 1.000.000)"
        
        return True, ""
    
    @staticmethod
    def validar_prioridade(prioridade: str) -> Tuple[bool, str]:
        """
        Valida prioridade da solicitação
        
        Args:
            prioridade: Prioridade a ser validada
            
        Returns:
            Tuple[bool, str]: (é_válida, mensagem_erro)
        """
        if not prioridade:
            return False, "Prioridade é obrigatória"
        
        if not isinstance(prioridade, str):
            return False, "Prioridade deve ser texto"
        
        prioridade_limpa = prioridade.strip()
        
        if prioridade_limpa not in PRIORIDADES_VALIDAS:
            return False, f"Prioridade inválida. Valores aceitos: {', '.join(PRIORIDADES_VALIDAS)}"
        
        return True, ""
    
    @staticmethod
    def validar_departamento(departamento: str) -> Tuple[bool, str]:
        """
        Valida departamento
        
        Args:
            departamento: Departamento a ser validado
            
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        if not departamento:
            return False, "Departamento é obrigatório"
        
        if not isinstance(departamento, str):
            return False, "Departamento deve ser texto"
        
        departamento_limpo = departamento.strip()
        
        if departamento_limpo not in DEPARTAMENTOS_VALIDOS:
            return False, f"Departamento inválido. Valores aceitos: {', '.join(DEPARTAMENTOS_VALIDOS)}"
        
        return True, ""
    
    @staticmethod
    def validar_quantidade(quantidade: float) -> Tuple[bool, str]:
        """
        Valida quantidade de itens
        
        Args:
            quantidade: Quantidade a ser validada
            
        Returns:
            Tuple[bool, str]: (é_válida, mensagem_erro)
        """
        if quantidade is None:
            return False, "Quantidade não pode ser nula"
        
        if not isinstance(quantidade, (int, float)):
            return False, "Quantidade deve ser numérica"
        
        if quantidade <= 0:
            return False, "Quantidade deve ser maior que zero"
        
        if quantidade > 10000:  # Limite máximo
            return False, "Quantidade excede limite máximo (10.000 unidades)"
        
        return True, ""
    
    @staticmethod
    def validar_unidade(unidade: str) -> Tuple[bool, str]:
        """
        Valida unidade de medida
        
        Args:
            unidade: Unidade a ser validada
            
        Returns:
            Tuple[bool, str]: (é_válida, mensagem_erro)
        """
        if not unidade:
            return False, "Unidade é obrigatória"
        
        if not isinstance(unidade, str):
            return False, "Unidade deve ser texto"
        
        unidade_limpa = unidade.strip().upper()
        
        if unidade_limpa not in UNIDADES_VALIDAS:
            return False, f"Unidade inválida. Valores aceitos: {', '.join(UNIDADES_VALIDAS)}"
        
        return True, ""
    
    @staticmethod
    def validar_descricao(descricao: str) -> Tuple[bool, str]:
        """
        Valida descrição da solicitação
        
        Args:
            descricao: Descrição a ser validada
            
        Returns:
            Tuple[bool, str]: (é_válida, mensagem_erro)
        """
        if not descricao:
            return False, "Descrição é obrigatória"
        
        if not isinstance(descricao, str):
            return False, "Descrição deve ser texto"
        
        descricao_limpa = descricao.strip()
        
        if len(descricao_limpa) < 10:
            return False, "Descrição deve ter pelo menos 10 caracteres"
        
        if len(descricao_limpa) > 1000:
            return False, "Descrição não pode exceder 1000 caracteres"
        
        return True, ""
    
    @staticmethod
    def validar_solicitacao_completa(solicitacao: Dict) -> Tuple[bool, List[str]]:
        """
        Valida uma solicitação completa
        
        Args:
            solicitacao: Dicionário com dados da solicitação
            
        Returns:
            Tuple[bool, List[str]]: (é_válida, lista_de_erros)
        """
        erros = []
        
        # Validações obrigatórias
        campos_obrigatorios = [
            'solicitante', 'departamento', 'prioridade', 
            'descricao', 'valor_total', 'itens'
        ]
        
        for campo in campos_obrigatorios:
            if campo not in solicitacao or not solicitacao[campo]:
                erros.append(f"Campo obrigatório ausente: {campo}")
        
        # Validações específicas
        if 'prioridade' in solicitacao:
            valido, erro = ValidadorSistema.validar_prioridade(solicitacao['prioridade'])
            if not valido:
                erros.append(f"Prioridade: {erro}")
        
        if 'departamento' in solicitacao:
            valido, erro = ValidadorSistema.validar_departamento(solicitacao['departamento'])
            if not valido:
                erros.append(f"Departamento: {erro}")
        
        if 'descricao' in solicitacao:
            valido, erro = ValidadorSistema.validar_descricao(solicitacao['descricao'])
            if not valido:
                erros.append(f"Descrição: {erro}")
        
        if 'valor_total' in solicitacao:
            valido, erro = ValidadorSistema.validar_valor_monetario(solicitacao['valor_total'])
            if not valido:
                erros.append(f"Valor total: {erro}")
        
        # Validação de itens
        if 'itens' in solicitacao and isinstance(solicitacao['itens'], list):
            if len(solicitacao['itens']) == 0:
                erros.append("Pelo menos um item deve ser adicionado")
            
            for i, item in enumerate(solicitacao['itens']):
                if 'quantidade' in item:
                    valido, erro = ValidadorSistema.validar_quantidade(item['quantidade'])
                    if not valido:
                        erros.append(f"Item {i+1} - Quantidade: {erro}")
                
                if 'unidade' in item:
                    valido, erro = ValidadorSistema.validar_unidade(item['unidade'])
                    if not valido:
                        erros.append(f"Item {i+1} - Unidade: {erro}")
                
                if 'valor_unitario' in item:
                    valido, erro = ValidadorSistema.validar_valor_monetario(item['valor_unitario'])
                    if not valido:
                        erros.append(f"Item {i+1} - Valor unitário: {erro}")
        
        return len(erros) == 0, erros
    
    @staticmethod
    def validar_transicao_status(status_atual: str, novo_status: str) -> Tuple[bool, str]:
        """
        Valida transição entre status
        
        Args:
            status_atual: Status atual da solicitação
            novo_status: Novo status desejado
            
        Returns:
            Tuple[bool, str]: (é_válida, mensagem_erro)
        """
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
        
        if status_atual not in transicoes_validas:
            return False, f"Status atual inválido: {status_atual}"
        
        proximos_validos = transicoes_validas[status_atual]
        
        if novo_status not in proximos_validos:
            if len(proximos_validos) == 0:
                return False, f"Status '{status_atual}' é final, não permite transições"
            else:
                return False, f"Transição inválida. De '{status_atual}' só é possível ir para: {', '.join(proximos_validos)}"
        
        return True, ""
    
    @staticmethod
    def validar_permissao_usuario(perfil: str, acao: str) -> Tuple[bool, str]:
        """
        Valida permissões do usuário
        
        Args:
            perfil: Perfil do usuário
            acao: Ação que o usuário quer executar
            
        Returns:
            Tuple[bool, str]: (tem_permissão, mensagem_erro)
        """
        permissoes_por_perfil = {
            "Solicitante": [
                "criar_solicitacao", "visualizar_minhas_solicitacoes",
                "editar_solicitacao_rascunho"
            ],
            "Estoque": [
                "visualizar_solicitacoes", "criar_requisicao",
                "mover_solicitacao_para_requisicao"
            ],
            "Suprimentos": [
                "visualizar_requisicoes", "processar_requisicoes",
                "criar_pedido_compras", "mover_entre_etapas_suprimentos",
                "gerenciar_catalogo", "finalizar_pedidos"
            ],
            "Gerência&Diretoria": [
                "visualizar_solicitacoes", "aprovar_solicitacoes",
                "reprovar_solicitacoes", "visualizar_dashboard_executivo"
            ],
            "Admin": [
                "*"  # Todas as permissões
            ]
        }
        
        if perfil == "Admin":
            return True, ""
        
        if perfil not in permissoes_por_perfil:
            return False, f"Perfil inválido: {perfil}"
        
        permissoes = permissoes_por_perfil[perfil]
        
        if acao not in permissoes:
            return False, f"Usuário com perfil '{perfil}' não tem permissão para: {acao}"
        
        return True, ""


def aplicar_validacoes_no_sistema():
    """
    Função para aplicar as validações no sistema principal
    Esta função deve ser chamada nos módulos principais
    """
    print("🔧 Aplicando validações no sistema...")
    
    # Lista de arquivos que precisam das validações
    arquivos_para_atualizar = [
        "profiles/solicitante_nova.py",
        "profiles/suprimentos_requisicao.py",
        "profiles/admin_usuarios.py"
    ]
    
    print("📋 Arquivos que precisam ser atualizados:")
    for arquivo in arquivos_para_atualizar:
        print(f"   • {arquivo}")
    
    print("\n✅ Validações definidas. Integre este módulo nos arquivos principais.")
    print("💡 Exemplo de uso:")
    print("   from validacoes_sistema import ValidadorSistema")
    print("   valido, erros = ValidadorSistema.validar_solicitacao_completa(dados)")


if __name__ == "__main__":
    aplicar_validacoes_no_sistema()
