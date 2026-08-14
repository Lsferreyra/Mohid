#!/usr/bin/env bash
set -euo pipefail

input_dir=${MOHID_INPUT_DIR:-/input}
results_dir=${MOHID_RESULTS_DIR:-/results}
executable=${MOHID_EXECUTABLE:?MOHID_EXECUTABLE must point to MohidWater.exe}
timeout_seconds=${MOHID_TIMEOUT_SECONDS:-300}

if [[ ! -d "$input_dir/exe" || ! -f "$input_dir/exe/nomfich.dat" ]]; then
    echo "Invalid MOHID case: expected $input_dir/exe/nomfich.dat" >&2
    exit 2
fi

if [[ ! -x "$executable" ]]; then
    echo "MOHID executable is not runnable: $executable" >&2
    exit 2
fi

work_root=$(mktemp -d /tmp/mohid-smoke.XXXXXX)
trap 'rm -rf -- "$work_root"' EXIT

mkdir -p "$work_root/case" "$results_dir"
cp -a "$input_dir/." "$work_root/case/"
mkdir -p "$work_root/case/res/Run1" "$work_root/case/res/Res1"

set +e
(
    cd "$work_root/case/exe"
    timeout "$timeout_seconds" "$executable"
) >"$results_dir/run.log" 2>&1
status=$?
set -e

cp -a "$work_root/case/res/." "$results_dir/"
printf 'exit_code=%s\nexecutable=%s\ntimeout_seconds=%s\n' \
    "$status" "$executable" "$timeout_seconds" >"$results_dir/status.txt"

cat "$results_dir/run.log"

if [[ $status -ne 0 ]]; then
    echo "MOHID smoke run failed with exit code $status" >&2
    exit "$status"
fi

if ! grep -Fq "Program Mohid Water successfully terminated" "$results_dir/run.log"; then
    echo "MOHID exited with zero but did not print its success marker" >&2
    exit 3
fi

echo "MOHID smoke run passed"
