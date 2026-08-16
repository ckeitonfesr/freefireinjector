#!/usr/bin/env python3
"""
patch_binary.py
===============
Injeta um novo LC_LOAD_DYLIB num binario Mach-O 64-bit (ARM64 iOS).
Funciona usando o espaco de padding entre os load commands e o primeiro segmento.

Uso:
    python patch_binary.py <binario_entrada> <dylib_path> <binario_saida>

Exemplo:
    python patch_binary.py 3105 @executable_path/Frameworks/FreeFirInjector.dylib 3105_patched
"""

import struct
import sys
import os

# ── Mach-O constants ──────────────────────────────────────────────────────────
MH_MAGIC_64   = 0xFEEDFACF  # little-endian 64-bit
MH_CIGAM_64   = 0xCFFAEDFE  # big-endian    64-bit (swapped)
FAT_MAGIC     = 0xCAFEBABE
FAT_CIGAM     = 0xBEBAFECA

LC_SEGMENT_64     = 0x19
LC_LOAD_DYLIB     = 0x0C
LC_LOAD_WEAK_DYLIB = 0x18

MACHO_HEADER_64_SIZE = 32   # sizeof(mach_header_64)
DYLIB_CMD_FIXED_SIZE = 24   # sizeof(dylib_command) sem o nome

# ── Parser ────────────────────────────────────────────────────────────────────
def parse_header_64(data, offset=0):
    """Retorna (endian_char, ncmds, sizeofcmds)"""
    magic = struct.unpack_from('<I', data, offset)[0]
    if magic == MH_MAGIC_64:
        endian = '<'
    elif magic == MH_CIGAM_64:
        endian = '>'
    else:
        raise ValueError(f"Nao e Mach-O 64-bit em offset {offset:#x} (magic={magic:#010x})")
    ncmds      = struct.unpack_from(f'{endian}I', data, offset + 16)[0]
    sizeofcmds = struct.unpack_from(f'{endian}I', data, offset + 20)[0]
    return endian, ncmds, sizeofcmds


def get_load_commands(data, endian, ncmds, base_offset):
    """Retorna lista de (cmd, cmdsize, absolute_offset)"""
    cmds = []
    off = base_offset + MACHO_HEADER_64_SIZE
    for _ in range(ncmds):
        cmd     = struct.unpack_from(f'{endian}I', data, off)[0]
        cmdsize = struct.unpack_from(f'{endian}I', data, off + 4)[0]
        if cmdsize == 0:
            break
        cmds.append((cmd, cmdsize, off))
        off += cmdsize
    return cmds


def find_first_segment_fileoff(data, endian, cmds, base_offset):
    """
    Retorna o file offset do primeiro byte de dados mapeados
    (o menor fileoff nao-zero entre os LC_SEGMENT_64).
    Isso define o limite maximo ate onde podemos escrever load commands.
    """
    min_fileoff = None
    for cmd, cmdsize, off in cmds:
        if cmd == LC_SEGMENT_64:
            fileoff  = struct.unpack_from(f'{endian}Q', data, off + 32)[0]
            filesize = struct.unpack_from(f'{endian}Q', data, off + 40)[0]
            if filesize > 0 and fileoff > 0:
                if min_fileoff is None or fileoff < min_fileoff:
                    min_fileoff = fileoff
    return min_fileoff


def already_injected(data, endian, cmds, dylib_name):
    """Checa se a dylib ja esta injetada."""
    for cmd, cmdsize, off in cmds:
        if cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB):
            name_off_in_cmd = struct.unpack_from(f'{endian}I', data, off + 8)[0]
            raw = data[off + name_off_in_cmd : off + cmdsize]
            existing = raw.split(b'\x00')[0].decode('utf-8', errors='replace')
            if existing == dylib_name:
                return True
    return False


# ── Injetor principal ─────────────────────────────────────────────────────────
def inject_dylib(input_path: str, dylib_name: str, output_path: str,
                 weak: bool = False):
    """
    Le o binario Mach-O em `input_path`, injeta um LC_LOAD_DYLIB apontando
    para `dylib_name` e salva o resultado em `output_path`.
    """
    with open(input_path, 'rb') as f:
        data = bytearray(f.read())

    # ── Suporte a FAT binaries (multi-arch) ──────────────────────────────────
    fat_magic = struct.unpack_from('<I', data, 0)[0]
    if fat_magic in (FAT_MAGIC, FAT_CIGAM):
        # Para binarios FAT vamos pegar o slice ARM64
        fat_endian = '>' if fat_magic == FAT_MAGIC else '<'
        nfat_arch = struct.unpack_from('>I', data, 4)[0]  # FAT e sempre big-endian
        print(f"[FAT] Binary multi-arch detectado com {nfat_arch} slice(s)")
        for i in range(nfat_arch):
            arch_off  = 8 + i * 20
            cputype   = struct.unpack_from('>I', data, arch_off)[0]
            cpusubtype= struct.unpack_from('>I', data, arch_off + 4)[0]
            offset    = struct.unpack_from('>I', data, arch_off + 8)[0]
            size      = struct.unpack_from('>I', data, arch_off + 12)[0]
            # ARM64 = 0x0100000C
            if cputype == 0x0100000C:
                print(f"   -> Slice ARM64 encontrado em offset {offset:#x}, size {size}")
                _inject_slice(data, dylib_name, offset, weak=weak)
        with open(output_path, 'wb') as f:
            f.write(data)
        print(f"[OK] FAT binary salvo: {output_path}")
        return

    # ── Binario Mach-O simples ───────────────────────────────────────────────
    _inject_slice(data, dylib_name, base_offset=0, weak=weak)

    with open(output_path, 'wb') as f:
        f.write(data)
    print(f"\n[OK] Binario salvo: {output_path}")


def _inject_slice(data: bytearray, dylib_name: str, base_offset: int = 0,
                  weak: bool = False):
    """Injeta o LC_LOAD_DYLIB num slice Mach-O dentro de `data` (in-place)."""

    endian, ncmds, sizeofcmds = parse_header_64(data, base_offset)
    cmds = get_load_commands(data, endian, ncmds, base_offset)

    # Checa duplicata
    if already_injected(data, endian, cmds, dylib_name):
        print(f"\n[AVISO] Dylib ja injetada: {dylib_name}")
        return  # ja injetada

    # -- Monta o novo comando LC_LOAD_DYLIB -----------------------------------
    lc_cmd = LC_LOAD_WEAK_DYLIB if weak else LC_LOAD_DYLIB
    name_bytes = dylib_name.encode('utf-8') + b'\x00'
    raw_size   = DYLIB_CMD_FIXED_SIZE + len(name_bytes)
    aligned_sz = (raw_size + 7) & ~7   # alinha em 8 bytes

    new_cmd = struct.pack(f'{endian}IIIIII',
        lc_cmd,               # cmd
        aligned_sz,           # cmdsize
        DYLIB_CMD_FIXED_SIZE, # name offset (from start of cmd)
        2,                    # timestamp
        0x00010000,           # current_version  (1.0)
        0x00010000,           # compat_version   (1.0)
    ) + name_bytes
    new_cmd = new_cmd.ljust(aligned_sz, b'\x00')

    # ── Verifica espaco disponivel ───────────────────────────────────────────
    first_seg_off = find_first_segment_fileoff(data, endian, cmds, base_offset)
    end_of_cmds   = base_offset + MACHO_HEADER_64_SIZE + sizeofcmds
    limit         = first_seg_off if first_seg_off else len(data)
    available     = limit - end_of_cmds

    print(f"\n  Fim dos load commands : {end_of_cmds:#x}")
    print(f"  Inicio do 1o segmento : {limit:#x}")
    print(f"  Espaco disponivel     : {available} bytes")
    print(f"  Tamanho novo comando  : {aligned_sz} bytes")

    if available < aligned_sz:
        raise RuntimeError(
            f"\n[ERRO] Espaco insuficiente!\n"
            f"   Precisa de {aligned_sz} bytes, disponivel: {available}.\n"
            f"   Dica: use o 'insert_dylib' (https://github.com/Tyilo/insert_dylib)\n"
            f"         que redimensiona o binario automaticamente."
        )

    # ── Escreve o novo comando no padding ────────────────────────────────────
    for i, b in enumerate(new_cmd):
        data[end_of_cmds + i] = b

    # ── Atualiza header ──────────────────────────────────────────────────────
    struct.pack_into(f'{endian}I', data, base_offset + 16, ncmds + 1)
    struct.pack_into(f'{endian}I', data, base_offset + 20, sizeofcmds + aligned_sz)

    print(f"[OK] Injetado: {dylib_name}")
    print(f"   ncmds: {ncmds} -> {ncmds + 1}")
    print(f"   sizeofcmds: {sizeofcmds} -> {sizeofcmds + aligned_sz}")


# ── Leitura rapida de info do binario ─────────────────────────────────────────
def print_dylibs(input_path: str):
    """Lista todas as dylibs que o binario ja carrega."""
    with open(input_path, 'rb') as f:
        data = f.read()
    endian, ncmds, sizeofcmds = parse_header_64(data, 0)
    cmds = get_load_commands(data, endian, ncmds, 0)
    print(f"\nDylibs carregadas por {os.path.basename(input_path)}:")
    for cmd, cmdsize, off in cmds:
        if cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB):
            name_off = struct.unpack_from(f'{endian}I', data, off + 8)[0]
            raw = data[off + name_off : off + cmdsize]
            name = raw.split(b'\x00')[0].decode('utf-8', errors='replace')
            kind = "(WEAK)" if cmd == LC_LOAD_WEAK_DYLIB else ""
            print(f"   {kind} {name}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        print("Uso: python patch_binary.py --list <binario>")
        sys.exit(0)

    if len(sys.argv) == 3 and sys.argv[1] == '--list':
        print_dylibs(sys.argv[2])
        sys.exit(0)

    if len(sys.argv) not in (4, 5):
        print(__doc__)
        print("\nFlags opcionais:")
        print("  --weak       Usa LC_LOAD_WEAK_DYLIB (nao crasha se dylib sumiu)")
        print("  --list <bin> Lista dylibs ja carregadas")
        sys.exit(1)

    weak = '--weak' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--weak']
    inject_dylib(args[0], args[1], args[2], weak=weak)
