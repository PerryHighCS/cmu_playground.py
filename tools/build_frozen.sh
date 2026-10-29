#!/usr/bin/env bash
# Run in Linux/WSL with CircuitPython's build dependencies installed.
# Usage: bash tools/build_frozen.sh /path/to/circuitpython-10.3.1
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -ne 1 ]]; then
    echo 'Usage: bash tools/build_frozen.sh /path/to/circuitpython-10.3.1' >&2
    exit 1
fi
cp_dir="$(cd "$1" && pwd)"
if [[ "$(git -C "$cp_dir" describe --tags --exact-match HEAD)" != '10.3.1' ]]; then
    echo 'Use a dedicated CircuitPython checkout at tag 10.3.1.' >&2
    exit 1
fi
for tool in make gcc arm-none-eabi-gcc python3; do
    command -v "$tool" >/dev/null || { echo "Missing build tool: $tool" >&2; exit 1; }
done

board_config="$cp_dir/ports/atmel-samd/boards/circuitplayground_express/mpconfigboard.mk"
test -f "$board_config"
mkdir -p "$cp_dir/cmu_frozen"
# Freeze the source using the firmware's own mpy-cross, not the standalone .mpy.
cp "$project_dir/cmu_playground.py" "$cp_dir/cmu_frozen/cmu_playground.py"
freeze_line='FROZEN_MPY_DIRS += $(TOP)/cmu_frozen'
if ! grep -Fxq "$freeze_line" "$board_config"; then
    printf '\n%s\n' "$freeze_line" >> "$board_config"
fi

make -C "$cp_dir/ports/atmel-samd" BOARD=circuitplayground_express fetch-port-submodules
make -C "$cp_dir/mpy-cross" -j2
make -C "$cp_dir/ports/atmel-samd" BOARD=circuitplayground_express -j2

mkdir -p "$project_dir/firmware"
cp "$cp_dir/ports/atmel-samd/build-circuitplayground_express/firmware.uf2" \
    "$project_dir/firmware/cmu-playground-cpx-10.3.1.uf2"
echo "Built $project_dir/firmware/cmu-playground-cpx-10.3.1.uf2"
