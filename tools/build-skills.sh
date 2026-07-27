#!/usr/bin/env bash
set -euo pipefail

VERSION=$(cat VERSION)
DIST="dist/skills"
rm -rf "$DIST"
mkdir -p "$DIST"

group_for() {
  case "$1" in
    rn-renhua)              echo "01-writing" ;;
    rn-motion-director)     echo "02-video-production" ;;
    rn-motion-replica)      echo "02-video-production" ;;
    rn-dark-saas-video)     echo "02-video-production" ;;
    rn-bw-text-opener)      echo "02-video-production" ;;
    rn-replica-qc)          echo "03-quality-control" ;;
    rn-cover-skill)         echo "04-design" ;;
    *)                      echo "99-other" ;;
  esac
}

COUNT=0
for skill_md in skills/*/SKILL.md; do
  skill_dir=$(dirname "$skill_md")
  skill_name=$(basename "$skill_dir")

  # Skip beta skills
  if [[ "$skill_name" == *beta* ]]; then
    echo "  skip (beta): $skill_name"
    continue
  fi

  group=$(group_for "$skill_name")
  out_dir="$DIST/$group"
  mkdir -p "$out_dir"

  tmp_dir=$(mktemp -d)
  trap 'rm -rf "$tmp_dir"' EXIT

  # Copy SKILL.md
  cp "$skill_md" "$tmp_dir/SKILL.md"

  # Copy companion directories if they exist
  for sub in agents references scripts templates docs tools assets; do
    if [[ -d "$skill_dir/$sub" ]]; then
      cp -R "$skill_dir/$sub" "$tmp_dir/$sub"
    fi
  done

  (cd "$tmp_dir" && zip -qr "$OLDPWD/$out_dir/$skill_name.zip" .)
  rm -rf "$tmp_dir"

  echo "  packed: $skill_name -> $group/"
  COUNT=$((COUNT + 1))
done

# Create combined archive
cat > "$DIST/README.md" <<EOF
# rnskill v${VERSION}

Packed $COUNT skills. Drag individual ZIPs into Trae Solo or extract manually.

## Categories

- 01-writing: 写作精修
- 02-video-production: 视频制作
- 03-quality-control: 视频质检
- 04-design: 视觉设计
EOF

(cd "$DIST" && zip -qr "../rnskill-${VERSION}.zip" .)

echo ""
echo "Done: $COUNT skills packed into dist/rnskill-${VERSION}.zip"
