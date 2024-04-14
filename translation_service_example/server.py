from concurrent import futures
from collections.abc import Iterator
import grpc
from threading import Event
from google.protobuf.empty_pb2 import Empty

from translation_service_example.models import TranslationService, Translator
from translation_service_example.config import load_config
from translation_service_example.proto.translation_service_example_pb2 import (
    SupportedLanguagesResponse,
    TranslationRequest,
    TranslationStreamRequest,
    TranslationResponse,
)

from translation_service_example.proto.translation_service_example_pb2_grpc import (
    TranslationServiceServicer,
    add_TranslationServiceServicer_to_server,
)


class TranslationServer(TranslationServiceServicer):
    server_port: int
    num_workers: int
    shutdown: Event
    translator: TranslationService

    def __init__(
        self, translator: TranslationService, port: int = 51005, num_workers: int = 4
    ):
        self.translator = translator
        self.server_port = port
        self.num_workers = num_workers
        self.shutdown = Event()

    def Ping(self, request: Empty, context: grpc.ServicerContext) -> Empty:
        _ = request
        context.set_code(grpc.StatusCode.OK)
        return Empty()

    def Shutdown(self, request: Empty, context: grpc.ServicerContext) -> Empty:
        _ = request
        context.set_code(grpc.StatusCode.OK)
        self.shutdown.set()
        return Empty()

    def Translate(
        self, request: TranslationRequest, context: grpc.ServicerContext
    ) -> TranslationResponse:
        src = request.config.src_lang
        tgt = request.config.tgt_lang
        if not self.translator.is_model_supported(src, tgt):
            context.abort(
                grpc.StatusCode.FAILED_PRECONDITION,
                f"Translation from {src} to {tgt} is not supported",
            )
        try:
            translation = self.translator.translate(request.text, src, tgt)
            return TranslationResponse(text=translation)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Translation failed: {e}")

    def TranslateStream(
        self,
        request_iterator: Iterator[TranslationStreamRequest],
        context: grpc.ServicerContext,
    ) -> Iterator[TranslationResponse]:
        config_msg = next(request_iterator)
        if not config_msg.HasField("config"):
            context.abort(
                grpc.StatusCode.FAILED_PRECONDITION,
                "First stream message must set the config field",
            )
        src = config_msg.config.src_lang
        tgt = config_msg.config.tgt_lang
        for msg in request_iterator:
            if not msg.HasField("text"):
                context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT, "cannot translation config"
                )
            try:
                translation = self.translator.translate(msg.text, src, tgt)
                yield TranslationResponse(text=translation)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"translation failed: {e}")

    def SupportedLanguages(
        self, request: Empty, context: grpc.ServicerContext
    ) -> SupportedLanguagesResponse:
        _ = request
        _ = context
        models = self.translator.supported_models()
        return SupportedLanguagesResponse(models=models)

    def serve(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.num_workers))
        add_TranslationServiceServicer_to_server(self, server)
        server.add_insecure_port(f"[::]:{self.server_port}")
        print("Starting gRPC translation service on port", self.server_port)
        server.start()
        try:
            self.shutdown.wait()
        except KeyboardInterrupt:
            print()
        except Exception as e:
            print(e)
        server.stop(None)
        print("Stopping gRPC translation service on port", self.server_port)


def main():
    cfg = load_config()
    svc = Translator(
        cfg.sentence_config.model_file,
        cfg.translation_configs,
    )
    server = TranslationServer(svc, cfg.server_port, cfg.num_workers)
    server.serve()


if __name__ == "__main__":
    main()
