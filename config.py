"""
Configurações centralizadas para a integração Snowflake Cortex Agents
"""

import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('dev.env')

class SnowflakeConfig:
    """
    Configurações do Snowflake
    """
    
    # Configurações de conexão
    ACCOUNT = os.getenv('ACCOUNT')
    HOST = os.getenv('HOST')
    AGENT_ENDPOINT = os.getenv('AGENT_ENDPOINT')
    
    # Configurações de autenticação
    PRIVATE_KEY = os.getenv('RSA_PRIVATE_KEY_PATH')
    USERNAME = os.getenv('DEMO_USER')
    ROLE = os.getenv('DEMO_USER_ROLE')
    
    # Configurações de recursos
    WAREHOUSE = os.getenv('WAREHOUSE')
    DATABASE = os.getenv('DEMO_DATABASE')
    SCHEMA = os.getenv('DEMO_SCHEMA')
    
    # Configurações do modelo
    MODEL = os.getenv('MODEL', 'llama3.1-70b')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Valida se todas as configurações obrigatórias estão presentes
        
        Returns:
            True se todas as configurações estão válidas
        """
        required_configs = [
            cls.ACCOUNT,
            cls.HOST,
            cls.AGENT_ENDPOINT,
            cls.PRIVATE_KEY,
            cls.USERNAME,
            cls.ROLE
        ]
        
        missing_configs = [config for config in required_configs if not config]
        
        if missing_configs:
            print("❌ Configurações obrigatórias não encontradas:")
            for config in missing_configs:
                print(f"   - {config}")
            return False
        
        return True
    
    @classmethod
    def get_connection_info(cls) -> dict:
        """
        Retorna informações de conexão para debug
        
        Returns:
            Dicionário com informações de conexão
        """
        return {
            'account': cls.ACCOUNT,
            'host': cls.HOST,
            'agent_endpoint': cls.AGENT_ENDPOINT,
            'username': cls.USERNAME,
            'role': cls.ROLE,
            'warehouse': cls.WAREHOUSE,
            'database': cls.DATABASE,
            'schema': cls.SCHEMA,
            'model': cls.MODEL
        } 