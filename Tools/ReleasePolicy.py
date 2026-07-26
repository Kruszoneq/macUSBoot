#!/usr/bin/env python3

from __future__ import annotations

import re


VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?")
EXPERIMENT_PATTERN = re.compile(rb"U-?[0-9]{3}")
RESTART_PROMPT = b"Press any key to restart..."
NORMAL_STATUS_LINES = (
    b"Preparing the boot environment...",
    b"Reading the Windows installation media...",
    b"Locating Windows Boot Manager...",
    b"Loading Windows Boot Manager...",
    b"Starting Windows Boot Manager...",
)
STAGE_ERROR_MESSAGES = {
    "C06": b"Error C06: The bootloader handoff is invalid.",
    "F01": b"Error F01: The Windows volume could not be read.",
    "F02": b"Error F02: The FAT32 volume layout is unsupported.",
    "F03": b"Error F03: The Windows file system could not be read.",
    "F04": b"Error F04: The root directory is invalid.",
    "F05": b"Error F05: Windows Boot Manager was not found.",
    "F06": b"Error F06: Windows Boot Manager data is invalid.",
    "F07": b"Error F07: Windows Boot Manager is too large.",
}
FORBIDDEN_RELEASE_STRINGS = (
    b"[Debug]",
    b"[Test]",
    b"BIOS drive DL",
    b"BOOTMGR handoff",
    b"Press any key to reboot",
    b"F01 Volume read",
    b"F05 BOOTMGR missing",
    b"/Users/",
    b"/home/",
    b"\\Users\\",
)


class ReleasePolicyError(ValueError):
    pass


def validate_version(version: str) -> bytes:
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ReleasePolicyError(
            "release version must use X.X or X.X.X numeric format"
        )
    return version.encode("ascii")


def release_transcript(version: str) -> bytes:
    encoded_version = validate_version(version)
    return (
        b"macUSBoot v"
        + encoded_version
        + b"\r\n\r\n"
        + b"\r\n".join(NORMAL_STATUS_LINES)
        + b"\r\n"
    )


def validate_release_stage(data: bytes, version: str) -> None:
    encoded_version = validate_version(version)
    banner_prefix = b"macUSBoot v"
    expected_banner = banner_prefix + encoded_version + b"\r\n\r\n"

    if data.count(banner_prefix) != 1 or data.count(expected_banner) != 1:
        raise ReleasePolicyError(
            f"embedded Release version is not exactly {version}"
        )

    required = [expected_banner]
    required.extend(line + b"\r\n" for line in NORMAL_STATUS_LINES)
    required.extend(message + b"\r\n" for message in STAGE_ERROR_MESSAGES.values())
    required.append(RESTART_PROMPT)

    missing = [value for value in required if value not in data]
    forbidden = [value for value in FORBIDDEN_RELEASE_STRINGS if value in data]
    experiment = EXPERIMENT_PATTERN.search(data)
    too_wide = [
        message for message in STAGE_ERROR_MESSAGES.values() if len(message) > 80
    ]
    if missing or forbidden or experiment is not None or too_wide:
        experiment_value = experiment.group(0) if experiment is not None else None
        raise ReleasePolicyError(
            "Release output policy failed: "
            f"missing={missing!r}; forbidden={forbidden!r}; "
            f"experiment={experiment_value!r}; too_wide={too_wide!r}"
        )
