# macUSBoot

macUSBoot is a classic-BIOS bootloader that loads the original Microsoft
`BOOTMGR` from compatible FAT32 Windows installation media.

> [!IMPORTANT]
> macUSBoot is installed by macUSB as part of its supported Windows-media
> workflow. It is not intended for standalone installation.

## Boot path and compatibility

The classic BIOS starts the macUSBoot Master Boot Record (MBR), which checks the
disk layout and BIOS disk access before loading StageTwo. StageTwo reads the
FAT32 partition, loads the original Microsoft `BOOTMGR`, restores the Windows
boot context, and transfers control to Windows Boot Manager.

The distributed macUSBoot `.bin` file is a versioned container intended for use
by macUSB, not a raw disk image. It contains separate MBR and StageTwo
components and must never be written directly to a USB device.

> [!NOTE]
> macUSBoot is designed for classic BIOS systems. Native UEFI is outside this
> boot path, and operation through firmware-provided Legacy or Compatibility
> Support Module (CSM) modes is not guaranteed.

## Building

Build the Release artifact on macOS with:

```sh
make release
```

## Troubleshooting

For boot errors and recovery guidance, see
[Troubleshooting](docs/Troubleshooting.md).

## License

Licensed under the MIT License.

Copyright © 2026 Krystian Pierz
