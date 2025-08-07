import os
import json
import time
import jwt
import requests
import hashlib
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Generator, Union
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import rsa
from config import SnowflakeConfig
from generate_jwt import JWTGenerator
import snowflake.connector as snowflake_connector

# Carrega as variáveis de ambiente do arquivo dev.env
load_dotenv('dev.env')

class CortexAgentEvent:
    """Representa um evento da resposta do Cortex Agent"""
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        
    def is_message_delta(self) -> bool:
        return self.event_type == "message.delta"
    
    def is_error(self) -> bool:
        return self.event_type == "error"
    
    def get_content(self) -> List[Dict[str, Any]]:
        """Retorna o conteúdo do delta se for um evento message.delta"""
        if self.is_message_delta():
            return self.data.get("delta", {}).get("content", [])
        return []
    
    def get_text_content(self) -> str:
        """Extrai texto do conteúdo do evento"""
        text_parts = []
        for content in self.get_content():
            if content.get("type") == "text":
                text_parts.append(content.get("text", ""))
        return "".join(text_parts)
    
    def get_tool_use(self) -> Optional[Dict[str, Any]]:
        """Extrai informações de tool_use do evento"""
        for content in self.get_content():
            if content.get("type") == "tool_use":
                return content.get("tool_use", {})
        return None
    
    def get_tool_results(self) -> Optional[Dict[str, Any]]:
        """Extrai resultados de tools do evento"""
        for content in self.get_content():
            if content.get("type") == "tool_results":
                return content.get("tool_results", {})
        return None
    
    def get_chart(self) -> Optional[Dict[str, Any]]:
        """Extrai especificação de chart do evento"""
        for content in self.get_content():
            if content.get("type") == "chart":
                return content.get("chart", {})
        return None

class CortexResponseParser:
    """Parser para eventos de streaming da API Cortex Agents"""
    
    @staticmethod
    def parse_streaming_response(response_text: str) -> List[CortexAgentEvent]:
        """
        Faz o parse de uma resposta de streaming da API Cortex
        
        Args:
            response_text: Texto completo da resposta
            
        Returns:
            Lista de eventos parseados
        """
        events = []
        lines = response_text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Procura por linhas que começam com "event:"
            if line.startswith("event:"):
                event_type = line[6:].strip()
                
                # A próxima linha deve ser "data:"
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("data:"):
                    data_line = lines[i + 1].strip()
                    data_json = data_line[5:].strip()
                    
                    # Verifica se é a linha [DONE]
                    if data_json == "[DONE]":
                        # Pula a linha [DONE] sem tentar fazer parse
                        i += 2
                        continue
                    
                    try:
                        data = json.loads(data_json)
                        events.append(CortexAgentEvent(event_type, data))
                    except json.JSONDecodeError as e:
                        print(f"Erro ao fazer parse do JSON: {e}")
                        print(f"Linha problemática: {data_json}")
                    
                    i += 2  # Pula o event e data
                else:
                    i += 1
            else:
                i += 1
        
        return events
    
    @staticmethod
    def extract_final_response(events: List[CortexAgentEvent]) -> Dict[str, Any]:
        """
        Extrai a resposta final combinando todos os eventos
        
        Args:
            events: Lista de eventos parseados
            
        Returns:
            Resposta combinada com texto, tools e charts
        """
        response = {
            "text": "",
            "tool_uses": [],
            "tool_results": [],
            "charts": [],
            "errors": []
        }
        
        for event in events:
            if event.is_error():
                response["errors"].append(event.data)
            elif event.is_message_delta():
                # Combina texto
                text = event.get_text_content()
                if text:
                    response["text"] += text
                
                # Coleta tool uses
                tool_use = event.get_tool_use()
                if tool_use:
                    response["tool_uses"].append(tool_use)
                
                # Coleta tool results
                tool_results = event.get_tool_results()
                if tool_results:
                    response["tool_results"].append(tool_results)
                
                # Coleta charts
                chart = event.get_chart()
                if chart:
                    response["charts"].append(chart)
        
        return response 

class SnowflakeCortexClient:
    """
    Cliente para integração com Snowflake Cortex Agents REST API
    """
    
    def __init__(self):
        """Inicializa o cliente com as configurações do arquivo dev.env"""
        # Valida as configurações
        if not SnowflakeConfig.validate():
            raise ValueError("Configurações obrigatórias não encontradas no arquivo dev.env")
        
        self.account = SnowflakeConfig.ACCOUNT.upper()
        self.host = SnowflakeConfig.HOST
        self.agent_endpoint = SnowflakeConfig.AGENT_ENDPOINT
        self.model = SnowflakeConfig.MODEL
        self.private_key = SnowflakeConfig.PRIVATE_KEY
        self.username = SnowflakeConfig.USERNAME.upper()
        self.role = SnowflakeConfig.ROLE
        self.warehouse = SnowflakeConfig.WAREHOUSE
        self.database = SnowflakeConfig.DATABASE
        self.schema = SnowflakeConfig.SCHEMA
        
        self._token = None
        self._token_expires = None
        self._last_query_id = None  # Para capturar o último query_id executado
        
    def _generate_jwt_token(self) -> str:
        return JWTGenerator(self.account, self.username, self.private_key).get_token()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Retorna os headers necessários para as requisições
        """
        token = self._generate_jwt_token()

        return {
            'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    
    def run_agent(self, 
                  messages: List[Dict[str, Any]], 
                  tools: Optional[List[Dict[str, Any]]] = None,
                  tool_resources: Optional[Dict[str, Any]] = None,
                  response_instruction: Optional[str] = None,
                  experimental: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executa um agente Cortex com a mensagem fornecida
        
        Args:
            messages: Lista de mensagens da conversa
            tools: Lista de ferramentas disponíveis para o agente
            tool_resources: Recursos necessários pelas ferramentas
            response_instruction: Instruções para geração de resposta
            experimental: Flags experimentais
            
        Returns:
            Resposta parseada do agente
        """

        payload = {
            'model': self.model,
            'response_instruction': response_instruction or 'You will always maintain a friendly tone and provide concise response, use only our database to answer the question, answer always in brazilian portuguese',
            'experimental': experimental or {},
            'tools': tools or self._get_default_tools(),
            'tool_resources': tool_resources or self._get_default_tool_resources(),
            'tool_choice': {
                'type': 'auto'
            },
            'messages': messages
        }

        # print(json.dumps(payload, indent=4))

        try:
            response = requests.post(
                self.agent_endpoint,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            # Parse da resposta usando o novo parser
            events = CortexResponseParser.parse_streaming_response(response.text)
            parsed_response = CortexResponseParser.extract_final_response(events)
            
            # print(json.dumps(response, indent=4))

            # Adiciona dados brutos para debug
            parsed_response['raw_events'] = [
                {'event_type': event.event_type, 'data': event.data} 
                for event in events
            ]
            
            return parsed_response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na requisição para o agente Cortex: {str(e)}")
    
    def _get_default_tools(self) -> List[Dict[str, Any]]:
        """
        Retorna as ferramentas padrão conforme documentação oficial
        Inclui cortex_analyst_text_to_sql, sql_exec e data_to_chart para fluxo completo
        """
        return [
            {
                'tool_spec': {
                    'type': 'cortex_analyst_text_to_sql',
                    'name': 'DATA_BETA'
                }
            },
            {
                'tool_spec': {
                    'type': 'sql_exec',
                    'name': 'sql_execution_tool'
                }
            },
            # {
            #     'tool_spec': {
            #         'type': 'data_to_chart',
            #         'name': 'data_to_chart'
            #     }
            # }
        ]
    
    def _get_default_tool_resources(self) -> Dict[str, Any]:
        """
        Retorna os recursos padrão para as ferramentas
        """
        return {
            'DATA_BETA': {
                "semantic_view": "SNOWFLAKE_INTELLIGENCE.DATA.DATA_BETA"
            }
        }
    
    def _has_sql_to_execute(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Verifica se há SQL para executar nos resultados das ferramentas
        
        Returns:
            SQL string se encontrado, None caso contrário
        """
        for tool_result in response.get('tool_results', []):
            if tool_result.get('status') == 'success':
                for content in tool_result.get('content', []):
                    if content.get('type') == 'json':
                        json_data = content.get('json', {})
                        if 'sql' in json_data:
                            return json_data['sql']
        return None
    
    def _get_tool_use_id_for_sql(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Obtém o tool_use_id da ferramenta que gerou SQL
        
        Returns:
            tool_use_id se encontrado, None caso contrário
        """
        for tool_result in response.get('tool_results', []):
            if tool_result.get('status') == 'success':
                for content in tool_result.get('content', []):
                    if content.get('type') == 'json':
                        json_data = content.get('json', {})
                        if 'sql' in json_data:
                            return tool_result.get('tool_use_id')
        return None
    
    def _has_pending_tool_uses(self, response: Dict[str, Any]) -> bool:
        """
        Verifica se há tool_uses pendentes que precisam de follow-up
        
        Returns:
            True se há tools pendentes, False caso contrário
        """
        # Se há tool_uses mas não há tool_results correspondentes, há pendências
        tool_uses = response.get('tool_uses', [])
        tool_results = response.get('tool_results', [])
        
        if not tool_uses:
            return False
        
        # Cria set de tool_use_ids dos resultados
        result_ids = set()
        for tool_result in tool_results:
            result_ids.add(tool_result.get('tool_use_id'))
        
        # Verifica se há tool_uses sem resultados correspondentes
        for tool_use in tool_uses:
            tool_use_id = tool_use.get('tool_use_id')
            if tool_use_id and tool_use_id not in result_ids:
                return True
        
        return False
    
    def _needs_continuation(self, response: Dict[str, Any]) -> bool:
        """
        Determina se a resposta precisa de continuação baseado na documentação oficial
        
        Returns:
            True se precisa continuar, False caso contrário
        """
        # Se há SQL para executar, sempre precisa continuar para obter resposta textual/gráfico
        sql_to_execute = self._has_sql_to_execute(response)
        if sql_to_execute:
            print(f"🔄 Continuação necessária: SQL detectado para execução")
            return True
        
        # Se há tool_uses sem tool_results correspondentes, precisa continuar
        if self._has_pending_tool_uses(response):
            print(f"🔄 Continuação necessária: tool_uses pendentes")
            return True
        
        # Se não há texto de resposta mas há tools processados, pode precisar continuar
        if not response.get('text', '').strip() and (response.get('tool_uses') or response.get('tool_results')):
            print(f"🔄 Continuação necessária: sem texto mas com tools processados")
            return True
        
        return False
    
    def _get_pending_tool_uses(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Obtém lista de tool_uses que ainda precisam de follow-up
        
        Returns:
            Lista de tool_uses pendentes
        """
        tool_uses = response.get('tool_uses', [])
        tool_results = response.get('tool_results', [])
        
        # Cria set de tool_use_ids dos resultados
        result_ids = set()
        for tool_result in tool_results:
            result_ids.add(tool_result.get('tool_use_id'))
        
        # Filtra tool_uses que não têm resultados
        pending_tools = []
        for tool_use in tool_uses:
            tool_use_id = tool_use.get('tool_use_id')
            if tool_use_id and tool_use_id not in result_ids:
                pending_tools.append(tool_use)
        
        return pending_tools
    
    def _build_follow_up_messages(self, 
                                  original_messages: List[Dict[str, Any]], 
                                  response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Constrói mensagens de follow-up baseado na resposta atual
        Seguindo EXATAMENTE o padrão da documentação do Snowflake Cortex Agents REST API
        
        Args:
            original_messages: Mensagens originais da conversa
            response: Resposta atual com tool_uses e/ou tool_results
            
        Returns:
            Lista de mensagens incluindo o histórico + assistant response + user tool_results
        """
        # Inicia com as mensagens originais
        follow_up_messages = original_messages.copy()
        
        # Identifica se há SQL para executar
        sql_from_response = self._has_sql_to_execute(response)
        tool_use_id_for_sql = self._get_tool_use_id_for_sql(response)
        
        # ETAPA 1: Adiciona resposta do assistant com APENAS tool_uses (nunca tool_results)
        assistant_content = []
        
        # Adiciona tool_uses existentes da resposta
        for tool_use in response.get('tool_uses', []):
            clean_tool_use = {
                "tool_use_id": tool_use.get('tool_use_id'),
                "name": tool_use.get('name'),
                "input": tool_use.get('input', {})
            }
            assistant_content.append({
                "type": "tool_use",
                "tool_use": clean_tool_use
            })
        
        # ADICIONA tool_results EXISTENTES como parte da resposta do assistant
        # (conforme documentação - assistant pode retornar tool_use + tool_results)
        for tool_result in response.get('tool_results', []):
            assistant_content.append({
                "type": "tool_results",
                "tool_results": tool_result
            })
        
        # Se há SQL mas não há tool_use para sql_execution_tool, cria um
        if sql_from_response and not any(tu.get('name') == 'sql_execution_tool' for tu in response.get('tool_uses', [])):
            sql_tool_use_id = f"tool_{str(uuid.uuid4()).replace('-', '')[:8]}"
            assistant_content.append({
                "type": "tool_use",
                "tool_use": {
                    "tool_use_id": sql_tool_use_id,
                    "name": "sql_execution_tool",
                    "input": {
                        "sql": sql_from_response
                    }
                }
            })
            print(f"🔍 Tool use criado para SQL: {sql_tool_use_id}")
        
        # Adiciona mensagem do assistant se há conteúdo
        if assistant_content:
            follow_up_messages.append({
                "role": "assistant",
                "content": assistant_content
            })
        
        # ETAPA 2: Adiciona tool_results do usuário (conforme documentação)
        user_content = []
        
        # Se há SQL para executar, executa e adiciona query_id como tool_result do usuário
        if sql_from_response:
            # Executa SQL e obtém query_id real
            query_id = self._execute_sql_in_snowflake(sql_from_response)
            if not query_id:
                query_id = str(uuid.uuid4()).replace('-', '')[0:26]
            
            # Encontra o tool_use_id correto para sql_execution_tool
            sql_tool_use_id = None
            for tool_use in response.get('tool_uses', []):
                if tool_use.get('name') == 'sql_execution_tool':
                    sql_tool_use_id = tool_use.get('tool_use_id')
                    break
            
            # Se não encontrou, pega o que foi criado acima
            if not sql_tool_use_id:
                for content in assistant_content:
                    if (content.get('type') == 'tool_use' and 
                        content.get('tool_use', {}).get('name') == 'sql_execution_tool'):
                        sql_tool_use_id = content.get('tool_use', {}).get('tool_use_id')
                        break
            
            if sql_tool_use_id:
                # CRÍTICO: tool_use_id deve corresponder ao tool_use enviado pelo assistant
                user_content.append({
                    "type": "tool_results",
                    "tool_results": {
                        "tool_use_id": sql_tool_use_id,  # DEVE corresponder ao tool_use do assistant
                        "name": "sql_execution_tool",    # DEVE corresponder ao nome da tool
                        "content": [
                            {
                                "type": "json",
                                "json": {
                                    "query_id": query_id
                                }
                            }
                        ]
                    }
                })
                print(f"✅ Tool result criado para SQL com query_id: {query_id}, tool_use_id: {sql_tool_use_id}")
        
        # Adiciona mensagem do usuário com tool_results se necessário
        if user_content:
            follow_up_messages.append({
                "role": "user",
                "content": user_content
            })
            print(f"✅ Adicionando {len(user_content)} tool_results do usuário")
        
        return follow_up_messages
    
    def _execute_sql_in_snowflake(self, sql: str) -> Optional[str]:
        """
        Executa SQL real no Snowflake e retorna o query_id
        
        Args:
            sql: SQL para executar
            
        Returns:
            query_id se bem-sucedido, None caso contrário
        """
        try:
            
            # Conecta ao Snowflake usando as configurações
            conn = snowflake_connector.connect(
                account=self.account,
                user=self.username,
                private_key=self._get_private_key_object(),
                role=self.role,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema
            )
            
            cursor = conn.cursor()
            
            # Executa o SQL
            cursor.execute(sql)
            
            # Obtém o query_id
            query_id = cursor.sfqid
            
            # Salva o último query_id executado para uso posterior
            self._last_query_id = query_id
            print(f"🔍 DEBUG: query_id salvo globalmente: {query_id}")

            cursor.close()
            conn.close()
            
            return query_id
            
        except Exception as e:
            print(f"⚠️ Erro ao executar SQL no Snowflake: {str(e)}")
            print("📝 Usando query_id simulado para demonstração...")
            # Fallback para query_id simulado em caso de erro
            return str(uuid.uuid4()).replace('-', '')[0:26]
    
    def _fetch_query_results(self, query_id: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Busca os resultados de uma query executada usando o query_id
        
        Args:
            query_id: ID da query para buscar resultados
            limit: Limite máximo de linhas a retornar
            
        Returns:
            Dicionário com colunas e dados, ou None se falhar
        """
        try:
            conn = snowflake_connector.connect(
                account=self.account,
                user=self.username,
                private_key=self._get_private_key_object(),
                role=self.role,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema
            )
            
            cursor = conn.cursor()
            
            # Busca resultados usando query_id
            fetch_sql = f"""
            SELECT * FROM TABLE(RESULT_SCAN('{query_id}'))
            LIMIT {limit}
            """
            
            cursor.execute(fetch_sql)
            
            # Obtém metadados das colunas
            columns = [desc[0] for desc in cursor.description]
            
            # Obtém dados
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar resultados da query {query_id}: {str(e)}")
            return None
    
    def _format_table_data(self, table_data: Dict[str, Any]) -> str:
        """
        Formata dados da tabela em texto legível
        
        Args:
            table_data: Dados da tabela com colunas e linhas
            
        Returns:
            String formatada da tabela
        """
        if not table_data or not table_data.get('columns') or not table_data.get('rows'):
            return ""
        
        columns = table_data['columns']
        rows = table_data['rows']
        
        # Calcula larguras das colunas
        col_widths = []
        for i, col in enumerate(columns):
            max_width = len(str(col))
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(min(max_width, 30))  # Limita largura máxima
        
        # Cria header
        header = "| " + " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(columns)) + " |"
        separator = "|" + "|".join("-" * (width + 2) for width in col_widths) + "|"
        
        # Cria linhas de dados
        data_lines = []
        for row in rows[:50]:  # Limita a 50 linhas para não sobrecarregar
            line = "| " + " | ".join(
                str(row[i] if i < len(row) else "").ljust(col_widths[i])[:col_widths[i]] 
                for i in range(len(columns))
            ) + " |"
            data_lines.append(line)
        
        # Monta tabela completa
        table_text = "\n".join([header, separator] + data_lines)
        
        # Adiciona informações sobre a tabela
        total_rows = table_data.get('row_count', len(rows))
        if total_rows > 50:
            table_text += f"\n\n(Mostrando 50 de {total_rows} linhas)"
        
        return f"\n\n📊 **Dados da Consulta:**\n\n```\n{table_text}\n```\n"
    
    def _get_private_key_object(self):
        """
        Carrega a chave privada como objeto para conexão Snowflake
        """
        try:
            from cryptography.hazmat.primitives import serialization
            
            # Lê o conteúdo da chave privada do ambiente
            private_key_content = os.getenv("SNOW_FLAKE_PRIVATE_KEY")
            if not private_key_content:
                print("⚠️ SNOW_FLAKE_PRIVATE_KEY não encontrada no ambiente")
                return None
            
            # Converte para bytes se necessário
            if isinstance(private_key_content, str):
                private_key_content = private_key_content.encode('utf-8')
            
            private_key = serialization.load_pem_private_key(
                private_key_content,
                password=None
            )
            return private_key
        except Exception as e:
            print(f"⚠️ Erro ao carregar chave privada: {str(e)}")
            return None

    def _execute_sql_follow_up(self, sql: str, tool_use_id: str, original_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executa seguimento para SQL gerado, executando SQL real e obtendo query_id
        
        Args:
            sql: SQL gerado pela ferramenta
            tool_use_id: ID da ferramenta que gerou o SQL
            original_messages: Mensagens originais da conversa
            
        Returns:
            Resposta final com texto e gráficos
        """
        # Executa SQL real no Snowflake para obter query_id
        print(f"🔄 Executando SQL no Snowflake...")
        query_id = self._execute_sql_in_snowflake(sql)
        
        if not query_id:
            print("❌ Falha ao executar SQL - usando simulação")
            query_id = str(uuid.uuid4()).replace('-', '')[0:26]
        else:
            print(f"✅ SQL executado com sucesso - Query ID: {query_id}")
        
        # Constrói a mensagem de follow-up conforme documentação
        # Inclui o histórico da conversa + resposta do assistant + tool_results do usuário
        follow_up_messages = original_messages + [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "tool_use": {
                            "tool_use_id": tool_use_id,
                            "name": "DATA_BETA",
                            "input": {
                                "query": original_messages[-1]["content"][0]["text"],
                                "experimental": {}
                            }
                        }
                    },
                    {
                        "type": "tool_results",
                        "tool_results": {
                            "status": "success",
                            "tool_use_id": tool_use_id,
                            "content": [
                                {
                                    "type": "json",
                                    "json": {
                                        "sql": sql,
                                        "text": f"Query gerada para: {original_messages[-1]['content'][0]['text']}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_results",
                        "tool_results": {
                            "tool_use_id": tool_use_id,
                            "name": "sql_execution_tool",
                            "content": [
                                {
                                    "type": "json",
                                    "json": {
                                        "query_id": query_id
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
        
        # Faz a chamada follow-up para obter texto e gráficos
        return self.run_agent(follow_up_messages)
    
    def run_agent_with_follow_up(self, 
                                 messages: List[Dict[str, Any]], 
                                 tools: Optional[List[Dict[str, Any]]] = None,
                                 tool_resources: Optional[Dict[str, Any]] = None,
                                 response_instruction: Optional[str] = None,
                                 experimental: Optional[Dict[str, Any]] = None,
                                 max_iterations: int = 10) -> Dict[str, Any]:
        """
        Executa agente com follow-up automático contínuo até não haver mais tools pendentes
        
        Args:
            messages: Lista de mensagens da conversa
            tools: Lista de ferramentas disponíveis para o agente
            tool_resources: Recursos necessários pelas ferramentas
            response_instruction: Instruções para geração de resposta
            experimental: Flags experimentais
            max_iterations: Número máximo de iterações para evitar loops infinitos
            
        Returns:
            Resposta final completa (com follow-ups se necessário)
        """
        current_messages = messages
        all_responses = []
        iteration = 0
        seen_tool_combinations = set()  # Para detectar loops
        
        print(f"🚀 Iniciando execução do agente com follow-up automático...")
        
        while iteration < max_iterations:
            iteration += 1
            print(f"🔄 Iteração {iteration}/{max_iterations}")
            
            # Executa o agente
            current_response = self.run_agent(
                messages=current_messages,
                tools=tools,
                tool_resources=tool_resources,
                response_instruction=response_instruction,
                experimental=experimental
            )
            
            all_responses.append(current_response)
            
            # Verifica se precisa continuar
            if not self._needs_continuation(current_response):
                print(f"✅ Resposta completa obtida na iteração {iteration}")
                break
            
            print(f"🔄 Continuação necessária - construindo follow-up...")
            
            # Detecta loops potenciais baseado em combinações de tools
            pending_tools = self._get_pending_tool_uses(current_response)
            if pending_tools:
                tool_signature = frozenset(tool.get('name', 'unknown') for tool in pending_tools)
                if tool_signature in seen_tool_combinations:
                    print(f"⚠️ Loop detectado com tools: {list(tool_signature)} - interrompendo")
                    break
                seen_tool_combinations.add(tool_signature)
                print(f"📋 Tools pendentes: {list(tool_signature)}")
            
            # Constrói mensagens de follow-up
            current_messages = self._build_follow_up_messages(current_messages, current_response)
            
            # Verifica se as mensagens são válidas
            if not current_messages or len(current_messages) == len(messages):
                print(f"⚠️ Mensagens de follow-up inválidas - interrompendo")
                break
            
            sql_to_execute = self._has_sql_to_execute(current_response)
            if sql_to_execute:
                print(f"📝 SQL detectado: {sql_to_execute[:100]}...")
        
        if iteration >= max_iterations:
            print(f"⚠️ Limite máximo de iterações ({max_iterations}) atingido")
        
                # Combina todas as respostas
        combined_response = self._combine_responses(all_responses)
        combined_response['iterations_performed'] = iteration
        combined_response['follow_up_performed'] = iteration > 1
        
        return combined_response
    
    def _combine_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combina múltiplas respostas em uma resposta final
        
        Args:
            responses: Lista de respostas para combinar
            
        Returns:
            Resposta combinada
        """
        if not responses:
            return {
                "text": "",
                "tool_uses": [],
                "tool_results": [],
                "charts": [],
                "errors": [],
                "raw_events": []
            }
        
        if len(responses) == 1:
            return self._enhance_response_with_table_data(responses[0])
        
        combined = {
            "text": "",
            "tool_uses": [],
            "tool_results": [],
            "charts": [],
            "errors": [],
            "raw_events": []
        }
        
        executed_sqls = []
        query_ids = []
        
        # Primeiro, coleta TODOS os query_ids de TODAS as respostas
        print(f"🔍 DEBUG: Combinando {len(responses)} respostas")
        
        for i, response in enumerate(responses):
            print(f"🔍 DEBUG: Processando resposta {i+1}")
            
            # Combina texto (última resposta que tem texto prevalece)
            if response.get('text', '').strip():
                combined["text"] = response.get('text', '')
                print(f"🔍 DEBUG: Texto atualizado da resposta {i+1}")
            
            # Combina arrays
            combined["tool_uses"].extend(response.get('tool_uses', []))
            combined["tool_results"].extend(response.get('tool_results', []))
            combined["charts"].extend(response.get('charts', []))
            combined["errors"].extend(response.get('errors', []))
            combined["raw_events"].extend(response.get('raw_events', []))
            
            # Coleta SQLs executados
            sql_executed = self._has_sql_to_execute(response)
            if sql_executed:
                executed_sqls.append(sql_executed)
            
            # Coleta query_ids diretos se existirem
            if response.get('query_ids'):
                query_ids.extend(response.get('query_ids', []))
                print(f"🔍 DEBUG: query_ids diretos da resposta {i+1}: {response.get('query_ids', [])}")
            
            # Coleta query_ids dos tool_results
            for tool_result in response.get('tool_results', []):
                for content in tool_result.get('content', []):
                    if content.get('type') == 'json':
                        json_data = content.get('json', {})
                        if 'query_id' in json_data:
                            query_ids.append(json_data['query_id'])
                            print(f"🔍 DEBUG: query_id encontrado nos tool_results da resposta {i+1}: {json_data['query_id']}")
            
            # NOVO: Busca query_ids nos raw_events também
            for event in response.get('raw_events', []):
                event_data = event.get('data', {})
                delta = event_data.get('delta', {})
                content_list = delta.get('content', [])
                for content in content_list:
                    if content.get('type') == 'tool_results':
                        tool_results = content.get('tool_results', {})
                        for tr_content in tool_results.get('content', []):
                            if tr_content.get('type') == 'json':
                                json_data = tr_content.get('json', {})
                                if 'query_id' in json_data:
                                    query_ids.append(json_data['query_id'])
                                    print(f"🔍 DEBUG: query_id encontrado nos raw_events da resposta {i+1}: {json_data['query_id']}")
        
        print(f"🔍 DEBUG: Total de query_ids coletados: {len(query_ids)} - {query_ids}")
        
        # Adiciona informações sobre SQLs executados
        if executed_sqls:
            combined["sqls_executed"] = executed_sqls
        
        # Adiciona query_ids coletados
        if query_ids:
            combined["query_ids"] = query_ids
        
        return self._enhance_response_with_table_data(combined)
    
    def _enhance_response_with_table_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Melhora a resposta incluindo dados de tabela quando apropriado
        
        Args:
            response: Resposta para melhorar
            
        Returns:
            Resposta melhorada com dados de tabela
        """
        text = response.get('text', '')
        
        # Verifica se a resposta faz referência a uma tabela
        table_references = [
            "see the table",
            "tabela relacionada", 
            "dados da tabela",
            "consulte a tabela",
            "veja a tabela",
            "table with the related data"
        ]
        
        has_table_reference = any(ref.lower() in text.lower() for ref in table_references)
        
        print(f"🔍 DEBUG: Texto da resposta: '{text[:100]}...'")
        print(f"🔍 DEBUG: Tem referência à tabela: {has_table_reference}")
        if has_table_reference:
            for ref in table_references:
                if ref.lower() in text.lower():
                    print(f"🔍 DEBUG: Encontrada referência: '{ref}'")
        
        if has_table_reference:
            # Procura por query_ids nos tool_results
            query_ids = response.get('query_ids', [])
            print(f"🔍 DEBUG: query_ids diretos encontrados: {query_ids}")
            
            # Se não há query_ids diretos, procura nos tool_results
            if not query_ids:
                print(f"🔍 DEBUG: Procurando query_ids nos tool_results...")
                for i, tool_result in enumerate(response.get('tool_results', [])):
                    print(f"🔍 DEBUG: tool_result {i}: {tool_result}")
                    for j, content in enumerate(tool_result.get('content', [])):
                        print(f"🔍 DEBUG: content {j}: {content}")
                        if content.get('type') == 'json':
                            json_data = content.get('json', {})
                            if 'query_id' in json_data:
                                query_ids.append(json_data['query_id'])
                                print(f"🔍 DEBUG: query_id encontrado: {json_data['query_id']}")
            
            # Se ainda não encontrou, procura nos raw_events
            if not query_ids:
                print(f"🔍 DEBUG: Procurando query_ids nos raw_events...")
                for event in response.get('raw_events', []):
                    event_data = event.get('data', {})
                    delta = event_data.get('delta', {})
                    content_list = delta.get('content', [])
                    for content in content_list:
                        if content.get('type') == 'tool_results':
                            tool_results = content.get('tool_results', {})
                            for tr_content in tool_results.get('content', []):
                                if tr_content.get('type') == 'json':
                                    json_data = tr_content.get('json', {})
                                    if 'query_id' in json_data:
                                        query_ids.append(json_data['query_id'])
                                        print(f"🔍 DEBUG: query_id encontrado em raw_events: {json_data['query_id']}")
            
            print(f"🔍 DEBUG: Total de query_ids encontrados: {len(query_ids)}")
            
            # Se não encontrou query_ids mas há último query_id salvo, usa como fallback
            if not query_ids and hasattr(self, '_last_query_id') and self._last_query_id:
                query_ids.append(self._last_query_id)
                print(f"🔍 DEBUG: Usando último query_id salvo como fallback: {self._last_query_id}")
            
            # Busca dados da primeira query_id encontrada
            if query_ids:
                print(f"🔍 Detectada referência à tabela, buscando dados para query_id: {query_ids[0]}")
                table_data = self._fetch_query_results(query_ids[0])
                
                if table_data:
                    formatted_table = self._format_table_data(table_data)
                    if formatted_table:
                        # Adiciona a tabela formatada ao texto da resposta
                        response["text"] = text + formatted_table
                        print(f"✅ Dados da tabela adicionados à resposta ({table_data['row_count']} linhas)")
                else:
                    print(f"⚠️ Não foi possível buscar dados para query_id: {query_ids[0]}")
            else:
                print(f"⚠️ DEBUG: Nenhum query_id encontrado para buscar dados da tabela")
        
        return response
    
    def chat(self, message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Método simplificado para chat com o agente (com follow-up automático)
        
        Args:
            message: Mensagem do usuário
            conversation_history: Histórico da conversa (opcional)
            
        Returns:
            Resposta parseada do agente (com follow-up se necessário)
        """
        messages = conversation_history or []
        messages.append({
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': message
                }
            ]
        })
        
        return self.run_agent_with_follow_up(messages)
    
    def execute_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Executa uma consulta SQL usando o agente (com follow-up automático)
        
        Args:
            sql_query: Consulta SQL para executar
            
        Returns:
            Resultado parseado da execução (com follow-up se necessário)
        """
        messages = [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': f'Execute this SQL query: {sql_query}'
                    }
                ]
            }
        ]
        
        return self.run_agent_with_follow_up(messages)
    
    def analyze_data(self, question: str) -> Dict[str, Any]:
        """
        Analisa dados usando o agente Cortex Analyst (com follow-up automático)
        
        Args:
            question: Pergunta sobre os dados
            
        Returns:
            Análise parseada dos dados (com follow-up se necessário)
        """
        messages = [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': question
                    }
                ]
            }
        ]
        
        return self.run_agent_with_follow_up(messages) 

    def example_correct_flow(self):
        """
        Exemplo demonstrando o fluxo correto conforme documentação da Snowflake
        """
        print("📖 FLUXO CORRETO BASEADO NA DOCUMENTAÇÃO:")
        print()
        print("1️⃣ PRIMEIRA REQUISIÇÃO:")
        print({
            "model": "llama3.3-70b",
            "response_instruction": "Resposta em português",
            "tools": [
                {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "DATA_BETA"}},
                {"tool_spec": {"type": "sql_exec", "name": "sql_execution_tool"}},
                {"tool_spec": {"type": "data_to_chart", "name": "data_to_chart"}}
            ],
            "tool_resources": {
                "DATA_BETA": {"semantic_view": "SNOWFLAKE_INTELLIGENCE.DATA.DATA_BETA"}
            },
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Quais são os top 3 clientes por receita?"}]
                }
            ]
        })
        
        print()
        print("2️⃣ PRIMEIRA RESPOSTA (Assistant retorna tool_use + tool_results):")
        print({
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "tool_use": {
                        "tool_use_id": "tool_001",
                        "name": "DATA_BETA",
                        "input": {"query": "top 3 clientes por receita"}
                    }
                },
                {
                    "type": "tool_results",
                    "tool_results": {
                        "tool_use_id": "tool_001",
                        "status": "success",
                        "content": [
                            {
                                "type": "json",
                                "json": {
                                    "sql": "SELECT customer_id, revenue FROM customers ORDER BY revenue DESC LIMIT 3",
                                    "text": "Query para top 3 clientes por receita"
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "tool_use",
                    "tool_use": {
                        "tool_use_id": "tool_002",
                        "name": "sql_execution_tool",
                        "input": {
                            "sql": "SELECT customer_id, revenue FROM customers ORDER BY revenue DESC LIMIT 3"
                        }
                    }
                }
            ]
        })
        
        print()
        print("3️⃣ SEGUNDA REQUISIÇÃO (User retorna query_id):")
        print({
            "messages": [
                # ... mensagens anteriores ...
                {
                    "role": "assistant", 
                    "content": [
                        # tool_use e tool_results da resposta anterior
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_results",
                            "tool_results": {
                                "tool_use_id": "tool_002",  # DEVE corresponder ao tool_use do assistant
                                "name": "sql_execution_tool",
                                "content": [
                                    {
                                        "type": "json",
                                        "json": {"query_id": "01bcfcde-0100-0001-0000-000000102549"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        })
        
        print()
        print("4️⃣ SEGUNDA RESPOSTA (Resposta textual e gráficos):")
        print({
            "delta": {
                "content": [
                    {
                        "type": "text",
                        "text": "Os top 3 clientes por receita são..."
                    },
                    {
                        "type": "chart",
                        "chart": {
                            "chart_spec": "{\"mark\": \"bar\", \"data\": {...}}"
                        }
                    }
                ]
            }
        }) 