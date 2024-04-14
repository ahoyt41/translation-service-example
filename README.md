# FastAPI Example

This project is an example of a gRPC service for [Rocky Python](https://rockypython.org). 
It is a gRPC service for machine translation (MT).

## gRPC

[gRPC](https://grpc.io/) is a langauge agnostic remote procedure call (RPC) fromework.
Types and interfaces are defined using the protobuf language in .proto files. These
files can then be compiled into source code for various languages. The benefit of protobuf
is that by using generated code, the encoding, decoding, and transport for each RPC is
handled for you.

## Machine Translation

Macine Translation is the process of translating text form one language to another
using deep learning. This project utilizes [Open-NMT](https://opennmt.net/), an open source
deep learnign frame work for machine translatin and summarization. Specifically
[sentencepiece](https://github.com/google/sentencepiece) for text encoding/decoding
and [ctranslate2](https://github.com/OpenNMT/CTranslate2) for the translation.

## Setup

The project uses poetry for dependency managment and poethepoet for running tasks.

### Install Poetry

```bash
# with the official installer
curl -sSL https://install.python-poetry.org | python3

#globally with pip
pip install poetry

# or with pipx
pipx install poetry
```

## Buidling

The following command will compile the protobuf file into python and install
all of the projets dependencies.

```
make prod
```

To install the dev dependencies as well, run

```
make dev
```

## Downloading the models.

This MT service uses [ctranslate2](https://github.com/OpenNMT/CTranslate2)
form machine translation and [sentencepiece](https://github.com/google/sentencepiece)
for encoding text into tokens that `ctranslate2` can understand and decoding the response
back into text. The models can be downloaded locally by running the following.

```
make models
```

## Configuration

The server uses a `json` configuration file with the following fields

```json
{
    "title": "Translation service config",
    "type": "object",
    "properties": {
        "translation_configs": {
            "type": "array",
            "description": "An array of translation configs, one per model"
            "items": {
                "type": "object",
                "properties": {
                    "model_path": {
                        "type": "string",
                        "description": "path to the translation model directory"
                    },
                    "source_language": {
                        "type": "string",
                        "description": "model source language"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "model target language"
                    }
                }
            }
        },
        "sentence_config": {
            "type": "object",
            "properties": {
                "model_file": {
                    "type": "string",
                    "description": "path to the sentencepiece model"
                }
            }
        },
        "server_port": {
            "type": "number",
            "description": "port for the gRPC server",
            "default": 50051
        },
        "num_workers": {
            "type": "number",
            "description": "The number of thread workers to use for the gPRC server",
            "default": 4
        }
    }
}
```


## Running the Service

Once the models have been downloaded, the protobuf files have been generated, and
the core dependencies have been installed
