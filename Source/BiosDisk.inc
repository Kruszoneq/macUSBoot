; Input: EAX is a 32-bit LBA. Output: CF reports the final one-sector EDD read
; result and FAT_SECTOR_BUFFER contains the sector on success. Preserves all
; general registers plus DS and ES, returns with DF clear, consumes bootdrive,
; and owns the packet and bounded-attempt state. No fatal route is taken here.
readsector:
    push ds
    push es
    pushad

    xor dx, dx
    mov ds, dx
    mov es, dx

    mov [STAGE(diskaddresspacketlba)], eax
    mov dword [STAGE(diskaddresspacketlba) + 4], 0

    mov byte [STAGE(readattemptsremaining)], BIOS_READ_ATTEMPTS

.retry:
    ; Firmware may replace the requested count with the number of blocks
    ; transferred before an error. Restore the one-sector request each time.
    mov word [STAGE(diskaddresspacketcount)], 1
    mov dl, [STAGE(bootdrive)]
    mov si, STAGE(diskaddresspacket)
    mov ah, 0x42
    pushad
    int 0x13
    popad
    jnc .done

    dec byte [STAGE(readattemptsremaining)]
    jz .done

    ; Reset the same BIOS-provided drive before the bounded retry. A reset
    ; failure does not replace the original read result or extend the limit.
    xor ax, ax
    mov dl, [STAGE(bootdrive)]
    pushad
    int 0x13
    popad
    jmp .retry

.done:
    cld
    popad
    pop es
    pop ds
    ret

align 4, db 0
diskaddresspacket:
    db 0x10
    db 0
diskaddresspacketcount:
    dw 1
    dw FAT_SECTOR_BUFFER
    dw 0
diskaddresspacketlba:
    dq 0

readattemptsremaining:
    db 0
