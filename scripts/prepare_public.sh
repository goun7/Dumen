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
PRUNE=(scripts/prepare_public.sh DUMEN_MASTER_100.md INSAA_SPECI_V1.md YOL_HARITASI.md task_plan.md docs/KAMUYA_ACMA.md REKIP_ANALIZI_2026-09.md "Yapay Zeka Denetim Projeleri Araştırması.md" .mergen-id)
# History'de dahi kabul-edilemez kalıplar (tarama-desenleri):
# Kendine-doyuran desenler: [karakter] sınıfı DESMENIN KENDİSİNE değmez, gerçek izlere değer.
BAN_GREP='[v]egoko7|/home/[g]okun|0[1]_unicorn|session\.[v]|DUMEN_MASTER_100|INSAA_SPECI(_V1)?|YOL_HARITASI|KAMUYA_ACMA|task_plan|REKIP_ANALIZI|\.mergen-id'

echo "🧱 kaynak : $SRC"
echo "📦 hedef  : $OUT (varsa silinir)"
echo "🙈 kimlik : $PUBLIC_NAME <$PUBLIC_EMAIL>"
echo "✂️  budama : ${PRUNE[*]}"
echo "🧪 DRY_RUN: $DRY_RUN (0 = maskele+budla+scrubla)"

P1="DUME"N_MASTER_100.md; P2="INS"AA_SPECI_V1.md; P3="YOL_"HARITASI.md; P4="task_"plan.md; P5="docs/KAM"UYA_ACMA.md; P6="REKIP_ANAL"IZI_2026-09.md; P7=".merg"en-id; P9="scripts/prep"are_public.sh; P8='"?Yapay Zeka[^"]*\.md"?'
rm -rf "$OUT"
git clone --quiet "$SRC" "$OUT"
cd "$OUT"

if [ "$DRY_RUN" != "0" ]; then
  echo "🧪 kuru-koşum CANLILIK KANITI (maskeleme öncesi — pozitif beklenir):"
  echo "   içerik-izi:   $(git log -p --all | grep -cE "$BAN_GREP" || true)"
  echo "   yol-izi:      $(git log --all --diff-filter=AM --name-only --format= | sort -u | grep -cE "^($P1|$P2|$P3|$P4|$P5|$P6|$P7|$P8|$P9)$" || true)"
  echo "   (ikisi de >0 olmalı — kapının mermisi var; gerçek eşik DRY_RUN=0 koşumunda 0 olmaktır)"
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
s = re.sub(rb'DUMEN_MASTER_100(\\.md)?', b'an internal planning doc', s)
s = re.sub(rb'YOL_HARITASI(\\.md)?', b'the private roadmap', s)
s = re.sub(rb'INSAA_SPECI(_V1)?(\\.md)?', b'an internal spec', s)
s = re.sub(rb'KAMUYA_ACMA(\\.md)?', b'the private launch checklist', s)
s = re.sub(rb'session\\.v[0-9]+\\.jsonl', b'a session journal', s)
s = re.sub(rb'session\\.v\\*', b'journal-*', s)
s = re.sub(rb'prepare_public(\\.sh)?', b'release-hygiene tooling', s)
s = re.sub(rb'\\.mergen\-id', b'a local tool artifact', s)
s = re.sub(rb'Yapay\\.\\.\\.', b'a quoted path', s)
s = re.sub(rb'REKIP_ANALIZI(_2026-09)?(\\.md)?', b'internal market research', s)
s = re.sub(rb'task_plan(\\.md)?', b'an internal worksheet', s)
s = re.sub('Yapay Zeka Denetim Projeleri Araştırması\\.md'.encode(), b'market research doc', s)
s = re.sub('Yapay[\\s\\S]{0,40}Araştırması\\.md'.encode('utf-8', 'surrogateescape'), b'market research doc', s)
s = re.sub(rb'INSAA', b'an-internal-spec', s)
s = re.sub(rb'REKIP', b'internal-research', s)
s = re.sub(rb'KAMUYA', b'the-private-launch-doc', s)
return s" \
  --blob-callback "
import re
b = blob.data
b = re.sub(rb'/home/gokun/projects/01_unicorn/77-Dumen', b'.', b)
b = b.replace(b'/home/gokun', b'~')
b = re.sub(rb'01_unicorn', b'private-hub', b)
b = b.replace(b'vegoko7@gmail.com', b'${PUBLIC_EMAIL}')
b = re.sub(rb'session\.v\*', b'journal-*', b)
b = re.sub(rb'DUMEN_MASTER_100(\.md)?', b'an internal planning doc', b)
b = re.sub(rb'INSAA_SPECI(_V1)?(\.md)?', b'an internal spec', b)
b = re.sub(rb'YOL_HARITASI(\.md)?', b'the private roadmap', b)
b = re.sub(rb'KAMUYA_ACMA(\.md)?', b'the private launch checklist', b)
b = re.sub(rb'task_plan(\.md)?', b'an internal worksheet', b)
b = re.sub(rb'REKIP_ANALIZI(_2026-09)?(\.md)?', b'internal market research', b)
b = b.replace(b'.mergen-id', b'a local tool artifact')
b = re.sub(rb'INSAA', b'an-internal-spec', b)
b = re.sub(rb'REKIP', b'internal-research', b)
b = re.sub(rb'KAMUYA', b'the-private-launch-doc', b)
blob.data = b
return blob" \
  "${PRUNE_ARGS[@]}"

echo "🔎 FAIL-LOUD kapı: working-tree + TÜM history + mesajlar yasaklı-desen taraması…"
LEAKS=0
# pipefail + grep -q SIGPIPE tuzağı: -q erken çıkınca git 141 döner ve if YANLIŞ
# yorumlanır → Sayaç-la tam-okuma zorunlu (2026-09-15 bulgusu: -q'lu sürüm ölüydü).
NL=$(git log -p --all | grep -cE "$BAN_GREP" || true)
if [ "$NL" -gt 0 ]; then
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
HITS_P=$(git log --all --diff-filter=AM --name-only --format= | sort -u | grep -cE "^($P1|$P2|$P3|$P4|$P5|$P6|$P7|$P8)$" || true)
echo "   budanan-belgelerin history-içi satır-izi: $HITS_P (0 olmalı; dosya-yolları parçalı-adla aranır)"
[ "$HITS_P" -eq 0 ] || { echo "🛑 PRUNE uygulanmamış — yayın YOK"; exit 1; }
echo
echo "📤 PUSH KASITLI OLARAK BURADA DEĞİL (çift-eller):"
echo "   cd $OUT && git remote add origin <url> && git push -u origin <dal> --follow-tags"
