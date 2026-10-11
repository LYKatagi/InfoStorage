.DEFAULT_GOAL := all

PYTHON ?= py
ANDROID_BUILD_FLAGS ?= --no-configuration-cache

ifeq ($(OS),Windows_NT)
ANDROID_BUILD = cmd /c "android\gradlew.bat -p android assembleDebug $(ANDROID_BUILD_FLAGS)"
else
ANDROID_BUILD = ./android/gradlew -p android assembleDebug $(ANDROID_BUILD_FLAGS)
endif

.PHONY: all compile-python android help

all: compile-python android

compile-python:
	$(PYTHON) -m compileall -q \
		python/info_storage/__init__.py \
		python/info_storage/__main__.py \
		python/info_storage/mobile_api.py \
		python/info_storage/auth \
		python/info_storage/main \
		python/info_storage/security \
		python/info_storage/storage \
		python/info_storage/vault \
		python/info_storage/desktop

android:
	$(ANDROID_BUILD)

help:
	@echo all            Compile non-web Python modules and build Android debug APK
	@echo compile-python Compile core, desktop, CLI and Android adapter Python sources
	@echo android        Build android/app/build/outputs/apk/debug/app-debug.apk