from pydantic import BaseModel
from pathlib import Path


class TranslationModelConfig(BaseModel):
    model_path: Path
    source_language: str
    target_language: str


class SentenceModelConfig(BaseModel):
    model_file: Path


class Config(BaseModel):
    translation_configs: list[TranslationModelConfig]
    sentence_config: SentenceModelConfig
    server_port: int = 50051
    num_workers: int = 4


def load_config(config_file: Path = Path("config.json")) -> Config:
    return Config.model_validate_json(config_file.read_text())
