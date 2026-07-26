# Troubleshooting

This guide covers safe first steps and every fatal error that macUSBoot can
display during the classic-BIOS boot path.

## If macUSBoot does not start

If the macUSBoot name and progress messages never appear, check that USB boot
is enabled in the BIOS and that the computer's BIOS supports booting from USB.
If the screen still does not appear, try another USB port and another USB flash
drive.

A normal start displays the installed product version followed by:

```text
macUSBoot v<version>

Preparing the boot environment...
Reading the Windows installation media...
Locating Windows Boot Manager...
Loading Windows Boot Manager...
Starting Windows Boot Manager...
```

## If macUSBoot reports an error

macUSBoot displays a stable error identifier and waits for a key before
restarting. Record the identifier and visible message before pressing a key.

Then:

1. Create the Windows installation medium again using macUSB.
2. If the error repeats, try another USB port.
3. If the problem continues, create the medium on another USB flash drive.

For `C01`, also check that USB boot and Legacy USB storage support are enabled
in the BIOS when those settings are available. For `F05` or `F07`, use an
official Windows ISO supported by the current macUSB version.

> [!WARNING]
> Do not manually repair or bypass macUSBoot structures, MBR data, StageTwo,
> FAT32 metadata, or installation checks. Recreate the Windows installation
> medium using macUSB instead.

## Error reference

| Displayed error | Meaning |
| --- | --- |
| `Error C01: No disk access.` | The BIOS disk interface required by the MBR is unavailable |
| `Error C02: Bad layout.` | The partition layout does not match the layout required by macUSBoot |
| `Error C03: Read failed.` | The MBR could not read StageTwo after three attempts |
| `Error C04: Bad header.` | The StageTwo header or entry metadata is invalid |
| `Error C05: Bad data.` | The final StageTwo data marker is invalid |
| `Error C06: The bootloader handoff is invalid.` | The MBR-to-StageTwo handoff data is invalid |
| `Error F01: The Windows volume could not be read.` | The FAT32 volume boot sector could not be read |
| `Error F02: The FAT32 volume layout is unsupported.` | The FAT32 metadata or derived volume layout is unsupported |
| `Error F03: The Windows file system could not be read.` | Required FAT32, directory, `BOOTMGR`, or volume data could not be read |
| `Error F04: The root directory is invalid.` | The FAT32 root-directory traversal is invalid |
| `Error F05: Windows Boot Manager was not found.` | A valid root `BOOTMGR` file was not found |
| `Error F06: Windows Boot Manager data is invalid.` | The `BOOTMGR` size or FAT32 cluster chain is invalid |
| `Error F07: Windows Boot Manager is too large.` | `BOOTMGR` does not fit the supported conventional-memory load area |

## Reporting a problem

macUSBoot is not intended for standalone installation on USB media. It is
installed by macUSB as part of the supported Windows media preparation
workflow.

If you encounter a problem while booting with macUSBoot, report it through
[macUSB Issues](https://github.com/Kruszoneq/macUSB/issues).
