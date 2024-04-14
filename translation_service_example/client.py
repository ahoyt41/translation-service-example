from google.protobuf.empty_pb2 import Empty
import grpc
from argparse import ArgumentParser
from collections.abc import Generator, Iterator
import sys

from translation_service_example.proto.translation_service_example_pb2 import (
    TranslationRequest,
    TranslationConfig,
    TranslationStreamRequest,
)
from translation_service_example.proto.translation_service_example_pb2_grpc import (
    TranslationServiceStub,
)


def iter_file() -> Generator[str, None, None]:
    while True:
        line = input("input> ")
        if not line:
            break
        yield line


class Client:
    host: str
    port: int

    stub: TranslationServiceStub
    chan: grpc.Channel

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def __enter__(self):
        self.chan = grpc.insecure_channel(f"{self.host}:{self.port}").__enter__()
        self.stub = TranslationServiceStub(self.chan)
        return self

    def __exit__(self, *args):
        self.chan.__exit__(*args)

    def supported_languages(self) -> list[TranslationConfig]:
        return list(self.stub.SupportedLanguages(Empty()).models)

    def translate(self, src_lang: str, tgt_lang: str, text: str) -> str:
        request = TranslationRequest(
            config=TranslationConfig(src_lang=src_lang, tgt_lang=tgt_lang),
            text=text,
        )
        return self.stub.Translate(request).text

    def translate_stream(
        self, src_lang: str, tgt_lang: str, text_iter: Iterator[str]
    ) -> Iterator[str]:
        def request_iter():
            yield TranslationStreamRequest(
                config=TranslationConfig(src_lang=src_lang, tgt_lang=tgt_lang)
            )
            yield from (TranslationStreamRequest(text=text) for text in text_iter)

        yield from (resp.text for resp in self.stub.TranslateStream(request_iter()))


def main():
    parser = ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=50051)
    parser.add_argument("--src_lang", default="en")
    parser.add_argument("--tgt_lang", default="de")
    parser.add_argument("--stream", action="store_true")

    args = parser.parse_args()

    client = Client(args.host, args.port)
    with client:
        if args.stream:
            src_iter = iter_file()
            tgt_iter = client.translate_stream(args.src_lang, args.tgt_lang, src_iter)

            for trans in tgt_iter:
                print(trans)

        else:
            text = input("src> ")
            print("tgt>", client.translate(args.src_lang, args.tgt_lang, text))


if __name__ == "__main__":
    main()
