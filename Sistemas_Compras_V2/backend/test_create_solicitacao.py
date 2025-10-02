#!/usr/bin/env python
"""
Script para testar a criação de uma nova solicitação de compras
"""

import os
import sys
import json
import requests

# URL base da API
BASE_URL = 'http://127.0.0.1:8000/api'

def login(username, password):
    """Login e obtenção do token JWT"""
    url = f"{BASE_URL}/usuarios/auth/login/"
    data = {
        'username': username,
        'password': password
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Erro no login: {response.status_code}")
        print(response.text)
        return None

def create_solicitacao(token, data):
    """Criar uma nova solicitação"""
    url = f"{BASE_URL}/solicitacoes/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Erro ao criar solicitação: {response.status_code}")
        print(response.text)
        return None

def main():
    """Função principal"""
    # Login como Leonardo.Fragoso (Solicitante)
    token = login('Leonardo.Fragoso', 'Teste123')
    if not token:
        print("Falha no login. Abortando.")
        return
    
    # Dados da nova solicitação
    solicitacao_data = {
        'departamento': 'TI',
        'prioridade': 'Normal',
        'descricao': 'Teste de criação de solicitação via API',
        'local_aplicacao': 'Sala de Reuniões',
        'observacoes': 'Teste automatizado',
        'valor_estimado': 150.00,
        'itens': [
            {
                'nome': 'Cabo HDMI',
                'quantidade': 5,
                'unidade': 'UN',
                'descricao': 'Cabo HDMI 2m'
            }
        ]
    }
    
    # Criar solicitação
    result = create_solicitacao(token, solicitacao_data)
    if result:
        print("Solicitação criada com sucesso!")
        print(json.dumps(result, indent=2))
    else:
        print("Falha ao criar solicitação.")

if __name__ == "__main__":
    main()
