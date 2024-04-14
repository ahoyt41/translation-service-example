MODEL_URL := https://s3.amazonaws.com/opennmt-models/transformer-ende-wmt-pyOnmt.tar.gz

MODEL_TAR := models/$(notdir $(MODEL_URL))
MODEL_PT_FILE := models/averaged-10-epoch.pt
SENTENCE_MODEL := models/sentencpice.model
MODEL_DIR := models/ende_ctranslate2

MODEL_FILES := \
	$(MODEL_DIR)/config.json \
	$(MODEL_DIR)/model.bin \
	$(MODEL_DIR)/shared_vocabulary.json


PROJECT_NAME := translation_service_example

PROTO_PATH := $(PROJECT_NAME)/proto
PROTO_PACKAGE := $(PROJECT_NAME).proto

PROTO_FILES := \
	$(PROTO_PATH)/$(PROJECT_NAME)_pb2.py \
	$(PROTO_PATH)/$(PROJECT_NAME)_pb2.pyi \
	$(PROTO_PATH)/$(PROJECT_NAME)_pb2_grpc.py


.PHONY: models grpc

prod:
	$(MAKE) grpc
	poetry install --only main --sync

dev:
	$(MAKE) grpc
	poetry install --with dev

models: $(MODEL_FILES)

grpc: $(PROTO_FILES)

$(PROTO_FILES): $(PROJECT_NAME).proto
	poetry install --only grpc
	poetry run python -m grpc_tools.protoc \
		-I. \
		--python_out=$(PROTO_PATH) \
		--pyi_out=$(PROTO_PATH) \
		--grpc_python_out=$(PROTO_PATH) \
		$(PROJECT_NAME).proto
	sed -i 's/import $(PROJECT_NAME)_pb2/import $(PROTO_PACKAGE).$(PROJECT_NAME)_pb2/g' $(PROTO_PATH)/$(PROJECT_NAME)_pb2_grpc.py


$(MODEL_FILES): $(MODEL_PT_FILE)
	poetry install --only opennmt
	poetry run ct2-opennmt-py-converter \
		--model_path $(MODEL_PT_FILE) \
		--output_dir $(MODEL_DIR) \
		--quantization int8

$(MODEL_TAR):
	curl -SL $(MODEL_URL) > $(MODEL_TAR)

$(MODEL_PT_FILE) $(SENTENCE_MODEL): $(MODEL_TAR)
	tar xzf $(MODEL_TAR)

clean:
	rm -rf models $(PROTO_PATH)

$(shell mkdir -p translation_service_example/proto && touch translation_service_example/proto/__init__.py)
$(shell mkdir -p models)
