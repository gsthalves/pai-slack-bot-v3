#!/bin/bash

# Script de instalação para a integração Snowflake Cortex Agents

echo "🚀 Instalando integração Snowflake Cortex Agents..."
echo "=================================================="

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale o Python 3.7+ primeiro."
    exit 1
fi

# Verifica se o pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Por favor, instale o pip primeiro."
    exit 1
fi

# Cria ambiente virtual (opcional)
read -p "Deseja criar um ambiente virtual? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Ambiente virtual criado e ativado"
fi

# Instala dependências
echo "📥 Instalando dependências..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas com sucesso"
else
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

# Verifica se o arquivo dev.env existe
if [ ! -f "dev.env" ]; then
    echo "❌ Arquivo dev.env não encontrado"
    echo "Por favor, certifique-se de que o arquivo dev.env está presente no diretório"
    exit 1
fi

# Testa a integração
echo "🧪 Testando integração..."
python3 test_integration.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
    echo "====================================="
    echo ""
    echo "📚 Próximos passos:"
    echo "   1. Execute 'python3 demo.py' para ver a demonstração completa"
    echo "   2. Execute 'python3 example_usage.py' para exemplos básicos"
    echo "   3. Consulte o README.md para documentação completa"
    echo ""
    echo "🔧 Comandos úteis:"
    echo "   - python3 demo.py          # Demonstração completa"
    echo "   - python3 test_integration.py  # Teste de integração"
    echo "   - python3 example_usage.py     # Exemplos de uso"
    echo ""
else
    echo "❌ Teste falhou. Verifique as configurações no arquivo dev.env"
    exit 1
fi 