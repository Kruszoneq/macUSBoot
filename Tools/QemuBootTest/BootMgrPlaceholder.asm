bits 16
cpu 386
org 0

%define SUCCESS_EXIT_VALUE 0x2a
%define FAILURE_EXIT_VALUE 0x2b
%define PARTITION_ENTRY_ADDRESS 0x07be
%define VBR_ADDRESS 0x7c00
%define QEMU_DEBUG_PORT 0x00e9
%define QEMU_EXIT_PORT 0x00f4

entry:
    cld
    mov bp, FAILURE_EXIT_VALUE

    mov ax, ds
    test ax, ax
    jnz invalidds
    cmp si, PARTITION_ENTRY_ADDRESS
    jne invalidsi
    cmp dl, 0x80
    jne invaliddrive
    cmp byte [si], 0x00
    jne invalidpartition
    cmp byte [si + 4], 0x0b
    jne invalidpartition
    cmp dword [si + 8], 2048
    jne invalidpartition
    cmp word [VBR_ADDRESS + 510], 0xaa55
    jne invalidvbr
    cmp word [VBR_ADDRESS + 11], 512
    jne invalidvbr
    cmp dword [VBR_ADDRESS + 28], 2048
    jne invalidvbr

    mov ax, cs
    mov ds, ax
    cmp dword [tailmagic - $$], 0x4c494154
    jne invalidtail

    mov bx, successmessage - $$
    mov bp, SUCCESS_EXIT_VALUE
    jmp short emit

invalidds:
    mov bx, invaliddsmessage - $$
    jmp short emit

invalidsi:
    mov bx, invalidsimessage - $$
    jmp short emit

invaliddrive:
    mov bx, invaliddrivemessage - $$
    jmp short emit

invalidpartition:
    mov bx, invalidpartitionmessage - $$
    jmp short emit

invalidvbr:
    mov bx, invalidvbrmessage - $$
    jmp short emit

invalidtail:
    mov bx, invalidtailmessage - $$

emit:
    mov ax, cs
    mov ds, ax
    mov si, bx
    mov dx, QEMU_DEBUG_PORT

.print:
    lodsb
    test al, al
    jz .exit
    out dx, al
    jmp short .print

.exit:
    mov dx, QEMU_EXIT_PORT
    mov ax, bp
    out dx, al

.halt:
    cli
    hlt
    jmp short .halt

successmessage:
    db "BOOTMGR_PLACEHOLDER_REACHED CONTEXT_OK", 10, 0
invaliddsmessage:
    db "BOOTMGR_PLACEHOLDER_REACHED INVALID_DS", 10, 0
invalidsimessage:
    db "BOOTMGR_PLACEHOLDER_REACHED INVALID_SI", 10, 0
invaliddrivemessage:
    db "BOOTMGR_PLACEHOLDER_REACHED INVALID_DRIVE", 10, 0
invalidpartitionmessage:
    db "BOOTMGR_PLACEHOLDER_REACHED INVALID_PARTITION", 10, 0
invalidvbrmessage:
    db "BOOTMGR_PLACEHOLDER_REACHED INVALID_VBR", 10, 0
invalidtailmessage:
    db "BOOTMGR_PLACEHOLDER_REACHED INVALID_FRAGMENT_TAIL", 10, 0

times 768 - ($ - $$) db 0xa5
tailmagic:
    db "TAIL"
times 1024 - ($ - $$) db 0
