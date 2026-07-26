%define HANDOFF_TRAMPOLINE_ADDRESS 0x0600

; Final non-returning BOOTMGR handoff.
; Input: BOOTMGR is loaded, partitionstart is valid, and bootdrive retains the
; BIOS drive. Output: FAT32 VBR restored at 0000:7C00, DL restored, DS:SI set
; to 0000:07BE, and control transferred to 2000:0000. Changes all working
; registers. A final VBR read failure exits through F03.
boothandoff:
    ; BOOTMGR expects the FAT32 volume boot record and its BPB to remain at
    ; the conventional BIOS load address. StageTwo currently occupies that
    ; range, so stage the VBR in the sector buffer before relocating the
    ; final non-returning copy-and-jump sequence below the MBR partition table.
    mov eax, [STAGE(partitionstart)]
    call readsector
    jc filesystemreaderror

%if BUILD_DEBUG
    mov si, STAGE(loadedmessage)
    call print
%endif

    mov si, STAGE(startingmessage)
    call print

    push ds
    pop es
    mov si, STAGE(handofftrampoline)
    mov di, HANDOFF_TRAMPOLINE_ADDRESS
    mov cx, handofftrampolineend - handofftrampoline
    cld
    rep movsb

    xor dx, dx
    mov dl, [STAGE(bootdrive)]
    mov si, EXPECTED_PARTITION_ENTRY
    jmp 0x0000:HANDOFF_TRAMPOLINE_ADDRESS

handofftrampoline:
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov si, FAT_SECTOR_BUFFER
    mov di, 0x7c00
    mov cx, 256
    cld
    rep movsw
    mov si, EXPECTED_PARTITION_ENTRY
    jmp BOOT_MANAGER_LOAD_SEGMENT:0x0000
handofftrampolineend:

%if HANDOFF_TRAMPOLINE_ADDRESS + (handofftrampolineend - handofftrampoline) > EXPECTED_PARTITION_ENTRY
    %error "Handoff trampoline overlaps the relocated partition entry"
%endif
