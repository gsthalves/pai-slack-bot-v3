# Integração Snowflake Cortex Agents REST API

Esta integração permite conectar e interagir com o Snowflake Cortex Agents REST API usando Python.

## Configuração

### Pré-requisitos

- Python 3.7+
- Conta Snowflake com acesso ao Cortex Agents
- Chave privada RSA para autenticação

### Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `dev.env` (já configurado)

## Uso

### Cliente Básico

```python
from snowflake_cortex_client import SnowflakeCortexClient

# Inicializa o cliente
client = SnowflakeCortexClient()

# Chat simples
response = client.chat("Olá! Como você pode me ajudar?")
print(response)
```

### Análise de Dados

```python
# Análise de dados usando Cortex Analyst
analysis = client.analyze_data("Quais são os top 3 clientes por receita?")
print(analysis)
```

### Execução de SQL

```python
# Executa uma consulta SQL
sql_result = client.execute_sql_query("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES")
print(sql_result)
```

### Conversa com Histórico

```python
# Conversa com histórico
conversation_history = [
    {
        "role": "user",
        "content": [{"type": "text", "text": "Me diga sobre o banco de dados"}]
    },
    {
        "role": "assistant", 
        "content": [{"type": "text", "text": "Posso ajudá-lo com informações sobre o banco de dados."}]
    }
]

response = client.chat("Quais tabelas existem?", conversation_history)
print(response)
```

### Uso Avançado

```python
# Uso direto do método run_agent
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Analise os dados de vendas do último mês"
            }
        ]
    }
]

# Configuração personalizada de ferramentas
tools = [
    {
        "tool_spec": {
            "type": "cortex_analyst_text_to_sql",
            "name": "Analyst1"
        }
    },
    {
        "tool_spec": {
            "type": "sql_exec",
            "name": "sql_execution_tool"
        }
    }
]

# Recursos para as ferramentas
tool_resources = {
    "Analyst1": {
        "semantic_model_file": "BETA_SNOWFLAKE_INTELLIGENCE.DATA"
    }
}

response = client.run_agent(
    messages=messages,
    tools=tools,
    tool_resources=tool_resources,
    response_instruction="Forneça análises detalhadas e insights acionáveis"
)
```

## Estrutura do Projeto

```
.
├── dev.env                          # Configurações de ambiente
├── requirements.txt                 # Dependências Python
├── snowflake_cortex_client.py      # Cliente principal
├── example_usage.py                # Exemplos de uso
└── README.md                       # Esta documentação
```

## Configurações

As seguintes variáveis devem estar configuradas no arquivo `dev.env`:

- `ACCOUNT`: ID da conta Snowflake
- `HOST`: Host do Snowflake
- `AGENT_ENDPOINT`: Endpoint da API Cortex Agents
- `MODEL`: Modelo a ser usado (padrão: llama3.1-70b)
- `SNOW_FLAKE_PRIVATE_KEY`: Chave privada RSA
- `DEMO_USER`: Usuário do Snowflake
- `DEMO_USER_ROLE`: Role do usuário
- `WAREHOUSE`: Warehouse a ser usado
- `DEMO_DATABASE`: Banco de dados
- `DEMO_SCHEMA`: Schema

## Funcionalidades

- ✅ Autenticação JWT automática
- ✅ Chat interativo com agentes
- ✅ Análise de dados com Cortex Analyst
- ✅ Execução de consultas SQL
- ✅ Suporte a histórico de conversas
- ✅ Configuração flexível de ferramentas
- ✅ Tratamento de erros robusto

## Exemplo de Execução

```bash
python example_usage.py
```

## Limitações

- Azure OpenAI models não são suportados
- Streamlit in Snowflake (SiS) apps não suportam execução de SQL
- Tokens JWT expiram em 1 hora e são renovados automaticamente

## Suporte

Para dúvidas ou problemas, consulte a [documentação oficial do Snowflake Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api). 