#!/usr/bin/env python
"""
Script de migração de dados do Sistema de Compras V1 para V2
Migra dados do SQLite V1 para o novo banco SQLite V2 com Django

Uso:
    python migrate_v1_to_v2.py --v1-db /caminho/para/sistema_compras.db --v2-db /caminho/para/sistema_compras_v2.db

Autor: Sistema de Compras V2
Data: 2024-09-15
"""

import os
import sys
import sqlite3
import hashlib
import json
import argparse
from datetime import datetime
from pathlib import Path
from django.utils import timezone

# Adiciona o diretório do Django ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.solicitacoes.models import Solicitacao, CatalogoProduto, Movimentacao
from apps.configuracoes.models import Configuracao, ConfiguracaoSLA, LimiteAprovacao
from apps.auditoria.models import AuditoriaAdmin, HistoricoLogin
from apps.usuarios.models import Sessao

User = get_user_model()


class V1ToV2Migrator:
    """Classe principal para migração de dados V1 → V2"""
    
    def __init__(self, v1_db_path, v2_db_path=None):
        self.v1_db_path = v1_db_path
        self.v2_db_path = v2_db_path
        self.v1_conn = None
        self.stats = {
            'usuarios': 0,
            'solicitacoes': 0,
            'configuracoes': 0,
            'catalogo_produtos': 0,
            'auditoria': 0,
            'movimentacoes': 0,
            'sessoes': 0,
            'errors': []
        }
    
    def connect_v1_db(self):
        """Conecta ao banco V1"""
        try:
            self.v1_conn = sqlite3.connect(self.v1_db_path)
            self.v1_conn.row_factory = sqlite3.Row
            print(f"✅ Conectado ao banco V1: {self.v1_db_path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar ao banco V1: {e}")
            return False
    
    def verify_v1_tables(self):
        """Verifica se as tabelas V1 existem"""
        required_tables = ['usuarios', 'solicitacoes', 'configuracoes', 'catalogo_produtos']
        cursor = self.v1_conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"❌ Tabelas obrigatórias não encontradas: {missing_tables}")
            return False
        
        print("✅ Todas as tabelas V1 encontradas")
        return True
    
    def migrate_usuarios(self):
        """Migra usuários do V1 para V2"""
        print("\n🔄 Migrando usuários...")
        
        cursor = self.v1_conn.cursor()
        cursor.execute("SELECT * FROM usuarios")
        usuarios_v1 = cursor.fetchall()
        
        for user_data in usuarios_v1:
            try:
                # Verifica se usuário já existe
                if User.objects.filter(username=user_data['username']).exists():
                    print(f"⚠️  Usuário {user_data['username']} já existe, pulando...")
                    continue
                
                # Cria usuário V2
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=f"{user_data['username']}@empresa.com",  # Email padrão
                    nome=user_data['nome'],
                    perfil=user_data['perfil'],
                    departamento=user_data['departamento'],
                    password='Teste123',  # Senha padrão, será alterada no primeiro login
                    is_active=True
                )
                
                # Salva hash V1 para compatibilidade
                user.senha_hash_v1 = user_data['senha_hash']
                user.save()
                
                self.stats['usuarios'] += 1
                print(f"✅ Usuário migrado: {user_data['username']} ({user_data['perfil']})")
                
            except Exception as e:
                error_msg = f"Erro ao migrar usuário {user_data['username']}: {e}"
                print(f"❌ {error_msg}")
                self.stats['errors'].append(error_msg)
    
    def migrate_configuracoes(self):
        """Migra configurações do V1 para V2"""
        print("\n🔄 Migrando configurações...")
        
        cursor = self.v1_conn.cursor()
        cursor.execute("SELECT * FROM configuracoes")
        configs_v1 = cursor.fetchall()
        
        for config_data in configs_v1:
            try:
                # Verifica se configuração já existe
                if Configuracao.objects.filter(chave=config_data['chave']).exists():
                    print(f"⚠️  Configuração {config_data['chave']} já existe, atualizando...")
                    config = Configuracao.objects.get(chave=config_data['chave'])
                    config.valor = config_data['valor']
                    config.save()
                else:
                    # Cria nova configuração
                    Configuracao.objects.create(
                        chave=config_data['chave'],
                        valor=config_data['valor'],
                        descricao=f"Migrado do V1 - {config_data['chave']}",
                        tipo='string'  # Tipo padrão
                    )
                
                self.stats['configuracoes'] += 1
                print(f"✅ Configuração migrada: {config_data['chave']}")
                
            except Exception as e:
                error_msg = f"Erro ao migrar configuração {config_data['chave']}: {e}"
                print(f"❌ {error_msg}")
                self.stats['errors'].append(error_msg)
    
    def migrate_catalogo_produtos(self):
        """Migra catálogo de produtos do V1 para V2"""
        print("\n🔄 Migrando catálogo de produtos...")
        
        cursor = self.v1_conn.cursor()
        cursor.execute("SELECT * FROM catalogo_produtos")
        produtos_v1 = cursor.fetchall()
        
        for produto_data in produtos_v1:
            try:
                # Verifica se produto já existe
                if CatalogoProduto.objects.filter(nome=produto_data['nome']).exists():
                    print(f"⚠️  Produto {produto_data['nome']} já existe, pulando...")
                    continue
                
                # Cria produto V2 baseado na estrutura real do V1 e V2
                CatalogoProduto.objects.create(
                    codigo=produto_data['codigo'] if 'codigo' in produto_data.keys() and produto_data['codigo'] else f"PRD-{produto_data['id']}",
                    nome=produto_data['nome'],
                    categoria=produto_data['categoria'] if 'categoria' in produto_data.keys() and produto_data['categoria'] else 'Geral',
                    unidade=produto_data['unidade'] if 'unidade' in produto_data.keys() and produto_data['unidade'] else 'UN',
                    ativo=bool(produto_data['ativo']) if 'ativo' in produto_data.keys() and produto_data['ativo'] is not None else True
                )
                
                self.stats['catalogo_produtos'] += 1
                print(f"✅ Produto migrado: {produto_data['nome']}")
                
            except Exception as e:
                nome_produto = produto_data['nome'] if 'nome' in produto_data.keys() else 'N/A'
                error_msg = f"Erro ao migrar produto {nome_produto}: {e}"
                print(f"❌ {error_msg}")
                self.stats['errors'].append(error_msg)
    
    def migrate_solicitacoes(self):
        """Migra solicitações do V1 para V2"""
        print("\n🔄 Migrando solicitações...")
        
        cursor = self.v1_conn.cursor()
        cursor.execute("SELECT * FROM solicitacoes ORDER BY id")
        solicitacoes_v1 = cursor.fetchall()
        
        for sol_data in solicitacoes_v1:
            try:
                # Verifica se solicitação já existe
                if Solicitacao.objects.filter(numero_solicitacao=sol_data['numero_solicitacao']).exists():
                    print(f"⚠️  Solicitação {sol_data['numero_solicitacao']} já existe, pulando...")
                    continue
                
                # Prepara dados para migração
                solicitacao_data = {
                    'numero_solicitacao': sol_data['numero_solicitacao'],
                    'solicitante_username': sol_data['solicitante_username'],
                    'solicitante_nome': sol_data['solicitante_nome'],
                    'departamento': sol_data['departamento'],
                    'prioridade': sol_data['prioridade'],
                    'status': sol_data['status'],
                    'descricao': sol_data['descricao'],
                    'descricao_resumida': sol_data['descricao_resumida'] if 'descricao_resumida' in sol_data else sol_data['descricao'][:100],
                    'local_aplicacao': sol_data['local_aplicacao'] if 'local_aplicacao' in sol_data else '',
                    'produto_nome': sol_data['produto_nome'] if 'produto_nome' in sol_data else '',
                    'quantidade': sol_data['quantidade'] if 'quantidade' in sol_data else 1,
                    'unidade': sol_data['unidade'] if 'unidade' in sol_data else 'UN',
                    'especificacoes_tecnicas': sol_data['especificacoes_tecnicas'] if 'especificacoes_tecnicas' in sol_data else '',
                    'observacoes': sol_data['observacoes'] if 'observacoes' in sol_data else '',
                    'valor_estimado': sol_data['valor_estimado'] if 'valor_estimado' in sol_data else 0,
                    'valor_final': sol_data['valor_final'] if 'valor_final' in sol_data else 0,
                }
                
                # Campos opcionais do fluxo
                optional_fields = [
                    'numero_requisicao', 'data_requisicao', 'responsavel_suprimentos',
                    'minimo_cotacoes', 'numero_pedido', 'fornecedor_recomendado',
                    'criterio_escolha', 'data_aprovacao', 'aprovado_por',
                    'observacoes_aprovacao', 'data_entrega_prevista', 'data_entrega_real',
                    'numero_nota_fiscal'
                ]
                
                for field in optional_fields:
                    try:
                        if field in sol_data:
                            solicitacao_data[field] = sol_data[field]
                    except (KeyError, IndexError):
                        # Campo não existe na tabela V1
                        pass
                
                # Cria solicitação V2
                solicitacao = Solicitacao.objects.create(**solicitacao_data)
                
                # Preserva timestamp original se disponível
                try:
                    if 'created_at' in sol_data and sol_data['created_at']:
                        solicitacao.created_at = sol_data['created_at']
                        solicitacao.save()
                except (KeyError, IndexError):
                    # Campo created_at não existe
                    pass
                
                self.stats['solicitacoes'] += 1
                print(f"✅ Solicitação migrada: {sol_data['numero_solicitacao']} - {sol_data['status']}")
                
            except Exception as e:
                error_msg = f"Erro ao migrar solicitação {sol_data['numero_solicitacao'] if 'numero_solicitacao' in sol_data else 'N/A'}: {e}"
                print(f"❌ {error_msg}")
                self.stats['errors'].append(error_msg)
    
    def migrate_movimentacoes(self):
        """Migra movimentações/histórico do V1 para V2"""
        print("\n🔄 Migrando movimentações...")
        
        cursor = self.v1_conn.cursor()
        
        # Verifica se tabela movimentacoes existe no V1
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movimentacoes'")
        if not cursor.fetchone():
            print("⚠️  Tabela 'movimentacoes' não encontrada no V1, pulando...")
            return
        
        cursor.execute("SELECT * FROM movimentacoes ORDER BY data_movimentacao")
        movimentacoes_v1 = cursor.fetchall()
        
        for mov_data in movimentacoes_v1:
            try:
                # Busca a solicitação
                solicitacao = None
                try:
                    if 'numero_solicitacao' in mov_data and mov_data['numero_solicitacao']:
                        solicitacao = Solicitacao.objects.get(numero_solicitacao=mov_data['numero_solicitacao'])
                except (Solicitacao.DoesNotExist, KeyError, IndexError):
                    pass
                
                # Busca o usuário pelo nome/username
                usuario = None
                try:
                    if 'usuario' in mov_data and mov_data['usuario']:
                        # Tenta primeiro por username
                        try:
                            usuario = User.objects.get(username=mov_data['usuario'])
                        except User.DoesNotExist:
                            # Se não encontrar, tenta por nome
                            usuario = User.objects.filter(first_name__icontains=mov_data['usuario']).first()
                except (KeyError, IndexError):
                    pass
                
                # Converte data_movimentacao
                data_movimentacao = timezone.now()
                if 'data_movimentacao' in mov_data and mov_data['data_movimentacao']:
                    try:
                        if isinstance(mov_data['data_movimentacao'], str):
                            data_movimentacao = timezone.datetime.fromisoformat(mov_data['data_movimentacao'].replace('Z', '+00:00'))
                        else:
                            data_movimentacao = mov_data['data_movimentacao']
                    except:
                        data_movimentacao = timezone.now()
                
                Movimentacao.objects.create(
                    solicitacao=solicitacao,
                    etapa_origem=mov_data['etapa_origem'] if 'etapa_origem' in mov_data else '',
                    etapa_destino=mov_data['etapa_destino'] if 'etapa_destino' in mov_data else '',
                    usuario=usuario,
                    observacoes=mov_data['observacoes'] if 'observacoes' in mov_data else '',
                    data_movimentacao=data_movimentacao
                )
                
                self.stats['movimentacoes'] += 1
                
            except Exception as e:
                print(f"   ❌ Erro ao migrar movimentação: {e}")
                continue
                
        print(f"✅ Movimentacoes migradas: {self.stats['movimentacoes']}")
    
    def migrate_auditoria(self):
        """Migra dados de auditoria do V1 para V2"""
        print("\n🔄 Migrando auditoria...")
        
        cursor = self.v1_conn.cursor()
        
        # Verifica se tabela auditoria_admin existe no V1
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auditoria_admin'")
        if not cursor.fetchone():
            print("⚠️  Tabela 'auditoria_admin' não encontrada no V1, pulando...")
            return
        
        cursor.execute("SELECT * FROM auditoria_admin ORDER BY timestamp")
        auditoria_v1 = cursor.fetchall()
        
        for audit_data in auditoria_v1:
            try:
                # Busca o usuário pelo nome (V1 usa campo 'usuario' como string)
                usuario = None
                try:
                    if 'usuario' in audit_data and audit_data['usuario']:
                        # Tenta primeiro por username
                        try:
                            usuario = User.objects.get(username=audit_data['usuario'])
                        except User.DoesNotExist:
                            # Se não encontrar, tenta por nome
                            usuario = User.objects.filter(first_name__icontains=audit_data['usuario']).first()
                except (KeyError, IndexError):
                    pass
                
                # Mapeia ação do V1 para V2
                acao_map = {
                    'create': 'CREATE',
                    'update': 'UPDATE', 
                    'delete': 'DELETE',
                    'login': 'LOGIN',
                    'logout': 'LOGOUT',
                    'approve': 'APPROVE',
                    'reject': 'REJECT'
                }
                
                acao = acao_map.get(audit_data['acao'].lower() if 'acao' in audit_data else '', 'UPDATE')
                
                # Converte timestamp
                timestamp = timezone.now()
                if 'timestamp' in audit_data and audit_data['timestamp']:
                    try:
                        if isinstance(audit_data['timestamp'], str):
                            timestamp = timezone.datetime.fromisoformat(audit_data['timestamp'].replace('Z', '+00:00'))
                        else:
                            timestamp = audit_data['timestamp']
                    except:
                        timestamp = timezone.now()
                
                # Cria entrada de auditoria V2
                AuditoriaAdmin.objects.create(
                    usuario=usuario,
                    usuario_nome=audit_data['usuario'] if 'usuario' in audit_data else 'Sistema',
                    acao=acao,
                    modulo=audit_data['modulo'] if 'modulo' in audit_data else 'Sistema',
                    detalhes=audit_data['detalhes'] if 'detalhes' in audit_data else '',
                    solicitacao_id=audit_data['solicitacao_id'] if 'solicitacao_id' in audit_data else None,
                    ip_address=audit_data['ip_address'] if 'ip_address' in audit_data else '127.0.0.1',
                    timestamp=timestamp
                )
                
                self.stats['auditoria'] += 1
                
            except Exception as e:
                print(f"   ❌ Erro ao migrar auditoria: {e}")
                continue
                
        print(f"✅ Registros de auditoria migrados: {self.stats['auditoria']}")
    
    def create_default_configurations(self):
        """Cria configurações padrão do sistema V2"""
        print("\n🔄 Criando configurações padrão...")
        
        default_configs = [
            # Configurações SLA por departamento
            ('sla_ti_urgente', '1', 'SLA para TI - Urgente (dias)'),
            ('sla_ti_alta', '2', 'SLA para TI - Alta (dias)'),
            ('sla_ti_normal', '3', 'SLA para TI - Normal (dias)'),
            ('sla_ti_baixa', '5', 'SLA para TI - Baixa (dias)'),
            
            ('sla_producao_urgente', '1', 'SLA para Produção - Urgente (dias)'),
            ('sla_producao_alta', '2', 'SLA para Produção - Alta (dias)'),
            ('sla_producao_normal', '3', 'SLA para Produção - Normal (dias)'),
            ('sla_producao_baixa', '5', 'SLA para Produção - Baixa (dias)'),
            
            # Configurações gerais
            ('sistema_nome', 'Sistema de Gestão de Compras V2', 'Nome do sistema'),
            ('empresa_nome', 'Empresa Ziran', 'Nome da empresa'),
            ('moeda_padrao', 'BRL', 'Moeda padrão do sistema'),
            ('timezone', 'America/Sao_Paulo', 'Fuso horário do sistema'),
        ]
        
        for chave, valor, descricao in default_configs:
            Configuracao.objects.get_or_create(
                chave=chave,
                defaults={
                    'valor': valor,
                    'descricao': descricao,
                    'tipo': 'string'
                }
            )
        
        # Cria configurações SLA por departamento
        departamentos = ['TI', 'Produção', 'Geral']
        for dept in departamentos:
            ConfiguracaoSLA.objects.get_or_create(
                departamento=dept,
                defaults={
                    'sla_urgente': 1,
                    'sla_alta': 2,
                    'sla_normal': 3,
                    'sla_baixa': 5,
                    'ativo': True
                }
            )
        
        # Cria limites de aprovação padrão
        limites_aprovacao = [
            ('Gerência', 0, 5000, 'Gerência'),
            ('Diretoria', 5000, 15000, 'Diretoria'),
            ('Especial', 15000, 999999, 'Especial'),
        ]
        
        for nome, min_val, max_val, aprovador in limites_aprovacao:
            LimiteAprovacao.objects.get_or_create(
                nome=nome,
                defaults={
                    'valor_minimo': min_val,
                    'valor_maximo': max_val,
                    'aprovador_necessario': aprovador,
                    'ativo': True
                }
            )
        
        print("✅ Configurações padrão criadas")
    
    def print_migration_summary(self):
        """Imprime resumo da migração"""
        print("\n" + "="*60)
        print("📊 RESUMO DA MIGRAÇÃO V1 → V2")
        print("="*60)
        print(f"✅ Usuários migrados: {self.stats['usuarios']}")
        print(f"✅ Solicitações migradas: {self.stats['solicitacoes']}")
        print(f"✅ Configurações migradas: {self.stats['configuracoes']}")
        print(f"✅ Produtos do catálogo: {self.stats['catalogo_produtos']}")
        print(f"✅ Movimentações migradas: {self.stats['movimentacoes']}")
        print(f"✅ Registros de auditoria: {self.stats['auditoria']}")
        
        total_migrated = sum([
            self.stats['usuarios'], self.stats['solicitacoes'],
            self.stats['configuracoes'], self.stats['catalogo_produtos'],
            self.stats['movimentacoes'], self.stats['auditoria']
        ])
        
        print(f"\n📈 Total de registros migrados: {total_migrated}")
        
        if self.stats['errors']:
            print(f"\n⚠️  Erros encontrados: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Mostra apenas os primeiros 5 erros
                print(f"   - {error}")
            if len(self.stats['errors']) > 5:
                print(f"   ... e mais {len(self.stats['errors']) - 5} erros")
        else:
            print("\n🎉 Migração concluída sem erros!")
        
        print("="*60)
    
    def run_migration(self):
        """Executa a migração completa"""
        print("🚀 INICIANDO MIGRAÇÃO DO SISTEMA DE COMPRAS V1 → V2")
        print("="*60)
        
        # Conecta ao banco V1
        if not self.connect_v1_db():
            return False
        
        # Verifica estrutura V1
        if not self.verify_v1_tables():
            return False
        
        try:
            # Executa migrações em ordem
            self.migrate_usuarios()
            self.migrate_configuracoes()
            self.migrate_catalogo_produtos()
            self.migrate_solicitacoes()
            self.migrate_movimentacoes()
            self.migrate_auditoria()
            self.create_default_configurations()
            
            # Imprime resumo
            self.print_migration_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro crítico durante a migração: {e}")
            return False
        
        finally:
            if self.v1_conn:
                self.v1_conn.close()


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Migra dados do Sistema de Compras V1 para V2')
    parser.add_argument('--v1-db', required=True, help='Caminho para o banco SQLite V1')
    parser.add_argument('--v2-db', help='Caminho para o banco SQLite V2 (opcional)')
    parser.add_argument('--dry-run', action='store_true', help='Executa sem fazer alterações')
    
    args = parser.parse_args()
    
    # Verifica se arquivo V1 existe
    if not os.path.exists(args.v1_db):
        print(f"❌ Arquivo do banco V1 não encontrado: {args.v1_db}")
        return 1
    
    # Executa migração
    migrator = V1ToV2Migrator(args.v1_db, args.v2_db)
    
    if args.dry_run:
        print("🔍 MODO DRY-RUN - Nenhuma alteração será feita")
        # TODO: Implementar modo dry-run
        return 0
    
    success = migrator.run_migration()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
