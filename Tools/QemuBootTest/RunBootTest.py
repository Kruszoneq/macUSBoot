#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIRECTORY.parents[1]
TOOLS_DIRECTORY = REPOSITORY_ROOT / "Tools"
sys.path.insert(0, str(TOOLS_DIRECTORY))

from ArtifactTool import ArtifactError, parse_artifact  # noqa: E402
from CreateTestDisk import TestDiskError, create_test_disk  # noqa: E402


EXPECTED_MARKER = b"BOOTMGR_PLACEHOLDER_REACHED CONTEXT_OK\n"
EXPECTED_QEMU_STATUS = 85


class BootTestError(RuntimeError):
    pass


def current_release_artifact() -> Path:
    version_path = REPOSITORY_ROOT / "version.json"
    try:
        version = json.loads(version_path.read_text(encoding="utf-8"))["version"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise BootTestError(f"unable to read {version_path}: {error}") from error
    return REPOSITORY_ROOT / "build" / f"macUSBoot-v{version}.bin"


def run_checked(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return
    details = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    if details:
        details = f"\n{details}"
    raise BootTestError(
        f"command failed with status {result.returncode}: {' '.join(command)}{details}"
    )


def compile_placeholder(nasm: str, output_path: Path) -> bytes:
    source_path = SCRIPT_DIRECTORY / "BootMgrPlaceholder.asm"
    run_checked(
        [
            nasm,
            "-w+all",
            "-Werror",
            "-f",
            "bin",
            "-o",
            str(output_path),
            str(source_path),
        ]
    )
    return output_path.read_bytes()


def run_scenario(
    qemu: str,
    work_directory: Path,
    mbr_payload: bytes,
    stage_payload: bytes,
    bootmgr: bytes,
    scenario: str,
    timeout: float,
) -> None:
    image_path = work_directory / f"{scenario}.img"
    log_path = work_directory / f"{scenario}.debugcon.log"
    create_test_disk(
        mbr_payload,
        stage_payload,
        bootmgr,
        image_path,
        fragmented=scenario == "fragmented",
    )

    command = [
        qemu,
        "-machine",
        "pc,accel=tcg",
        "-m",
        "64M",
        "-drive",
        f"file={image_path},format=raw,if=ide,index=0,media=disk",
        "-snapshot",
        "-boot",
        "order=c,menu=off,strict=on",
        "-display",
        "none",
        "-serial",
        "none",
        "-parallel",
        "none",
        "-monitor",
        "none",
        "-no-reboot",
        "-chardev",
        f"file,id=debug,path={log_path}",
        "-device",
        "isa-debugcon,iobase=0xe9,chardev=debug",
        "-device",
        "isa-debug-exit,iobase=0xf4,iosize=0x04",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise BootTestError(
            f"{scenario}: QEMU did not reach the placeholder within {timeout:g} seconds"
        ) from error

    marker = log_path.read_bytes() if log_path.is_file() else b""
    if result.returncode != EXPECTED_QEMU_STATUS or marker != EXPECTED_MARKER:
        stderr = result.stderr.strip()
        details = (
            f"status={result.returncode}, marker={marker!r}"
            + (f", stderr={stderr!r}" if stderr else "")
        )
        raise BootTestError(f"{scenario}: boot handoff failed ({details})")

    print(f"PASS {scenario}: {marker.decode('ascii').strip()}")


def execute(arguments: argparse.Namespace, work_directory: Path) -> None:
    artifact_path = arguments.artifact.resolve()
    mbr_payload, stage_payload = parse_artifact(artifact_path)
    nasm = shutil.which(arguments.nasm)
    qemu = shutil.which(arguments.qemu)
    if nasm is None:
        raise BootTestError(f"required tool not found: {arguments.nasm}")
    if qemu is None:
        raise BootTestError(f"required tool not found: {arguments.qemu}")

    bootmgr = compile_placeholder(nasm, work_directory / "BOOTMGR")
    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    print(f"Artifact: {artifact_path}")
    print(f"SHA-256: {digest}")
    print("Firmware: QEMU classic PC BIOS (TCG)")

    for scenario in ("contiguous", "fragmented"):
        run_scenario(
            qemu,
            work_directory,
            mbr_payload,
            stage_payload,
            bootmgr,
            scenario,
            arguments.timeout,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="boot a validated macUSBoot container through QEMU legacy BIOS"
    )
    parser.add_argument(
        "artifact",
        nargs="?",
        type=Path,
        default=None,
        help="macUSBoot container (default: current Release artifact in build/)",
    )
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--nasm", default="nasm")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--keep-work-directory", action="store_true")
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    if arguments.artifact is None:
        arguments.artifact = current_release_artifact()
    if arguments.timeout <= 0:
        raise SystemExit("QEMU boot test failed: --timeout must be positive")

    temporary_directory: tempfile.TemporaryDirectory[str] | None = None
    if arguments.keep_work_directory:
        work_directory = Path(tempfile.mkdtemp(prefix="macUSBoot-qemu-"))
    else:
        temporary_directory = tempfile.TemporaryDirectory(prefix="macUSBoot-qemu-")
        work_directory = Path(temporary_directory.name)

    try:
        execute(arguments, work_directory)
    except (ArtifactError, BootTestError, TestDiskError, OSError) as error:
        raise SystemExit(f"QEMU boot test failed: {error}") from None
    finally:
        if temporary_directory is not None:
            temporary_directory.cleanup()

    if arguments.keep_work_directory:
        print(f"Work directory retained: {work_directory}")


if __name__ == "__main__":
    main()
