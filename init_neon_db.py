import os
import sys
import argparse
from typing import Optional

# Use tomllib if Python >=3.11, otherwise try toml or fallback to a simple parser
try:
    import tomllib as toml_loader  # type: ignore
except Exception:  # pragma: no cover
    try:
        import toml as toml_loader  # type: ignore
    except Exception:
        toml_loader = None

import psycopg2


def load_url_from_secrets(secrets_path: str) -> Optional[str]:
    """Attempts to read postgres URL from a secrets.toml-like file.
    Supported keys: postgres_url, database_url, or a [postgres] table with connection parts.
    """
    if not os.path.exists(secrets_path):
        return None
    if toml_loader is None:
        # naive line parser fallback for simple 'key = "value"' cases
        try:
            with open(secrets_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'postgres_url' in line or 'database_url' in line:
                        # very simple parse: key = "value"
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            val = parts[1].strip().strip('"').strip("'")
                            if val:
                                return val
        except Exception:
            return None
        return None

    try:
        with open(secrets_path, 'rb') as f:
            data = toml_loader.load(f)
        # direct URL keys
        url = data.get('postgres_url') or data.get('database_url')
        if url:
            return str(url)
        # nested table [postgres]
        pg = data.get('postgres') or data.get('database')
        if isinstance(pg, dict) and 'host' in pg:
            host = pg.get('host')
            dbname = pg.get('database') or pg.get('name')
            user = pg.get('user')
            password = pg.get('password')
            port = pg.get('port', 5432)
            sslmode = pg.get('sslmode', 'require')
            if host and dbname and user and password:
                return f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
    except Exception:
        return None
    return None


def get_conn_url(cli_url: Optional[str], secrets_path: str) -> str:
    # Priority: CLI > env(DATABASE_URL/postgres_url) > secrets.toml
    if cli_url:
        return cli_url
    env_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    if env_url:
        return env_url
    sec_url = load_url_from_secrets(secrets_path)
    if sec_url:
        return sec_url
    raise RuntimeError(
        'Nenhuma URL de conexão encontrada. Informe --url, defina DATABASE_URL, ou configure secrets.toml.'
    )


def create_tables(conn) -> None:
    cur = conn.cursor()

    # usuarios
    cur.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        nome VARCHAR(100) NOT NULL,
        perfil VARCHAR(50) NOT NULL,
        departamento VARCHAR(50) NOT NULL,
        senha_hash VARCHAR(64) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # solicitacoes
    cur.execute('''
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
        anexos_requisicao TEXT,
        cotacoes TEXT,
        aprovacoes TEXT,
        historico_etapas TEXT,
        itens TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # configuracoes
    cur.execute('''
    CREATE TABLE IF NOT EXISTS configuracoes (
        id SERIAL PRIMARY KEY,
        chave TEXT UNIQUE NOT NULL,
        valor TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # catalogo_produtos
    cur.execute('''
    CREATE TABLE IF NOT EXISTS catalogo_produtos (
        id SERIAL PRIMARY KEY,
        codigo TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        categoria TEXT,
        unidade TEXT NOT NULL,
        ativo BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # movimentacoes
    cur.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id SERIAL PRIMARY KEY,
        numero_solicitacao INTEGER NOT NULL,
        etapa_origem TEXT NOT NULL,
        etapa_destino TEXT NOT NULL,
        usuario TEXT NOT NULL,
        data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        observacoes TEXT
    )
    ''')

    # notificacoes
    cur.execute('''
    CREATE TABLE IF NOT EXISTS notificacoes (
        id SERIAL PRIMARY KEY,
        perfil TEXT NOT NULL,
        numero INTEGER NOT NULL,
        mensagem TEXT NOT NULL,
        data TIMESTAMP NOT NULL,
        lida BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # sessoes
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sessoes (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()


def ensure_columns(conn) -> None:
    """Adds missing columns to existing tables (idempotent)."""
    cur = conn.cursor()
    # Only solicitacoes needs historical optional columns
    required_cols = [
        # keep all as nullable for safe migrations
        "numero_pedido_compras INTEGER",
        "etapa_atual TEXT",
        "data_numero_pedido TEXT",
        "data_cotacao TEXT",
        "data_entrega TEXT",
        "dias_atendimento INTEGER",
        "sla_cumprido TEXT",
        "observacoes TEXT",
        "numero_requisicao_interno TEXT",
        "data_requisicao_interna TEXT",
        "responsavel_suprimentos TEXT",
        "valor_estimado DOUBLE PRECISION",
        "valor_final DOUBLE PRECISION",
        "fornecedor_recomendado TEXT",
        "fornecedor_final TEXT",
        "anexos_requisicao TEXT",
        "cotacoes TEXT",
        "aprovacoes TEXT",
        "historico_etapas TEXT",
        "itens TEXT",
    ]
    for coldef in required_cols:
        cur.execute(f"ALTER TABLE IF EXISTS solicitacoes ADD COLUMN IF NOT EXISTS {coldef}")
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description='Inicializa as tabelas no banco Neon/PostgreSQL.')
    parser.add_argument('--url', help='postgresql://usuario:senha@host:porta/banco?sslmode=require')
    parser.add_argument('--secrets', default='secrets.toml', help='Caminho para secrets.toml (opcional)')
    args = parser.parse_args()

    try:
        url = get_conn_url(args.url, args.secrets)
        print(f'Conectando em: {url.split("@")[-1]}')
        conn = psycopg2.connect(url)
        try:
            create_tables(conn)
            ensure_columns(conn)
            print('Tabelas criadas/validadas com sucesso!')
        finally:
            conn.close()
    except Exception as e:
        print(f'Falha ao criar tabelas: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
