import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""

    # API 配置
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Sherpa ASR 配置
    sherpa_encoder_path: str = "assets/models/zipformer/encoder-epoch-99-avg-1.onnx"
    sherpa_decoder_path: str = "assets/models/zipformer/decoder-epoch-99-avg-1.onnx"
    sherpa_joiner_path: str = "assets/models/zipformer/joiner-epoch-99-avg-1.onnx"
    sherpa_tokens_path: str = "assets/models/zipformer/tokens.txt"
    sherpa_num_threads: int = 4
    sherpa_provider: str = "cpu"
    sherpa_decoding_method: str = "greedy_search"

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
