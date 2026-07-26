# Architecture

## Purpose

macUSBoot is a classic-BIOS bootloader for compatible FAT32 Windows
installation media. It provides the legacy BIOS path that locates, loads, and
transfers control to the root `BOOTMGR` file. It is not a standalone USB
preparation tool.

macUSBoot contains no Microsoft boot files and does not replace or modify
`BOOTMGR`. Native UEFI is outside this boot path. Operation through UEFI Legacy
or CSM may work on some firmware, but it is not guaranteed by macUSBoot.

## Boot flow

The implemented boot path is:

1. The classic BIOS loads the master boot record from LBA 0.
2. The macUSBoot MBR bootstrap relocates itself, validates the controlled disk
   layout, checks BIOS Extended Disk Drive access, and loads StageTwo from
   LBA 1-5.
3. StageTwo validates the MBR handoff and the FAT32 volume geometry.
4. StageTwo traverses the FAT32 root directory and locates the exact short-name
   `BOOTMGR` entry.
5. It follows the complete FAT32 cluster chain and loads both contiguous and
   fragmented files without modifying the filesystem.
6. It restores the original FAT32 volume boot record and BIOS boot context.
7. It transfers control to Microsoft Windows Boot Manager.

macUSBoot finishes its responsibility at the control transfer. Windows Boot
Manager, the Boot Configuration Data, Windows PE, Windows Setup, and the
subsequent installation process are outside the macUSBoot runtime.

## Disk layout

macUSBoot uses the following controlled layout:

| Disk area | Contents |
| --- | --- |
| LBA 0 bytes 0-439 | macUSBoot MBR bootstrap |
| LBA 0 bytes 440-511 | Target-owned disk signature, reserved bytes, partition table, and MBR signature |
| LBA 1-5 | Five-sector macUSBoot StageTwo |
| LBA 6-2047 | Pre-partition space not used by macUSBoot |
| LBA 2048 onward | FAT32 Windows installation partition containing the original `BOOTMGR` |

The distributed macUSBoot `.bin` file is a host-side container. It is not a raw
disk image and cannot be written verbatim at one disk offset. It contains
separate MBR and StageTwo payloads.

## Runtime components

### MBR bootstrap

`Source/MbrBootstrap.asm` produces the exact 440-byte first-stage payload. It
owns:

- real-mode entry normalization and complete-MBR relocation;
- controlled first-partition validation;
- BIOS INT 13h Extensions discovery;
- bounded StageTwo reads with three total attempts per read;
- StageTwo header, entry, size, and final-marker validation;
- the C01-C05 fatal paths;
- transfer to StageTwo with the BIOS drive and relocated partition entry.

MBR bytes 440-511 are outside the macUSBoot payload and remain target-owned
metadata.

### StageTwo

`Source/StageLoader.asm` produces the five-sector StageTwo payload and
orchestrates the visible boot workflow. Its included modules have focused
ownership:

| Module | Responsibility |
| --- | --- |
| `StageMessages.inc` | Screen initialization, progress output, C06/F01-F07 fatal output, and restart behavior |
| `BiosDisk.inc` | One-sector BIOS reads, reset-before-retry behavior, and disk-address-packet state |
| `FatVolume.inc` | FAT32 BPB validation, FAT selection, and derived volume geometry |
| `FatChain.inc` | Cluster validation, FAT entry reads, and cluster-to-sector conversion |
| `FatDirectory.inc` | Root-directory traversal, entry filtering, and `BOOTMGR` discovery |
| `BootManagerLoader.inc` | File-size validation, cluster-chain consumption, and complete file loading |
| `BootHandoff.inc` | VBR restoration, register restoration, and final transfer to `BOOTMGR` |

`StageFormat.inc`, `FatFormat.inc`, and `BiosConstants.inc` contain shared
format and firmware constants used by the runtime components.

## Memory and handoff

StageTwo is loaded at physical address `0x00007C00`. The current five-sector
payload occupies 2,560 bytes. `BOOTMGR` is loaded at physical address
`0x00020000` and may grow only within the conventional-memory extent reported
by BIOS.

Before the final transfer, macUSBoot rereads the FAT32 volume boot record,
restores it at `0x00007C00`, restores the BIOS drive in `DL`, restores the
relocated first partition entry at `DS:SI=0000:07BE`, and jumps to
`BOOTMGR` at `2000:0000`.

## Compatibility boundary

The macUSBoot runtime requires:

- classic x86 BIOS execution;
- BIOS INT 13h Extensions packet reads;
- 512-byte logical sectors;
- an MBR-partitioned disk;
- an inactive type-`0x0B` FAT32 partition in the first MBR entry;
- that partition beginning at absolute LBA 2048.

There is no CHS fallback, alternate partition-start fallback, filesystem repair,
or automatic conversion of an incompatible medium.

## User-visible behavior

Release builds display the product version, five progress lines, and stable
C01-C06 or F01-F07 fatal errors. A fatal error remains visible until a key is
pressed, after which macUSBoot invokes the BIOS bootstrap restart path once.

The exact public error catalog and recovery guidance are maintained in
[Troubleshooting](Troubleshooting.md).
