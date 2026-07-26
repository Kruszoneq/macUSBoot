#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

from ReleasePolicy import (
    ReleasePolicyError,
    validate_release_stage,
    validate_version,
)


MAGIC = b"MUSBPKG\0"
FORMAT_VERSION = 1
HEADER_SIZE = 32
FLAGS = 0
MBR_PAYLOAD_SIZE = 440
STAGE_SECTOR_SIZE = 512
STAGE_MAX_SECTORS = 64
HEADER = struct.Struct("<8sBBHIIIII")


class ArtifactError(ValueError):
    pass


def validate_stage(data: bytes) -> None:
    if not data:
        raise ArtifactError("StageTwo payload is empty")
    if len(data) % STAGE_SECTOR_SIZE != 0:
        raise ArtifactError("StageTwo payload is not sector aligned")
    if data[0] != 0xEB or data[1] > 0x7F:
        raise ArtifactError("StageTwo entry jump is invalid")
    if data[2:6] != b"MUSB":
        raise ArtifactError("StageTwo magic is invalid")
    if data[6] != 1 or data[7] != 16:
        raise ArtifactError("StageTwo format version or header size is invalid")

    sector_count, entry_offset = struct.unpack_from("<HH", data, 8)
    flags = struct.unpack_from("<I", data, 12)[0]
    if not 1 <= sector_count <= STAGE_MAX_SECTORS:
        raise ArtifactError("StageTwo sector count is outside the supported range")
    if len(data) != sector_count * STAGE_SECTOR_SIZE:
        raise ArtifactError("StageTwo sector count does not match its payload size")
    if not 16 <= entry_offset < len(data) - 4:
        raise ArtifactError("StageTwo entry offset is outside its payload")
    if entry_offset != 2 + data[1]:
        raise ArtifactError("StageTwo entry offset does not match its entry jump")
    if flags != 0:
        raise ArtifactError("StageTwo version 1 flags are not zero")
    if data[-4:] != b"MEND":
        raise ArtifactError("StageTwo final marker is invalid")


def parse_artifact(path: Path) -> tuple[bytes, bytes]:
    if not path.is_file():
        raise ArtifactError("artifact is not a regular file")
    data = path.read_bytes()
    if len(data) < HEADER_SIZE:
        raise ArtifactError("artifact is shorter than its header")

    (
        magic,
        version,
        header_size,
        flags,
        artifact_size,
        mbr_offset,
        mbr_size,
        stage_offset,
        stage_size,
    ) = HEADER.unpack_from(data)

    if magic != MAGIC:
        raise ArtifactError("container magic is invalid")
    if version != FORMAT_VERSION:
        raise ArtifactError("container format version is unsupported")
    if header_size != HEADER_SIZE:
        raise ArtifactError("container header size is invalid")
    if flags != FLAGS:
        raise ArtifactError("container version 1 flags are not zero")
    if artifact_size != len(data):
        raise ArtifactError("declared container size does not match the file")
    if mbr_offset != HEADER_SIZE:
        raise ArtifactError("MBR payload does not immediately follow the header")
    if mbr_size != MBR_PAYLOAD_SIZE:
        raise ArtifactError("MBR payload is not exactly 440 bytes")
    if stage_offset != mbr_offset + mbr_size:
        raise ArtifactError("StageTwo payload does not immediately follow the MBR payload")
    if stage_size == 0 or stage_size % STAGE_SECTOR_SIZE != 0:
        raise ArtifactError("StageTwo payload size is invalid")
    if stage_offset + stage_size != artifact_size:
        raise ArtifactError("component extents do not exactly fill the container")

    mbr = data[mbr_offset : mbr_offset + mbr_size]
    stage = data[stage_offset : stage_offset + stage_size]
    validate_stage(stage)
    return mbr, stage


def create_artifact(mbr_path: Path, stage_path: Path, output_path: Path) -> None:
    if not mbr_path.is_file():
        raise ArtifactError("MBR payload is not a regular file")
    if not stage_path.is_file():
        raise ArtifactError("StageTwo payload is not a regular file")

    mbr = mbr_path.read_bytes()
    stage = stage_path.read_bytes()
    if len(mbr) != MBR_PAYLOAD_SIZE:
        raise ArtifactError("MBR payload is not exactly 440 bytes")
    validate_stage(stage)

    mbr_offset = HEADER_SIZE
    stage_offset = mbr_offset + len(mbr)
    artifact_size = stage_offset + len(stage)
    header = HEADER.pack(
        MAGIC,
        FORMAT_VERSION,
        HEADER_SIZE,
        FLAGS,
        artifact_size,
        mbr_offset,
        len(mbr),
        stage_offset,
        len(stage),
    )
    output_path.write_bytes(header + mbr + stage)
    parse_artifact(output_path)


def validate_release_artifact(
    artifact_path: Path,
    checksum_path: Path,
    expected_version: str,
    expected_stage_size: int,
) -> tuple[bytes, bytes, str]:
    try:
        validate_version(expected_version)
    except ReleasePolicyError as error:
        raise ArtifactError(str(error)) from None

    expected_artifact_name = f"macUSBoot-v{expected_version}.bin"
    expected_checksum_name = f"{expected_artifact_name}.sha256"
    if artifact_path.name != expected_artifact_name:
        raise ArtifactError(
            f"Release artifact name is not exactly {expected_artifact_name}"
        )
    if checksum_path.name != expected_checksum_name:
        raise ArtifactError(
            f"Release checksum name is not exactly {expected_checksum_name}"
        )
    if expected_stage_size <= 0 or expected_stage_size % STAGE_SECTOR_SIZE != 0:
        raise ArtifactError("expected Release StageTwo size is invalid")

    mbr, stage = parse_artifact(artifact_path)
    if len(stage) != expected_stage_size:
        raise ArtifactError(
            "Release StageTwo size is "
            f"{len(stage)} bytes, expected {expected_stage_size}"
        )
    try:
        validate_release_stage(stage, expected_version)
    except ReleasePolicyError as error:
        raise ArtifactError(str(error)) from None

    if not checksum_path.is_file():
        raise ArtifactError("Release checksum is not a regular file")
    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    expected_checksum = f"{digest}  {expected_artifact_name}\n"
    try:
        checksum = checksum_path.read_bytes().decode("ascii")
    except UnicodeError as error:
        raise ArtifactError("Release checksum is not ASCII text") from error
    if checksum != expected_checksum:
        raise ArtifactError(
            "Release checksum content or referenced filename is invalid"
        )

    return mbr, stage, digest


def command_create(arguments: argparse.Namespace) -> None:
    create_artifact(Path(arguments.mbr), Path(arguments.stage), Path(arguments.output))
    print(f"macUSBoot container created: {arguments.output}")


def command_validate(arguments: argparse.Namespace) -> None:
    mbr, stage = parse_artifact(Path(arguments.artifact))
    print(
        "macUSBoot container valid: "
        f"format {FORMAT_VERSION}, {len(mbr)}-byte MBR payload, "
        f"{len(stage)}-byte StageTwo payload."
    )


def command_validate_version(arguments: argparse.Namespace) -> None:
    try:
        validate_version(arguments.version)
    except ReleasePolicyError as error:
        raise ArtifactError(str(error)) from None
    print(f"macUSBoot version valid: {arguments.version}.")


def command_validate_release(arguments: argparse.Namespace) -> None:
    mbr, stage, digest = validate_release_artifact(
        Path(arguments.artifact),
        Path(arguments.checksum),
        arguments.version,
        arguments.stage_size,
    )
    print(
        "macUSBoot Release valid: "
        f"version {arguments.version}, {len(mbr)}-byte MBR payload, "
        f"{len(stage)}-byte StageTwo payload, SHA-256 {digest}."
    )


def command_extract(arguments: argparse.Namespace) -> None:
    mbr, stage = parse_artifact(Path(arguments.artifact))
    Path(arguments.mbr_output).write_bytes(mbr)
    Path(arguments.stage_output).write_bytes(stage)
    print("macUSBoot container extracted.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and validate macUSBoot containers")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="create one container from both disk payloads")
    create.add_argument("mbr")
    create.add_argument("stage")
    create.add_argument("output")
    create.set_defaults(function=command_create)

    validate = commands.add_parser("validate", help="validate a complete container")
    validate.add_argument("artifact")
    validate.set_defaults(function=command_validate)

    validate_version_command = commands.add_parser(
        "validate-version", help="validate the configured release version"
    )
    validate_version_command.add_argument("version")
    validate_version_command.set_defaults(function=command_validate_version)

    validate_release = commands.add_parser(
        "validate-release", help="validate a distributable Release and checksum"
    )
    validate_release.add_argument("artifact")
    validate_release.add_argument("checksum")
    validate_release.add_argument("version")
    validate_release.add_argument("stage_size", type=int)
    validate_release.set_defaults(function=command_validate_release)

    extract = commands.add_parser("extract", help="extract both validated payloads")
    extract.add_argument("artifact")
    extract.add_argument("mbr_output")
    extract.add_argument("stage_output")
    extract.set_defaults(function=command_extract)
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    try:
        arguments.function(arguments)
    except (ArtifactError, OSError) as error:
        raise SystemExit(f"macUSBoot artifact error: {error}") from None


if __name__ == "__main__":
    main()
