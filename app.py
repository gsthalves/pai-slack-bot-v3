from cgitb import text
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

from snowflake_cortex_client import SnowflakeCortexClient

load_dotenv('dev.env')

ACCOUNT = os.getenv("ACCOUNT")
HOST = os.getenv("HOST")
USER = os.getenv("DEMO_USER")
DATABASE = os.getenv("DEMO_DATABASE")
SCHEMA = os.getenv("DEMO_SCHEMA")
ROLE = os.getenv("DEMO_USER_ROLE")
WAREHOUSE = os.getenv("WAREHOUSE")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT")
SEMANTIC_MODEL = os.getenv("SEMANTIC_MODEL")
SEARCH_SERVICE = os.getenv("SEARCH_SERVICE")
RSA_PRIVATE_KEY_PATH = os.getenv("RSA_PRIVATE_KEY_PATH")
MODEL = os.getenv("MODEL")

DEBUG = True
USE_WHITE_LIST = True

# Initializes app
app = App(token=SLACK_BOT_TOKEN)
messages = []

white_list = [
    'gustavo.alves@pagaleve.com.br',
    'gabriela.widmer@pagaleve.com.br',
    'maisa.cota@pagaleve.com.br',
    'felipe.iasbik@pagaleve.com.br',
    'beatriz.castro@pagaleve.com.br',
    'estefany.inocencio@pagaleve.com.br',
    'felipe.coxa@pagaleve.com.br',
    'georgia.oliveira@pagaleve.com.br',
    'guilherme.cirino@pagaleve.com.br',
    'lucila.cardenas@pagaleve.com.br',
    'humberto.fagundes@pagaleve.com.br',
    'guilherme.leonardi@pagaleve.com.br',
    'gerson.pechim@pagaleve.com.br',
    'mike@pagaleve.com.br',
    'luiz@pagaleve.com.br',
    'handel@pagaleve.com.br',
    'alexis.montanaro@pagaleve.com.br',
    'guilherme.romao@pagaleve.com.br',
    'henrique.weaver@pagaleve.com.br',
    'vinicius.carvalho@pagaleve.com.br',
    'eduardo.zucareli@pagaleve.com.br',
    'daniela.santos@pagaleve.com.br',
    'william@pagaleve.com.br',
    'ivan.marasco@pagaleve.com.br',
    'lucas.simoes@pagaleve.com.br',
    'rafael.fernandes@pagaleve.com.br',
    'mariana.vasconcellos@pagaleve.com.br',
    'hyuk.choi@pagaleve.com.br',
    'joao.prado@pagaleve.com.br'
]

@app.command("/pai")
def pai_command(ack, say, command):
    ack()

    user_id = command['user_id']

    user_info = app.client.users_info(user=user_id)
    user_name = user_info['user']['profile']['real_name']
    user_email = user_info['user']['profile']['email']
    
    if USE_WHITE_LIST and user_email not in white_list:
        say(
            text = "😢 Foi mal {user_name} mas o PAI aqui não pode responder.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": f"😢 Foi mal {user_name} mas o PAI aqui não pode responder.",
                    }
                }
            ]
        )
        return
    
    try:
        prompt = command['text']
        say(
            text = "PAI ta pensando, deixa comigo...",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "💬 Chamou o PAI? Deixa que o PAI resolve...",
                    }
                }
            ]
        )
        response = ask_agent(prompt)
        display_agent_response(response, say, prompt, user_name)
    except Exception as e:
        error_info = f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"
        print(error_info)
        say(
            text = "🤦 Ihhhh deu ruim pro PAI, mas lembre-se que sou só um MVP.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": f"🤦 Ihhhh deu ruim pro PAI, {user_name} mas lembre-se que sou só um MVP.",
                    }
                }
            ]
        )        

def ask_agent(prompt):
    client = SnowflakeCortexClient()
    
    response = client.analyze_data(prompt)

    return response

def display_agent_response(content, say, prompt, user_name):

    response = content['text'].encode('latin1', errors='ignore').decode('utf8', errors='ignore')
    # response = content['text']

    say(
        text = "PAI Answer",
        blocks = [
            {
                "type": "divider",
            },
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_quote",
                        "elements": [
                            {
                                "type": "text",
                                "text": f"❓ {user_name}: {prompt}"
                            },
                            {
                                "type": "text",
                                "text": f"\r\n\r\n"
                            },
                            {
                                "type": "text",
                                "text": f"✅ {response}"
                            },
                        ]
                    },
                   
                ]
            },
            {
                "type": "divider",
            },
        ]                
    )

if __name__ == "__main__":
    with open(RSA_PRIVATE_KEY_PATH, "w") as f:
        f.write(os.getenv("SNOW_FLAKE_PRIVATE_KEY"))

    SocketModeHandler(app, SLACK_APP_TOKEN).start()
