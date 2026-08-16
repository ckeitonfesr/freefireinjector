# 🎮 FreeFire Injector — Filza IPA Modifier

Modifica o IPA do Filza customizado (`Apps.ipa`) para adicionar um **botão flutuante** que injeta um arquivo no diretório do Free Fire no iPhone.

---

## 📂 Estrutura do Projeto

```
PENISPROMAX/
├── Apps.ipa                    ← IPA original do Filza (input)
├── Apps_Modified.ipa           ← IPA modificado (gerado pelo script)
├── run_all.py                  ← Script mestre (rode este no Windows)
│
├── tools/
│   ├── patch_binary.py         ← Injetor Mach-O (LC_LOAD_DYLIB)
│   └── repack_ipa.py           ← Reempacotador de IPA
│
└── tweak/
    ├── Tweak.x                 ← Código ObjC/Logos do botão (compile no Mac)
    ├── Makefile                ← Build config (Theos)
    ├── control                 ← Metadados do pacote
    └── FreeFirInjector.dylib   ← Dylib compilada (você gera no Mac)
```

---

## 🔄 Fluxo Completo

```
[Mac com Theos]          [Windows PC]              [iPhone]
     │                       │                        │
     │  cd tweak/            │                        │
     │  make package         │                        │
     │                       │                        │
     │─ FreeFirInjector.dylib ─→│                     │
     │                       │                        │
     │                       │  python run_all.py     │
     │                       │  ┌─ extrai IPA         │
     │                       │  ├─ copia dylib        │
     │                       │  ├─ patcha binário     │
     │                       │  └─ repacota IPA       │
     │                       │                        │
     │                       │─ Apps_Modified.ipa ─→  │
     │                       │                        │  instala via
     │                       │                        │  TrollStore/AltStore
```

---

## 📋 Passo a Passo

### Etapa 1 — Compilar a dylib (Mac necessário)

1. Instale o **Theos** no Mac:
   ```bash
   bash -c "$(curl -fsSL https://raw.githubusercontent.com/theos/theos/master/bin/install-theos)"
   ```

2. Compile o tweak:
   ```bash
   cd /caminho/para/PENISPROMAX/tweak
   make package
   ```

3. A dylib será copiada automaticamente para `tweak/FreeFirInjector.dylib`

> ⚠️ **Alternativa sem Mac**: Use uma VM macOS, GitHub Actions com runner macOS, ou peça para alguém compilar por você.

---

### Etapa 2 — Injetar no IPA (Windows)

Certifique-se que o Python 3.8+ está instalado, então:

```powershell
cd C:\Users\Lopes\Downloads\PENISPROMAX
python run_all.py
```

Saída esperada:
```
[Etapa 1] Verificando pre-requisitos...
  ✅ Apps.ipa encontrado (2.1 MB)
  ✅ FreeFirInjector.dylib encontrada (XX KB)

[Etapa 2] Extraindo Apps.ipa...
  ✅ Extraido em: ./Extracted

[Etapa 3] Copiando dylib para Frameworks/...
  ✅ Dylib copiada

[Etapa 4] Injetando load command no binário Mach-O...
  ✅ Load command injetado com sucesso

[Etapa 5] Reempacotando como Apps_Modified.ipa...
  ✅ IPA criado: Apps_Modified.ipa

  🎉 CONCLUIDO COM SUCESSO!
```

---

### Etapa 3 — Instalar no iPhone

| Método | Passos |
|--------|--------|
| **TrollStore** | Copie o IPA para o iPhone → Abra no TrollStore → Instalar |
| **AltStore** | Arraste o IPA para o AltStore ou Sideloadly |
| **Jailbreak** | `ideviceinstaller -i Apps_Modified.ipa` |

---

## 🎮 Como o Botão Funciona

Após instalar, abra o Filza. Você verá um **botão laranja flutuante** no canto inferior direito:

```
┌─────────────────────────────┐
│  [Filza File Manager...]    │
│                             │
│                             │
│                  ┌────────┐ │
│                  │🎮 Inject│ │  ← botão flutuante
│                  └────────┘ │
└─────────────────────────────┘
```

**Ao clicar:**
1. O app localiza o UUID do container do Free Fire em `/var/mobile/Containers/Data/Application/`
2. Cria as pastas necessárias
3. Escreve o arquivo em:
   ```
   .../com.dts.freefireth/Documents/contentcache/Compulsory/ios/
   gameassetbundles/avatar/assetindexer.H5ak1JM1Eck~2FxRcJrEp~2FMzeuqmY~3D
   ```
4. Mostra alerta de ✅ sucesso ou ❌ erro

---

## 🔧 Comandos Úteis

```powershell
# Verificar dylibs que o binario ja carrega (sem modificar nada)
python run_all.py --check

# Listar dylibs diretamente
python tools/patch_binary.py --list Extracted/Payload/3105.app/3105

# Apenas reempacotar (sem reinjetar)
python tools/repack_ipa.py Extracted Apps_Modified.ipa
```

---

## ⚠️ Notas Importantes

- O IPA gerado **não é re-assinado**. Dispositivos sem TrollStore ou Jailbreak precisam de assinatura (use `ldid`, `zsign`, ou AltStore)
- O tweak usa `UIWindowLevel = UIWindowLevelAlert + 100`, portanto o botão aparece **sobre toda a UI** do Filza
- O botão funciona apenas se o Free Fire estiver instalado no mesmo dispositivo
- Testado para iOS 14.0+, ARM64

---

## 📁 Arquivo Alvo

| Campo | Valor |
|-------|-------|
| Bundle ID | `com.dts.freefireth` |
| Caminho relativo | `/Documents/contentcache/Compulsory/ios/gameassetbundles/avatar/assetindexer.H5ak1JM1Eck~2FxRcJrEp~2FMzeuqmY~3D` |
| Conteúdo escrito | `LOPES_INJECTED_OK` |
