#!/bin/zsh
# 더블클릭: 바뀐 내용을 GitHub에 올립니다. 1~2분 뒤 teddictive.com 에 반영됩니다.
cd "$(dirname "$0")"
git pull --rebase -q || { echo "GitHub에서 받아오기 실패. 위 메시지를 확인하세요."; read; exit 1; }
git add -A
if git diff --cached --quiet; then echo "바뀐 내용이 없습니다."; read; exit 0; fi
git status --short
git commit -q -m "사이트 수정 $(date '+%Y-%m-%d %H:%M')" && git push -q && echo "올리기 완료: 1~2분 뒤 https://teddictive.com 에 반영됩니다."
echo "엔터를 누르면 창이 닫힙니다."; read
