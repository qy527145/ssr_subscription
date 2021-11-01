import atexit
import configparser
import logging
import os
from signal import signal, SIGTERM
from typing import List

__all__ = [
    'auto_generate_sections',
    'get_str_config',
    'set_str_config',
    'get_bool_config',
    'get_int_config',
    'get_float_config',
    'save_configs',
    'logging',
    'config',
    'ENABLE_AUTO_SAVE',
    'CONFIG_FILE',
]

# 全局配置项

CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True, strict=False)
if os.path.exists(CONFIG_FILE):
    config.read(CONFIG_FILE)

# 常量配置
# 启用配置自动保存
ENABLE_AUTO_SAVE = True


# 自动生成配置sections
def auto_generate_sections(sections: List[str]):
    for section in sections:
        if not config.has_section(section):
            config.add_section(section)


def get_str_config(group: str, key: str, fallback=None, *args, **kwargs) -> str:
    value = config[group].get(key)
    if not value and fallback:
        new_value = fallback(*args, **kwargs) if callable(fallback) else fallback
        if value != new_value:
            set_str_config(group, key, new_value)
            value = new_value
    return value


def set_str_config(group: str, key: str, value: str) -> str:
    old_value = get_str_config(group, key)
    config[group][key] = value
    return old_value


def get_bool_config(group: str, key: str, fallback=None, *args, **kwargs) -> bool:
    value = config[group].getboolean(key)
    if value is None and fallback:
        new_value = fallback(*args, **kwargs) if callable(fallback) else fallback
        if value != new_value:
            set_bool_config(group, key, new_value)
            value = new_value
    return value


def set_bool_config(group: str, key: str, value: bool) -> bool:
    old_value = get_bool_config(group, key)
    config[group][key] = str(value)
    return old_value


def get_int_config(group: str, key: str, fallback=None, *args, **kwargs) -> int:
    value = config[group].getint(key)
    if not value and fallback:
        new_value = int(fallback(*args, **kwargs)) if callable(fallback) else fallback
        if value != new_value:
            set_int_config(group, key, new_value)
            value = new_value
    return value


def set_int_config(group: str, key: str, value: int) -> int:
    old_value = get_int_config(group, key)
    config[group][key] = str(value)
    return old_value


def get_float_config(group: str, key: str, fallback=None, *args, **kwargs) -> bool:
    value = config[group].getfloat(key)
    if not value and fallback:
        new_value = float(fallback(*args, **kwargs)) if callable(fallback) else fallback
        if value != new_value:
            set_float_config(group, key, new_value)
            value = new_value
    return value


def set_float_config(group: str, key: str, value: float) -> bool:
    old_value = get_float_config(group, key)
    config[group][key] = str(value)
    return old_value


def save_configs():
    with open(CONFIG_FILE, 'w') as file:
        config.write(file)


if ENABLE_AUTO_SAVE:
    @atexit.register
    def auto_save():
        logging.debug('自动保存配置中...')
        save_configs()
        logging.debug('配置保存成功')


    signal(SIGTERM, lambda signum, stack_frame: exit(1))

# 日志配置
log_format = '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
logging.basicConfig(
    level=get_str_config('DEFAULT', 'loglevel', 'INFO'),
    filename=get_str_config('DEFAULT', 'logfile', 'tool.log'),
    filemode='a',
    format=log_format
)

sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(sh)

# 兼容配置section不存在
CONFIG_SECTIONS = [
    'COMMON',
    'DNS',
    'QINIU',
]
auto_generate_sections(CONFIG_SECTIONS)