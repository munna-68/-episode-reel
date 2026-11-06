#!/bin/zsh
# Create the next episode folder next to the others, with the standard layout and a fresh copy of the tools.
#   zsh .claude/skills/episode-reel/scripts/new_episode.sh [N]      (run from the series folder: the one with the project-local .mcp.json)
# Without N it picks the next free number. Never touches existing episodes or the client's repo.
set -e
SKILL="${0:A:h:h}"
ROOT="$PWD"
[[ -f "$ROOT/.mcp.json" ]] || { echo "Run this from the series folder (the one with the project-local .mcp.json)."; exit 1; }
N=${1:-$(( $(ls -d reel-episode-* 2>/dev/null | sed 's/.*-//' | sort -n | tail -1) + 1 ))}
EP="$ROOT/reel-episode-$N"
[[ -e "$EP" ]] && { echo "$EP already exists"; exit 1; }
mkdir -p "$EP"/{brief,assets,shots,footage,audio/raw,music,comp,out,tools}
for f in "$SKILL"/scripts/*; do [[ ${f:t} == new_episode.sh ]] || cp "$f" "$EP/tools/"; done
cp "$SKILL/assets/comp/one.html" "$EP/comp/"
chmod +x "$EP"/tools/*.sh
# playwright: reuse an installed copy from an earlier episode if there is one (same version), else install (small; browsers are cached)
PREV=$(ls -d "$ROOT"/reel-episode-*/tools/node_modules/playwright 2>/dev/null | head -1)
if [[ -n "$PREV" ]]; then cp -R "${PREV:h}" "$EP/tools/node_modules"; else (cd "$EP/tools" && npm install --no-audit --no-fund --silent); fi
cat > "$EP/NOTES.md" <<MD
# Episode $N notes
(inputs, script versions, claims to stand behind, placeholders on screen, voice, music, what changed per version, re-render steps)
MD
echo "$EP"
