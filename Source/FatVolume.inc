; FAT32 volume discovery and geometry ownership.

; Input: partitionstart and partitionsectors were validated and populated by
; StageLoader. Output: all volume geometry fields are valid. Changes EAX, ECX,
; and EDX. A read failure exits through F01 and an invalid layout through F02.
fatdiscovery:
    mov eax, [STAGE(partitionstart)]
    call readsector
    jc volumereaderror

    call validatefatlayout
    jc fatlayouterror
    ret

; Input: FAT_SECTOR_BUFFER contains the partition VBR. Output: CF clear with
; geometry populated, or CF set without a usable volume contract. Changes EAX,
; ECX, and EDX; consumes the shared validatecluster primitive.
validatefatlayout:
    mov eax, [STAGE(partitionstart)]
    add eax, [STAGE(partitionsectors)]
    jc .invalid

    cmp word [FAT_SECTOR_BUFFER + FAT_BPB_BYTES_PER_SECTOR], 512
    jne .invalid
    cmp word [FAT_SECTOR_BUFFER + FAT_BOOT_SIGNATURE], 0xaa55
    jne .invalid

    mov al, [FAT_SECTOR_BUFFER + FAT_BPB_SECTORS_PER_CLUSTER]
    test al, al
    jz .invalid
    cmp al, 128
    ja .invalid
    mov ah, al
    dec ah
    test al, ah
    jnz .invalid
    mov [STAGE(sectorspercluster)], al

    movzx eax, word [FAT_SECTOR_BUFFER + FAT_BPB_RESERVED_SECTORS]
    test eax, eax
    jz .invalid
    mov [STAGE(reservedsectors)], eax

    movzx eax, byte [FAT_SECTOR_BUFFER + FAT_BPB_NUMBER_OF_FATS]
    test eax, eax
    jz .invalid
    cmp eax, 2
    ja .invalid
    mov [STAGE(numberoffats)], al

    cmp word [FAT_SECTOR_BUFFER + FAT_BPB_ROOT_ENTRY_COUNT], 0
    jne .invalid
    cmp word [FAT_SECTOR_BUFFER + FAT_BPB_TOTAL_SECTORS_SIXTEEN], 0
    jne .invalid
    cmp word [FAT_SECTOR_BUFFER + FAT_BPB_SECTORS_PER_FAT_SIXTEEN], 0
    jne .invalid
    cmp word [FAT_SECTOR_BUFFER + FAT_BPB_VERSION], 0
    jne .invalid

    mov eax, [FAT_SECTOR_BUFFER + FAT_BPB_HIDDEN_SECTORS]
    cmp eax, [STAGE(partitionstart)]
    jne .invalid

    mov eax, [FAT_SECTOR_BUFFER + FAT_BPB_TOTAL_SECTORS_THIRTYTWO]
    test eax, eax
    jz .invalid
    cmp eax, [STAGE(partitionsectors)]
    ja .invalid
    mov [STAGE(totalsectors)], eax

    mov eax, [FAT_SECTOR_BUFFER + FAT_BPB_SECTORS_PER_FAT_THIRTYTWO]
    test eax, eax
    jz .invalid
    mov [STAGE(sectorsperfat)], eax

    mov ax, [FAT_SECTOR_BUFFER + FAT_BPB_EXTENDED_FLAGS]
    test ax, 0xff70
    jnz .invalid
    test ax, 0x0080
    jnz .activefat
    test ax, 0x000f
    jnz .invalid
    xor eax, eax
    jmp short .activefatselected

.activefat:
    and ax, 0x000f
    cmp al, [STAGE(numberoffats)]
    jae .invalid
    movzx eax, al

.activefatselected:
    mov [STAGE(activefatindex)], eax

    mov eax, [STAGE(partitionstart)]
    add eax, [STAGE(reservedsectors)]
    jc .invalid
    mov [STAGE(firstfatsector)], eax

    mov eax, [STAGE(sectorsperfat)]
    movzx ecx, byte [STAGE(numberoffats)]
    mul ecx
    test edx, edx
    jnz .invalid
    mov [STAGE(fatregionsectors)], eax

    mov edx, [STAGE(reservedsectors)]
    add edx, eax
    jc .invalid
    cmp edx, [STAGE(totalsectors)]
    jae .invalid

    mov eax, [STAGE(partitionstart)]
    add eax, edx
    jc .invalid
    mov [STAGE(firstdatasector)], eax

    mov eax, [STAGE(totalsectors)]
    sub eax, edx
    jc .invalid
    xor edx, edx
    movzx ecx, byte [STAGE(sectorspercluster)]
    div ecx
    cmp eax, FAT_MINIMUM_FATTHIRTYTWO_CLUSTERS
    jb .invalid
    cmp eax, FAT_MAXIMUM_DATA_CLUSTER - 1
    ja .invalid
    mov [STAGE(clustercount)], eax
    inc eax
    mov [STAGE(maximumcluster)], eax

    mov eax, [STAGE(sectorsperfat)]
    cmp eax, 0x01ffffff
    ja .invalid
    shl eax, 7
    mov edx, [STAGE(clustercount)]
    add edx, 2
    jc .invalid
    cmp eax, edx
    jb .invalid

    mov eax, [STAGE(activefatindex)]
    mul dword [STAGE(sectorsperfat)]
    test edx, edx
    jnz .invalid
    add eax, [STAGE(firstfatsector)]
    jc .invalid
    mov [STAGE(activefatsector)], eax

    mov eax, [FAT_SECTOR_BUFFER + FAT_BPB_ROOT_CLUSTER]
    call validatecluster
    jc .invalid
    mov [STAGE(rootcluster)], eax

    movzx eax, byte [STAGE(sectorspercluster)]
    shl eax, 9
    mov [STAGE(clusterbytes)], eax

    clc
    ret

.invalid:
    stc
    ret

partitionstart:
    dd 0
partitionsectors:
    dd 0
reservedsectors:
    dd 0
totalsectors:
    dd 0
sectorsperfat:
    dd 0
fatregionsectors:
    dd 0
firstfatsector:
    dd 0
activefatsector:
    dd 0
firstdatasector:
    dd 0
clustercount:
    dd 0
maximumcluster:
    dd 0
rootcluster:
    dd 0
clusterbytes:
    dd 0
activefatindex:
    dd 0
sectorspercluster:
    db 0
numberoffats:
    db 0
