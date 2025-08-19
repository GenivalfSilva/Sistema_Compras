#!/usr/bin/env python3
"""
Script para criar e atualizar todas as tabelas do Sistema de Compras no Neon DB.
Este script garante que todas as tabelas estejam atualizadas com o schema mais recente.

Uso:
    python setup_neon_db.py

Requisitos:
    - psycopg2-binary
    - Variáveis de ambiente ou arquivo secrets.toml configurado
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import Dict, Any
import datetime

class NeonDBSetup:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Conecta ao banco Neon usando diferentes métodos de configuração"""
        connection_configs = [
            self._get_secrets_toml_config(),
            self._get_env_config(),
            self._get_streamlit_secrets_config()
        ]
        
        for config in connection_configs:
            if config:
                try:
                    print(f"Tentando conectar ao Neon DB...")
                    self.conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
                    self.cursor = self.conn.cursor()
                    print("✅ Conexão estabelecida com sucesso!")
                    return True
                except Exception as e:
                    print(f"❌ Falha na conexão: {e}")
                    continue
        
        print("❌ Não foi possível conectar ao banco. Verifique as configurações.")
        return False
    
    def _get_secrets_toml_config(self) -> Dict[str, Any]:
        """Tenta ler configuração do secrets.toml"""
        try:
            import toml
            if os.path.exists("secrets.toml"):
                secrets = toml.load("secrets.toml")
                if "postgres" in secrets:
                    pg = secrets["postgres"]
                    return {
                        "host": pg["host"],
                        "database": pg.get("database") or pg.get("name"),
                        "user": pg["user"],
                        "password": pg["password"],
                        "port": int(pg.get("port", 5432)),
                        "sslmode": pg.get("sslmode", "require")
                    }
        except Exception:
            pass
        return None
    
    def _get_env_config(self) -> Dict[str, Any]:
        """Tenta ler configuração das variáveis de ambiente"""
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return {"dsn": database_url}
        
        # Configuração individual por variáveis
        host = os.getenv("POSTGRES_HOST")
        if host:
            return {
                "host": host,
                "database": os.getenv("POSTGRES_DATABASE") or os.getenv("POSTGRES_DB"),
                "user": os.getenv("POSTGRES_USER"),
                "password": os.getenv("POSTGRES_PASSWORD"),
                "port": int(os.getenv("POSTGRES_PORT", 5432)),
                "sslmode": os.getenv("POSTGRES_SSLMODE", "require")
            }
        return None
    
    def _get_streamlit_secrets_config(self) -> Dict[str, Any]:
        """Tenta ler configuração do Streamlit secrets (se disponível)"""
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                if "postgres" in st.secrets:
                    pg = st.secrets["postgres"]
                    return {
                        "host": pg["host"],
                        "database": pg.get("database") or pg.get("name"),
                        "user": pg["user"],
                        "password": pg["password"],
                        "port": int(pg.get("port", 5432)),
                        "sslmode": pg.get("sslmode", "require")
                    }
        except Exception:
            pass
        return None
    
    def create_all_tables(self):
        """Cria todas as tabelas necessárias para o sistema"""
        print("\n🔧 Criando tabelas...")
        
        tables = [
            ("usuarios", self._create_usuarios_table),
            ("solicitacoes", self._create_solicitacoes_table),
            ("configuracoes", self._create_configuracoes_table),
            ("catalogo_produtos", self._create_catalogo_produtos_table),
            ("movimentacoes", self._create_movimentacoes_table),
            ("notificacoes", self._create_notificacoes_table),
            ("sessoes", self._create_sessoes_table)
        ]
        
        for table_name, create_func in tables:
            try:
                create_func()
                print(f"✅ Tabela '{table_name}' criada/atualizada")
            except Exception as e:
                print(f"❌ Erro ao criar tabela '{table_name}': {e}")
                return False
        
        self.conn.commit()
        print("✅ Todas as tabelas foram criadas com sucesso!")
        return True
    
    def _create_usuarios_table(self):
        """Cria tabela de usuários"""
        sql = '''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            nome VARCHAR(100) NOT NULL,
            perfil VARCHAR(50) NOT NULL,
            departamento VARCHAR(50) NOT NULL,
            senha_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.cursor.execute(sql)
    
    def _create_solicitacoes_table(self):
        """Cria tabela de solicitações com todos os campos necessários"""
        sql = '''
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id SERIAL PRIMARY KEY,
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
            valor_estimado DOUBLE PRECISION,
            valor_final DOUBLE PRECISION,
            fornecedor_recomendado TEXT,
            fornecedor_final TEXT,
            anexos_requisicao TEXT,  -- JSON string
            cotacoes TEXT,  -- JSON string
            aprovacoes TEXT,  -- JSON string
            historico_etapas TEXT,  -- JSON string
            itens TEXT,  -- JSON string
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.cursor.execute(sql)
    
    def _create_configuracoes_table(self):
        """Cria tabela de configurações"""
        sql = '''
        CREATE TABLE IF NOT EXISTS configuracoes (
            id SERIAL PRIMARY KEY,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.cursor.execute(sql)
    
    def _create_catalogo_produtos_table(self):
        """Cria tabela de catálogo de produtos"""
        sql = '''
        CREATE TABLE IF NOT EXISTS catalogo_produtos (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT,
            unidade TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.cursor.execute(sql)
    
    def _create_movimentacoes_table(self):
        """Cria tabela de movimentações (histórico de mudanças)"""
        sql = '''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id SERIAL PRIMARY KEY,
            numero_solicitacao INTEGER NOT NULL,
            etapa_origem TEXT NOT NULL,
            etapa_destino TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observacoes TEXT
        )
        '''
        self.cursor.execute(sql)
    
    def _create_notificacoes_table(self):
        """Cria tabela de notificações"""
        sql = '''
        CREATE TABLE IF NOT EXISTS notificacoes (
            id SERIAL PRIMARY KEY,
            perfil TEXT NOT NULL,
            numero INTEGER NOT NULL,
            mensagem TEXT NOT NULL,
            data TIMESTAMP NOT NULL,
            lida BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.cursor.execute(sql)
    
    def _create_sessoes_table(self):
        """Cria tabela de sessões (para persistência de login)"""
        sql = '''
        CREATE TABLE IF NOT EXISTS sessoes (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.cursor.execute(sql)
    
    def add_missing_columns(self):
        """Adiciona colunas que podem estar faltando em tabelas existentes"""
        print("\n🔧 Verificando e adicionando colunas faltantes...")
        
        # Verifica colunas da tabela solicitacoes
        missing_columns = [
            ("solicitacoes", "numero_pedido_compras", "INTEGER"),
            ("solicitacoes", "etapa_atual", "TEXT"),
            ("solicitacoes", "data_numero_pedido", "TEXT"),
            ("solicitacoes", "data_cotacao", "TEXT"),
            ("solicitacoes", "data_entrega", "TEXT"),
            ("solicitacoes", "dias_atendimento", "INTEGER"),
            ("solicitacoes", "sla_cumprido", "TEXT"),
            ("solicitacoes", "observacoes", "TEXT"),
            ("solicitacoes", "numero_requisicao_interno", "TEXT"),
            ("solicitacoes", "data_requisicao_interna", "TEXT"),
            ("solicitacoes", "responsavel_suprimentos", "TEXT"),
            ("solicitacoes", "valor_estimado", "DOUBLE PRECISION"),
            ("solicitacoes", "valor_final", "DOUBLE PRECISION"),
            ("solicitacoes", "fornecedor_recomendado", "TEXT"),
            ("solicitacoes", "fornecedor_final", "TEXT"),
            ("solicitacoes", "anexos_requisicao", "TEXT"),
            ("solicitacoes", "cotacoes", "TEXT"),
            ("solicitacoes", "aprovacoes", "TEXT"),
            ("solicitacoes", "historico_etapas", "TEXT"),
            ("solicitacoes", "itens", "TEXT"),
        ]
        
        for table, column, data_type in missing_columns:
            self._add_column_if_not_exists(table, column, data_type)
        
        self.conn.commit()
        print("✅ Verificação de colunas concluída!")
    
    def _add_column_if_not_exists(self, table: str, column: str, data_type: str):
        """Adiciona coluna se ela não existir"""
        try:
            # Verifica se a coluna existe
            self.cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, (table, column))
            
            if not self.cursor.fetchone():
                # Coluna não existe, adiciona
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {data_type}"
                self.cursor.execute(sql)
                print(f"  ➕ Adicionada coluna '{column}' na tabela '{table}'")
        except Exception as e:
            print(f"  ⚠️ Erro ao adicionar coluna '{column}' em '{table}': {e}")
    
    def create_indexes(self):
        """Cria índices para melhorar performance"""
        print("\n🔧 Criando índices...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_numero ON solicitacoes(numero_solicitacao_estoque)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_etapa ON solicitacoes(etapa_atual)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_departamento ON solicitacoes(departamento)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_prioridade ON solicitacoes(prioridade)",
            "CREATE INDEX IF NOT EXISTS idx_movimentacoes_numero ON movimentacoes(numero_solicitacao)",
            "CREATE INDEX IF NOT EXISTS idx_notificacoes_perfil ON notificacoes(perfil)",
            "CREATE INDEX IF NOT EXISTS idx_sessoes_expires ON sessoes(expires_at)",
        ]
        
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
                print(f"  ✅ Índice criado")
            except Exception as e:
                print(f"  ⚠️ Erro ao criar índice: {e}")
        
        self.conn.commit()
        print("✅ Índices criados!")
    
    def insert_default_data(self):
        """Insere dados padrão se necessário"""
        print("\n🔧 Inserindo dados padrão...")
        
        # Verifica se já existe usuário admin
        self.cursor.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = 'Admin'")
        admin_count = self.cursor.fetchone()[0]
        
        if admin_count == 0:
            # Cria usuário admin padrão
            import hashlib
            SALT = "ziran_local_salt_v1"
            senha_hash = hashlib.sha256((SALT + "admin123").encode("utf-8")).hexdigest()
            
            self.cursor.execute("""
                INSERT INTO usuarios (username, nome, perfil, departamento, senha_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, ("admin", "Administrador", "Admin", "TI", senha_hash))
            print("  ➕ Usuário admin criado (login: admin, senha: admin123)")
        
        # Insere catálogo padrão se vazio
        self.cursor.execute("SELECT COUNT(*) FROM catalogo_produtos")
        produto_count = self.cursor.fetchone()[0]
        
        if produto_count == 0:
            produtos_padrao = [
                ("PRD-001", "Cabo de Rede Cat6", "TI", "UN", True),
                ("PRD-002", "Notebook 14\"", "TI", "UN", True),
                ("PRD-003", "Tinta Látex Branca", "Manutenção", "L", True),
                ("PRD-004", "Parafuso 5mm", "Manutenção", "CX", True),
                ("PRD-005", "Papel A4 75g", "Escritório", "CX", True),
            ]
            
            for codigo, nome, categoria, unidade, ativo in produtos_padrao:
                self.cursor.execute("""
                    INSERT INTO catalogo_produtos (codigo, nome, categoria, unidade, ativo)
                    VALUES (%s, %s, %s, %s, %s)
                """, (codigo, nome, categoria, unidade, ativo))
            print("  ➕ Catálogo padrão de produtos inserido")
        
        # Insere configurações padrão
        configs_padrao = [
            ("proximo_numero_solicitacao", "1"),
            ("proximo_numero_pedido", "1"),
            ("limite_gerencia", "5000.0"),
            ("limite_diretoria", "15000.0"),
            ("upload_dir", "uploads"),
            ("suprimentos_min_cotacoes", "1"),
            ("suprimentos_anexo_obrigatorio", "true"),
        ]
        
        for chave, valor in configs_padrao:
            self.cursor.execute("""
                INSERT INTO configuracoes (chave, valor) 
                VALUES (%s, %s) 
                ON CONFLICT (chave) DO NOTHING
            """, (chave, valor))
        
        self.conn.commit()
        print("✅ Dados padrão inseridos!")
    
    def verify_setup(self):
        """Verifica se o setup foi realizado corretamente"""
        print("\n🔍 Verificando setup...")
        
        tables_to_check = [
            "usuarios", "solicitacoes", "configuracoes", 
            "catalogo_produtos", "movimentacoes", "notificacoes", "sessoes"
        ]
        
        for table in tables_to_check:
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                print(f"  ✅ Tabela '{table}': {count} registros")
            except Exception as e:
                print(f"  ❌ Erro na tabela '{table}': {e}")
                return False
        
        print("✅ Verificação concluída com sucesso!")
        return True
    
    def close(self):
        """Fecha conexão com o banco"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("🔌 Conexão fechada")

def main():
    """Função principal"""
    print("🚀 Iniciando setup do Neon DB para Sistema de Compras")
    print("=" * 60)
    
    setup = NeonDBSetup()
    
    try:
        # Conecta ao banco
        if not setup.connect():
            return 1
        
        # Executa setup completo
        if not setup.create_all_tables():
            return 1
        
        setup.add_missing_columns()
        setup.create_indexes()
        setup.insert_default_data()
        
        if not setup.verify_setup():
            return 1
        
        print("\n" + "=" * 60)
        print("🎉 Setup do Neon DB concluído com sucesso!")
        print("📋 O sistema está pronto para uso.")
        print("\n📝 Próximos passos:")
        print("   1. Execute o app.py para testar a conexão")
        print("   2. Faça login com: admin / admin123")
        print("   3. Configure usuários adicionais se necessário")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrompido pelo usuário")
        return 1
    except Exception as e:
        print(f"\n❌ Erro durante o setup: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        setup.close()

if __name__ == "__main__":
    sys.exit(main())
