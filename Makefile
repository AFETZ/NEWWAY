SHELL := /usr/bin/env bash

NS3_DIR ?= ns-3-dev
NS3 ?= $(NS3_DIR)/ns3
JOBS ?= 2
CONFIGURE_FLAGS ?= --build-profile=optimized --enable-examples --enable-tests --disable-python --disable-werror
BUILD_TARGET ?=
RUN_TARGET ?= v2v-simple-cam-exchange-80211p
TEST_SUITE ?=

.PHONY: help bootstrap bootstrap-deps check-ns3 configure build run test-list test-suite

help:
	@echo "Targets:"
	@echo "  bootstrap       Run sandbox bootstrap (destructive in current directory)"
	@echo "  bootstrap-deps  Same as bootstrap + dependency install"
	@echo "  configure       Configure generated ns-3 tree"
	@echo "  build           Build (optionally set BUILD_TARGET=...)"
	@echo "  run             Run built target (set RUN_TARGET=...)"
	@echo "  test-list       List test suites (builds test-runner if needed)"
	@echo "  test-suite      Run one suite (set TEST_SUITE=...)"
	@echo ""
	@echo "Variables:"
	@echo "  JOBS=$(JOBS)"
	@echo "  NS3_DIR=$(NS3_DIR)"

bootstrap:
	@echo "WARNING: sandbox_builder.sh is destructive in-place."
	@echo "Run this target only in a disposable clone."
	printf '\n' | ./sandbox_builder.sh

bootstrap-deps:
	@echo "WARNING: sandbox_builder.sh is destructive in-place."
	@echo "Run this target only in a disposable clone."
	printf '\n' | ./sandbox_builder.sh install-dependencies

check-ns3:
	@if [[ ! -x "$(NS3)" ]]; then \
		echo "Missing $(NS3). Run bootstrap first (preferably in disposable workspace)."; \
		exit 1; \
	fi

configure: check-ns3
	cd $(NS3_DIR) && ./ns3 configure $(CONFIGURE_FLAGS)

build: check-ns3
	cd $(NS3_DIR) && ./ns3 build -j $(JOBS) $(BUILD_TARGET)

run: check-ns3
	cd $(NS3_DIR) && ./ns3 run --no-build "$(RUN_TARGET)"

test-list: check-ns3
	cd $(NS3_DIR) && ./test.py --list

test-suite: check-ns3
	@if [[ -z "$(TEST_SUITE)" ]]; then \
		echo "Set TEST_SUITE, e.g. make test-suite TEST_SUITE=nr-test-timings"; \
		exit 1; \
	fi
	cd $(NS3_DIR) && ./test.py --no-build --suite="$(TEST_SUITE)"
