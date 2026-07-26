bits 16
cpu 386
org 0x7c00

%include "Version.inc"
%include "StageFormat.inc"
%include "FatFormat.inc"
%include "BiosConstants.inc"

%define EXPECTED_PARTITION_ENTRY 0x07be
%define STAGE_SECTORS 5
%define STAGE(label) (label - $$ + STAGE_LOAD_ADDRESS)

stageheader:
    jmp short entry
    db "MUSB"
    db STAGE_FORMAT_VERSION
    db STAGE_HEADER_SIZE
    dw STAGE_SECTORS
    dw entry - $$
    dd 0

%if ($ - $$) != STAGE_HEADER_SIZE
    %error "Stage header size does not match STAGE_HEADER_SIZE"
%endif

; StageTwo workflow orchestrator.
; Input: DL is the BIOS drive and DS:SI points to the relocated MBR partition
; entry. This routine establishes all segment and stack state itself.
; Output: none; success transfers through boothandoff, while every failure
; reaches a stable non-returning fatal route in StageMessages.
; Owned state: bootdrive. Partition inputs are validated here and then written
; to the fields owned by FatVolume.
entry:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7c00
    sti
    cld

    mov [STAGE(bootdrive)], dl
    push si

    call initializescreen

    mov si, STAGE(bannermessage)
    call print

    mov si, STAGE(preparingmessage)
    call print

%if BUILD_DEBUG
    mov si, STAGE(bootdrivemessage)
    call print

    mov al, [STAGE(bootdrive)]
    shr al, 4
    call printnibble

    mov al, [STAGE(bootdrive)]
    call printnibble

    mov si, STAGE(newline)
    call print
%endif

    pop si

    cmp si, EXPECTED_PARTITION_ENTRY
    jne handofferror
    cmp byte [si], 0x00
    jne handofferror
    cmp byte [si + 4], 0x0b
    jne handofferror
    cmp word [si + 8], 2048
    jne handofferror
    cmp word [si + 10], 0
    jne handofferror

    mov eax, [si + 8]
    mov [STAGE(partitionstart)], eax
    mov eax, [si + 12]
    mov [STAGE(partitionsectors)], eax

    mov si, STAGE(readingmessage)
    call print

    call fatdiscovery

    mov si, STAGE(locatingmessage)
    call print

    call findbootmanager

    mov si, STAGE(loadingmessage)
    call print

    call loadbootmanager

    jmp boothandoff

%include "StageMessages.inc"
%include "BiosDisk.inc"
%include "FatChain.inc"
%include "FatVolume.inc"
%include "FatDirectory.inc"
%include "BootManagerLoader.inc"
%include "BootHandoff.inc"

bootdrive:
    db 0

times STAGE_SECTORS * 512 - 4 - ($ - $$) db 0
db "MEND"
