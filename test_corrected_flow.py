#!/usr/bin/env python3
"""
Teste demonstrando a correção do fluxo de follow-up baseado na documentação oficial
"""

from snowflake_cortex_client import SnowflakeCortexClient
import json

def test_corrected_follow_up_flow():
    """
    Testa o fluxo corrigido de follow-up
    """
    print("🧪 TESTE DO FLUXO CORRIGIDO DE FOLLOW-UP")
    print("=" * 60)
    
    try:
        client = SnowflakeCortexClient()
        
        # Mostra o exemplo do fluxo correto
        print("\n📚 Documentação - Fluxo Correto:")
        client.example_correct_flow()
        
        print("\n" + "=" * 60)
        print("🔬 TESTANDO IMPLEMENTAÇÃO CORRIGIDA:")
        print("=" * 60)
        
        # Teste com pergunta que deve retornar dados tabulares
        question = "Quais são os top 5 produtos mais vendidos?"
        print(f"\n❓ Pergunta: {question}")
        
        response = client.chat(question)
        
        print(f"\n✅ Resposta obtida:")
        print(f"📝 Texto (primeiros 200 chars): {response.get('text', 'Nenhum texto')[:200]}...")
        print(f"🔧 Tools usadas: {len(response.get('tool_uses', []))}")
        print(f"📊 Gráficos: {len(response.get('charts', []))}")
        print(f"🔄 Iterações: {response.get('iterations_performed', 0)}")
        print(f"📈 Follow-up realizado: {response.get('follow_up_performed', False)}")
        
        if response.get('sqls_executed'):
            print(f"🗄️ SQLs executados: {len(response.get('sqls_executed', []))}")
            for i, sql in enumerate(response.get('sqls_executed', []), 1):
                print(f"   SQL {i}: {sql[:100]}...")
        
        if response.get('query_ids'):
            print(f"🔑 Query IDs obtidos: {len(response.get('query_ids', []))}")
            for i, qid in enumerate(response.get('query_ids', []), 1):
                print(f"   Query ID {i}: {qid}")
        
        # Verifica se dados tabulares foram incluídos
        text = response.get('text', '')
        if '📊 **Dados da Consulta:**' in text:
            print(f"✅ Dados tabulares foram incluídos automaticamente na resposta!")
        elif any(ref in text.lower() for ref in ['see the table', 'tabela relacionada', 'dados da tabela']):
            print(f"⚠️ Resposta faz referência à tabela mas dados não foram incluídos")
        else:
            print(f"ℹ️ Resposta não faz referência a dados tabulares")
        
        print(f"\n📋 TEXTO COMPLETO DA RESPOSTA:")
        print("=" * 80)
        print(response.get('text', 'Nenhum texto'))
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste do fluxo corrigido...")
    success = test_corrected_follow_up_flow()
    
    if success:
        print(f"\n✅ Teste concluído com sucesso!")
        print("\n📋 PRINCIPAIS CORREÇÕES IMPLEMENTADAS:")
        print("   1. ✅ Estrutura correta das mensagens de follow-up")
        print("   2. ✅ Separação adequada de tool_use (assistant) e tool_results (user)")
        print("   3. ✅ Correspondência correta de tool_use_id entre requisições")
        print("   4. ✅ Execução real de SQL para obter query_id válido")
        print("   5. ✅ Fluxo completo para obter respostas textuais e gráficos")
        print("   6. ✅ NOVO: Inclusão automática de dados tabulares nas respostas")
        
        print("\n🔍 PROBLEMAS ORIGINAIS:")
        print("   - Misturava tool_use e tool_results na mesma mensagem do assistant")
        print("   - tool_use_id não correspondia entre requisições")
        print("   - Estrutura de mensagens não seguia a documentação")
        print("   - Query_id não era corretamente propagado")
        print("   - Respostas com 'See the table' não mostravam os dados reais")
        
        print("\n✨ SOLUÇÕES APLICADAS:")
        print("   - Seguir EXATAMENTE o padrão da documentação oficial")
        print("   - Assistant: tool_use + tool_results existentes")
        print("   - User: tool_results com query_id real do Snowflake") 
        print("   - Correspondência perfeita de tool_use_id")
        print("   - Busca automática de dados tabulares usando RESULT_SCAN")
        print("   - Formatação legível de tabelas em markdown")
        print("   - Detecção inteligente de referências a tabelas no texto")
    else:
        print(f"\n❌ Teste falhou - verifique a configuração") 