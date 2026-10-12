#!/usr/bin/env bash
# Run the Slidev dev server for one deck.
#
#   ./run.sh 01-information-theory.md     # full file name
#   ./run.sh 01                           # or just the lecture number
#   ./run.sh 05 --port 3031               # extra arguments go to slidev
#
# Without an argument, lists the available decks.
set -euo pipefail

cd "$(dirname "$0")"

if [[ $# -eq 0 ]]; then
    echo "usage: $0 <deck.md | lecture number> [slidev args...]" >&2
    echo "decks:" >&2
    ls [0-9][0-9]-*.md | sed 's/^/  /' >&2
    exit 1
fi

deck=$1
shift

if [[ ! -f $deck ]]; then
    matches=("${deck}"-*.md)
    if [[ -f ${matches[0]} ]]; then
        deck=${matches[0]}
    else
        echo "no deck matching '$deck'" >&2
        exit 1
    fi
fi

[[ -d node_modules ]] || npm install

exec npx slidev --open "$deck" "$@"
