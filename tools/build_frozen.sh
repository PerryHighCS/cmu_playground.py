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
arm_gcc_major="$(arm-none-eabi-gcc -dumpversion | cut -d. -f1)"
if (( arm_gcc_major < 14 )); then
    echo "CircuitPython 10.3.1 requires ARM GCC >= 14; found $arm_gcc_major." >&2
    exit 1
fi
arm-none-eabi-gcc --version

board_config="$cp_dir/ports/atmel-samd/boards/circuitplayground_express/mpconfigboard.mk"
test -f "$board_config"
# Remove the board edit left by the earlier version of this script.
python3 - "$board_config" <<'PY'
import pathlib
import sys
path = pathlib.Path(sys.argv[1])
text = path.read_text()
legacy_line = 'FROZEN_MPY_DIRS += $(TOP)/cmu_frozen'
if legacy_line in text.splitlines():
    path.write_text(''.join(line for line in text.splitlines(keepends=True)
                            if line.strip() != legacy_line))
PY

# Select dependencies by board, before adding our non-submodule source directory.
# The port-wide target clones every frozen library and unrelated port libraries.
make -C "$cp_dir/ports/atmel-samd" BOARD=circuitplayground_express fetch-board-submodules
# CircuitPython 10.3.1's board fetch omits this frozen-manifest dependency.
# Fetch only the pinned submodule; do not initialize its nested libraries.
git -C "$cp_dir" submodule update --init --depth 1 -- lib/micropython-lib
test -f "$cp_dir/lib/micropython-lib/README.md"

mkdir -p "$cp_dir/cmu_frozen"
# Freeze the source using the firmware's own mpy-cross, not the standalone .mpy.
cp "$project_dir/cmu_playground.py" "$cp_dir/cmu_frozen/cmu_playground.py"
mkdir -p "$cp_dir/cmu_build_config"
cat > "$cp_dir/cmu_build_config/user_post_mpconfigport.mk" <<'MAKE'
FROZEN_MPY_DIRS += $(TOP)/cmu_frozen
# Leave flash space for the framework. Hardware pulse counting is unused.
CIRCUITPY_COUNTIO = 0
MAKE

make -C "$cp_dir/mpy-cross" -j2
make -C "$cp_dir/ports/atmel-samd" -I "$cp_dir/cmu_build_config" \
    BOARD=circuitplayground_express -j2

mkdir -p "$project_dir/firmware"
cp "$cp_dir/ports/atmel-samd/build-circuitplayground_express/firmware.uf2" \
    "$project_dir/firmware/cmu-playground-cpx-10.3.1.uf2"
echo "Built $project_dir/firmware/cmu-playground-cpx-10.3.1.uf2"
