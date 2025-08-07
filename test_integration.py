#!/usr/bin/env python3
"""
Script de teste para verificar a integração com Snowflake Cortex Agents
"""

import sys
import json
from snowflake_cortex_client import SnowflakeCortexClient

def test_connection():
    """
    Testa a conexão com o Snowflake Cortex Agents
    """
    try:
        print("Testando conexão com Snowflake Cortex Agents...")
        
        # Inicializa o cliente
        client = SnowflakeCortexClient()
        print("✅ Cliente inicializado com sucesso")
        
        # Testa a geração de token
        token = client._generate_jwt_token()
        print(f"✅ Token JWT gerado com sucesso (primeiros 20 caracteres: {token[:20]}...)")
        
        # Testa uma requisição simples
        print("Testando requisição simples...")
        response = client.chat("Olá! Este é um teste de conexão.")
        print("✅ Requisição executada com sucesso")
        
        # Exibe informações da resposta
        if 'delta' in response and 'content' in response['delta']:
            print("📝 Resposta recebida:")
            for content in response['delta']['content']:
                if content.get('type') == 'text' and 'text' in content:
                    print(f"   {content['text']}")
                elif content.get('type') == 'tool_use':
                    print(f"   🔧 Ferramenta usada: {content['tool_use']['name']}")
        else:
            print("📝 Resposta completa:")
            print(response)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        return False

def main():
    """
    Função principal do teste
    """
    print("=" * 50)
    print("TESTE DE INTEGRAÇÃO SNOWFLAKE CORTEX AGENTS")
    print("=" * 50)
    
    success = test_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ TESTE CONCLUÍDO COM SUCESSO")
        print("A integração está funcionando corretamente!")
    else:
        print("❌ TESTE FALHOU")
        print("Verifique as configurações no arquivo dev.env")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 