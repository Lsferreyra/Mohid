#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ci_dir=$(cd -- "$script_dir/.." && pwd)
repo_root=$(cd -- "$ci_dir/../.." && pwd)

profile=${1:-reference}
case_dir=${2:-$repo_root/Solutions/mohid-in-linux/test/mohidwater/25m_deep}
results_dir=${3:-$ci_dir/results/$profile}

case "$profile" in
    reference)
        image=${MOHID_IMAGE:-mohid-water:reference}
        executable=/mohid/MohidWater.exe
        ;;
    gfortran)
        image=${MOHID_IMAGE:-mohid-water:gfortran}
        executable=/opt/mohid/bin/MohidWater.exe
        ;;
    ifx)
        image=${MOHID_IMAGE:-mohid-water:ifx}
        executable=/opt/mohid/bin/MohidWater.exe
        ;;
    *)
        echo "Unknown profile '$profile'. Use reference, gfortran or ifx." >&2
        exit 2
        ;;
esac

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required but was not found" >&2
    exit 2
fi

if [[ ! -d "$case_dir" ]]; then
    echo "MOHID case directory does not exist: $case_dir" >&2
    exit 2
fi

mkdir -p "$results_dir"
case_dir=$(cd -- "$case_dir" && pwd)
results_dir=$(cd -- "$results_dir" && pwd)

docker run --rm \
    --user "$(id -u):$(id -g)" \
    --entrypoint /bin/bash \
    -e "MOHID_EXECUTABLE=$executable" \
    -e "MOHID_TIMEOUT_SECONDS=${MOHID_TIMEOUT_SECONDS:-300}" \
    -v "$case_dir:/input:ro" \
    -v "$results_dir:/results" \
    -v "$script_dir/smoke-in-container.sh:/usr/local/bin/mohid-smoke:ro" \
    "$image" /usr/local/bin/mohid-smoke
