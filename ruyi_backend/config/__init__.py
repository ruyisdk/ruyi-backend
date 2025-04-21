from ..cache import init_main_redis
from ..db.conn import init_main_db
from ..es import init_main_es
from ..gh import init_github
from .env import get_env_config as get_env_config, init_env_config


def init() -> None:
    init_env_config()
    cfg = get_env_config()
    init_main_redis(cfg)
    init_main_db(cfg)
    init_main_es(cfg)
    init_github(cfg)
