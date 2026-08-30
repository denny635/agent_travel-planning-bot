import logging
import logging.config
import os

import yaml
from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI


def load_config(path):
    root = os.path.dirname(path)
    config_file_path = os.path.join(root, "config/config.yaml")

    with open(config_file_path, "r") as file:
        config = yaml.safe_load(file)

    return config


def setup_logging(path):
    root = os.path.dirname(path)
    logging.config.fileConfig(os.path.join(root, "config/logging.ini"))
    # 屏蔽 httpcore 的 DEBUG 日志
    logging.getLogger("httpcore").setLevel(logging.INFO)


class LLMManager:
    _llm_client: ChatOpenAI = None

    @classmethod
    def use_llm(cls, llmtype=""):
        """指定使用哪个厂商的大模型，并配置好对应的大模型环境变量

        Args:
            llmtype (str, optional): 选择的大模型厂商类别，默认是会读取 OPENAI_API_KEY、OPENAI_API_BASE、MODEL 环境变量

        Raises:
            ValueError: 没有找到 .env 文件时，返回异常

        Returns:
            返回 bool 类型，表示配置成功或失败
        """
        dotenv_file = find_dotenv()
        print("dotenv_file:", dotenv_file)
        load_env = load_dotenv(dotenv_file)
        if not load_env:
            raise ValueError("没有找到 .env 文件")

        env_names = None  #  后面分别用来存储 api_key, base_url, model 的对应环境变量名称
        if llmtype.lower() == "chatgpt":
            env_names = ("CHATGPT_OPENAI_API_KEY", "CHATGPT_OPENAI_BASE_URL", "CHATGPT_MODEL")
        elif llmtype.lower() == "deepseek":
            env_names = ("DEEPSEEK_OPENAI_API_KEY", "DEEPSEEK_OPENAI_BASE_URL", "DEEPSEEK_MODEL")
        elif llmtype.lower() == "qianwen":
            env_names = ("QIANWEN_OPENAI_API_KEY", "QIANWEN_OPENAI_BASE_URL", "QIANWEN_MODEL")
        if env_names:
            os.environ["OPENAI_API_KEY"], os.environ["OPENAI_API_BASE"], os.environ["MODEL"] = (
                os.getenv(env_names[0]),
                os.getenv(env_names[1]),
                os.getenv(env_names[2]),
            )
        if not (os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_BASE") and os.getenv("MODEL")):
            raise ValueError("没有找到大模型实例化时的环境参数")
        return True

    @classmethod
    def get_llm_client(cls) -> ChatOpenAI:
        # 初始化大语言模型
        if not cls._llm_client:
            cls._llm_client = ChatOpenAI(model=os.environ["MODEL"])
        return cls._llm_client
