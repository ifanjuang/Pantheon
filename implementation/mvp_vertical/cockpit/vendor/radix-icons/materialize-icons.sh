#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$here/upstream/packages/radix-icons/icons"
destination="$here/icons"
expected_commit="$(tr -d '[:space:]' < "$here/UPSTREAM_COMMIT")"

if [[ ! -d "$source_dir" ]]; then
  echo "Radix submodule is not initialized. Run: git submodule update --init --recursive" >&2
  exit 2
fi

actual_commit="$(git -C "$here/upstream" rev-parse HEAD)"
if [[ "$actual_commit" != "$expected_commit" ]]; then
  echo "Refusing to materialize: upstream checkout is $actual_commit, expected $expected_commit" >&2
  exit 3
fi

mapfile -t source_icons < <(find "$source_dir" -maxdepth 1 -type f -name '*.svg' -print | sort)
if [[ ${#source_icons[@]} -ne 331 ]]; then
  echo "Refusing to materialize: expected 331 SVGs, found ${#source_icons[@]}" >&2
  exit 4
fi

mkdir -p "$destination"
find "$destination" -maxdepth 1 -type f -name '*.svg' -delete
cp -- "${source_icons[@]}" "$destination/"

materialized="$(find "$destination" -maxdepth 1 -type f -name '*.svg' | wc -l | tr -d ' ')"
if [[ "$materialized" != "331" ]]; then
  echo "Materialization count mismatch: $materialized" >&2
  exit 5
fi

printf 'Materialized %s Radix SVG icons from %s\n' "$materialized" "$actual_commit"
printf 'Review the diff before committing. This script never commits or updates the upstream pin.\n'
