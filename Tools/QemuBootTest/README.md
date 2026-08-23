# QEMU boot test

This directory contains the development preflight test for the macUSBoot
classic-BIOS boot path. Run it after validating a Release container and before
final trials on physical hardware.

The test uses only synthetic, unlicensed content. Its `BOOTMGR` file is a
purpose-built 16-bit placeholder and is not Microsoft Windows Boot Manager.

## What the test covers

The runner extracts the MBR and StageTwo payloads from the supplied, validated
macUSBoot container and creates temporary raw disk images with the supported
layout:

- an inactive type-`0x0B` MBR partition beginning at LBA 2048;
- the macUSBoot MBR payload in bytes 0-439 of LBA 0;
- StageTwo beginning at LBA 1;
- a FAT32 partition containing a root short-name `BOOTMGR` entry.

QEMU boots each image through its classic PC BIOS. Two scenarios are required
to pass:

1. `BOOTMGR` stored in two contiguous FAT32 clusters;
2. `BOOTMGR` stored in a deliberately fragmented two-cluster chain.

After macUSBoot transfers control, the placeholder checks that:

- the BIOS drive remains in `DL`;
- `DS:SI` identifies the relocated first MBR partition entry;
- the partition entry still describes the required inactive FAT32 layout;
- the FAT32 VBR and BPB were restored at `0000:7C00`;
- data from the second `BOOTMGR` cluster reached memory.

It then reports a marker through QEMU's debug console and exits through the
QEMU-only `isa-debug-exit` device. A pass therefore requires both the expected
marker and the expected emulator exit status.

## Prerequisites

Use the supported macOS build environment described in
[Building](../../docs/Building.md).
The boot test additionally requires `qemu-system-x86_64`; Homebrew provides it
in the `qemu` formula.

The runner does not install or update dependencies.

## Running the preflight

Build and validate the Release container, then test that exact container:

```sh
make release
python3 Tools/QemuBootTest/RunBootTest.py
```

With no argument, the runner selects the current Release artifact in `build/`
from the version in `version.json`. A different macUSBoot container, including
a Debug artifact, can be supplied as the optional positional argument.

Successful output ends with both scenarios reported as `PASS`. Any invalid
container, build failure, timeout, unexpected QEMU exit, or missing handoff
marker fails the command.

Pass `--keep-work-directory` only when the generated images and logs are needed
for diagnosis. Otherwise the runner removes its private system-temporary
directory automatically.

## Safety and test boundary

The runner creates regular files under the system temporary directory and
passes them to QEMU as snapshot-backed virtual disks. It never enumerates,
opens, or writes a physical disk device.

This preflight validates macUSBoot's emulated legacy-BIOS path and handoff
contract. It does not validate Microsoft `BOOTMGR`, Windows Setup, a particular
computer's BIOS implementation, USB-controller compatibility, or physical
media. Final hardware media must be created through macUSB's supported
workflow.
