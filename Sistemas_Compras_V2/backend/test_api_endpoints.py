#!/usr/bin/env python
"""
Script para testar todos os endpoints da API Django V2 com dados V1
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')
django.setup()

def test_api_endpoints():
    """Testa todos os endpoints da API"""
    
    # Base URL for API
    base_url = "http://127.0.0.1:8000/api"
    
    print("🚀 Iniciando testes dos endpoints da API Django V2...")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        # Test endpoint
        {"url": f"{base_url}/usuarios/test/", "method": "GET", "name": "Test Endpoint"},
        
        # Usuarios endpoints
        {"url": f"{base_url}/usuarios/", "method": "GET", "name": "Lista Usuários"},
        
        # Solicitacoes endpoints
        {"url": f"{base_url}/solicitacoes/", "method": "GET", "name": "Lista Solicitações"},
        {"url": f"{base_url}/solicitacoes/dashboard/", "method": "GET", "name": "Dashboard Data"},
        
        # Catalog endpoints
        {"url": f"{base_url}/catalogo/", "method": "GET", "name": "Lista Catálogo"},
        
        # Configuracoes endpoints
        {"url": f"{base_url}/configuracoes/", "method": "GET", "name": "Lista Configurações"},
        
        # Auditoria endpoints
        {"url": f"{base_url}/auditoria/", "method": "GET", "name": "Lista Auditoria"},
        {"url": f"{base_url}/auditoria/statistics/", "method": "GET", "name": "Estatísticas Auditoria"},
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testando: {endpoint['name']}")
            print(f"   URL: {endpoint['url']}")
            
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], timeout=10)
            else:
                response = requests.post(endpoint['url'], timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if 'results' in data:
                            print(f"   ✅ Sucesso - {len(data['results'])} itens retornados")
                        elif 'count' in data:
                            print(f"   ✅ Sucesso - Dados: {data}")
                        else:
                            print(f"   ✅ Sucesso - Objeto retornado")
                    elif isinstance(data, list):
                        print(f"   ✅ Sucesso - {len(data)} itens retornados")
                    else:
                        print(f"   ✅ Sucesso - Dados retornados")
                    
                    results.append({"endpoint": endpoint['name'], "status": "SUCCESS", "code": response.status_code})
                except json.JSONDecodeError:
                    print(f"   ✅ Sucesso - Resposta não-JSON")
                    results.append({"endpoint": endpoint['name'], "status": "SUCCESS", "code": response.status_code})
            else:
                print(f"   ❌ Erro - Status {response.status_code}")
                print(f"   Resposta: {response.text[:200]}...")
                results.append({"endpoint": endpoint['name'], "status": "ERROR", "code": response.status_code})
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Erro de Conexão - Servidor Django não está rodando?")
            results.append({"endpoint": endpoint['name'], "status": "CONNECTION_ERROR", "code": None})
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results.append({"endpoint": endpoint['name'], "status": "EXCEPTION", "code": None})
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    success_count = len([r for r in results if r['status'] == 'SUCCESS'])
    total_count = len(results)
    
    print(f"✅ Sucessos: {success_count}/{total_count}")
    print(f"❌ Falhas: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 TODOS OS ENDPOINTS FUNCIONANDO PERFEITAMENTE!")
        print("✅ Django V2 backend está pronto para uso com dados V1")
    else:
        print("\n⚠️  ALGUNS ENDPOINTS COM PROBLEMAS")
        print("Verifique se o servidor Django está rodando: python manage.py runserver")
    
    return results

if __name__ == "__main__":
    test_api_endpoints()
