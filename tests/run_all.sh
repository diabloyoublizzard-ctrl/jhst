#!/bin/zsh
# 執行全部 JXA 回歸測試；任一失敗即回傳非 0
cd "${0:A:h}" || exit 1
fail=0
for t in test_*.py; do
  if python3 "$t" >/dev/null 2>&1; then echo "PASS  $t"; else echo "FAIL  $t"; fail=1; fi
done
exit $fail
