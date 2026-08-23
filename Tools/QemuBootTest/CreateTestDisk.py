#!/usr/bin/env python3

from __future__ import annotations

import struct
from pathlib import Path


SECTOR_SIZE = 512
DISK_SECTORS = 131072
PARTITION_START = 2048
PARTITION_SECTORS = DISK_SECTORS - PARTITION_START
RESERVED_SECTORS = 32
NUMBER_OF_FATS = 2
SECTORS_PER_FAT = 1000
SECTORS_PER_CLUSTER = 1
ROOT_CLUSTER = 2
BOOTMGR_FIRST_CLUSTER = 3
CONTIGUOUS_SECOND_CLUSTER = 4
FRAGMENTED_SECOND_CLUSTER = 5
FIRST_DATA_SECTOR = (
    PARTITION_START + RESERVED_SECTORS + NUMBER_OF_FATS * SECTORS_PER_FAT
)


class TestDiskError(ValueError):
    pass


def put_u16(buffer: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<H", buffer, offset, value)


def put_u32(buffer: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", buffer, offset, value)


def cluster_lba(cluster: int) -> int:
    return FIRST_DATA_SECTOR + (cluster - 2) * SECTORS_PER_CLUSTER


def build_mbr(mbr_payload: bytes) -> bytes:
    if len(mbr_payload) != 440:
        raise TestDiskError(
            f"MBR payload has {len(mbr_payload)} bytes, expected 440"
        )

    mbr = bytearray(SECTOR_SIZE)
    mbr[:440] = mbr_payload
    partition = 446
    mbr[partition] = 0x00
    mbr[partition + 1 : partition + 4] = b"\x00\x02\x00"
    mbr[partition + 4] = 0x0B
    mbr[partition + 5 : partition + 8] = b"\xff\xff\xff"
    put_u32(mbr, partition + 8, PARTITION_START)
    put_u32(mbr, partition + 12, PARTITION_SECTORS)
    mbr[510:512] = b"\x55\xaa"
    return bytes(mbr)


def build_vbr() -> bytes:
    vbr = bytearray(SECTOR_SIZE)
    vbr[0:3] = b"\xeb\x58\x90"
    vbr[3:11] = b"MUSBOOT "
    put_u16(vbr, 11, SECTOR_SIZE)
    vbr[13] = SECTORS_PER_CLUSTER
    put_u16(vbr, 14, RESERVED_SECTORS)
    vbr[16] = NUMBER_OF_FATS
    put_u16(vbr, 17, 0)
    put_u16(vbr, 19, 0)
    vbr[21] = 0xF8
    put_u16(vbr, 22, 0)
    put_u16(vbr, 24, 63)
    put_u16(vbr, 26, 255)
    put_u32(vbr, 28, PARTITION_START)
    put_u32(vbr, 32, PARTITION_SECTORS)
    put_u32(vbr, 36, SECTORS_PER_FAT)
    put_u16(vbr, 40, 0)
    put_u16(vbr, 42, 0)
    put_u32(vbr, 44, ROOT_CLUSTER)
    put_u16(vbr, 48, 1)
    put_u16(vbr, 50, 6)
    vbr[64] = 0x80
    vbr[66] = 0x29
    put_u32(vbr, 67, 0x4D555342)
    vbr[71:82] = b"MACUSBOOT  "
    vbr[82:90] = b"FAT32   "
    vbr[510:512] = b"\x55\xaa"
    return bytes(vbr)


def build_fat(second_cluster: int) -> bytes:
    fat = bytearray(SECTORS_PER_FAT * SECTOR_SIZE)
    put_u32(fat, 0, 0x0FFFFFF8)
    put_u32(fat, 4, 0x0FFFFFFF)
    put_u32(fat, ROOT_CLUSTER * 4, 0x0FFFFFFF)
    put_u32(fat, BOOTMGR_FIRST_CLUSTER * 4, second_cluster)
    put_u32(fat, second_cluster * 4, 0x0FFFFFFF)
    return bytes(fat)


def build_root_directory(bootmgr_size: int) -> bytes:
    root = bytearray(SECTOR_SIZE)
    root[0:11] = b"BOOTMGR    "
    root[11] = 0x20
    put_u16(root, 20, BOOTMGR_FIRST_CLUSTER >> 16)
    put_u16(root, 26, BOOTMGR_FIRST_CLUSTER & 0xFFFF)
    put_u32(root, 28, bootmgr_size)
    return bytes(root)


def create_test_disk(
    mbr_payload: bytes,
    stage_payload: bytes,
    bootmgr: bytes,
    image_path: Path,
    *,
    fragmented: bool,
) -> None:
    if not stage_payload or len(stage_payload) % SECTOR_SIZE != 0:
        raise TestDiskError("StageTwo payload is empty or not sector aligned")
    if len(stage_payload) > (PARTITION_START - 1) * SECTOR_SIZE:
        raise TestDiskError("StageTwo payload overlaps the FAT32 partition")
    if len(bootmgr) != 2 * SECTOR_SIZE:
        raise TestDiskError(
            f"BOOTMGR placeholder has {len(bootmgr)} bytes, expected 1024"
        )

    data_clusters = (
        PARTITION_SECTORS - RESERVED_SECTORS - NUMBER_OF_FATS * SECTORS_PER_FAT
    ) // SECTORS_PER_CLUSTER
    fat_capacity = SECTORS_PER_FAT * SECTOR_SIZE // 4
    if data_clusters < 65525 or fat_capacity < data_clusters + 2:
        raise TestDiskError("synthetic FAT32 geometry is internally invalid")

    second_cluster = (
        FRAGMENTED_SECOND_CLUSTER if fragmented else CONTIGUOUS_SECOND_CLUSTER
    )
    fat = build_fat(second_cluster)

    with image_path.open("w+b") as image:
        image.truncate(DISK_SECTORS * SECTOR_SIZE)
        image.seek(0)
        image.write(build_mbr(mbr_payload))
        image.seek(SECTOR_SIZE)
        image.write(stage_payload)
        image.seek(PARTITION_START * SECTOR_SIZE)
        image.write(build_vbr())

        for fat_index in range(NUMBER_OF_FATS):
            fat_lba = (
                PARTITION_START
                + RESERVED_SECTORS
                + fat_index * SECTORS_PER_FAT
            )
            image.seek(fat_lba * SECTOR_SIZE)
            image.write(fat)

        image.seek(cluster_lba(ROOT_CLUSTER) * SECTOR_SIZE)
        image.write(build_root_directory(len(bootmgr)))
        image.seek(cluster_lba(BOOTMGR_FIRST_CLUSTER) * SECTOR_SIZE)
        image.write(bootmgr[:SECTOR_SIZE])
        image.seek(cluster_lba(second_cluster) * SECTOR_SIZE)
        image.write(bootmgr[SECTOR_SIZE:])
