# Building

## Supported environment

macOS is the supported build host. The build uses:

- Xcode Command Line Tools, including `make`;
- NASM for the 16-bit flat-binary bootloader components;
- Python 3 and its standard library for container creation and validation;
- standard macOS command-line utilities.

The Homebrew dependencies are declared in the root `Brewfile`. Install them
explicitly with:

```sh
brew bundle
```

The build never installs or updates dependencies automatically.

Plain `make` displays the available targets and does not build an artifact.

## Release build

Build and validate the distributable configuration with:

```sh
make release
```

The command reads the product version from `version.json` and creates:

```text
build/macUSBoot-v<version>.bin
build/macUSBoot-v<version>.bin.sha256
```

The `.bin` file is a versioned host-side container containing the MBR and
StageTwo payloads. It is not a raw disk image and is intended for macUSB
integration.

## Debug build

Build and validate the diagnostic configuration with:

```sh
make debug
```

The command creates:

```text
build/macUSBoot-v<version>-debug.bin
build/macUSBoot-v<version>-debug.bin.sha256
```

The Debug artifact is built from the production source with additional
diagnostic output for bootloader development.

The Debug target runs its validation automatically. Invoke the same validation
as a separate target with:

```sh
make validate
```

## Generated files

By default, generated files are placed under the ignored `build/` directory.
Remove them with:

```sh
make clean
```

Generated artifacts are not source files.

## Source layout

- `Source/` contains the production NASM sources and included runtime modules.
- `Tools/ArtifactTool.py` creates, parses, extracts, and validates macUSBoot
  containers.
- `Tools/ReleasePolicy.py` defines the Release output policy.
- `Tools/ValidateStage.sh` validates the StageTwo binary format used by the
  build.
- `version.json` is the single product-version source.

Runtime module responsibilities are documented in
[Architecture](Architecture.md).
