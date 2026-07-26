; Root-directory traversal, entry filtering, and BOOTMGR metadata ownership.

; Input: valid FatVolume geometry. Output: bootmanagercluster and
; bootmanagersize identify a matching root short-name file. Changes EAX, ECX,
; EDX, SI, and DI; consumes BiosDisk and FatChain. Failures exit through F03,
; F04, or F05 and do not return.
findbootmanager:
    mov eax, [STAGE(rootcluster)]
    mov [STAGE(currentcluster)], eax
    mov dword [STAGE(directoryentriesremaining)], FAT_MAXIMUM_DIRECTORY_ENTRIES

.cluster:
    mov eax, [STAGE(currentcluster)]
    call validatecluster
    jc rootdirectoryerror
    call clustertosector
    jc rootdirectoryerror
    mov [STAGE(currentsector)], eax
    movzx ecx, byte [STAGE(sectorspercluster)]

.sector:
    mov eax, [STAGE(currentsector)]
    call readsector
    jc filesystemreaderror

    push cx
    call scandirectorysector
    pop cx
    cmp al, 1
    je .found
    cmp al, 2
    je bootmanagermissing
    cmp al, 3
    je rootdirectoryerror

    inc dword [STAGE(currentsector)]
    loop .sector

    mov eax, [STAGE(currentcluster)]
    call getfatentry
    jc filesystemreaderror
    cmp eax, FAT_END_OF_CHAIN
    jae bootmanagermissing
    call validatecluster
    jc rootdirectoryerror
    mov [STAGE(currentcluster)], eax
    jmp .cluster

.found:
    ret

; Input: FAT_SECTOR_BUFFER contains one directory sector. Output: AL is 0 to
; continue, 1 for a match, 2 for directory end, or 3 for exhausted bounded
; traversal. Changes AX, CX, DX, SI, and DI; owns selected BOOTMGR metadata.
scandirectorysector:
    mov si, FAT_SECTOR_BUFFER
    mov dx, FAT_DIRECTORY_ENTRIES_PER_SECTOR

.entry:
    cmp dword [STAGE(directoryentriesremaining)], 0
    je .directoryinvalid
    dec dword [STAGE(directoryentriesremaining)]

    mov al, [si]
    test al, al
    jz .directoryend
    cmp al, 0xe5
    je .next

    mov al, [si + FAT_DIRECTORY_ATTRIBUTE]
    mov ah, al
    test ah, FAT_DIRECTORY_RESERVED_ATTRIBUTE_MASK
    jnz .next
    and al, FAT_DIRECTORY_LONG_NAME_MASK
    cmp al, FAT_DIRECTORY_LONG_NAME
    je .next
    test ah, FAT_DIRECTORY_VOLUME_LABEL | FAT_DIRECTORY_SUBDIRECTORY
    jnz .next

    push si
    mov di, STAGE(bootmanagername)
    mov cx, 11
    cld
    repe cmpsb
    pop si
    jne .next

    movzx eax, word [si + FAT_DIRECTORY_CLUSTER_HIGH]
    shl eax, 16
    mov ax, [si + FAT_DIRECTORY_CLUSTER_LOW]
    mov [STAGE(bootmanagercluster)], eax
    mov eax, [si + FAT_DIRECTORY_FILE_SIZE]
    mov [STAGE(bootmanagersize)], eax
    mov al, 1
    ret

.next:
    add si, FAT_DIRECTORY_ENTRY_SIZE
    dec dx
    jnz .entry
    xor al, al
    ret

.directoryend:
    mov al, 2
    ret

.directoryinvalid:
    mov al, 3
    ret

directoryentriesremaining:
    dd 0
bootmanagercluster:
    dd 0
bootmanagersize:
    dd 0

bootmanagername:
    db "BOOTMGR    "
