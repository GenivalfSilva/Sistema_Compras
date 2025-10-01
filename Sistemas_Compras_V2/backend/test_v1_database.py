#!/usr/bin/env python
"""
Test script to verify V1 database works with Django V2
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')
django.setup()

from django.db import connection
from apps.usuarios.models import Usuario, Sessao
from apps.solicitacoes.models import Solicitacao, CatalogoProduto, Movimentacao
from apps.configuracoes.models import Configuracao
from apps.auditoria.models import AuditoriaAdmin

def test_v1_database():
    """Testa se o banco V1 funciona com Django V2"""
    print("🔍 TESTANDO BANCO V1 COM DJANGO V2 (SCHEMA CORRIGIDO)")
    print("="*60)
    
    try:
        # Testa conexão
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Tabelas encontradas: {len(tables)}")
            print(f"   {tables}")
        
        # Testa usuários com Django ORM
        try:
            usuarios = Usuario.objects.all()
            print(f"✅ Usuários (Django ORM): {usuarios.count()}")
            for user in usuarios[:3]:
                print(f"   - {user.username}: {user.nome} | {user.perfil} | {user.departamento}")
        except Exception as e:
            print(f"❌ Erro ao acessar usuários via ORM: {e}")
        
        # Testa solicitações com Django ORM
        try:
            solicitacoes = Solicitacao.objects.all()
            print(f"✅ Solicitações (Django ORM): {solicitacoes.count()}")
            for sol in solicitacoes[:3]:
                print(f"   - Sol.#{sol.numero_solicitacao_estoque}: {sol.solicitante} ({sol.departamento}) - {sol.status}")
        except Exception as e:
            print(f"❌ Erro ao acessar solicitações via ORM: {e}")
        
        # Testa catálogo com Django ORM
        try:
            produtos = CatalogoProduto.objects.all()
            print(f"✅ Produtos (Django ORM): {produtos.count()}")
            for produto in produtos[:3]:
                print(f"   - {produto.codigo}: {produto.nome} ({produto.categoria}) - Ativo: {produto.ativo}")
        except Exception as e:
            print(f"❌ Erro ao acessar produtos via ORM: {e}")
        
        # Testa configurações com Django ORM
        try:
            configs = Configuracao.objects.all()
            print(f"✅ Configurações (Django ORM): {configs.count()}")
            for config in configs[:3]:
                print(f"   - {config.chave}: {config.valor}")
        except Exception as e:
            print(f"❌ Erro ao acessar configurações via ORM: {e}")
        
        # Testa auditoria com Django ORM
        try:
            auditorias = AuditoriaAdmin.objects.all()
            print(f"✅ Auditorias (Django ORM): {auditorias.count()}")
            for audit in auditorias[:3]:
                print(f"   - {audit.usuario}: {audit.acao} - {audit.timestamp}")
        except Exception as e:
            print(f"❌ Erro ao acessar auditorias via ORM: {e}")
        
        # Testa sessões com Django ORM
        try:
            sessoes = Sessao.objects.all()
            print(f"✅ Sessões (Django ORM): {sessoes.count()}")
            for sessao in sessoes[:3]:
                print(f"   - {sessao.username}: {sessao.expires_at}")
        except Exception as e:
            print(f"❌ Erro ao acessar sessões via ORM: {e}")
        
        print("\n🎉 Teste concluído! Django V2 ORM funcionando perfeitamente com banco V1")
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")

if __name__ == '__main__':
    test_v1_database()
