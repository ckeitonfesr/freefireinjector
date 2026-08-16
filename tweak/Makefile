# ─────────────────────────────────────────────────────────────────────────────
#  Makefile — FreeFirInjector Tweak
#  Requer: Theos instalado (https://theos.dev/docs/installation)
# ─────────────────────────────────────────────────────────────────────────────

# Target: iOS 14+ ARM64 apenas (Filza moderno so roda em ARM64)
ARCHS  = arm64
TARGET = iphone:clang:latest:14.0

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = FreeFirInjector

FreeFirInjector_FILES       = Tweak.x
FreeFirInjector_CFLAGS      = -fobjc-arc -Wall
FreeFirInjector_LDFLAGS     =
FreeFirInjector_FRAMEWORKS  = UIKit Foundation

# Filtra apenas o executavel "3105" (o app do Filza modificado)
# Isso evita que o tweak carregue em TODOS os apps
FreeFirInjector_FILTER_EXECUTABLES = 3105

include $(THEOS_MAKE_PATH)/tweak.mk

# Apos build, copia a dylib para a pasta do projeto
after-stage::
	@echo "📦 Copiando dylib para ../tweak/..."
	@cp -f $(THEOS_STAGING_DIR)/Library/MobileSubstrate/DynamicLibraries/FreeFirInjector.dylib \
	       ../tweak/FreeFirInjector.dylib 2>/dev/null || true
	@echo "✅ FreeFirInjector.dylib pronta"
