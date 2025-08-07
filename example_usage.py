#!/usr/bin/env python3
"""
Exemplo de uso da integração com Snowflake Cortex Agents REST API
"""

from snowflake_cortex_client import SnowflakeCortexClient
import json

def main():
    """
    Exemplo principal de uso da integração
    """
    try:
        # Inicializa o cliente
        print("Inicializando cliente Snowflake Cortex...")
        client = SnowflakeCortexClient()
        print("Cliente inicializado com sucesso!")
        
        # Exemplo 1: Chat simples
        print("\n=== Exemplo 1: Chat simples ===")
        response = client.chat("Olá! Como você pode me ajudar hoje?")
        print("Resposta do agente:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # Exemplo 2: Análise de dados
        print("\n=== Exemplo 2: Análise de dados ===")
        analysis_response = client.analyze_data("Quais são os top 3 clientes por receita?")
        print("Análise de dados:")
        print(json.dumps(analysis_response, indent=2, ensure_ascii=False))
        
        # Exemplo 3: Execução de SQL
        print("\n=== Exemplo 3: Execução de SQL ===")
        sql_response = client.execute_sql_query("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES")
        print("Execução SQL:")
        print(json.dumps(sql_response, indent=2, ensure_ascii=False))
        
        # Exemplo 4: Conversa com histórico
        print("\n=== Exemplo 4: Conversa com histórico ===")
        conversation_history = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Me diga sobre o banco de dados"
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Posso ajudá-lo com informações sobre o banco de dados. Que tipo de informação você gostaria de saber?"
                    }
                ]
            }
        ]
        
        follow_up_response = client.chat("Quais tabelas existem?", conversation_history)
        print("Resposta com histórico:")
        print(json.dumps(follow_up_response, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Erro durante a execução: {str(e)}")

if __name__ == "__main__":
    main() 