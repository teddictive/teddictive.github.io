#!/bin/zsh
# 더블클릭: '새페이지' 폴더 안의 작업 폴더를 골라 새 페이지를 만듭니다.
cd "$(dirname "$0")"
dirs=(새페이지/*(/N))
dirs=(${dirs:#새페이지/_예시})
if [ ${#dirs} -eq 0 ]; then echo "새페이지 폴더 안에 작업 폴더가 없습니다. README의 '새 페이지 만들기'를 보세요."; read; exit 1; fi
echo "어느 폴더로 페이지를 만들까요?"
select d in $dirs; do [ -n "$d" ] && break; done
python3 tools/add_page.py "$d" && echo "확인은 '미리보기.command', 올리기는 '사이트에 올리기.command'"
echo "엔터를 누르면 창이 닫힙니다."; read
