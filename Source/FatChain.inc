; Shared FAT32 chain primitives and cursor state. Geometry is consumed from
; FatVolume. FatDirectory and BootManagerLoader assign the shared cursors only
; for their current traversal; this module owns their common meaning/storage.

; Input: EAX is a cluster. Output: CF clear only for a valid data cluster.
; Preserves EAX and changes flags; consumes maximumcluster.
validatecluster:
    cmp eax, FAT_FIRST_DATA_CLUSTER
    jb .invalid
    cmp eax, [STAGE(maximumcluster)]
    ja .invalid
    clc
    ret

.invalid:
    stc
    ret

; Input: EAX is a validated cluster. Output: EAX is its first absolute sector
; and CF is clear, or CF is set on arithmetic failure. Changes ECX and EDX;
; consumes sectorspercluster and firstdatasector.
clustertosector:
    sub eax, FAT_FIRST_DATA_CLUSTER
    jc .invalid
    movzx ecx, byte [STAGE(sectorspercluster)]
    mul ecx
    test edx, edx
    jnz .invalid
    add eax, [STAGE(firstdatasector)]
    jc .invalid
    clc
    ret

.invalid:
    stc
    ret

; Input: EAX is a cluster. Output: EAX is its masked FAT entry and CF is clear,
; or CF reports the failed FAT-sector read. Changes BX and EDX; consumes the
; active FAT geometry and BiosDisk, and owns fatentryoffset.
getfatentry:
    mov edx, eax
    and edx, 0x7f
    shl edx, 2
    mov [STAGE(fatentryoffset)], dx

    shr eax, 7
    add eax, [STAGE(activefatsector)]
    call readsector
    jc .done

    mov bx, [STAGE(fatentryoffset)]
    mov eax, [bx + FAT_SECTOR_BUFFER]
    and eax, FAT_ENTRY_MASK
    clc

.done:
    ret

currentcluster:
    dd 0
currentsector:
    dd 0
fatentryoffset:
    dw 0
