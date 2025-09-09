#!/usr/bin/env python3
"""
Script para limpar o banco e criar APENAS os 6 usuários REAIS
"""

import os
import sys

# Adiciona o diretório atual ao path para importar database_local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_local import get_local_database

def clean_and_create_real_users():
    """Remove todos os usuários e cria apenas os 6 usuários REAIS"""
    
    # Lista dos 6 usuários REAIS baseada na MATRIZ_PERMISSOES.md
    usuarios_reais = [
        {"username": "Leonardo.Fragoso", "nome": "Leonardo Fragoso", "perfil": "Solicitante", "departamento": "TI"},
        {"username": "Genival.Silva", "nome": "Genival Silva", "perfil": "Solicitante", "departamento": "Produção"},
        {"username": "Estoque.Sistema", "nome": "Sistema de Estoque", "perfil": "Estoque", "departamento": "Estoque"},
        {"username": "Fabio.Ramos", "nome": "Fábio Ramos", "perfil": "Suprimentos", "departamento": "Suprimentos"},
        {"username": "Diretoria", "nome": "Diretoria Executiva", "perfil": "Diretoria", "departamento": "Diretoria"},
        {"username": "admin", "nome": "Administrador do Sistema", "perfil": "Admin", "departamento": "TI"},
    ]
    
    # Conecta ao banco
    db = get_local_database()
    
    if not db.db_available:
        print("❌ Erro: Banco de dados não disponível")
        return False
    
    try:
        cursor = db.conn.cursor()
        
        print("🧹 Limpando banco de dados...")
        print("⚠️  Removendo TODOS os usuários existentes...")
        
        # Remove todos os usuários
        cursor.execute('DELETE FROM usuarios')
        db.conn.commit()
        
        print("✅ Banco limpo com sucesso!")
        print("\n👥 Criando apenas os 6 usuários REAIS...")
        print("-" * 80)
        
        # Cria apenas os usuários reais
        for usuario in usuarios_reais:
            sucesso = db.add_user(
                username=usuario["username"],
                nome=usuario["nome"],
                perfil=usuario["perfil"],
                departamento=usuario["departamento"],
                senha_hash="Teste123"
            )
            
            if sucesso:
                print(f"✅ {usuario['username']:<20} | {usuario['nome']:<25} | {usuario['perfil']:<12} | {usuario['departamento']}")
            else:
                print(f"❌ {usuario['username']:<20} | Erro ao criar usuário")
                return False
        
        print("-" * 80)
        print("✅ Banco configurado com APENAS os 6 usuários reais!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        return False

def verify_users():
    """Verifica e mostra apenas os usuários no banco"""
    
    db = get_local_database()
    
    if not db.db_available:
        return
    
    usuarios = db.get_all_users()
    
    print(f"\n📊 Verificação Final - Total: {len(usuarios)} usuários")
    print("=" * 60)
    
    for usuario in sorted(usuarios, key=lambda x: x['perfil']):
        print(f"👤 {usuario['username']:<20} | {usuario['perfil']:<12} | {usuario['departamento']}")
    
    print("=" * 60)
    
    if len(usuarios) == 6:
        print("✅ PERFEITO! Apenas os 6 usuários reais estão no banco")
    else:
        print(f"⚠️  ATENÇÃO! Esperado 6 usuários, encontrado {len(usuarios)}")

def main():
    """Função principal"""
    print("🧹 Limpeza e Setup dos Usuários REAIS")
    print("📋 Baseado na MATRIZ_PERMISSOES.md")
    print("=" * 80)
    print("⚠️  ATENÇÃO: Este script irá REMOVER todos os usuários existentes!")
    print("📝 Criará apenas os 6 usuários reais do sistema original")
    print("=" * 80)
    
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("❌ Operação cancelada")
        return False
    
    # Executa limpeza e criação
    sucesso = clean_and_create_real_users()
    
    if sucesso:
        # Verifica resultado
        verify_users()
        
        print("\n🎯 Usuários REAIS criados:")
        print("   👤 Leonardo.Fragoso - Solicitante (TI)")
        print("   👤 Genival.Silva - Solicitante (Produção)")
        print("   👤 Estoque.Sistema - Estoque")
        print("   👤 Fabio.Ramos - Suprimentos")
        print("   👤 Diretoria - Aprovador")
        print("   👤 admin - Administrador")
        
        print("\n🔑 Todos com senha: 'Teste123'")
        print("✅ Banco pronto para uso!")
        
    return sucesso

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
