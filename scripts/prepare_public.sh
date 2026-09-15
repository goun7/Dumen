#!/usr/bin/env bash
# =============================================================================
# scripts/prepare_public.sh — güvenli açık-repo yayın-hazırlığı
# =============================================================================
# ORİJİNAL depoya DOKUNMAZ: temiz bir klon üretir, commit imzalarını
# (author+committer) tek proje kimliğine MASKELER, kişisel-veri/anahtar
# son-taraması yapar. PUSH ASLA bu scriptin içinde değildir — yayın kararı
# ve kimlik seçimi kullanıcıya aittir; script hazır depoyu teslim eder.
#
# Neden zorunlu: mevcut history'deki 35 commit kişisel kimlik taşıyor
# (goun7 <vegoko7@gmail.com>) — public repoda bu kalıcı sızıntı olur.
#
# Kullanım:
#   bash scripts/prepare_public.sh                 # kuru-koşum (maskeleme YOK)
#   DRY_RUN=0 \
#   PUBLIC_NAME="Dumen Contributors" \
#   PUBLIC_EMAIL="dev@dumen.ai" \
#   bash scripts/prepare_public.sh                 # maskeleme uygula
#
# Sonra SİZ:
#   cd ../77-Dumen-public
#   git remote add origin https://github.com/<org>/dumen.git && git push -u origin master
#   # PyPI isteğe bağlı: python -m build && twine upload dist/*
# =============================================================================
set -euo pipefail

DRY_RUN="${DRY_RUN:-1}"
SRC="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
OUT="${OUT:-${SRC}-public}"
PUBLIC_NAME="${PUBLIC_NAME:-Dumen Contributors}"
PUBLIC_EMAIL="${PUBLIC_EMAIL:-dev@dumen.ai}"

echo "🧱 kaynak : $SRC"
echo "📦 hedef  : $OUT (varsa silinir)"
echo "🙈 kimlik : $PUBLIC_NAME <$PUBLIC_EMAIL>"
echo "🧪 DRY_RUN: $DRY_RUN (0 = maskeleme uygula)"

rm -rf "$OUT"
git clone --quiet "$SRC" "$OUT"
cd "$OUT"

echo "🔎 son-tarama: çalışan-ağaçta kişisel-izin/anahtar araması…"
HITS=""
HITS+="$(grep -rInE "(api[_-]?key|secret|token|passwd|password)[\"' ]*[:=][\"' ]*[A-Za-z0-9_./+-]{12,}" \
  --include='*.py' --include='*.md' --include='*.toml' --include='*.json' --include='*.yml' . 2>/dev/null \
  | grep -viE 'your[_-]|placeholder|example|sk-test|\{.*\}|<[a-z_]+>|api_key: Optional|api_key=api_key|Bearer \{' || true)"
HITS+="$(grep -rIn '/home/gokun' --include='*.py' --include='*.md' --include='*.json' --include='*.log' . 2>/dev/null || true)"
if [ -n "$HITS" ]; then
  echo "$HITS"
  echo "⚠️  yukarıdaki izleri DOĞRULAMADAN yayınlamayın."
else
  echo "✅ çalışan ağaç temiz (kişisel yol/anahtar izi yok)"
fi

if [ "$DRY_RUN" != "0" ]; then
  echo "🧪 kuru-koşum: $OUT incelendi — maskeleme UYGULANMADI."
  echo "   memnunsan:  DRY_RUN=0 bash scripts/prepare_public.sh"
  exit 0
fi

echo "🎭 tüm commit imzaları maskeleniyor…"
git-filter-repo --force \
  --name-callback  "return b'${PUBLIC_NAME}'" \
  --email-callback "return b'${PUBLIC_EMAIL}'"

echo "✅ maskelenmiş geçmişteki benzersiz imzalar:"
git log --format='%an <%ae>' | sort -u
echo "   commit sayısı: $(git rev-list --count HEAD)"
echo
echo "📤 PUSH KASITLI OLARAK BURADA DEĞİL (yayın kararı sizindir):"
echo "   cd $OUT"
echo "   git remote add origin https://github.com/<org>/<repo>.git"
echo "   git push -u origin <dal>"
