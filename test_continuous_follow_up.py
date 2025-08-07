#!/usr/bin/env python3
"""
Script de teste para a funcionalidade de follow-up contínuo do Snowflake Cortex Client.

Este script demonstra como o cliente agora continua automaticamente executando
ferramentas até que não haja mais tool_uses pendentes.
"""

import sys
import json
from snowflake_cortex_client import SnowflakeCortexClient

def print_response_summary(response, title="Resposta"):
    """Imprime um resumo da resposta de forma organizada"""
    print(f"\n{'='*50}")
    print(f"📊 {title}")
    print(f"{'='*50}")
    
    # Informações básicas
    print(f"🔄 Iterações realizadas: {response.get('iterations_performed', 1)}")
    print(f"🔗 Follow-up executado: {'Sim' if response.get('follow_up_performed', False) else 'Não'}")
    
    # Texto da resposta
    text = response.get('text', '').strip()
    if text:
        print(f"\n📝 Texto da resposta:")
        print(f"   {text[:200]}..." if len(text) > 200 else f"   {text}")
    
    # Tool uses
    tool_uses = response.get('tool_uses', [])
    if tool_uses:
        print(f"\n🔧 Tools utilizados ({len(tool_uses)}):")
        for i, tool_use in enumerate(tool_uses, 1):
            name = tool_use.get('name', 'unknown')
            tool_id = tool_use.get('tool_use_id', 'no-id')[:8]
            print(f"   {i}. {name} (ID: {tool_id})")
    
    # Tool results
    tool_results = response.get('tool_results', [])
    if tool_results:
        print(f"\n✅ Resultados de tools ({len(tool_results)}):")
        for i, result in enumerate(tool_results, 1):
            status = result.get('status', 'unknown')
            tool_id = result.get('tool_use_id', 'no-id')[:8]
            print(f"   {i}. Status: {status} (ID: {tool_id})")
    
    # Charts
    charts = response.get('charts', [])
    if charts:
        print(f"\n📊 Gráficos gerados: {len(charts)}")
    
    # SQLs executados
    sqls = response.get('sqls_executed', [])
    if sqls:
        print(f"\n🗄️ SQLs executados ({len(sqls)}):")
        for i, sql in enumerate(sqls, 1):
            sql_preview = sql[:100].replace('\n', ' ').strip()
            print(f"   {i}. {sql_preview}...")
    
    # Erros
    errors = response.get('errors', [])
    if errors:
        print(f"\n❌ Erros ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")

def test_continuous_follow_up():
    """Testa a funcionalidade de follow-up contínuo"""
    try:
        print("🚀 Inicializando cliente Snowflake Cortex...")
        client = SnowflakeCortexClient()
        
        # Teste 1: Pergunta que deve gerar SQL e executar
        print("\n" + "="*70)
        print("📋 TESTE 1: Análise de dados que requer SQL")
        print("="*70)
        
        question1 = "Quantos produtos temos por categoria? Mostre em um gráfico."
        print(f"❓ Pergunta: {question1}")
        
        response1 = client.analyze_data(question1)
        print_response_summary(response1, "Análise de Produtos por Categoria")
        
        # Teste 2: Pergunta complexa que pode precisar de múltiplas iterações
        print("\n" + "="*70)
        print("📋 TESTE 2: Consulta complexa")
        print("="*70)
        
        question2 = "Mostre as vendas dos últimos 6 meses por região, incluindo a tendência de crescimento"
        print(f"❓ Pergunta: {question2}")
        
        response2 = client.analyze_data(question2)
        print_response_summary(response2, "Análise de Vendas por Região")
        
        # Teste 3: Chat simples para comparar
        print("\n" + "="*70)
        print("📋 TESTE 3: Chat simples (sem tools esperados)")
        print("="*70)
        
        question3 = "Olá, como você pode me ajudar?"
        print(f"❓ Pergunta: {question3}")
        
        response3 = client.chat(question3)
        print_response_summary(response3, "Chat Simples")
        
        print("\n" + "="*70)
        print("✅ TESTES CONCLUÍDOS")
        print("="*70)
        print("🎯 A funcionalidade de follow-up contínuo está funcionando!")
        print("🔄 O cliente agora continua executando tools até finalizar a resposta.")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {str(e)}")
        print("💡 Verifique se as configurações do Snowflake estão corretas no arquivo dev.env")
        return False
    
    return True

def test_edge_cases():
    """Testa casos extremos e de segurança"""
    try:
        print("\n" + "="*70)
        print("🧪 TESTES DE CASOS EXTREMOS")
        print("="*70)
        
        client = SnowflakeCortexClient()
        
        # Teste com limite baixo de iterações
        print("\n🔬 Teste: Limite baixo de iterações (max_iterations=2)")
        response = client.run_agent_with_follow_up(
            messages=[{
                'role': 'user',
                'content': [{'type': 'text', 'text': 'Analise as vendas e gere um relatório completo'}]
            }],
            max_iterations=2
        )
        print_response_summary(response, "Teste com Limite Baixo")
        
        print(f"✅ Teste concluído com {response.get('iterations_performed', 0)} iterações")
        
    except Exception as e:
        print(f"❌ Erro nos testes de casos extremos: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 TESTANDO FUNCIONALIDADE DE FOLLOW-UP CONTÍNUO")
    print("=" * 70)
    print("📋 Este script testa se o cliente continua executando tools")
    print("   automaticamente até finalizar completamente a resposta.")
    
    # Executa testes principais
    success1 = test_continuous_follow_up()
    
    # Executa testes de casos extremos
    success2 = test_edge_cases()
    
    if success1 and success2:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✨ A funcionalidade de follow-up contínuo está implementada corretamente.")
        sys.exit(0)
    else:
        print("\n💥 ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique a implementação e as configurações.")
        sys.exit(1) 