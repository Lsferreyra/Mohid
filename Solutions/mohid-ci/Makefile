REPO_ROOT := $(abspath ../..)
GIT_SHA := $(shell git -C $(REPO_ROOT) rev-parse HEAD)
CASE ?= $(REPO_ROOT)/Solutions/mohid-in-linux/test/mohidwater/25m_deep

.PHONY: check reference-build reference-smoke gfortran-build gfortran-smoke ifx-build ifx-smoke

check:
	python3 tests/test_manifest.py
	bash -n scripts/run-container-case.sh scripts/smoke-in-container.sh

reference-build:
	docker build \
		--file $(REPO_ROOT)/Solutions/dockers/MohidWater/dockerfile \
		--tag mohid-water:reference \
		$(REPO_ROOT)

reference-smoke: reference-build
	bash ./scripts/run-container-case.sh reference "$(CASE)"

gfortran-build:
	docker build \
		--build-arg MOHID_GIT_SHA=$(GIT_SHA) \
		--file containers/Dockerfile.gfortran \
		--tag mohid-water:gfortran \
		$(REPO_ROOT)

gfortran-smoke: gfortran-build
	bash ./scripts/run-container-case.sh gfortran "$(CASE)"

ifx-build:
	docker build \
		--build-arg MOHID_GIT_SHA=$(GIT_SHA) \
		--file containers/Dockerfile.ifx \
		--tag mohid-water:ifx \
		$(REPO_ROOT)

ifx-smoke: ifx-build
	bash ./scripts/run-container-case.sh ifx "$(CASE)"
