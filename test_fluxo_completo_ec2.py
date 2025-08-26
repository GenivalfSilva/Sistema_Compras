#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste Completo do Fluxo de Compras - EC2
Simula uma solicitação completa do início ao fim testando todos os perfis
"""

import sys
import os
import hashlib
import datetime
from decimal import Decimal
import time

# Adicionar o diretório atual ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database_local import get_local_database
    print("✅ Módulo database_local importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar database_local: {e}")
    sys.exit(1)

class TestFluxoCompleto:
    def __init__(self):
        self.db = get_local_database()
        self.solicitacao_id = None
        self.test_results = []
        self.start_time = datetime.datetime.now()
        
        # Usuários de teste (baseado nas memórias)
        self.usuarios = {
            'solicitante': {'usuario': 'Leonardo.Fragoso', 'senha': 'Teste123'},
            'suprimentos': {'usuario': 'Fabio.Ramos', 'senha': 'Teste123'},
            'diretoria': {'usuario': 'Diretoria', 'senha': 'Teste123'},
            'estoque': {'usuario': 'Estoque.Sistema', 'senha': 'Teste123'},
            'admin': {'usuario': 'admin', 'senha': 'admin123'}
        }
    
    def log_result(self, step, status, message, details=None):
        """Registra resultado de um teste"""
        result = {
            'step': step,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.datetime.now()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "⚠️"
        print(f"{status_icon} {step}: {message}")
        if details:
            print(f"   Detalhes: {details}")
    
    def hash_password(self, password):
        """Gera hash da senha usando o método SALT do sistema"""
        salt = "ziran_local_salt_v1"  # Usando o mesmo SALT do database_local.py
        return hashlib.sha256((salt + password).encode()).hexdigest()
    
    def authenticate_user(self, usuario, senha):
        """Autentica usuário no sistema"""
        try:
            # Usar método de autenticação da classe LocalDatabaseManager
            user_data = self.db.authenticate_user(usuario, senha)
            
            if user_data:
                user_info = {
                    'id': user_data.get('id'),
                    'usuario': user_data.get('username'),
                    'perfil': user_data.get('perfil'),
                    'departamento': user_data.get('departamento')
                }
                return user_info, "Autenticado com sucesso"
            else:
                return None, "Usuário ou senha incorretos"
            
        except Exception as e:
            return None, f"Erro na autenticação: {str(e)}"
    
    def test_database_connection(self):
        """Testa conexão com o banco de dados"""
        try:
            # Teste mais simples - apenas verificar se a conexão existe e está ativa
            if self.db.db_available and self.db.conn:
                # Testar com uma query simples
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                
                if result:
                    self.log_result("DB_CONNECTION", "SUCCESS", 
                                  f"Conexão com PostgreSQL estabelecida", 
                                  f"Teste de conectividade passou - db_available: {self.db.db_available}")
                    return True
                else:
                    self.log_result("DB_CONNECTION", "ERROR", 
                                  "Query de teste falhou", "SELECT 1 não retornou resultado")
                    return False
            else:
                self.log_result("DB_CONNECTION", "ERROR", 
                              "Banco de dados não disponível", 
                              f"db_available: {self.db.db_available}, conn: {self.db.conn is not None}")
                return False
        except Exception as e:
            self.log_result("DB_CONNECTION", "ERROR", 
                          f"Falha na conexão com banco", str(e))
            return False
    
    def test_user_authentication(self):
        """Testa autenticação de todos os usuários"""
        all_success = True
        
        for perfil, creds in self.usuarios.items():
            user_info, message = self.authenticate_user(creds['usuario'], creds['senha'])
            
            if user_info:
                self.log_result(f"AUTH_{perfil.upper()}", "SUCCESS", 
                              f"Usuário {creds['usuario']} autenticado", 
                              f"Perfil: {user_info['perfil']}")
            else:
                self.log_result(f"AUTH_{perfil.upper()}", "ERROR", 
                              f"Falha na autenticação de {creds['usuario']}", message)
                all_success = False
        
        return all_success
    
    def create_solicitacao(self):
        """1. SOLICITANTE: Cria nova solicitação"""
        try:
            # Autenticar solicitante
            user_info, _ = self.authenticate_user(
                self.usuarios['solicitante']['usuario'], 
                self.usuarios['solicitante']['senha']
            )
            
            if not user_info:
                self.log_result("CREATE_SOLICITACAO", "ERROR", "Falha na autenticação do solicitante")
                return False
            
            # Gerar próximo número de solicitação
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT MAX(numero_solicitacao_estoque) FROM solicitacoes")
            result = cursor.fetchone()
            # RealDictCursor retorna dict, acessar pela chave correta
            if result:
                # A chave será o nome da função MAX()
                max_val = list(result.values())[0] if result else None
                next_numero = (max_val + 1) if max_val else 1
            else:
                next_numero = 1
            cursor.close()
            
            # Inserir diretamente no banco com SQL simples
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO solicitacoes (
                    numero_solicitacao_estoque, solicitante, departamento, descricao, 
                    justificativa, prioridade, valor_estimado, local_aplicacao, 
                    tipo_solicitacao, observacoes, status, etapa_atual, sla_dias, 
                    carimbo_data_hora
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING numero_solicitacao_estoque
            """, (
                next_numero,
                user_info['usuario'],
                user_info['departamento'],
                'Notebook Dell Inspiron 15 para desenvolvimento',
                'Equipamento atual apresenta falhas constantes, impactando produtividade',
                'Alta',
                2500.00,
                'Escritório - Setor TI',
                'Equipamento',
                'Preferência por modelo com SSD e 16GB RAM',
                'Solicitação',
                'Solicitação',
                3,
                datetime.datetime.now().isoformat()
            ))
            
            result = cursor.fetchone()
            if result:
                # RealDictCursor retorna dict para RETURNING também
                self.solicitacao_id = list(result.values())[0]
                self.db.conn.commit()
                cursor.close()
                
                self.log_result("CREATE_SOLICITACAO", "SUCCESS", 
                              f"Solicitação criada com número {self.solicitacao_id}",
                              f"Valor: R$ 2.500,00")
                return True
            else:
                self.db.conn.rollback()
                cursor.close()
                self.log_result("CREATE_SOLICITACAO", "ERROR", "Falha ao obter ID da solicitação")
                return False
            
        except Exception as e:
            if self.db.conn:
                self.db.conn.rollback()
            # Log detalhado do erro para debug
            import traceback
            error_details = f"Erro: {str(e)}\nTraceback: {traceback.format_exc()}"
            print(f"DEBUG - Erro detalhado na criação da solicitação:\n{error_details}")
            self.log_result("CREATE_SOLICITACAO", "ERROR", 
                          "Erro ao criar solicitação", error_details)
            return False
    
    def process_suprimentos(self):
        """2. SUPRIMENTOS: Processa solicitação e move para cotação"""
        try:
            # Autenticar suprimentos
            user_info, _ = self.authenticate_user(
                self.usuarios['suprimentos']['usuario'], 
                self.usuarios['suprimentos']['senha']
            )
            
            if not user_info:
                self.log_result("PROCESS_SUPRIMENTOS", "ERROR", "Falha na autenticação do suprimentos")
                return False
            
            # Atualizar solicitação usando método da classe
            updates = {
                'status': 'Em Cotação',
                'etapa_atual': 'Em Cotação',
                'responsavel_suprimentos': user_info['usuario'],
                'data_cotacao': datetime.datetime.now().isoformat(),
                'fornecedor_recomendado': 'Dell Computadores Ltda',
                'valor_final': 2350.00,
                'observacoes': 'Cotação realizada com 3 fornecedores - melhor proposta selecionada'
            }
            
            success = self.db.update_solicitacao(self.solicitacao_id, updates)
            
            if success:
                self.log_result("PROCESS_SUPRIMENTOS", "SUCCESS", 
                              "Solicitação processada pelo suprimentos",
                              "Status: Em Cotação - Valor cotado: R$ 2.350,00")
                return True
            else:
                self.log_result("PROCESS_SUPRIMENTOS", "ERROR", "Falha ao atualizar solicitação")
                return False
            
        except Exception as e:
            self.log_result("PROCESS_SUPRIMENTOS", "ERROR", 
                          "Erro no processamento do suprimentos", str(e))
            return False
    
    def move_to_approval(self):
        """3. SUPRIMENTOS: Move para aprovação da diretoria"""
        try:
            updates = {
                'status': 'Aguardando Aprovação',
                'etapa_atual': 'Aguardando Aprovação',
                'observacoes': 'Solicitação enviada para aprovação da diretoria - Valor dentro do orçamento'
            }
            
            success = self.db.update_solicitacao(self.solicitacao_id, updates)
            
            if success:
                self.log_result("MOVE_TO_APPROVAL", "SUCCESS", 
                              "Solicitação enviada para aprovação",
                              "Status: Aguardando Aprovação")
                return True
            else:
                self.log_result("MOVE_TO_APPROVAL", "ERROR", "Falha ao atualizar para aprovação")
                return False
            
        except Exception as e:
            self.log_result("MOVE_TO_APPROVAL", "ERROR", 
                          "Erro ao enviar para aprovação", str(e))
            return False
    
    def approve_request(self):
        """4. DIRETORIA: Aprova solicitação"""
        try:
            # Autenticar diretoria
            user_info, _ = self.authenticate_user(
                self.usuarios['diretoria']['usuario'], 
                self.usuarios['diretoria']['senha']
            )
            
            if not user_info:
                self.log_result("APPROVE_REQUEST", "ERROR", "Falha na autenticação da diretoria")
                return False
            
            updates = {
                'status': 'Aprovado',
                'etapa_atual': 'Aprovado',
                'observacoes': 'Solicitação aprovada - Equipamento necessário para manutenção da produtividade'
            }
            
            success = self.db.update_solicitacao(self.solicitacao_id, updates)
            
            if success:
                self.log_result("APPROVE_REQUEST", "SUCCESS", 
                              "Solicitação aprovada pela diretoria",
                              f"Aprovador: {user_info['usuario']} - Valor: R$ 2.350,00")
                return True
            else:
                self.log_result("APPROVE_REQUEST", "ERROR", "Falha ao atualizar aprovação")
                return False
            
        except Exception as e:
            self.log_result("APPROVE_REQUEST", "ERROR", 
                          "Erro na aprovação", str(e))
            return False
    
    def process_purchase(self):
        """5. SUPRIMENTOS: Realiza compra"""
        try:
            # Gerar próximo número de pedido
            next_pedido = self.db.get_next_numero_pedido()
            
            updates = {
                'status': 'Compra feita',
                'etapa_atual': 'Compra feita',
                'numero_pedido_compras': next_pedido,
                'fornecedor_final': 'Dell Computadores Ltda',
                'valor_final': 2350.00,
                'data_entrega_prevista': (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat(),
                'observacoes_pedido_compras': 'Pedido realizado - Prazo de entrega: 7 dias úteis'
            }
            
            success = self.db.update_solicitacao(self.solicitacao_id, updates)
            
            if success:
                self.log_result("PROCESS_PURCHASE", "SUCCESS", 
                              "Compra realizada com sucesso",
                              f"Status: Compra feita - Pedido: {next_pedido} - Entrega prevista: 7 dias")
                return True
            else:
                self.log_result("PROCESS_PURCHASE", "ERROR", "Falha ao atualizar compra")
                return False
            
        except Exception as e:
            self.log_result("PROCESS_PURCHASE", "ERROR", 
                          "Erro na realização da compra", str(e))
            return False
    
    def process_delivery(self):
        """6. ESTOQUE: Processa entrega"""
        try:
            # Autenticar estoque
            user_info, _ = self.authenticate_user(
                self.usuarios['estoque']['usuario'], 
                self.usuarios['estoque']['senha']
            )
            
            if not user_info:
                self.log_result("PROCESS_DELIVERY", "ERROR", "Falha na autenticação do estoque")
                return False
            
            updates = {
                'status': 'Aguardando Entrega',
                'etapa_atual': 'Aguardando Entrega',
                'data_entrega_real': datetime.datetime.now().isoformat(),
                'responsavel_recebimento': user_info['usuario'],
                'entrega_conforme': 'Sim',
                'nota_fiscal': f'NF-{datetime.datetime.now().strftime("%Y%m%d")}-12345',
                'observacoes_entrega': 'Produto recebido conforme especificação - Sem avarias'
            }
            
            success = self.db.update_solicitacao(self.solicitacao_id, updates)
            
            if success:
                self.log_result("PROCESS_DELIVERY", "SUCCESS", 
                              "Entrega processada pelo estoque",
                              f"Responsável: {user_info['usuario']} - Conforme: Sim")
                return True
            else:
                self.log_result("PROCESS_DELIVERY", "ERROR", "Falha ao atualizar entrega")
                return False
            
        except Exception as e:
            self.log_result("PROCESS_DELIVERY", "ERROR", 
                          "Erro no processamento da entrega", str(e))
            return False
    
    def finalize_request(self):
        """7. FINALIZAÇÃO: Finaliza solicitação"""
        try:
            updates = {
                'status': 'Pedido Finalizado',
                'etapa_atual': 'Pedido Finalizado',
                'data_finalizacao': datetime.datetime.now().isoformat(),
                'observacoes_finalizacao': 'Solicitação finalizada com sucesso - Equipamento entregue ao solicitante'
            }
            
            success = self.db.update_solicitacao(self.solicitacao_id, updates)
            
            if success:
                self.log_result("FINALIZE_REQUEST", "SUCCESS", 
                              "Solicitação finalizada com sucesso",
                              "Status: Pedido Finalizado")
                return True
            else:
                self.log_result("FINALIZE_REQUEST", "ERROR", "Falha ao finalizar solicitação")
                return False
            
        except Exception as e:
            self.log_result("FINALIZE_REQUEST", "ERROR", 
                          "Erro na finalização", str(e))
            return False
    
    def verify_final_state(self):
        """Verifica estado final da solicitação"""
        try:
            solicitacao = self.db.get_solicitacao_by_numero(self.solicitacao_id)
            
            if solicitacao and solicitacao.get('status') == 'Pedido Finalizado':
                self.log_result("VERIFY_FINAL_STATE", "SUCCESS", 
                              "Estado final verificado com sucesso",
                              f"Número: {solicitacao.get('numero_solicitacao_estoque')} - Status: {solicitacao.get('status')} - Valor: R$ {solicitacao.get('valor_final', 0)}")
                return True
            else:
                self.log_result("VERIFY_FINAL_STATE", "ERROR", 
                              "Estado final incorreto", 
                              f"Status atual: {solicitacao.get('status') if solicitacao else 'Não encontrado'}")
                return False
                
        except Exception as e:
            self.log_result("VERIFY_FINAL_STATE", "ERROR", 
                          "Erro na verificação final", str(e))
            return False
    
    def generate_report(self):
        """Gera relatório final dos testes"""
        end_time = datetime.datetime.now()
        duration = end_time - self.start_time
        
        success_count = len([r for r in self.test_results if r['status'] == 'SUCCESS'])
        error_count = len([r for r in self.test_results if r['status'] == 'ERROR'])
        total_tests = len(self.test_results)
        
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL DO TESTE DE FLUXO COMPLETO")
        print("="*80)
        print(f"🕐 Duração total: {duration.total_seconds():.2f} segundos")
        print(f"📈 Testes executados: {total_tests}")
        print(f"✅ Sucessos: {success_count}")
        print(f"❌ Erros: {error_count}")
        print(f"📊 Taxa de sucesso: {(success_count/total_tests)*100:.1f}%")
        
        if self.solicitacao_id:
            print(f"🆔 ID da solicitação criada: {self.solicitacao_id}")
        
        print("\n📋 DETALHES DOS TESTES:")
        print("-"*80)
        
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "SUCCESS" else "❌"
            print(f"{status_icon} {result['step']}: {result['message']}")
            if result['details']:
                print(f"   └─ {result['details']}")
        
        print("\n" + "="*80)
        
        if error_count == 0:
            print("🎉 TODOS OS TESTES PASSARAM! Sistema funcionando perfeitamente.")
        else:
            print(f"⚠️  {error_count} teste(s) falharam. Verifique os detalhes acima.")
        
        print("="*80)
    
    def run_complete_test(self):
        """Executa teste completo do fluxo"""
        print("🚀 INICIANDO TESTE COMPLETO DO FLUXO DE COMPRAS")
        print("="*80)
        
        # Sequência de testes
        tests = [
            ("Conexão com banco", self.test_database_connection),
            ("Autenticação de usuários", self.test_user_authentication),
            ("1. Criar solicitação", self.create_solicitacao),
            ("2. Processar suprimentos", self.process_suprimentos),
            ("3. Enviar para aprovação", self.move_to_approval),
            ("4. Aprovar solicitação", self.approve_request),
            ("5. Realizar compra", self.process_purchase),
            ("6. Processar entrega", self.process_delivery),
            ("7. Finalizar solicitação", self.finalize_request),
            ("Verificar estado final", self.verify_final_state)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔄 Executando: {test_name}")
            success = test_func()
            
            if not success and test_name not in ["Autenticação de usuários"]:
                print(f"❌ Teste '{test_name}' falhou. Interrompendo execução.")
                break
            
            # Pequena pausa entre testes
            time.sleep(0.5)
        
        # Gerar relatório final
        self.generate_report()

def main():
    """Função principal"""
    print("Sistema de Teste do Fluxo Completo de Compras - EC2")
    print("Desenvolvido para testar todas as etapas do processo")
    print("-"*80)
    
    try:
        tester = TestFluxoCompleto()
        tester.run_complete_test()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro crítico durante execução: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
