#!/bin/sh
# 변경사항이 있으면 자동 커밋 후 push (post-commit 훅이 push 수행)
cd "$(dirname "$0")/.." || exit 1
if git status --short | grep -q .; then
  git add -A
  git commit -m "Auto commit: $(date '+%Y-%m-%d %H:%M')"
  # post-commit 훅이 자동 push 함 (없으면 아래 주석 해제)
  # git push
fi
