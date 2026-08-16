#!/usr/bin/env python3
"""
repack_ipa.py
=============
Reempacota um diretorio extraido de volta num arquivo .ipa (ZIP).
Preserva permissoes Unix e nao comprime binarios grandes.

Uso:
    python repack_ipa.py <pasta_extraida> <saida.ipa>

Exemplo:
    python repack_ipa.py ./Extracted ./Apps_Modified.ipa
"""

import zipfile
import os
import sys
import stat


# Extensoes que NAO devem ser comprimidas (binarios ARM64, assets compilados)
NO_COMPRESS_EXTS = {'.app', '.dylib', '.so', '.o', '.framework',
                    '.car', '', }  # sem extensao = binario executavel


def should_compress(filepath: str) -> bool:
    ext = os.path.splitext(filepath)[1].lower()
    if ext in NO_COMPRESS_EXTS:
        return False
    # Nao comprime binarios Mach-O (magic bytes)
    try:
        with open(filepath, 'rb') as f:
            magic = f.read(4)
        if magic in (b'\xCF\xFA\xED\xFE', b'\xFE\xED\xFA\xCF',
                     b'\xCA\xFE\xBA\xBE', b'\xCE\xFA\xED\xFE'):
            return False
    except Exception:
        pass
    return True


def repack_ipa(source_dir: str, output_ipa: str):
    source_dir = os.path.abspath(source_dir)
    output_ipa = os.path.abspath(output_ipa)

    if not os.path.isdir(source_dir):
        print(f"❌ Pasta nao encontrada: {source_dir}")
        sys.exit(1)

    total_files = sum(len(files) for _, _, files in os.walk(source_dir))
    print(f"📦 Empacotando {total_files} arquivo(s) em: {output_ipa}")

    written = 0
    with zipfile.ZipFile(output_ipa, 'w', allowZip64=True) as zf:
        for root, dirs, files in os.walk(source_dir):
            # Ordena para output determinista
            dirs.sort()
            files.sort()
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, source_dir)
                # Normaliza separadores para '/' (padrao ZIP/IPA)
                arcname = arcname.replace('\\', '/')

                compress = should_compress(fpath)
                method = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED

                # Preserva permissoes Unix no campo external_attr
                file_stat = os.stat(fpath)
                unix_perms = (file_stat.st_mode & 0xFFFF) << 16

                info = zipfile.ZipInfo(arcname)
                info.compress_type = method
                info.external_attr = unix_perms

                with open(fpath, 'rb') as f:
                    zf.writestr(info, f.read())

                written += 1
                if written % 50 == 0 or written == total_files:
                    print(f"   [{written}/{total_files}] {arcname}")

    size_mb = os.path.getsize(output_ipa) / 1_048_576
    print(f"\n✅ IPA criado: {output_ipa}")
    print(f"   Tamanho: {size_mb:.2f} MB")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    repack_ipa(sys.argv[1], sys.argv[2])
