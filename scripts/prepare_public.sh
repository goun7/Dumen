#!/usr/bin/env bash
# =============================================================================
# scripts/prepare_public.sh v2 — güvenli açık-repo yayın-hazırlığı
# =============================================================================
# ORİJİNAL depoya DOKUNMAZ: temiz klon üretir ve history'yi üç katta temizler:
#   1) MASKE   : tüm commit imzaları (author+committer) tek kamusal kimliğe
#   2) PRUNE   : strateji/iç-belgeler GEÇMİŞTEN sökültülür (--invert-paths)
#   3) SCRUB   : commit mesajlarındaki iç-yol/iç-belge/ad-soyad izleri yazılır-öncesi
#                callback ile dönüştürülür; + son-tarama artık FAIL-LOUD kapıdır.
# PUSH bu scriptin içinde DEĞİL (bilinçli: çift-eller kuralı — script hazırlar,
# yayını insan/ajan ayrı komutla yapar).
#
# Kullanım:
#   bash scripts/prepare_public.sh            # kuru-koşum: tarama VAR, değişiklik YOK
#   DRY_RUN=0 bash scripts/prepare_public.sh  # aile-standardı kimlikle maskele
#   # ya da kendin seç:
#   DRY_RUN=0 PUBLIC_NAME="..." PUBLIC_EMAIL="..." bash scripts/prepare_public.sh
#
# Sonra:
#   cd ../77-Dumen-public
#   git remote add origin https://github.com/<hesap>/Dumen.git && git push -u origin master
# =============================================================================
set -euo pipefail

DRY_RUN="${DRY_RUN:-1}"
SRC="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
OUT="${OUT:-${SRC}-public}"
# Aile içtihadı (Sester, 14-Eyl): kamusal imza = hesap + GitHub-noreply e-posta.
PUBLIC_NAME="${PUBLIC_NAME:-goun7}"
PUBLIC_EMAIL="${PUBLIC_EMAIL:-256555322+goun7@users.noreply.github.com}"
# Yayın-DIŞI kalacak strateji/iç belgeler (working-tree + tüm history'den sökülür):
PRUNE=(DUMEN_MASTER_100.md INSAA_SPECI_V1.md YOL_HARITASI.md task_plan.md docs/KAMUYA_ACMA.md)
# History'de dahi kabul-edilemez kalıplar (tarama-desenleri):
BAN_GREP='vegoko7|@gmail\.com|/home/gokun|01_unicorn|DUMEN_MASTER_100|INSAA_SPECI_V1|YOL_HARITASI|KAMUYA_ACMA|session\.v[0-9]'

echo "🧱 kaynak : $SRC"
echo "📦 hedef  : $OUT (varsa silinir)"
echo "🙈 kimlik : $PUBLIC_NAME <$PUBLIC_EMAIL>"
echo "✂️  budama : ${PRUNE[*]}"
echo "🧪 DRY_RUN: $DRY_RUN (0 = maskele+budla+scrubla)"

rm -rf "$OUT"
git clone --quiet "$SRC" "$OUT"
cd "$OUT"

if [ "$DRY_RUN" != "0" ]; then
  echo "🧪 kuru-koşum: ham-history'de yasaklı-iz sayımı (maskeleme öncesi — pozitif beklenir):"
  git log -p --all | grep -cE "$BAN_GREP" || true
  echo "   gerçek kapı DRY_RUN=0 koşumunda çalışır."
  exit 0
fi

echo "🎭+✂️  maskele, buda, mesajları scrubla…"
PRUNE_ARGS=()
for p in "${PRUNE[@]}"; do PRUNE_ARGS+=(--invert-paths --path "$p"); done
git-filter-repo --force \
  --name-callback  "return b'${PUBLIC_NAME}'" \
  --email-callback "return b'${PUBLIC_EMAIL}'" \
  --message-callback "
import re
s = message
s = re.sub(rb'/home/gokun/projects/01_unicorn/77-Dumen', b'the-repo', s)
s = re.sub(rb'/home/gokun', b'~', s)
s = re.sub(rb'01_unicorn', b'private-hub', s)
s = re.sub(rb'vegoko7@gmail\\.com', b'${PUBLIC_EMAIL}', s)
s = re.sub(rb'DUMEN_MASTER_100\\.md', b'an internal planning doc', s)
s = re.sub(rb'YOL_HARITASI(\\.md)?', b'the private roadmap', s)
s = re.sub(rb'INSAA_SPECI_V1\\.md', b'an internal spec', s)
s = re.sub(rb'KAMUYA_ACMA\\.md', b'the private launch checklist', s)
s = re.sub(rb'session\\.v[0-9]+\\.jsonl', b'a session journal', s)
return s" \
  "${PRUNE_ARGS[@]}"

echo "🔎 FAIL-LOUD kapı: working-tree + TÜM history + mesajlar yasaklı-desen taraması…"
LEAKS=0
if git log -p --all | grep -qE "$BAN_GREP"; then
  git log -p --all | grep -nE "$BAN_GREP" | head -5
  LEAKS=1
fi
# anahtar/secret deseni (placeholder örnekler muaf):
if grep -rInE "(api[_-]?key|secret|token|passwd|password)[\"' ]*[:=][\"' ]*[A-Za-z0-9_./+-]{12,}" \
     --include='*.py' --include='*.md' --include='*.toml' --include='*.json' --include='*.yml' . 2>/dev/null \
   | grep -viE 'your[_-]|placeholder|example|sk-test|\{.*\}|<[a-z_]+>|api_key: Optional|api_key=api_key|Bearer \{'; then
  LEAKS=1
fi
if [ "$LEAKS" -ne 0 ]; then
  echo "🛑 YAYIN YOK — yukarıdaki izler temizlenmeden push edilmemeli."
  exit 1
fi
echo "✅ history + ağaç temiz"

echo "✅ benzersiz imzalar: $(git log --format='%an <%ae>' | sort -u | wc -l) adet"
git log --format='%an <%ae>' | sort -u
echo "   commit sayısı: $(git rev-list --count HEAD) | bütünlük: $(git fsck --no-progress 2>&1 | grep -c 'broken' | xargs -I{} sh -c 'test {} -eq 0 && echo temiz || echo "{} KIRIK"')"
echo "   pruned-belgeler hâlâ var mı?: $(git ls-files | grep -cE "^(DUMEN_MASTER_100|INSAA_SPECI_V1|YOL_HARITASI|task_plan)\.md$|^docs/KAMUYA_ACMA\.md$" || true) (0 olmalı)"
echo
echo "📤 PUSH KASITLI OLARAK BURADA DEĞİL (çift-eller):"
echo "   cd $OUT && git remote add origin <url> && git push -u origin <dal> --follow-tags"
