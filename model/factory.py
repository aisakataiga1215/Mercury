from dotenv import load_dotenv
load_dotenv()

from langchain_community.chat_models.tongyi import ChatTongyi
from utils.config_handler import agent_conf

chat_model = ChatTongyi(model=agent_conf["chat_model_name"])
