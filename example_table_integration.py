#!/usr/bin/env python3
"""
Exemplo demonstrando a nova funcionalidade de inclusão automática de dados tabulares
quando o Cortex Agent retorna "See the table with the related data"
"""

from snowflake_cortex_client import SnowflakeCortexClient

def example_table_integration():
    """
    Demonstra como dados tabulares são automaticamente incluídos na resposta
    """
    print("🧪 EXEMPLO: INTEGRAÇÃO AUTOMÁTICA DE DADOS TABULARES")
    print("=" * 70)
    
    try:
        client = SnowflakeCortexClient()
        
        # Exemplos de perguntas que tipicamente retornam dados tabulares
        sample_questions = [
            "Quais são os top 10 clientes por receita?",
            "Mostre os produtos mais vendidos por categoria",
            "Liste as vendas por região nos últimos 6 meses",
            "Quais funcionários têm melhor performance?",
            "Mostre o faturamento mensal do último ano"
        ]
        
        print("📋 Perguntas que tipicamente referenciam tabelas:")
        for i, q in enumerate(sample_questions, 1):
            print(f"   {i}. {q}")
        
        print(f"\n" + "=" * 70)
        print("🔬 TESTANDO COM PERGUNTA SAMPLE...")
        
        # Testa com primeira pergunta
        question = sample_questions[0]
        print(f"\n❓ Pergunta: {question}")
        
        response = client.chat(question)
        
        print(f"\n📊 ANÁLISE DA RESPOSTA:")
        print("-" * 50)
        
        text = response.get('text', '')
        
        # Analisa tipo de resposta
        if '📊 **Dados da Consulta:**' in text:
            print("✅ SUCESSO: Dados tabulares incluídos automaticamente!")
            
            # Conta linhas da tabela
            lines = text.split('\n')
            table_lines = [line for line in lines if line.startswith('|') and not line.startswith('|---')]
            if table_lines:
                print(f"📈 Tabela contém aproximadamente {len(table_lines)-1} linhas de dados")
            
        elif any(ref in text.lower() for ref in ['see the table', 'tabela relacionada', 'dados da tabela', 'table with the related data']):
            print("⚠️ PROBLEMA: Resposta referencia tabela mas dados não foram incluídos")
            print("🔍 Frases encontradas que referenciam tabela:")
            for ref in ['see the table', 'tabela relacionada', 'dados da tabela', 'table with the related data']:
                if ref in text.lower():
                    print(f"   - '{ref}'")
        else:
            print("ℹ️ Resposta não faz referência direta a dados tabulares")
        
        # Informações técnicas
        print(f"\n🔧 INFORMAÇÕES TÉCNICAS:")
        print(f"   - Query IDs: {len(response.get('query_ids', []))}")
        print(f"   - SQLs executados: {len(response.get('sqls_executed', []))}")
        print(f"   - Iterações: {response.get('iterations_performed', 0)}")
        print(f"   - Follow-up: {response.get('follow_up_performed', False)}")
        
        print(f"\n📄 RESPOSTA COMPLETA:")
        print("=" * 70)
        print(text)
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no exemplo: {str(e)}")
        return False

def explain_table_detection():
    """
    Explica como funciona a detecção automática de tabelas
    """
    print("\n🧠 COMO FUNCIONA A DETECÇÃO AUTOMÁTICA DE TABELAS:")
    print("-" * 60)
    
    print("1️⃣ DETECÇÃO DE REFERÊNCIAS:")
    print("   O sistema procura por frases como:")
    references = [
        "see the table",
        "tabela relacionada", 
        "dados da tabela",
        "consulte a tabela",
        "veja a tabela",
        "table with the related data"
    ]
    for ref in references:
        print(f"   - '{ref}'")
    
    print("\n2️⃣ BUSCA DE QUERY_ID:")
    print("   - Extrai query_id dos tool_results")
    print("   - Usa o query_id para buscar dados via RESULT_SCAN")
    
    print("\n3️⃣ FORMATAÇÃO:")
    print("   - Busca dados reais do Snowflake")
    print("   - Formata em tabela markdown legível")
    print("   - Adiciona automaticamente ao texto da resposta")
    
    print("\n4️⃣ LIMITAÇÕES:")
    print("   - Máximo 50 linhas por tabela (para não sobrecarregar)")
    print("   - Largura máxima 30 caracteres por coluna")
    print("   - Funciona apenas com queries que retornam dados")

if __name__ == "__main__":
    print("🚀 Executando exemplo de integração de tabelas...")
    
    success = example_table_integration()
    
    if success:
        explain_table_detection()
        print(f"\n✅ Exemplo executado com sucesso!")
        print(f"\n💡 BENEFÍCIOS DA NOVA FUNCIONALIDADE:")
        print(f"   ✅ Elimina respostas vazias com 'See the table'")
        print(f"   ✅ Dados reais do Snowflake incluídos automaticamente")
        print(f"   ✅ Formatação legível e profissional")
        print(f"   ✅ Não requer intervenção manual do usuário")
        print(f"   ✅ Mantém compatibilidade com gráficos e textos")
    else:
        print(f"\n❌ Falha na execução - verifique configuração") 