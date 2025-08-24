#!/usr/bin/env python3
"""
Script para configurar SQLite local como solução imediata
"""

import sqlite3
import hashlib
import os
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash da senha usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_sqlite_database():
    """Configura banco SQLite local com todos os usuários"""
    
    db_path = "compras_sla.db"
    
    print("📋 Criando banco SQLite local...")
    
    # Remove banco antigo se existir
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Banco antigo removido")
    
    # Conecta e cria tabelas
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            perfil TEXT NOT NULL DEFAULT 'Solicitante',
            departamento TEXT NOT NULL DEFAULT 'Outro',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de solicitações (schema completo)
    cursor.execute('''
        CREATE TABLE solicitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_solicitacao_estoque INTEGER UNIQUE NOT NULL,
            numero_pedido_compras INTEGER,
            solicitante TEXT NOT NULL,
            departamento TEXT NOT NULL,
            descricao TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            local_aplicacao TEXT NOT NULL,
            status TEXT NOT NULL,
            etapa_atual TEXT NOT NULL,
            carimbo_data_hora TEXT NOT NULL,
            data_numero_pedido TEXT,
            data_cotacao TEXT,
            data_entrega TEXT,
            sla_dias INTEGER NOT NULL,
            dias_atendimento INTEGER,
            sla_cumprido TEXT,
            observacoes TEXT,
            numero_requisicao_interno TEXT,
            data_requisicao_interna TEXT,
            responsavel_suprimentos TEXT,
            valor_estimado REAL,
            valor_final REAL,
            fornecedor_recomendado TEXT,
            fornecedor_final TEXT,
            anexos_requisicao TEXT,
            cotacoes TEXT,
            aprovacoes TEXT,
            historico_etapas TEXT,
            itens TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_entrega_prevista DATE,
            data_entrega_real DATE,
            entrega_conforme TEXT,
            nota_fiscal TEXT,
            responsavel_recebimento TEXT,
            observacoes_entrega TEXT,
            observacoes_finalizacao TEXT,
            data_finalizacao TIMESTAMP,
            tipo_solicitacao TEXT,
            justificativa TEXT
        )
    ''')
    
    # Tabela de configurações
    cursor.execute('''
        CREATE TABLE configuracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de catálogo de produtos
    cursor.execute('''
        CREATE TABLE catalogo_produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
            unidade TEXT NOT NULL DEFAULT 'UN',
            preco_referencia REAL,
            categoria TEXT,
            ativo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("✅ Tabelas criadas!")
    
    # Insere usuários padrão
    print("👥 Inserindo usuários...")
    usuarios = [
        ('admin', hash_password('admin123'), 'Administrador', 'Admin', 'TI'),
        ('Leonardo.Fragoso', hash_password('Teste123'), 'Leonardo Fragoso', 'Solicitante', 'TI'),
        ('Genival.Silva', hash_password('Teste123'), 'Genival Silva', 'Solicitante', 'Operações'),
        ('Diretoria', hash_password('Teste123'), 'Diretoria', 'Gerência&Diretoria', 'Diretoria'),
        ('Fabio.Ramos', hash_password('Teste123'), 'Fábio Ramos', 'Suprimentos', 'Suprimentos')
    ]
    
    for username, senha_hash, nome, perfil, departamento in usuarios:
        cursor.execute('''
            INSERT INTO usuarios (username, senha_hash, nome, perfil, departamento)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, senha_hash, nome, perfil, departamento))
    
    # Insere configurações padrão
    print("⚙️ Inserindo configurações...")
    configuracoes = [
        ('sistema_nome', 'Sistema de Gestão de Compras - SLA'),
        ('sla_urgente', '1'),
        ('sla_alta', '2'),
        ('sla_normal', '3'),
        ('sla_baixa', '5')
    ]
    
    for chave, valor in configuracoes:
        cursor.execute('''
            INSERT INTO configuracoes (chave, valor)
            VALUES (?, ?)
        ''', (chave, valor))
    
    # Insere produtos padrão
    print("📦 Inserindo catálogo de produtos...")
    produtos = [
        ('CANETA-001', 'Caneta Esferográfica Azul', 'Caneta esferográfica ponta média', 'UN', 2.50, 'Material de Escritório'),
        ('PAPEL-A4', 'Papel A4 75g Resma 500 folhas', 'Papel sulfite branco A4', 'PC', 25.00, 'Material de Escritório'),
        ('TONER-HP', 'Toner HP LaserJet Preto', 'Cartucho de toner original HP', 'UN', 180.00, 'Suprimentos TI'),
        ('CABO-REDE', 'Cabo de Rede Cat6 3m', 'Cabo ethernet categoria 6', 'UN', 15.00, 'Suprimentos TI'),
        ('MOUSE-USB', 'Mouse Óptico USB', 'Mouse óptico com scroll', 'UN', 35.00, 'Equipamentos TI')
    ]
    
    for codigo, nome, descricao, unidade, preco, categoria in produtos:
        cursor.execute('''
            INSERT INTO catalogo_produtos (codigo, nome, descricao, unidade, preco_referencia, categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (codigo, nome, descricao, unidade, preco, categoria))
    
    conn.commit()
    conn.close()
    
    print("🎉 Banco SQLite configurado com sucesso!")
    print(f"📁 Arquivo: {os.path.abspath(db_path)}")
    
    return True

def test_authentication():
    """Testa autenticação no banco local"""
    
    print("\n🔐 Testando autenticação...")
    
    conn = sqlite3.connect("compras_sla.db")
    cursor = conn.cursor()
    
    # Testa login do admin
    test_password = hash_password('admin123')
    cursor.execute('''
        SELECT username, nome, perfil FROM usuarios 
        WHERE username = ? AND senha_hash = ?
    ''', ('admin', test_password))
    
    result = cursor.fetchone()
    if result:
        print(f"✅ Login funcionando: {result[1]} ({result[2]})")
    else:
        print("❌ Erro no login")
        return False
    
    # Conta total de usuários
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    total_users = cursor.fetchone()[0]
    print(f"👥 Total de usuários: {total_users}")
    
    conn.close()
    return True

def main():
    print("🚀 Configuração SQLite Local")
    print("=" * 50)
    
    if setup_sqlite_database():
        if test_authentication():
            print("\n🎯 Sistema pronto para uso!")
            print("\n📋 Credenciais de acesso:")
            print("  👤 admin / admin123 (Administrador)")
            print("  👤 Leonardo.Fragoso / Teste123")
            print("  👤 Genival.Silva / Teste123")
            print("  👤 Diretoria / Teste123")
            print("  👤 Fabio.Ramos / Teste123")
            print("\n✅ Execute: streamlit run app.py")
            print("\n💡 O sistema usará SQLite local (sem problemas de quota)")
        else:
            print("\n❌ Erro na configuração")
    else:
        print("\n❌ Falha na criação do banco")

if __name__ == "__main__":
    main()
