#!/usr/bin/env python3
"""
Script para criar APENAS os usuários REAIS do sistema baseado na MATRIZ_PERMISSOES.md
"""

import os
import sys

# Adiciona o diretório atual ao path para importar database_local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_local import get_local_database

def create_real_users():
    """Cria apenas os usuários REAIS que existiam no PostgreSQL"""
    
    # Lista dos usuários REAIS baseada na MATRIZ_PERMISSOES.md
    usuarios_reais = [
        # Solicitantes
        {"username": "Leonardo.Fragoso", "nome": "Leonardo Fragoso", "perfil": "Solicitante", "departamento": "TI"},
        {"username": "Genival.Silva", "nome": "Genival Silva", "perfil": "Solicitante", "departamento": "Produção"},
        
        # Estoque
        {"username": "Estoque.Sistema", "nome": "Sistema de Estoque", "perfil": "Estoque", "departamento": "Estoque"},
        
        # Suprimentos
        {"username": "Fabio.Ramos", "nome": "Fábio Ramos", "perfil": "Suprimentos", "departamento": "Suprimentos"},
        
        # Diretoria
        {"username": "Diretoria", "nome": "Diretoria Executiva", "perfil": "Diretoria", "departamento": "Diretoria"},
        
        # Admin
        {"username": "admin", "nome": "Administrador do Sistema", "perfil": "Admin", "departamento": "TI"},
    ]
    
    # Conecta ao banco
    db = get_local_database()
    
    if not db.db_available:
        print("❌ Erro: Banco de dados não disponível")
        return False
    
    print("👥 Criando usuários REAIS do sistema...")
    print("📋 Baseado na MATRIZ_PERMISSOES.md")
    print("-" * 80)
    
    usuarios_criados = 0
    usuarios_existentes = 0
    erros = 0
    
    for usuario in usuarios_reais:
        try:
            # Tenta adicionar o usuário (senha padrão: Teste123)
            sucesso = db.add_user(
                username=usuario["username"],
                nome=usuario["nome"],
                perfil=usuario["perfil"],
                departamento=usuario["departamento"],
                senha_hash="Teste123"  # Senha padrão
            )
            
            if sucesso:
                print(f"✅ {usuario['username']:<20} | {usuario['nome']:<25} | {usuario['perfil']:<12} | {usuario['departamento']}")
                usuarios_criados += 1
            else:
                print(f"⚠️  {usuario['username']:<20} | {usuario['nome']:<25} | {usuario['perfil']:<12} | {usuario['departamento']} (já existe)")
                usuarios_existentes += 1
                
        except Exception as e:
            print(f"❌ {usuario['username']:<20} | Erro: {e}")
            erros += 1
    
    print("-" * 80)
    print(f"📊 Resumo:")
    print(f"   ✅ Usuários criados: {usuarios_criados}")
    print(f"   ⚠️  Usuários já existentes: {usuarios_existentes}")
    print(f"   ❌ Erros: {erros}")
    print(f"   📝 Senha padrão para todos: 'Teste123'")
    
    return erros == 0

def show_real_users():
    """Mostra os usuários reais organizados por perfil"""
    
    db = get_local_database()
    
    if not db.db_available:
        print("❌ Erro: Banco de dados não disponível")
        return
    
    usuarios = db.get_all_users()
    
    if not usuarios:
        print("⚠️ Nenhum usuário encontrado")
        return
    
    # Organiza usuários por perfil
    por_perfil = {}
    for usuario in usuarios:
        perfil = usuario['perfil']
        if perfil not in por_perfil:
            por_perfil[perfil] = []
        por_perfil[perfil].append(usuario)
    
    print("\n👥 Usuários REAIS por Perfil:")
    print("=" * 80)
    
    # Ordem específica dos perfis
    ordem_perfis = ["Admin", "Diretoria", "Suprimentos", "Estoque", "Solicitante"]
    
    for perfil in ordem_perfis:
        if perfil in por_perfil:
            print(f"\n🎯 {perfil.upper()}")
            print("-" * 40)
            
            for usuario in sorted(por_perfil[perfil], key=lambda x: x['username']):
                print(f"   👤 {usuario['username']:<20} | {usuario['nome']:<25} | {usuario['departamento']}")

def main():
    """Função principal"""
    print("👥 Setup de Usuários REAIS - Sistema de Compras")
    print("📋 Baseado na documentação MATRIZ_PERMISSOES.md")
    print("=" * 80)
    
    # Cria apenas os usuários reais
    sucesso = create_real_users()
    
    if sucesso:
        print("\n✅ Todos os usuários REAIS foram criados com sucesso!")
        
        # Mostra organização por perfil
        show_real_users()
        
        print("\n🎯 Usuários do Sistema:")
        print("   👤 Leonardo.Fragoso - Solicitante (TI)")
        print("   👤 Genival.Silva - Solicitante (Produção)")
        print("   👤 Estoque.Sistema - Estoque")
        print("   👤 Fabio.Ramos - Suprimentos")
        print("   👤 Diretoria - Aprovador")
        print("   👤 admin - Administrador")
        
        print("\n🔑 Credenciais:")
        print("   • Todos os usuários têm senha: 'Teste123'")
        print("   • Faça login com qualquer usuário para testar")
        
    else:
        print("\n❌ Alguns erros ocorreram durante a criação dos usuários")
    
    return sucesso

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
