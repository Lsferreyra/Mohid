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

tree_mode=unchanged
tree_file="$work_root/case/exe/tree.dat"
if [[ -f "$tree_file" ]]; then
    if grep -Eq '^[[:space:]]*\+.*:[[:space:]]*(0|[2-9][0-9]*|1[0-9]+)[[:space:]]*$' "$tree_file"; then
        echo "Invalid serial smoke case: tree.dat requests zero or multiple domains" >&2
        exit 2
    fi

    if grep -Eq '^[[:space:]]*\+.*:[[:space:]]*1[[:space:]]*$' "$tree_file"; then
        sed -E '/^[[:space:]]*\+/ s/[[:space:]]*:[[:space:]]*1[[:space:]]*$//' \
            "$tree_file" >"$tree_file.serial"
        mv -- "$tree_file.serial" "$tree_file"
        tree_mode=single-domain-normalized
    fi
fi

set +e
(
    cd "$work_root/case/exe"
    timeout "$timeout_seconds" "$executable"
) >"$results_dir/run.log" 2>&1
status=$?
set -e

cp -a "$work_root/case/res/." "$results_dir/"
printf 'exit_code=%s\nexecutable=%s\ntimeout_seconds=%s\ntree_mode=%s\n' \
    "$status" "$executable" "$timeout_seconds" "$tree_mode" \
    >"$results_dir/status.txt"

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
