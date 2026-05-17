import yaml
from utils.path_tool import get_abs_path


def _load_yml(relative_path: str) -> dict:
    with open(get_abs_path(relative_path), "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


agent_conf = _load_yml("config/agent.yml")
prompts_conf = _load_yml("config/prompts.yml")
