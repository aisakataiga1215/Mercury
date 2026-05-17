from utils.config_handler import prompts_conf
from utils.path_tool import get_abs_path
from utils.logger_handler import logger


def _load_prompt(key: str) -> str:
    try:
        path = get_abs_path(prompts_conf[key])
    except KeyError:
        logger.error(f"[prompt_loader] Missing config key: {key}")
        raise
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"[prompt_loader] Failed to load {path}: {e}")
        raise


def load_system_prompts() -> str:
    return _load_prompt("main_prompt_path")


def load_listing_prompts() -> str:
    return _load_prompt("listing_prompt_path")


def load_review_prompts() -> str:
    return _load_prompt("review_prompt_path")


def load_campaign_prompts() -> str:
    return _load_prompt("campaign_prompt_path")


def load_daily_report_prompts() -> str:
    return _load_prompt("daily_report_prompt_path")


WORKFLOW_PROMPTS = {
    "listing": load_listing_prompts,
    "review": load_review_prompts,
    "campaign": load_campaign_prompts,
    "daily_report": load_daily_report_prompts,
}
