#!/usr/bin/env python3
"""
run_all.py — Script mestre: injeta a dylib no Filza IPA e repacota
═══════════════════════════════════════════════════════════════════

PRE-REQUISITOS:
  1. Python 3.8+ instalado
  2. A dylib ja compilada: tweak/FreeFirInjector.dylib
     (compile no Mac com Theos: cd tweak && make package)

USO:
  python run_all.py
  python run_all.py --check     # apenas verifica o binario sem modificar
"""

import os
import sys
import zipfile
import shutil
import struct

# ── Adiciona a pasta tools ao path ────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, 'tools')
sys.path.insert(0, TOOLS_DIR)

from patch_binary import inject_dylib, print_dylibs

# ── Caminhos do projeto ───────────────────────────────────────────────────────
IPA_INPUT      = os.path.join(BASE_DIR, 'Apps.ipa')
EXTRACT_DIR    = os.path.join(BASE_DIR, 'Extracted')
APP_DIR        = os.path.join(EXTRACT_DIR, 'Payload', '3105.app')
BINARY_PATH    = os.path.join(APP_DIR, '3105')
FRAMEWORKS_DIR = os.path.join(APP_DIR, 'Frameworks')

DYLIB_NAME     = 'FreeFirInjector.dylib'
DYLIB_SOURCE   = os.path.join(BASE_DIR, 'tweak', DYLIB_NAME)
DYLIB_DEST     = os.path.join(FRAMEWORKS_DIR, DYLIB_NAME)
DYLIB_IN_BINARY = f'@executable_path/Frameworks/{DYLIB_NAME}'

IPA_OUTPUT     = os.path.join(BASE_DIR, 'Apps_Modified.ipa')

# ── Utils ─────────────────────────────────────────────────────────────────────
CYAN   = '\033[96m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
RESET  = '\033[0m'
BOLD   = '\033[1m'

def step(n, msg):
    print(f"\n{CYAN}{BOLD}[Etapa {n}]{RESET} {msg}")

def ok(msg):
    print(f"  {GREEN}✅ {msg}{RESET}")

def warn(msg):
    print(f"  {YELLOW}⚠️  {msg}{RESET}")

def err(msg):
    print(f"  {RED}❌ {msg}{RESET}")

# ── Etapas ────────────────────────────────────────────────────────────────────

def check_prerequisites():
    step(1, "Verificando pre-requisitos...")
    missing = False

    if not os.path.exists(IPA_INPUT):
        err(f"IPA nao encontrado: {IPA_INPUT}")
        missing = True
    else:
        size = os.path.getsize(IPA_INPUT) / 1_048_576
        ok(f"Apps.ipa encontrado ({size:.1f} MB)")

    if not os.path.exists(DYLIB_SOURCE):
        err(f"Dylib nao encontrada: {DYLIB_SOURCE}")
        print(f"\n{YELLOW}  Como compilar a dylib:{RESET}")
        print(f"    1. No Mac, instale o Theos: https://theos.dev/docs/installation")
        print(f"    2. Execute no terminal Mac:")
        print(f"       cd \"{os.path.join(BASE_DIR, 'tweak')}\"")
        print(f"       make package")
        print(f"    3. A dylib sera copiada automaticamente para tweak/FreeFirInjector.dylib")
        missing = True
    else:
        size = os.path.getsize(DYLIB_SOURCE) / 1024
        ok(f"FreeFirInjector.dylib encontrada ({size:.0f} KB)")

    if missing:
        sys.exit(1)


def extract_ipa():
    step(2, "Extraindo Apps.ipa...")

    if os.path.exists(EXTRACT_DIR):
        shutil.rmtree(EXTRACT_DIR)
    os.makedirs(EXTRACT_DIR)

    with zipfile.ZipFile(IPA_INPUT, 'r') as z:
        z.extractall(EXTRACT_DIR)

    if not os.path.exists(BINARY_PATH):
        err(f"Binario nao encontrado apos extracao: {BINARY_PATH}")
        sys.exit(1)

    ok(f"Extraido em: {EXTRACT_DIR}")


def copy_dylib():
    step(3, "Copiando dylib para Frameworks/...")
    os.makedirs(FRAMEWORKS_DIR, exist_ok=True)
    shutil.copy2(DYLIB_SOURCE, DYLIB_DEST)
    ok(f"Dylib copiada: {DYLIB_DEST}")


def patch_binary():
    step(4, "Injetando load command no binario Mach-O...")
    print(f"  Binario: {BINARY_PATH}")
    print(f"  Dylib  : {DYLIB_IN_BINARY}")
    inject_dylib(BINARY_PATH, DYLIB_IN_BINARY, BINARY_PATH)
    ok("Load command injetado com sucesso")


def repack_ipa():
    step(5, "Reempacotando como Apps_Modified.ipa...")

    if os.path.exists(IPA_OUTPUT):
        os.remove(IPA_OUTPUT)

    # Importa o repackager
    sys.path.insert(0, TOOLS_DIR)
    from repack_ipa import repack_ipa as do_repack
    do_repack(EXTRACT_DIR, IPA_OUTPUT)


def print_summary():
    size_mb = os.path.getsize(IPA_OUTPUT) / 1_048_576
    print(f"\n{'═'*55}")
    print(f"{GREEN}{BOLD}  🎉 CONCLUIDO COM SUCESSO!{RESET}")
    print(f"{'═'*55}")
    print(f"\n  IPA modificado: {BOLD}{IPA_OUTPUT}{RESET}")
    print(f"  Tamanho       : {size_mb:.2f} MB")
    print(f"\n{BOLD}  Como instalar no iPhone:{RESET}")
    print(f"  ┌─ TrollStore ─────────────────────────────────────┐")
    print(f"  │  Copie Apps_Modified.ipa para o iPhone e abra    │")
    print(f"  │  no TrollStore → Instalar                        │")
    print(f"  ├─ AltStore / Sideloadly ──────────────────────────┤")
    print(f"  │  Arraste o IPA para o AltStore/Sideloadly        │")
    print(f"  ├─ Jailbreak (dpkg) ───────────────────────────────┤")
    print(f"  │  ideviceinstaller -i Apps_Modified.ipa           │")
    print(f"  └──────────────────────────────────────────────────┘")
    print(f"\n  {YELLOW}Nota: o IPA nao esta re-assinado. Se o dispositivo")
    print(f"  nao tiver TrollStore/JB, assine com ldid ou Zsign.{RESET}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}{'═'*55}")
    print(f"   FreeFire Injector — Filza IPA Modifier")
    print(f"{'═'*55}{RESET}")

    if '--check' in sys.argv:
        # Modo inspecao apenas
        if not os.path.exists(BINARY_PATH):
            # Extrai temporariamente
            extract_ipa()
        print_dylibs(BINARY_PATH)
        return

    check_prerequisites()
    extract_ipa()
    copy_dylib()
    patch_binary()
    repack_ipa()
    print_summary()


if __name__ == '__main__':
    main()
