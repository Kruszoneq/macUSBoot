SHELL := /bin/sh
export PYTHONDONTWRITEBYTECODE := 1

NASM := nasm
NASM_FLAGS := -w+all -Werror
NASM_SOURCE_FLAGS := -I Source/
SHASUM := shasum
SED := sed
WC := wc

BUILD_DIRECTORY := build
MBR_SOURCE := Source/MbrBootstrap.asm
STAGE_SOURCE := Source/StageLoader.asm
STAGE_FORMAT := Source/StageFormat.inc
FAT_FORMAT := Source/FatFormat.inc
BIOS_CONSTANTS := Source/BiosConstants.inc
STAGE_MESSAGES := Source/StageMessages.inc
BIOS_DISK := Source/BiosDisk.inc
FAT_VOLUME := Source/FatVolume.inc
FAT_DIRECTORY := Source/FatDirectory.inc
FAT_CHAIN := Source/FatChain.inc
BOOT_MANAGER_LOADER := Source/BootManagerLoader.inc
BOOT_HANDOFF := Source/BootHandoff.inc
ARTIFACT_TOOL := Tools/ArtifactTool.py
STAGE_VALIDATOR := Tools/ValidateStage.sh
VERSION_FILE := version.json
VERSION := $(shell $(SED) -n 's/^[[:space:]]*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' $(VERSION_FILE))
VERSION_INCLUDE := $(BUILD_DIRECTORY)/Version.inc
DEBUG_ARTIFACT := $(BUILD_DIRECTORY)/macUSBoot-v$(VERSION)-debug.bin
DEBUG_CHECKSUM := $(DEBUG_ARTIFACT).sha256
DEBUG_MBR_PAYLOAD := $(BUILD_DIRECTORY)/MbrPayload.bin
DEBUG_STAGE_PAYLOAD := $(BUILD_DIRECTORY)/StagePayload.bin
RELEASE_ARTIFACT := $(BUILD_DIRECTORY)/macUSBoot-v$(VERSION).bin
RELEASE_CHECKSUM := $(RELEASE_ARTIFACT).sha256
RELEASE_MBR_PAYLOAD := $(BUILD_DIRECTORY)/ReleaseMbrPayload.bin
RELEASE_STAGE_PAYLOAD := $(BUILD_DIRECTORY)/ReleaseStagePayload.bin
MBR_BOOTSTRAP_SIZE := 440
STAGE_SIZE := 2560
STAGE_PREREQUISITES := $(STAGE_SOURCE) $(STAGE_FORMAT) $(FAT_FORMAT) \
	$(BIOS_CONSTANTS) $(STAGE_MESSAGES) $(BIOS_DISK) $(FAT_VOLUME) \
	$(FAT_DIRECTORY) $(FAT_CHAIN) $(BOOT_MANAGER_LOADER) $(BOOT_HANDOFF) \
	$(VERSION_INCLUDE)

.DEFAULT_GOAL := help

.PHONY: help debug release validate validaterelease clean checktools

help:
	@echo "Available targets:"
	@echo "  make debug     Build the self-contained debug artifact"
	@echo "  make release   Build and self-validate the distributable Release artifact"
	@echo "  make validate  Validate the Debug container, StageTwo, and checksum"
	@echo "  make clean     Remove generated build artifacts"

debug: checktools $(DEBUG_ARTIFACT) $(DEBUG_CHECKSUM) validate

release: checktools $(RELEASE_ARTIFACT) $(RELEASE_CHECKSUM) validaterelease

validate: $(DEBUG_ARTIFACT) $(DEBUG_CHECKSUM) $(DEBUG_MBR_PAYLOAD) $(DEBUG_STAGE_PAYLOAD)
	@python3 "$(ARTIFACT_TOOL)" validate "$(DEBUG_ARTIFACT)"
	@size=`$(WC) -c < "$(DEBUG_MBR_PAYLOAD)" | tr -d ' '`; \
	if [ "$$size" -ne "$(MBR_BOOTSTRAP_SIZE)" ]; then \
		echo "Invalid MBR bootstrap size: $$size bytes (expected $(MBR_BOOTSTRAP_SIZE))." >&2; \
		exit 1; \
	fi
	@size=`$(WC) -c < "$(DEBUG_STAGE_PAYLOAD)" | tr -d ' '`; \
	if [ "$$size" -ne "$(STAGE_SIZE)" ]; then \
		echo "Invalid stage size: $$size bytes (expected $(STAGE_SIZE))." >&2; \
		exit 1; \
	fi
	@/bin/sh "$(STAGE_VALIDATOR)" "$(DEBUG_STAGE_PAYLOAD)"
	@cd "$(BUILD_DIRECTORY)" && $(SHASUM) -a 256 -c "$(notdir $(DEBUG_CHECKSUM))"

validaterelease: $(RELEASE_ARTIFACT) $(RELEASE_CHECKSUM) $(RELEASE_MBR_PAYLOAD) $(RELEASE_STAGE_PAYLOAD)
	@python3 "$(ARTIFACT_TOOL)" validate-release "$(RELEASE_ARTIFACT)" "$(RELEASE_CHECKSUM)" "$(VERSION)" "$(STAGE_SIZE)"

checktools:
	@command -v "$(NASM)" >/dev/null 2>&1 || { \
		echo "Missing NASM. Install declared dependencies with: brew bundle" >&2; \
		exit 1; \
	}
	@for tool in od python3 shasum; do \
		command -v "$$tool" >/dev/null 2>&1 || { \
			echo "Missing required host tool: $$tool" >&2; \
			exit 1; \
		}; \
		done
	@test -n "$(VERSION)" || { \
		echo "Unable to read the version from $(VERSION_FILE)." >&2; \
		exit 1; \
	}
	@python3 "$(ARTIFACT_TOOL)" validate-version "$(VERSION)"

$(BUILD_DIRECTORY):
	@mkdir -p "$@"

$(VERSION_INCLUDE): $(VERSION_FILE) | $(BUILD_DIRECTORY)
	@printf '%%define VERSION_STRING "%s"\n' "$(VERSION)" > "$@"

$(DEBUG_MBR_PAYLOAD): BUILD_DEBUG_VALUE := 1
$(RELEASE_MBR_PAYLOAD): BUILD_DEBUG_VALUE := 0
$(DEBUG_MBR_PAYLOAD) $(RELEASE_MBR_PAYLOAD): $(MBR_SOURCE) $(STAGE_FORMAT) $(BIOS_CONSTANTS) | $(BUILD_DIRECTORY)
	$(NASM) $(NASM_FLAGS) $(NASM_SOURCE_FLAGS) -f bin -DBUILD_DEBUG=$(BUILD_DEBUG_VALUE) -o "$@" "$(MBR_SOURCE)"
	@size=`$(WC) -c < "$@" | tr -d ' '`; \
	if [ "$$size" -ne "$(MBR_BOOTSTRAP_SIZE)" ]; then \
		echo "Invalid MBR bootstrap size: $$size bytes (expected $(MBR_BOOTSTRAP_SIZE))." >&2; \
		exit 1; \
	fi

$(DEBUG_STAGE_PAYLOAD): BUILD_DEBUG_VALUE := 1
$(RELEASE_STAGE_PAYLOAD): BUILD_DEBUG_VALUE := 0
$(DEBUG_STAGE_PAYLOAD) $(RELEASE_STAGE_PAYLOAD): $(STAGE_PREREQUISITES) | $(BUILD_DIRECTORY)
	$(NASM) $(NASM_FLAGS) $(NASM_SOURCE_FLAGS) -f bin -I "$(BUILD_DIRECTORY)/" -DBUILD_DEBUG=$(BUILD_DEBUG_VALUE) -o "$@" "$(STAGE_SOURCE)"
	@size=`$(WC) -c < "$@" | tr -d ' '`; \
	if [ "$$size" -ne "$(STAGE_SIZE)" ]; then \
		echo "Invalid stage size: $$size bytes (expected $(STAGE_SIZE))." >&2; \
		exit 1; \
	fi
	@/bin/sh "$(STAGE_VALIDATOR)" "$@"

$(DEBUG_ARTIFACT): $(DEBUG_MBR_PAYLOAD) $(DEBUG_STAGE_PAYLOAD) $(ARTIFACT_TOOL) | $(BUILD_DIRECTORY)
	@python3 "$(ARTIFACT_TOOL)" create "$(DEBUG_MBR_PAYLOAD)" "$(DEBUG_STAGE_PAYLOAD)" "$@"

$(RELEASE_ARTIFACT): $(RELEASE_MBR_PAYLOAD) $(RELEASE_STAGE_PAYLOAD) $(ARTIFACT_TOOL) | $(BUILD_DIRECTORY)
	@python3 "$(ARTIFACT_TOOL)" create "$(RELEASE_MBR_PAYLOAD)" "$(RELEASE_STAGE_PAYLOAD)" "$@"

$(DEBUG_CHECKSUM): $(DEBUG_ARTIFACT)
	@cd "$(BUILD_DIRECTORY)" && $(SHASUM) -a 256 "$(notdir $(DEBUG_ARTIFACT))" > "$(notdir $(DEBUG_CHECKSUM))"

$(RELEASE_CHECKSUM): $(RELEASE_ARTIFACT)
	@cd "$(BUILD_DIRECTORY)" && $(SHASUM) -a 256 "$(notdir $(RELEASE_ARTIFACT))" > "$(notdir $(RELEASE_CHECKSUM))"

clean:
	@rm -rf "$(BUILD_DIRECTORY)"
