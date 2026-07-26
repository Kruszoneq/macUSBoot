# Source Provenance

## Policy

macUSBoot is independently implemented and distributed under the MIT License.
Consulting a specification, article, repository, or binary behavior does not
grant permission to copy its code or data.

The project does not contain:

- Microsoft boot files or binary boot records;
- source or binary code copied, translated, or adapted from another bootloader;
- GPL or other copyleft implementation code;
- raw physical-media images or Windows installation content.

Any future source reuse requires exact source identification, license review,
distribution analysis, and explicit approval before incorporation.

## Project integration source

### macUSB

- Project: `Kruszoneq/macUSB`
- URL: https://github.com/Kruszoneq/macUSB
- License: MIT
- Purpose: define the Windows-media workflow, integration boundary, and required
  MBR/FAT32/LBA-2048 disk layout.
- Code reused: no.

## Firmware and disk interfaces

### IBM Personal Computer AT Technical Reference

- Source: IBM Personal Computer AT Technical Reference, September 1985.
- URL: https://www.bitsavers.org/pdf/ibm/pc/at/6139362_PC_AT_Technical_Reference_Sep85.pdf
- Purpose: document the real-mode BIOS video, keyboard, disk, and bootstrap
  service roles used by macUSBoot.
- Code reused: no BIOS listing or binary data was copied or embedded.

### BIOS Boot Specification

- Source: BIOS Boot Specification, version 1.01.
- URL: https://www.scs.stanford.edu/nyu/04fa/lab/specsbbs101.pdf
- Purpose: define the BIOS boot-drive value in `DL`, legacy boot-device
  behavior, and BIOS bootstrap restart boundary.
- Code reused: no.

### Enhanced Disk Drive Specification

- Source: Enhanced Disk Drive Specification, version 1.1.
- URL: https://www.t10.org/ftp/t10/document.95/95-153r0.pdf
- Purpose: define INT 13h Extensions discovery, packet reads, the disk address
  packet, BIOS drive input, transfer limits, and error behavior.
- Implementation impact: macUSBoot requires packet access, uses the
  BIOS-provided drive, restores packet inputs before retrying, and keeps its
  StageTwo transfer within the documented block limit.
- Code reused: no.

## Filesystem and Windows boot path

### Microsoft FAT32 File System Specification

- Source: Microsoft Extensible Firmware Initiative FAT32 File System
  Specification, version 1.03.
- URL: https://download.microsoft.com/download/1/6/1/161ba512-40e2-4cc9-843a-923143f3456c/fatgen103.doc
- Owner: Microsoft Corporation.
- Purpose: define FAT32 BPB fields, FAT selection and cluster calculations,
  directory entries, short-name matching, and file-chain traversal.
- Implementation impact: StageTwo independently implements the read-only FAT32
  validation, root traversal, exact `BOOTMGR` lookup, and cluster-chain loading
  required by its controlled boot path.
- Code reused: no sample code, binary data, or boot record was copied,
  translated, or adapted.

### Microsoft BIOS/MBR boot documentation

- Sources: Microsoft Learn documentation for `bootsect`, BIOS/MBR deployment,
  and Windows startup troubleshooting.
- URLs:
  - https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/bootsect-command-line-options
  - https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/configure-biosmbr-based-hard-drive-partitions
  - https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/windows-boot-issues-troubleshooting
- Purpose: define terminology and the boundary between MBR execution,
  volume boot context, Windows Boot Manager, and Windows Setup.
- Code reused: no.

### BOOTMGR interoperability behavior

- Source: original Microsoft `BOOTMGR` supplied by a user-owned Windows
  installation source.
- Owner: Microsoft Corporation.
- Purpose: determine the legacy runtime state required for an independently
  implemented handoff.
- Implementation impact: macUSBoot loads `BOOTMGR` at physical address
  `0x00020000`, restores the original FAT32 VBR/BPB at `0x00007C00`, preserves
  the BIOS drive and relocated partition entry, and transfers control.
- Code reused: no Microsoft byte, boot record, disassembly, or derived
  implementation code is embedded or distributed.

## Firmware-mode boundary

### UEFI and CSM documentation

- Sources: UEFI Forum specifications and Microsoft firmware documentation.
- URLs:
  - https://uefi.org/specifications
  - https://learn.microsoft.com/en-us/windows-hardware/drivers/bringup/frequently-asked-questions
- Purpose: distinguish native UEFI from classic BIOS and firmware-provided
  Legacy/CSM execution.
- Implementation impact: native UEFI is outside macUSBoot; Legacy/CSM is not a
  guaranteed macUSBoot target.
- Code reused: no.

## Independent implementation references

The Rufus, ms-sys, and GNU GRUB projects were consulted only to understand
general bootloader approaches and licensing boundaries:

- https://github.com/pbatard/rufus — GPL-3.0;
- https://ms-sys.sourceforge.net/ — GNU GPL;
- https://www.gnu.org/software/grub/ — GPL-3.0-or-later.

No source code, algorithm translation, binary boot record, or redistributable
material from these projects is present in macUSBoot.
