# Reproducible MOHID Water build and smoke tests

This directory introduces three deliberately separate build profiles:

| Profile | Purpose | Compiler and dependencies |
|---|---|---|
| `reference` | Reproduce the repository's existing Linux container before changing toolchains. | Intel oneAPI 2023.2.1, `ifort`, HDF5 1.8.17, zlib 1.2.11. |
| `gfortran` | Detect non-portable interfaces and runtime errors with an independent compiler. | Ubuntu 24.04 packages, `gfortran`, runtime checks enabled. |
| `ifx` | Test the supported Intel migration path. | Intel oneAPI 2026.1 `ifx`, HDF5 1.14.6 built from commit `7bf3404`. |

The reference profile is a compatibility baseline, not a recommendation for
production or for processing untrusted files. Its old HDF5 and zlib versions
are retained only to answer the question: "can we reproduce the existing
MOHID binary before modernising it?"

## Requirements

- WSL2 or Linux;
- Docker Engine or Docker Desktop with WSL integration;
- GNU Make;
- at least 16 GB RAM recommended for the Intel image;
- approximately 15 GB free disk space for the three images and build cache.

## First commands

From this directory:

```bash
make check
make reference-smoke
```

The second command builds the existing reference image, copies the bundled
`25m_deep` case into an isolated temporary directory, runs MOHID, checks its
exit code and success marker, and writes logs under `results/reference/`.

The current bundled case is only a startup/smoke test. It does **not** validate
hydrodynamics or numerical accuracy.

To exercise the modern compiler lanes:

```bash
make gfortran-smoke
make ifx-smoke
```

Compiler failures in these lanes are useful results: they identify concrete
portability and interface defects that must be corrected without changing the
reference baseline.

## Run a local case

Set `CASE` to an absolute or repository-relative case directory containing
`exe/nomfich.dat`:

```bash
make ifx-smoke CASE=/path/to/a/mohid/case
```

The input is mounted read-only. Results and the full log are copied to
`results/<profile>/`, so the source case is not modified.

## What this does not certify

A successful smoke run proves only that the executable starts, reads the
bundled input, exits with status zero, and prints MOHID's success marker. A
scientific validation suite must subsequently add:

1. a lake-at-rest and mass-conservation test;
2. an analytical M2 channel with amplitude and phase gates;
3. a wetting/drying case with changing masks;
4. continuous versus restart equivalence;
5. serial, OpenMP and MPI comparisons;
6. the Canal Beagle case with observational and numerical metrics kept separate.

NetCDF, MPI and OpenMP are intentionally disabled in the first serial baseline.
They will be enabled one at a time after the serial reference is reproducible.
The modern lanes select the effective upstream instance limit explicitly
(`increased`, 2000) instead of defining the contradictory `increased` and
`extra` macros together.
