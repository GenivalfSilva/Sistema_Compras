#!/usr/bin/env python
"""
Script para copiar o banco V1 para o diretório V2
"""
import shutil
import os

def copy_v1_database():
    """Copia o banco V1 para o diretório V2"""
    
    # Caminhos
    v1_db_path = r"c:\Users\leonardo.fragoso\Desktop\Projetos\Sistema_Compras\Sistemas_Compras_V1\sistema_compras.db"
    v2_db_path = r"c:\Users\leonardo.fragoso\Desktop\Projetos\Sistema_Compras\Sistemas_Compras_V2\backend\db\sistema_compras_v1.db"
    
    # Verifica se o banco V1 existe
    if not os.path.exists(v1_db_path):
        print(f"❌ Banco V1 não encontrado: {v1_db_path}")
        return False
    
    # Cria diretório db se não existir
    db_dir = os.path.dirname(v2_db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    try:
        # Copia o arquivo
        shutil.copy2(v1_db_path, v2_db_path)
        print(f"✅ Banco V1 copiado com sucesso!")
        print(f"   Origem: {v1_db_path}")
        print(f"   Destino: {v2_db_path}")
        
        # Verifica o tamanho do arquivo
        size = os.path.getsize(v2_db_path)
        print(f"   Tamanho: {size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao copiar banco: {e}")
        return False

if __name__ == '__main__':
    copy_v1_database()
