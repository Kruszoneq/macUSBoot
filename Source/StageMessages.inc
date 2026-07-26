; StageTwo screen, message, and fatal-policy module.
; All procedures assume the flat StageTwo runtime with DS=0. Error routes are
; non-returning and preserve the stable C06/F01-F07 classifications.

halt:
    cli
    hlt
    jmp halt

handofferror:
    mov si, STAGE(handofferrormessage)
    jmp fatal

volumereaderror:
    mov si, STAGE(volumereaderrormessage)
    jmp fatal

fatlayouterror:
    mov si, STAGE(fatlayouterrormessage)
    jmp fatal

filesystemreaderror:
    mov si, STAGE(filesystemreaderrormessage)
    jmp fatal

rootdirectoryerror:
    mov si, STAGE(rootdirectoryerrormessage)
    jmp fatal

bootmanagermissing:
    mov si, STAGE(bootmanagermissingmessage)
    jmp fatal

bootmanagerchainerror:
    mov si, STAGE(bootmanagerchainerrormessage)
    jmp fatal

bootmanagermemoryerror:
    mov si, STAGE(bootmanagermemoryerrormessage)

; Input: DS:SI points to a zero-terminated fatal message.
; Output: none. Waits for a key, invokes BIOS restart once, and halts if it
; returns. Changes AX and SI; owns the fatal presentation and restart policy.
fatal:
    call print

    mov si, STAGE(restartmessage)
    call print

    xor ax, ax
    int 0x16
    int 0x19
    jmp halt

; Input: none. Output: current text screen cleared and cursor at its upper-left
; corner. Changes AX, BX, CX, and DX; owns displaypage.
initializescreen:
    ; Query the current text width and page, use the BIOS data-area row count,
    ; and scroll that complete window by zero lines to clear it without
    ; selecting a new video mode.
    mov ah, 0x0f
    push ds
    int 0x10
    pop ds
    mov [STAGE(displaypage)], bh
    push bx
    mov dl, ah
    dec dl
    mov dh, [0x0484]
    test dh, dh
    jnz .dimensionsready
    mov dh, 24

.dimensionsready:
    mov ax, 0x0600
    mov bh, 0x07
    xor cx, cx
    push ds
    int 0x10
    pop ds

    mov ah, 0x02
    pop bx
    xor dx, dx
    push ds
    int 0x10
    pop ds
    ret

; Input: DS:SI points to a zero-terminated string. Output: string emitted on
; the active page, SI advanced past its terminator, and DF clear. Changes AX,
; BX, and SI; consumes displaypage.
print:
    ; Reassert forward traversal before every byte because a preceding BIOS
    ; teletype call is not trusted to preserve the direction flag.
    cld
    lodsb
    test al, al
    jz .done

    mov ah, 0x0e
    mov bh, [STAGE(displaypage)]
    mov bl, 0x07
    push ds
    push si
    int 0x10
    pop si
    pop ds
    jmp print

.done:
    ret

; Input: low nibble of AL. Output: one uppercase hexadecimal digit emitted.
; Changes AX and BX; consumes displaypage.
printnibble:
    and al, 0x0f
    cmp al, 9
    jbe .decimal
    add al, 'A' - 10
    jmp .emit

.decimal:
    add al, '0'

.emit:
    mov ah, 0x0e
    mov bh, [STAGE(displaypage)]
    mov bl, 0x07
    push ds
    int 0x10
    pop ds
    ret

displaypage:
    db 0

bannermessage:
    db "macUSBoot v", VERSION_STRING, 13, 10, 13, 10, 0

preparingmessage:
    db "Preparing the boot environment...", 13, 10, 0

readingmessage:
    db "Reading the Windows installation media...", 13, 10, 0

locatingmessage:
    db "Locating Windows Boot Manager...", 13, 10, 0

loadingmessage:
    db "Loading Windows Boot Manager...", 13, 10, 0

startingmessage:
    db "Starting Windows Boot Manager...", 13, 10, 0

%if BUILD_DEBUG
bootdrivemessage:
    db "[Debug] BIOS drive DL=0x", 0

newline:
    db 13, 10, 0
%endif

handofferrormessage:
    db "Error C06: The bootloader handoff is invalid.", 13, 10, 0

volumereaderrormessage:
    db "Error F01: The Windows volume could not be read.", 13, 10, 0

fatlayouterrormessage:
    db "Error F02: The FAT32 volume layout is unsupported.", 13, 10, 0

filesystemreaderrormessage:
    db "Error F03: The Windows file system could not be read.", 13, 10, 0

rootdirectoryerrormessage:
    db "Error F04: The root directory is invalid.", 13, 10, 0

bootmanagermissingmessage:
    db "Error F05: Windows Boot Manager was not found.", 13, 10, 0

bootmanagerchainerrormessage:
    db "Error F06: Windows Boot Manager data is invalid.", 13, 10, 0

bootmanagermemoryerrormessage:
    db "Error F07: Windows Boot Manager is too large.", 13, 10, 0

%if BUILD_DEBUG
loadedmessage:
    db "[Debug] Windows Boot Manager loaded.", 13, 10, 0
%endif

restartmessage:
    db 13, 10, "Press any key to restart...", 0
