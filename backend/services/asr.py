import os
import asyncio
import logging
from typing import Optional

try:
    import sherpa_onnx
    SHERPA_AVAILABLE = True
except ImportError:
    SHERPA_AVAILABLE = False
    logging.warning("sherpa-onnx not installed, online ASR will not be available")

from config import settings
from utils import get_logger

logger = get_logger(__name__)


class SherpaASRManager:
    """
    管理 sherpa-onnx ASR 识别器的生命周期

    负责：
    - 识别器初始化
    - 创建/管理识别流
    - 音频解码
    """

    def __init__(self):
        self.recognizer: Optional[sherpa_onnx.OnlineRecognizer] = None
        self.stream: Optional[sherpa_onnx.OnlineStream] = None
        self.is_initialized: bool = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """初始化 ASR 识别器"""
        if self.is_initialized:
            return

        async with self._lock:
            if self.is_initialized:
                return

            if not SHERPA_AVAILABLE:
                raise RuntimeError("sherpa-onnx is not installed")

            # 获取模型路径
            encoder_path = os.getenv("SHERPA_ENCODER_PATH", settings.sherpa_encoder_path)
            decoder_path = os.getenv("SHERPA_DECODER_PATH", settings.sherpa_decoder_path)
            joiner_path = os.getenv("SHERPA_JOINTER_PATH", settings.sherpa_joiner_path)
            tokens_path = os.getenv("SHERPA_TOKENS_PATH", settings.sherpa_tokens_path)

            # 创建识别器
            self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
                tokens=tokens_path,
                encoder=encoder_path,
                decoder=decoder_path,
                joiner=joiner_path,
                num_threads=int(os.getenv("SHERPA_NUM_THREADS", settings.sherpa_num_threads)),
                provider=os.getenv("SHERPA_PROVIDER", settings.sherpa_provider),
                sample_rate=16000,
                feature_dim=80,
                decoding_method=os.getenv("SHERPA_DECODING_METHOD", settings.sherpa_decoding_method),
                max_active_paths=1,
                model_type="zipformer",
                modeling_unit="bpe",
            )
            self.is_initialized = True
            logger.info("Sherpa ASR recognizer initialized successfully")

    def create_stream(self) -> sherpa_onnx.OnlineStream:
        """创建新的识别流"""
        if not self.recognizer:
            raise RuntimeError("ASR recognizer not initialized")
        return self.recognizer.create_stream()

    def decode_stream(self, stream: sherpa_onnx.OnlineStream) -> str:
        """对输入流进行解码，返回当前识别结果"""
        if not self.recognizer:
            raise RuntimeError("ASR recognizer not initialized")

        while self.recognizer.is_ready(stream):
            self.recognizer.decode_stream(stream)
        return self.recognizer.get_result(stream)

    def reset_stream(self, stream: sherpa_onnx.OnlineStream) -> None:
        """重置识别流"""
        if self.recognizer and stream:
            self.recognizer.reset(stream)

    def free_stream(self, stream: sherpa_onnx.OnlineStream) -> None:
        """释放识别流（sherpa-onnx 新版本不需要手动释放）"""
        pass


# 全局 ASR 管理器实例
asr_manager = SherpaASRManager()
