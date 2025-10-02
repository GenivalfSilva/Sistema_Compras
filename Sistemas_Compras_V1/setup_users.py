#!/usr/bin/env python3
"""
Script para criar todos os usuários do sistema com seus departamentos e perfis
"""

import os
import sys

# Adiciona o diretório atual ao path para importar database_local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_local import get_local_database

def create_all_users():
    """Cria todos os usuários do sistema"""
    
    # Lista completa de usuários com seus departamentos e perfis
    usuarios = [
        # Administradores
        {"username": "admin", "nome": "Administrador do Sistema", "perfil": "Admin", "departamento": "TI"},
        {"username": "leonardo.fragoso", "nome": "Leonardo Fragoso", "perfil": "Admin", "departamento": "TI"},
        
        # Solicitantes por departamento
        {"username": "joao.silva", "nome": "João Silva", "perfil": "Solicitante", "departamento": "Manutenção"},
        {"username": "maria.santos", "nome": "Maria Santos", "perfil": "Solicitante", "departamento": "Manutenção"},
        {"username": "pedro.oliveira", "nome": "Pedro Oliveira", "perfil": "Solicitante", "departamento": "Manutenção"},
        
        {"username": "ana.costa", "nome": "Ana Costa", "perfil": "Solicitante", "departamento": "TI"},
        {"username": "carlos.lima", "nome": "Carlos Lima", "perfil": "Solicitante", "departamento": "TI"},
        
        {"username": "lucia.ferreira", "nome": "Lúcia Ferreira", "perfil": "Solicitante", "departamento": "RH"},
        {"username": "roberto.alves", "nome": "Roberto Alves", "perfil": "Solicitante", "departamento": "RH"},
        
        {"username": "fernanda.rocha", "nome": "Fernanda Rocha", "perfil": "Solicitante", "departamento": "Financeiro"},
        {"username": "marcos.pereira", "nome": "Marcos Pereira", "perfil": "Solicitante", "departamento": "Financeiro"},
        
        {"username": "juliana.martins", "nome": "Juliana Martins", "perfil": "Solicitante", "departamento": "Marketing"},
        {"username": "rafael.souza", "nome": "Rafael Souza", "perfil": "Solicitante", "departamento": "Marketing"},
        
        {"username": "patricia.gomes", "nome": "Patrícia Gomes", "perfil": "Solicitante", "departamento": "Produção"},
        {"username": "andre.barbosa", "nome": "André Barbosa", "perfil": "Solicitante", "departamento": "Produção"},
        
        {"username": "camila.reis", "nome": "Camila Reis", "perfil": "Solicitante", "departamento": "Qualidade"},
        {"username": "diego.carvalho", "nome": "Diego Carvalho", "perfil": "Solicitante", "departamento": "Qualidade"},
        
        {"username": "renata.silva", "nome": "Renata Silva", "perfil": "Solicitante", "departamento": "Logística"},
        {"username": "gustavo.mendes", "nome": "Gustavo Mendes", "perfil": "Solicitante", "departamento": "Logística"},
        
        # Responsáveis de Estoque
        {"username": "estoque.supervisor", "nome": "Supervisor de Estoque", "perfil": "Estoque", "departamento": "Estoque"},
        {"username": "claudia.estoque", "nome": "Cláudia Estoque", "perfil": "Estoque", "departamento": "Estoque"},
        {"username": "ricardo.almoxarife", "nome": "Ricardo Almoxarife", "perfil": "Estoque", "departamento": "Estoque"},
        
        # Responsáveis de Suprimentos
        {"username": "suprimentos.gestor", "nome": "Gestor de Suprimentos", "perfil": "Suprimentos", "departamento": "Suprimentos"},
        {"username": "monica.compras", "nome": "Mônica Compras", "perfil": "Suprimentos", "departamento": "Suprimentos"},
        {"username": "fernando.cotacao", "nome": "Fernando Cotação", "perfil": "Suprimentos", "departamento": "Suprimentos"},
        
        # Aprovadores
        {"username": "diretor.geral", "nome": "Diretor Geral", "perfil": "Aprovador", "departamento": "Diretoria"},
        {"username": "gerente.operacoes", "nome": "Gerente de Operações", "perfil": "Aprovador", "departamento": "Gerência"},
        {"username": "supervisor.financeiro", "nome": "Supervisor Financeiro", "perfil": "Aprovador", "departamento": "Financeiro"},
    ]
    
    # Conecta ao banco
    db = get_local_database()
    
    if not db.db_available:
        print("❌ Erro: Banco de dados não disponível")
        return False
    
    print(f"🔄 Criando {len(usuarios)} usuários...")
    print("-" * 80)
    
    usuarios_criados = 0
    usuarios_existentes = 0
    erros = 0
    
    for usuario in usuarios:
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

def show_users_by_department():
    """Mostra usuários organizados por departamento"""
    
    db = get_local_database()
    
    if not db.db_available:
        print("❌ Erro: Banco de dados não disponível")
        return
    
    usuarios = db.get_all_users()
    
    if not usuarios:
        print("⚠️ Nenhum usuário encontrado")
        return
    
    # Organiza usuários por departamento
    por_departamento = {}
    for usuario in usuarios:
        dept = usuario['departamento']
        if dept not in por_departamento:
            por_departamento[dept] = []
        por_departamento[dept].append(usuario)
    
    print("\n👥 Usuários por Departamento:")
    print("=" * 80)
    
    for departamento in sorted(por_departamento.keys()):
        print(f"\n📁 {departamento.upper()}")
        print("-" * 40)
        
        for usuario in sorted(por_departamento[departamento], key=lambda x: x['perfil']):
            print(f"   👤 {usuario['username']:<20} | {usuario['nome']:<25} | {usuario['perfil']}")

def main():
    """Função principal"""
    print("👥 Setup de Usuários - Sistema de Compras")
    print("=" * 80)
    
    # Cria todos os usuários
    sucesso = create_all_users()
    
    if sucesso:
        print("\n✅ Todos os usuários foram criados com sucesso!")
        
        # Mostra organização por departamento
        show_users_by_department()
        
        print("\n🎯 Próximos passos:")
        print("   • Todos os usuários têm senha 'Teste123'")
        print("   • Faça login com qualquer usuário para testar")
        print("   • Recomenda-se alterar senhas após primeiro acesso")
        print("   • Execute 'python reset_all_passwords.py' se precisar resetar senhas")
        
    else:
        print("\n❌ Alguns erros ocorreram durante a criação dos usuários")
    
    return sucesso

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
