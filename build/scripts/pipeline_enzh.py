#!/usr/bin/env python3
"""
Apple Dictionary 构建流水线
把 ECDICT(英中) / Webster(英英) / WordRoot(词根词缀) 合成 Apple Dictionary XML。

用法:
    python3 pipeline.py all        # 构建全部
    python3 pipeline.py roots      # 只构建词根词缀词典
    python3 pipeline.py enzh       # 只构建英中词典
    python3 pipeline.py enen       # 只构建英英词典
"""
import csv
import html
import json
import os
import re
import sys
import collections

SRC = os.path.expanduser("~/dict-build/src")
OUT = os.path.expanduser("~/dict-build/out")
csv.field_size_limit(10 ** 9)


# ---------------------------------------------------------------- 工具函数
# XML 1.0 合法字符：允许 \t \n \r，以及 >= 0x20 的字符（排除代理区和 0xFFFE/0xFFFF）
_ILLEGAL = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ud800-\udfff\ufffe\uffff]"
)


def esc(t):
    """转义为 XML 文本，并清除 XML 1.0 非法控制字符"""
    if not t:
        return ""
    if not isinstance(t, str):
        t = str(t)
    t = _ILLEGAL.sub(" ", t)
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = t.replace('"', "&quot;")
    return t


def xid(word):
    """生成合法的 entry id"""
    s = re.sub(r"[^A-Za-z0-9_.-]", "_", word)
    if not s or s[0].isdigit():
        s = "w_" + s
    return s


def make_uid(prefix, key, used):
    """生成全局唯一的 entry id；重复时追加序号"""
    base = xid(prefix + key)
    if base not in used:
        used.add(base)
        return base
    i = 2
    while f"{base}_{i}" in used:
        i += 1
    uid = f"{base}_{i}"
    used.add(uid)
    return uid


def stars(n, total=5):
    """柯林斯星级"""
    try:
        n = int(n)
    except (ValueError, TypeError):
        return ""
    if n <= 0:
        return ""
    return "●" * n + "○" * (total - n)


# ---------------------------------------------------------------- 词根库
class RootBook:
    """词根词缀数据 + 反查索引 + 前后缀规则"""

    def __init__(self, path):
        self.roots = json.load(open(path, encoding="utf-8"))
        # 单词 -> [词根key]（来自 example 字段）
        self.index = collections.defaultdict(list)
        for key, val in self.roots.items():
            for ex in val.get("example", []):
                ex = ex.strip()
                if not ex:
                    continue
                self.index[ex.lower()].append(key)
                if " " in ex:
                    self.index[ex.split()[0].lower()].append(key)
            # 词根自身的拼写变体也建索引，例如 "cis, cid1, -cide"
            for variant in self._variants(key):
                self.index.setdefault("__root__" + variant, []).append(key)

    @staticmethod
    def _variants(key):
        """从 'cis, cid1, -cide' 拆出各个变体"""
        out = []
        for part in key.split(","):
            p = part.strip().strip("-").strip()
            p = re.sub(r"\d+$", "", p)  # cid1 -> cid
            if p and len(p) >= 2:
                out.append(p.lower())
        return out

    def lookup(self, word):
        """查一个单词涉及的词根"""
        w = word.lower().strip()
        hits = list(dict.fromkeys(self.index.get(w, [])))
        # 前缀/后缀自动识别
        for key, val in self.roots.items():
            cls = val.get("class", "")
            if cls in ("prefix",) or "suffix" in cls:
                for variant in self._variants(key):
                    if len(variant) < 2:
                        continue
                    if "suffix" in cls and w.endswith(variant) and len(w) > len(variant) + 2:
                        if key not in hits:
                            hits.append(key)
                    if cls == "prefix" and w.startswith(variant) and len(w) > len(variant) + 2:
                        if key not in hits:
                            hits.append(key)
        return hits


def emit_roots(rootbook, out_path):
    """词根词缀词典"""
    n = 0
    used = set()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<d:dictionary xmlns="http://www.w3.org/1999/xhtml" '
                'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')

        for key in sorted(rootbook.roots):
            val = rootbook.roots[key]
            meaning = val.get("meaning", "")
            cls = val.get("class", "")
            origin = val.get("origin", "")
            func = val.get("function", "")
            examples = val.get("example", [])
            syn = val.get("synonyms", "")
            ant = val.get("antonyms", "")

            eid = make_uid("root_", key, used)
            title = key

            f.write(f'\t<d:entry id="{eid}" d:title="{esc(title)}">\n')
            # 索引：词根本体 + 各变体
            f.write(f'\t\t<d:index d:value="{esc(key)}" d:title="{esc(title)}"/>\n')
            seen_idx = {key.strip().lower()}
            for v in RootBook._variants(key):
                if v in seen_idx:
                    continue
                seen_idx.add(v)
                f.write(f'\t\t<d:index d:value="{esc(v)}" d:title="{esc(title)}"/>\n')

            f.write(f'\t\t<h1>{esc(title)}</h1>\n')
            # 元信息
            f.write('\t\t<div class="meta">\n')
            if cls:
                f.write(f'\t\t\t<span class="tag">{esc(cls)}</span>\n')
            if origin:
                f.write(f'\t\t\t<span class="origin">来源: {esc(origin)}</span>\n')
            f.write('\t\t</div>\n')

            if meaning:
                f.write(f'\t\t<div class="meaning"><b>含义</b>　{esc(meaning)}</div>\n')
            if func:
                f.write(f'\t\t<div class="function"><b>构词功能</b>　{esc(func)}</div>\n')
            if syn:
                f.write(f'\t\t<div class="syn"><b>同义</b>　{esc(syn)}</div>\n')
            if ant:
                f.write(f'\t\t<div class="ant"><b>反义</b>　{esc(ant)}</div>\n')
            if examples:
                f.write('\t\t<div class="examples"><b>例词</b><ul>\n')
                for ex in examples:
                    f.write(f'\t\t\t<li>{esc(ex)}</li>\n')
                f.write('\t\t</ul></div>\n')
            f.write('\t</d:entry>\n')
            n += 1

        f.write('</d:dictionary>\n')
    return n


# ---------------------------------------------------------------- ECDICT
def load_ecdict(path):
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            w = (row.get("word") or "").strip()
            if w:
                rows[w.lower()] = row
    return rows


def emit_enzh(ecdict, rootbook, out_path, only_oxford=False):
    """英中双解词典（按牛津/柯林斯权威度标注）"""
    n = 0
    used = set()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<d:dictionary xmlns="http://www.w3.org/1999/xhtml" '
                'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')

        for w in sorted(ecdict):
            row = ecdict[w]
            trans = (row.get("translation") or "").strip()
            defin = (row.get("definition") or "").strip()
            phon = (row.get("phonetic") or "").strip()
            collins = (row.get("collins") or "").strip()
            oxford = (row.get("oxford") or "").strip()
            tag = (row.get("tag") or "").strip()

            if only_oxford and oxford not in ("1", "2"):
                continue
            if not trans and not defin:
                continue

            eid = make_uid("e_", w, used)
            f.write(f'\t<d:entry id="{eid}" d:title="{esc(w)}">\n')
            f.write(f'\t\t<d:index d:value="{esc(w)}" d:title="{esc(w)}"/>\n')

            f.write(f'\t\t<h1>{esc(w)}</h1>\n')
            # 音标 + 权威度
            f.write('\t\t<div class="head">\n')
            if phon:
                f.write(f'\t\t\t<span class="phon">/{esc(phon)}/</span>\n')
            if oxford in ("1", "2"):
                f.write('\t\t\t<span class="oxford">OXFORD</span>\n')
            if collins and collins != "0":
                f.write(f'\t\t\t<span class="collins">{stars(collins)}</span>\n')
            if tag:
                f.write(f'\t\t\t<span class="tag">{esc(tag)}</span>\n')
            f.write('\t\t</div>\n')

            # 中文释义
            if trans:
                f.write('\t\t<div class="trans">\n')
                for line in trans.replace("\\n", "\n").split("\n"):
                    line = line.strip()
                    if line:
                        f.write(f'\t\t\t<p>{esc(line)}</p>\n')
                f.write('\t\t</div>\n')

            # 英文释义
            if defin:
                f.write('\t\t<div class="def">\n')
                for line in defin.replace("\\n", "\n").split("\n"):
                    line = line.strip()
                    if line:
                        f.write(f'\t\t\t<p>{esc(line)}</p>\n')
                f.write('\t\t</div>\n')

            # 词根词缀（自动关联）
            hits = rootbook.lookup(w)
            if hits:
                f.write('\t\t<div class="roots"><b>词根词缀</b>\n')
                for k in hits[:8]:
                    v = rootbook.roots.get(k, {})
                    m = v.get("meaning", "")
                    f.write(f'\t\t\t<span class="rootitem">{esc(k)}'
                            f'<i>{esc(m)}</i></span>\n')
                f.write('\t\t</div>\n')

            f.write('\t</d:entry>\n')
            n += 1

        f.write('</d:dictionary>\n')
    return n


# ---------------------------------------------------------------- Webster
def emit_enen(webster, out_path):
    n = 0
    used = set()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<d:dictionary xmlns="http://www.w3.org/1999/xhtml" '
                'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')
        for w in sorted(webster):
            body = webster[w]
            if not body:
                continue
            eid = make_uid("w_", w, used)
            f.write(f'\t<d:entry id="{eid}" d:title="{esc(w)}">\n')
            f.write(f'\t\t<d:index d:value="{esc(w)}" d:title="{esc(w)}"/>\n')
            f.write(f'\t\t<h1>{esc(w)}</h1>\n')
            f.write('\t\t<div class="def">\n')
            for line in body.split("\n"):
                line = line.strip()
                if line:
                    f.write(f'\t\t\t<p>{esc(line)}</p>\n')
            f.write('\t\t</div>\n')
            f.write('\t</d:entry>\n')
            n += 1
        f.write('</d:dictionary>\n')
    return n


# ---------------------------------------------------------------- main
def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs(OUT, exist_ok=True)

    print("载入词根库 ...")
    rb = RootBook(os.path.join(SRC, "wordroot.txt"))
    print(f"  词根条目 {len(rb.roots)}，反查索引 {len(rb.index)}")

    if what in ("all", "roots"):
        p = os.path.join(OUT, "rootdict.xml")
        n = emit_roots(rb, p)
        print(f"[词根词缀词典] {n} 条 -> {p} ({os.path.getsize(p)/1048576:.1f} MB)")

    if what in ("all", "enzh", "enen"):
        print("载入 ECDICT ...")
        ecd = load_ecdict(os.path.join(SRC, "ecdict.csv"))
        print(f"  ECDICT {len(ecd)} 条")

    if what in ("all", "enzh"):
        p = os.path.join(OUT, "enzh.xml")
        n = emit_enzh(ecd, rb, p)
        print(f"[英中双解词典] {n} 条 -> {p} ({os.path.getsize(p)/1048576:.1f} MB)")

    if what in ("all", "enen"):
        print("载入 Webster ...")
        web = json.load(open(os.path.join(SRC, "websters.json"), encoding="utf-8"))
        p = os.path.join(OUT, "enen.xml")
        n = emit_enen(web, p)
        print(f"[英英词典] {n} 条 -> {p} ({os.path.getsize(p)/1048576:.1f} MB)")


if __name__ == "__main__":
    main()
