from pathlib import Path
from typing import Protocol
import ctranslate2
import sentencepiece

from translation_service_example.config import TranslationModelConfig
from translation_service_example.proto.translation_service_example_pb2 import (
    TranslationConfig,
)


class NoResultsException(ValueError):
    input_text: str

    def __init__(self, input_text: str):
        self.input_text = input_text
        super().__init__(f'Failed to translate "{input_text}". No results')


class ModelNotSupported(ValueError):
    def __init__(self, src: str, tgt: str):
        self.src = src
        self.tgt = tgt
        super().__init__(f"Translation for {src} to {tgt} not supported")


class TranslationModel:
    model: ctranslate2.Translator

    def __init__(
        self,
        model_path: Path,
    ):
        self.model = ctranslate2.Translator(str(model_path))

    def translate(
        self, text: str, tokenizer: sentencepiece.SentencePieceProcessor
    ) -> str:
        tokens = tokenizer.Encode(text, out_type=str)
        result = self.model.translate_batch([tokens])
        if len(result) == 0:
            raise NoResultsException(text)

        return tokenizer.Decode(result[0].hypotheses[0])


class TranslationService(Protocol):

    def is_model_supported(self, src_lang: str, tgt_lang: str) -> bool: ...

    def supported_models(self) -> list[TranslationConfig]: ...

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str: ...


class Translator(TranslationService):
    _tokenizer: sentencepiece.SentencePieceProcessor
    _translators: dict[str, TranslationModel]

    def __init__(
        self,
        tokenizer_model_file: Path,
        translation_models: list[TranslationModelConfig],
    ):
        self._tokenizer = sentencepiece.SentencePieceProcessor()
        self._tokenizer.LoadFromFile(str(tokenizer_model_file))
        self._translators = {}
        for model in translation_models:
            self._translators[f"{model.source_language}:{model.target_language}"] = (
                TranslationModel(model.model_path)
            )

    def supported_models(self) -> list[TranslationConfig]:
        models = []
        for key in self._translators.keys():
            src, tgt = key.split(":")
            models.append(TranslationConfig(src_lang=src, tgt_lang=tgt))
        return models

    def is_model_supported(self, src_lang: str, tgt_lang: str) -> bool:
        return f"{src_lang}:{tgt_lang}" in self._translators

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        if not self.is_model_supported(src_lang, tgt_lang):
            raise ModelNotSupported(src_lang, tgt_lang)
        model = self._translators[f"{src_lang}:{tgt_lang}"]
        return model.translate(text, self._tokenizer)
