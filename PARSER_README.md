# Parser de Eventos da API Snowflake Cortex Agents

Este documento descreve como usar o parser implementado para processar as respostas de streaming da API Snowflake Cortex Agents REST API.

## Visão Geral

A API `api/v2/cortex/agent:run` retorna eventos de streaming em formato de texto estruturado, que precisam ser parseados para extrair informações úteis como texto, resultados de ferramentas, gráficos e erros.

## Estrutura da Resposta

A resposta da API vem no formato:
```
event: message.delta
data: {"id": "msg_001", "object": "message.delta", "delta": {"content": [...]}}

event: message.delta  
data: {"id": "msg_002", "object": "message.delta", "delta": {"content": [...]}}

event: error
data: {"code": "399505", "message": "Internal server error"}
```

## Classes Implementadas

### 1. `CortexAgentEvent`

Representa um único evento da resposta:

```python
from snowflake_cortex_client import CortexAgentEvent

event = CortexAgentEvent("message.delta", data)

# Métodos disponíveis:
event.is_message_delta()    # Verifica se é evento message.delta
event.is_error()            # Verifica se é evento de erro
event.get_content()         # Retorna conteúdo do delta
event.get_text_content()    # Extrai texto do evento
event.get_tool_use()        # Extrai informações de tool_use
event.get_tool_results()    # Extrai resultados de tools
event.get_chart()           # Extrai especificação de gráfico
```

### 2. `CortexResponseParser`

Parser principal para processar eventos:

```python
from snowflake_cortex_client import CortexResponseParser

# Parse de resposta de streaming
events = CortexResponseParser.parse_streaming_response(response_text)

# Extração da resposta final combinada
final_response = CortexResponseParser.extract_final_response(events)
```

## Estrutura da Resposta Final

O parser retorna um dicionário estruturado:

```python
{
    "text": "Texto combinado da resposta",
    "tool_uses": [
        {
            "tool_use_id": "tool_001",
            "name": "DATA_BETA", 
            "input": {...}
        }
    ],
    "tool_results": [
        {
            "tool_use_id": "tool_001",
            "status": "success",
            "content": [...]
        }
    ],
    "charts": [
        {
            "chart_spec": "{JSON com especificação Vega-Lite}"
        }
    ],
    "errors": [
        {
            "code": "399505",
            "message": "Internal server error"
        }
    ],
    "raw_events": [...]  # Eventos brutos para debug
}
```

## Tipos de Conteúdo Suportados

### 1. Texto
```json
{
    "type": "text",
    "text": "Resposta textual do agente"
}
```

### 2. Tool Use (Uso de Ferramenta)
```json
{
    "type": "tool_use",
    "tool_use": {
        "tool_use_id": "tool_001",
        "name": "cortex_analyst_text_to_sql",
        "input": {
            "messages": [...],
            "model": "snowflake-hosted-semantic"
        }
    }
}
```

### 3. Tool Results (Resultados de Ferramenta)
```json
{
    "type": "tool_results", 
    "tool_results": {
        "tool_use_id": "tool_001",
        "status": "success",
        "content": [
            {
                "type": "json",
                "json": {
                    "sql": "SELECT * FROM table",
                    "text": "Interpretação da consulta"
                }
            }
        ]
    }
}
```

### 4. Charts (Gráficos)
```json
{
    "type": "chart",
    "chart": {
        "chart_spec": "{\"$schema\": \"https://vega.github.io/schema/vega-lite/v5.json\", ...}"
    }
}
```

## Uso no Cliente

O `SnowflakeCortexClient` já integra automaticamente o parser:

```python
from snowflake_cortex_client import SnowflakeCortexClient

client = SnowflakeCortexClient()

# Todos os métodos retornam respostas parseadas
response = client.chat("Olá!")
response = client.analyze_data("Top 3 customers by revenue")
response = client.execute_sql_query("SELECT 1")

# Acessar dados estruturados
print(response['text'])              # Texto da resposta
print(response['tool_uses'])         # Ferramentas utilizadas
print(response['tool_results'])      # Resultados das ferramentas
print(response['charts'])            # Gráficos gerados
print(response['errors'])            # Erros encontrados
```

## Exemplos Práticos

### Exemplo 1: Resposta Simples de Texto
```python
# Resposta apenas com texto
response = client.chat("Olá!")
print(f"Resposta: {response['text']}")
```

### Exemplo 2: Análise com SQL e Gráfico
```python
# Análise que gera SQL e gráfico
response = client.analyze_data("Top 5 products by sales")

print(f"Resposta: {response['text']}")

# Verificar se SQL foi gerado
if response['tool_results']:
    for result in response['tool_results']:
        if result['status'] == 'success':
            for content in result['content']:
                if content['type'] == 'json' and 'sql' in content['json']:
                    print(f"SQL gerado: {content['json']['sql']}")

# Verificar se gráfico foi gerado  
if response['charts']:
    print(f"Gráficos gerados: {len(response['charts'])}")
    for chart in response['charts']:
        import json
        spec = json.loads(chart['chart_spec'])
        print(f"Título: {spec.get('title', 'N/A')}")
        print(f"Tipo: {spec.get('mark', 'N/A')}")
```

### Exemplo 3: Tratamento de Erros
```python
response = client.analyze_data("Query inválida")

if response['errors']:
    for error in response['errors']:
        print(f"Erro {error['code']}: {error['message']}")
else:
    print(f"Sucesso: {response['text']}")
```

## Arquivos de Exemplo

- `demo.py` - Demonstração do cliente com parser integrado
- `parser_examples.py` - Exemplos específicos do parser com dados de teste
- `snowflake_cortex_client.py` - Implementação do cliente e parser

## Execução de Testes

```bash
# Testar exemplos do parser
python3 parser_examples.py

# Testar demo completo
python3 demo.py
```

## Limitações e Considerações

1. **JSON Malformado**: O parser trata erros de JSON graciosamente, logando problemas
2. **Eventos Grandes**: Para responses muito grandes, considere streaming processamento
3. **Debugging**: Use `raw_events` para debug detalhado dos eventos
4. **Tipos de Conteúdo**: O parser suporta os tipos principais da documentação oficial

## Referência da API

Baseado na documentação oficial: 
https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api#response

## Changelog

- ✅ Parser de eventos streaming implementado
- ✅ Suporte a message.delta e error events  
- ✅ Extração de texto, tool_use, tool_results e charts
- ✅ Integração automática no SnowflakeCortexClient
- ✅ Tratamento de erros e JSON malformado
- ✅ Exemplos e documentação completa 