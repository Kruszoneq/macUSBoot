bits 16
cpu 386
org 0x7c00

%include "StageFormat.inc"
%include "BiosConstants.inc"

%define LOAD_ADDRESS 0x7c00
%define RELOCATED_ADDRESS 0x0600
%define PARTITION_TABLE_OFFSET 446
%define FIRST_PARTITION_ADDRESS (RELOCATED_ADDRESS + PARTITION_TABLE_OFFSET)
%define RELOCATED(label) (label - $$ + RELOCATED_ADDRESS)

bootstrap:
    ; BIOS implementations may enter as either 0000:7C00 or 07C0:0000.
    ; Normalize CS before using labels assembled for an origin of 0x7C00.
    jmp 0x0000:(entry - $$ + LOAD_ADDRESS)

entry:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7c00
    sti
    cld

    ; Relocate the complete MBR before loading the stage over 0000:7C00.
    mov si, LOAD_ADDRESS
    mov di, RELOCATED_ADDRESS
    mov cx, 256
    rep movsw
    jmp 0x0000:RELOCATED(relocated)

relocated:
    ; Keep the BIOS-provided drive below the call stack. INT 13h extension
    ; discovery is not required to preserve DX, while the later read helper
    ; preserves it around every firmware call.
    push dx

    ; The controlled layout reserves LBA 1-2047 for the second stage.
    cmp byte [FIRST_PARTITION_ADDRESS], 0x00
    jne partitionerrorjump
    cmp byte [FIRST_PARTITION_ADDRESS + 4], 0x0b
    jne partitionerrorjump

    cmp dword [FIRST_PARTITION_ADDRESS + 8], 2048
    jne partitionerrorjump

    mov bx, 0x55aa
    mov ah, 0x41
    int 0x13
    pop dx
    push dx
    jc extensionserrorjump
    cmp bx, 0xaa55
    jne extensionserrorjump
    test cx, 0x0001
    jz extensionserrorjump

    jmp short readfirstsector

partitionerrorjump:
    call fatal
partitionerrormessage:
    db "2: Bad layout.", 0

extensionserrorjump:
    call fatal
extensionserrormessage:
    db "1: No disk access.", 0

headererrorjump:
    call fatal
headererrormessage:
    db "4: Bad header.", 0

readfirstsector:
    ; Read the first sector so its metadata can define the exact remaining
    ; transfer without trusting unvalidated disk content.
    call readstage
    jnc validateheader

readerror:
    call fatal
readerrormessage:
    db "3: Read failed.", 0

validateheader:
    cmp dword [STAGE_LOAD_ADDRESS + STAGE_MAGIC_OFFSET], STAGE_MAGIC_DWORD
    jne headererrorjump
    cmp word [STAGE_LOAD_ADDRESS + STAGE_VERSION_OFFSET], \
        (STAGE_HEADER_SIZE << 8) | STAGE_FORMAT_VERSION
    jne headererrorjump
    cmp dword [STAGE_LOAD_ADDRESS + STAGE_FLAGS_OFFSET], 0
    jne headererrorjump

    mov cx, [STAGE_LOAD_ADDRESS + STAGE_SECTOR_COUNT_OFFSET]
    dec cx
    cmp cx, STAGE_MAX_SECTORS - 1
    ja headererrorjump

    mov bx, [STAGE_LOAD_ADDRESS + STAGE_ENTRY_OFFSET]
    sub bx, 2
    cmp bx, STAGE_HEADER_SIZE - 2
    jb headererrorjump
    cmp bx, 0x7f
    ja headererrorjump
    xchg bl, bh
    mov bl, 0xeb
    cmp bx, [STAGE_LOAD_ADDRESS]
    jne headererrorjump

    ; The first sector is already present. Read only the declared remainder.
    jcxz stagecomplete
    mov [RELOCATED(diskaddresspacketcount)], cx
    add byte [RELOCATED(diskaddresspacketoffset) + 1], 2
    inc byte [RELOCATED(diskaddresspacketlba)]
    call readstage
    jc readerror

stagecomplete:
    inc cx
    mov bx, cx
    shl bx, 9
    add bx, STAGE_LOAD_ADDRESS - 4

    cmp dword [bx], STAGE_END_DWORD
    je stagevalid

tailerror:
    call fatal
tailerrormessage:
    db "5: Bad data.", 0

stagevalid:
    mov bx, [STAGE_LOAD_ADDRESS + STAGE_ENTRY_OFFSET]
    add bh, STAGE_LOAD_ADDRESS >> 8
    pop dx
    mov si, FIRST_PARTITION_ADDRESS
    jmp bx

readstage:
    mov di, [RELOCATED(diskaddresspacketcount)]
    mov bp, BIOS_READ_ATTEMPTS

.retry:
    ; EDD permits firmware to replace the count with the number of blocks
    ; transferred before an error, so restore the requested value each time.
    mov [RELOCATED(diskaddresspacketcount)], di
    mov si, RELOCATED(diskaddresspacket)
    mov ah, 0x42
    pusha
    int 0x13
    popa
    jnc .done

    dec bp
    jz .done

    ; Reset the same BIOS-provided drive before another bounded attempt.
    pusha
    xor ax, ax
    int 0x13
    popa
    jmp .retry

.done:
    ret

fatal:
    pop di
    mov si, RELOCATED(errorprefix)
    call print

    mov si, di
    call print

    mov si, RELOCATED(restartmessage)
    call print

    xor ax, ax
    int 0x16
    int 0x19

halt:
    cli
    hlt
    jmp halt

print:
    ; Firmware services are not allowed to leak a set direction flag into the
    ; loader's forward string traversal.
    cld
    lodsb
    test al, al
    jz .done

    mov ah, 0x0e
    mov bx, 0x0007
    push ds
    push si
    int 0x10
    pop si
    pop ds
    jmp print

.done:
    ret

errorprefix:
    db "Error C0", 0

restartmessage:
    db 13, 10, 13, 10, "Press any key to restart...", 0

align 4, db 0
diskaddresspacket:
    db 0x10
    db 0
diskaddresspacketcount:
    dw 1
diskaddresspacketoffset:
    dw STAGE_LOAD_ADDRESS
    dw 0
diskaddresspacketlba:
    dq STAGE_START_LBA

; This artifact replaces only MBR bytes 0-439. The disk signature,
; reserved bytes, partition table, and 0x55AA signature are preserved from
; the target's existing sector and therefore are intentionally absent here.
times 440 - ($ - $$) db 0
