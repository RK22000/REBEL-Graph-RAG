import os
from dotenv import load_dotenv

load_dotenv()

ARANGO_URL = os.getenv("ARANGO_URL", "https://f284f452336b.arangodb.cloud:8529")
ARANGO_DB = os.getenv("ARANGO_DB", "node2vec")
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ADBPASS", "")

API_HOST = "0.0.0.0"
API_PORT = 8000

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TEMPERATURE = 0

REBEL_API_URL = os.getenv("REBEL_API_URL", "https://rebel-server-139095284696.us-central1.run.app/kb")
