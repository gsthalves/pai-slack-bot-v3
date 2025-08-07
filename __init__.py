"""
Integração Snowflake Cortex Agents REST API

Este pacote fornece uma integração completa com o Snowflake Cortex Agents REST API,
permitindo chat interativo, análise de dados e execução de consultas SQL.
"""

from .snowflake_cortex_client import SnowflakeCortexClient

__version__ = "1.0.0"
__author__ = "Snowflake Integration"
__all__ = ["SnowflakeCortexClient"] 