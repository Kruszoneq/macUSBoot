; BOOTMGR size validation, chain consumption, and memory-copy ownership.

; Input: FatDirectory selected bootmanagercluster and bootmanagersize, and the
; FatVolume geometry is valid. Output: the exact file is loaded beginning at
; BOOT_MANAGER_LOAD_ADDRESS. Changes EAX, ECX, EDX, DS, ES, SI, and DI;
; consumes BiosDisk and FatChain. Failures exit through F03, F06, or F07.
loadbootmanager:
    mov eax, [STAGE(bootmanagersize)]
    test eax, eax
    jz bootmanagerchainerror

    ; Round the file extent up to a complete sector and require it to fit
    ; below the conventional-memory limit reported by the BIOS.
    mov edx, eax
    add edx, 511
    jc bootmanagermemoryerror
    and edx, 0xfffffe00
    add edx, BOOT_MANAGER_LOAD_ADDRESS
    jc bootmanagermemoryerror
    push edx
    int 0x12
    movzx eax, ax
    shl eax, 10
    pop edx
    cmp edx, eax
    ja bootmanagermemoryerror

    mov eax, [STAGE(bootmanagercluster)]
    mov [STAGE(currentcluster)], eax
    mov eax, [STAGE(bootmanagersize)]
    mov [STAGE(filebytesremaining)], eax
    mov word [STAGE(loadsegment)], BOOT_MANAGER_LOAD_SEGMENT

.cluster:
    mov eax, [STAGE(currentcluster)]
    call validatecluster
    jc bootmanagerchainerror
    call clustertosector
    jc bootmanagerchainerror
    mov [STAGE(currentsector)], eax
    movzx ecx, byte [STAGE(sectorspercluster)]

.sector:
    mov eax, [STAGE(currentsector)]
    call readsector
    jc filesystemreaderror

    push cx
    xor ax, ax
    mov ds, ax
    mov ax, [STAGE(loadsegment)]
    mov es, ax
    mov si, FAT_SECTOR_BUFFER
    xor di, di
    mov cx, 256
    cld
    rep movsw
    add word [STAGE(loadsegment)], 0x20
    pop cx

    cmp dword [STAGE(filebytesremaining)], 512
    jbe .filecomplete
    sub dword [STAGE(filebytesremaining)], 512
    inc dword [STAGE(currentsector)]
    loop .sector

    mov eax, [STAGE(currentcluster)]
    call getfatentry
    jc filesystemreaderror
    cmp eax, FAT_END_OF_CHAIN
    jae bootmanagerchainerror
    call validatecluster
    jc bootmanagerchainerror
    mov [STAGE(currentcluster)], eax
    jmp .cluster

.filecomplete:
    mov dword [STAGE(filebytesremaining)], 0
    mov eax, [STAGE(currentcluster)]
    call getfatentry
    jc filesystemreaderror
    cmp eax, FAT_END_OF_CHAIN
    jb bootmanagerchainerror
    ret

filebytesremaining:
    dd 0
loadsegment:
    dw 0
