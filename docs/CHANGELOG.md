# Changelog

## v1.0

macUSBoot 1.0 brings classic-BIOS boot support to Windows installation media created by macUSB. It starts the original Windows Boot Manager from the installation partition and provides clear on-screen information throughout the boot process.

### ADDED

- Boot support for macUSB-created MBR/FAT32 Windows installation media on computers using a classic BIOS.
- Loading and handoff to the original Microsoft `BOOTMGR`, including fragmented files, without replacing or modifying Microsoft boot files.
- Clear boot progress and stable C01-C06 and F01-F07 diagnostic codes, with a key-triggered restart after a fatal error.
