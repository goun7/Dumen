// JCS oracle — RFC 8785 referans uygulaması (ECMAScript-native ground truth)
// Kullanım: node /tmp/jcs_oracle.js < vektörler.json
// Vektörler: [{"name": ..., "obj": {...}}]
// Çıktı: [{"name":..., "canonical": "..."}]

const crypto = require('crypto');
const readline = require('readline');

// RFC 8785 number canonicalization (Number.prototype.toString algoritması)
function esNumber(x) {
  if (typeof x !== 'number') throw new Error('not a number: ' + x);
  if (Number.isNaN(x)) throw new Error('NaN has no canonical form');
  if (!Number.isFinite(x)) throw new Error('Infinity has no canonical form');
  return String(x); // V8 String(number) == Number.prototype.toString
}

// UTF-16 code-unit comparison for keys
function utf16Compare(a, b) {
  const ua = Buffer.from(a, 'utf16le');
  const ub = Buffer.from(b, 'utf16le');
  const n = Math.min(ua.length, ub.length);
  for (let i = 0; i < n; i += 2) {
    const va = ua.readUInt16LE(i), vb = ub.readUInt16LE(i);
    if (va !== vb) return va - vb;
  }
  return ua.length - ub.length;
}

function serialize(value) {
  if (value === null) return 'null';
  const t = typeof value;
  if (t === 'string') return JSON.stringify(value);
  if (t === 'number') return esNumber(value);
  if (t === 'boolean') return String(value);
  if (Array.isArray(value)) {
    return '[' + value.map(serialize).join(',') + ']';
  }
  if (t === 'object') {
    const keys = Object.keys(value).sort(utf16Compare);
    return '{' + keys.map(k => JSON.stringify(k) + ':' + serialize(value[k])).join(',') + '}';
  }
  throw new Error('unsupported type: ' + t);
}

function canonicalize(obj) { return serialize(obj); }

function main() {
  const rl = readline.createInterface({ input: process.stdin });
  let buf = '';
  rl.on('line', l => buf += l);
  rl.on('close', () => {
    const vectors = JSON.parse(buf);
    const out = vectors.map(v => ({
      name: v.name,
      canonical: canonicalize(v.obj)
    }));
    console.log(JSON.stringify(out, null, 0));
  });
}
main();
