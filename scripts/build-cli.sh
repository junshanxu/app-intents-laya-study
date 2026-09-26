#!/bin/zsh
set -euo pipefail
project_dir=${0:A:h:h}
mkdir -p "$project_dir/bin"
swiftc "$project_dir/Shared/StudyStore.swift" "$project_dir/CLI/main.swift" -o "$project_dir/bin/studyctl"
