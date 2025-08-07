#!/usr/bin/env python3
"""
Demo de uso do Snowflake Cortex Client com parser de eventos
"""

import json
from snowflake_cortex_client import SnowflakeCortexClient, CortexResponseParser, CortexAgentEvent

def print_response_details(response):
    """
    Exibe detalhes da resposta parseada
    """
    print("\n" + "="*60)
    print("RESPOSTA DETALHADA DO CORTEX AGENT")
    print("="*60)
    
    # Texto principal
    if response.get("text"):
        print(f"\n📝 TEXTO DA RESPOSTA:")
        print(f"   {response['text']}")
    
    # Tool uses
    if response.get("tool_uses"):
        print(f"\n🛠️  FERRAMENTAS UTILIZADAS ({len(response['tool_uses'])}):")
        for i, tool_use in enumerate(response["tool_uses"], 1):
            print(f"   {i}. {tool_use.get('name', 'Unknown')} ({tool_use.get('tool_use_id', 'no-id')})")
            if tool_use.get('input'):
                print(f"      Input: {json.dumps(tool_use['input'], indent=6)}")
    
    # Tool results
    if response.get("tool_results"):
        print(f"\n📊 RESULTADOS DE FERRAMENTAS ({len(response['tool_results'])}):")
        for i, result in enumerate(response["tool_results"], 1):
            print(f"   {i}. Status: {result.get('status', 'unknown')}")
            print(f"      Tool ID: {result.get('tool_use_id', 'no-id')}")
            if result.get('content'):
                print(f"      Content: {len(result['content'])} item(s)")
    
    # Charts
    if response.get("charts"):
        print(f"\n📈 GRÁFICOS ({len(response['charts'])}):")
        for i, chart in enumerate(response["charts"], 1):
            spec = chart.get("chart_spec", {})
            if isinstance(spec, str):
                try:
                    spec = json.loads(spec)
                except:
                    pass
            print(f"   {i}. Tipo: {spec.get('mark', 'unknown') if isinstance(spec, dict) else 'raw'}")
            print(f"      Título: {spec.get('title', 'Sem título') if isinstance(spec, dict) else 'N/A'}")
    
    # Erros
    if response.get("errors"):
        print(f"\n❌ ERROS ({len(response['errors'])}):")
        for i, error in enumerate(response["errors"], 1):
            print(f"   {i}. Código: {error.get('code', 'unknown')}")
            print(f"      Mensagem: {error.get('message', 'Sem mensagem')}")
    
    # Informações sobre follow-up e SQL
    if response.get("follow_up_performed"):
        print(f"\n🔄 FOLLOW-UP REALIZADO:")
        print(f"   ✅ SQL detectado e follow-up executado automaticamente")
        if response.get("sql_executed"):
            sql_preview = response["sql_executed"][:100] + "..." if len(response["sql_executed"]) > 100 else response["sql_executed"]
            print(f"   📝 SQL: {sql_preview}")
    
    # Eventos brutos (apenas quantidade para não poluir)
    if response.get("raw_events"):
        print(f"\n🔍 EVENTOS BRUTOS: {len(response['raw_events'])} evento(s)")
        event_types = {}
        for event in response["raw_events"]:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        for event_type, count in event_types.items():
            print(f"   - {event_type}: {count}")

def test_parser_with_sample_data():
    """
    Testa o parser com dados de exemplo da documentação
    """
    print("\n" + "="*60)
    print("TESTE DO PARSER COM DADOS DE EXEMPLO")
    print("="*60)
    
    # Exemplo de resposta de streaming baseado na documentação
    sample_response = '''event: message.delta
data: {"id": "msg_001", "object": "message.delta", "delta": {"content": [{"index": 0, "type": "text", "text": "Aqui estão os top 3 clientes por receita baseado nos dados:"}]}}

event: message.delta
data: {"id": "msg_002", "object": "message.delta", "delta": {"content": [{"index": 0, "type": "tool_use", "tool_use": {"tool_use_id": "tool_001", "name": "DATA_BETA", "input": {"messages": ["role:USER content:{text:{text:\\"What are the top three customers by revenue?\\"}}"], "model": "snowflake-hosted-semantic"}}}]}}

event: message.delta
data: {"id": "msg_003", "object": "message.delta", "delta": {"content": [{"index": 0, "type": "tool_results", "tool_results": {"tool_use_id": "tool_001", "status": "success", "content": [{"type": "json", "json": {"sql": "SELECT customer_id, revenue FROM customers ORDER BY revenue DESC LIMIT 3", "text": "Query gerada para os top 3 clientes"}}]}}]}}

event: message.delta
data: {"id": "msg_004", "object": "message.delta", "delta": {"content": [{"index": 0, "type": "chart", "chart": {"chart_spec": "{\\"$schema\\": \\"https://vega.github.io/schema/vega-lite/v5.json\\", \\"title\\": \\"Top 3 Clientes\\", \\"mark\\": \\"bar\\"}"}}]}}'''
    
    # Parse dos eventos
    events = CortexResponseParser.parse_streaming_response(sample_response)
    
    print(f"\nEventos parseados: {len(events)}")
    for i, event in enumerate(events, 1):
        print(f"  {i}. {event.event_type} - {len(event.get_content())} item(s) de conteúdo")
    
    # Extração da resposta final
    final_response = CortexResponseParser.extract_final_response(events)
    print_response_details(final_response)

def main():
    """
    Função principal de demonstração
    """
    print("🎯 SNOWFLAKE CORTEX CLIENT - DEMO COM PARSER")
    print("Demonstrando o parser de eventos da API Cortex Agents")
    
    # Teste do parser com dados de exemplo
    # test_parser_with_sample_data()
    
    try:
        # Inicializa o cliente
        print(f"\n🔧 Inicializando cliente Snowflake Cortex...")
        client = SnowflakeCortexClient()
        
        # Teste de análise de dados simples
        print(f"\n💬 Testando análise de dados...")
        # question = "Quanto cresceu o GMV do Ali Express Oficial do mes 06 para o mes 07 de 2025?"
        question = "Quais os usuários com mais compras nos ultimos 10 dias que podem indicar fraude?"
        # question = "Oi"
        
        print(f"Pergunta: {question}")
        print("Enviando para o Cortex Agent...")
        
        response = client.analyze_data(question)

        print(response['text'])

        # print_response_details(response)
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        print("\nVerifique se:")
        print("1. O arquivo dev.env está configurado corretamente")
        print("2. As credenciais do Snowflake estão válidas")
        print("3. A conectividade com o Snowflake está funcionando")

if __name__ == "__main__":
    main() 