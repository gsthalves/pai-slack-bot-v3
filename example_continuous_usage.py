#!/usr/bin/env python3
"""
Exemplo simples de uso da funcionalidade de follow-up contínuo.

Este exemplo mostra como usar o cliente atualizado que automaticamente
continua executando ferramentas até finalizar completamente a resposta.
"""

from snowflake_cortex_client import SnowflakeCortexClient

def main():
    """Exemplo principal de uso"""
    
    print("🚀 Exemplo de Follow-up Contínuo - Snowflake Cortex")
    print("=" * 60)
    
    try:
        # Inicializa o cliente
        client = SnowflakeCortexClient()
        print("✅ Cliente inicializado com sucesso!")
        
        # Exemplo 1: Pergunta que requer análise de dados
        print("\n📊 EXEMPLO 1: Análise de dados com follow-up automático")
        print("-" * 60)
        
        question = "Quantos pedidos tivemos no último trimestre por categoria de produto? Mostre em um gráfico de barras."
        print(f"❓ Pergunta: {question}")
        
        # O método analyze_data agora usa automaticamente o follow-up contínuo
        response = client.analyze_data(question)
        
        # Mostra informações sobre o processamento
        print(f"\n🔄 Processamento:")
        print(f"   • Iterações realizadas: {response.get('iterations_performed', 1)}")
        print(f"   • Follow-up executado: {'Sim' if response.get('follow_up_performed', False) else 'Não'}")
        print(f"   • Tools utilizados: {len(response.get('tool_uses', []))}")
        print(f"   • SQLs executados: {len(response.get('sqls_executed', []))}")
        
        # Mostra a resposta final
        if response.get('text'):
            print(f"\n💬 Resposta final:")
            print(f"   {response['text']}")
        
        if response.get('charts'):
            print(f"\n📊 Gráficos gerados: {len(response['charts'])}")
        
        # Exemplo 2: Usando o método de baixo nível com configurações customizadas
        print("\n\n🔧 EXEMPLO 2: Uso avançado com configurações customizadas")
        print("-" * 60)
        
        custom_question = "Crie um relatório das vendas por região nos últimos 6 meses"
        print(f"❓ Pergunta: {custom_question}")
        
        # Usando o método run_agent_with_follow_up diretamente
        custom_response = client.run_agent_with_follow_up(
            messages=[{
                'role': 'user',
                'content': [{'type': 'text', 'text': custom_question}]
            }],
            max_iterations=5,  # Limite personalizado
            response_instruction="Seja detalhado na análise e sempre inclua insights relevantes."
        )
        
        print(f"\n🔄 Processamento customizado:")
        print(f"   • Iterações realizadas: {custom_response.get('iterations_performed', 1)}")
        print(f"   • Limite configurado: 5 iterações")
        print(f"   • Follow-up executado: {'Sim' if custom_response.get('follow_up_performed', False) else 'Não'}")
        
        if custom_response.get('text'):
            print(f"\n💬 Resposta final:")
            print(f"   {custom_response['text'][:200]}..." if len(custom_response['text']) > 200 else f"   {custom_response['text']}")
        
        print("\n✨ BENEFÍCIOS DO FOLLOW-UP CONTÍNUO:")
        print("  🔄 Execução automática de todas as ferramentas necessárias")
        print("  🛡️ Proteção contra loops infinitos")
        print("  📊 Respostas mais completas com dados e visualizações")
        print("  🚀 Não requer intervenção manual entre etapas")
        
        print("\n🎯 FUNCIONALIDADE IMPLEMENTADA COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        print("💡 Verifique se o arquivo dev.env está configurado corretamente")

if __name__ == "__main__":
    main() 