#!/usr/bin/env python3
"""
词根词缀反查词典 —— 紧凑版
目标：单条词条 ≤ 1 个 <p>，总长 ≤ 450 字符，保证系统查词浮窗不折叠。

结构：
  <h1>word</h1>
  <p>构词拆解<br/>中文释义<br/>同根词: a, b, c</p>
"""
import json
import os
import re
import glob
import collections

ML = os.path.expanduser("~/dict-build/src/ml")
OUT = os.path.expanduser("~/dict-build/out/rootdict3.xml")

_ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ud800-\udfff\ufffe\uffff]")

MAX_ENTRY = 450          # 单条总长上限
MAX_FAMILY = 8           # 同根词最多展示数
MAX_TRANS_CHARS = 60     # 中文释义截断


def esc(t):
    if t is None:
        return ""
    if not isinstance(t, str):
        t = str(t)
    t = _ILLEGAL.sub(" ", t)
    return (t.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def make_uid(prefix, key, used):
    s = re.sub(r"[^A-Za-z0-9_.-]", "_", prefix + key)
    if not s or s[0].isdigit():
        s = "w_" + s
    if s not in used:
        used.add(s)
        return s
    i = 2
    while f"{s}_{i}" in used:
        i += 1
    used.add(f"{s}_{i}")
    return f"{s}_{i}"


def load_words():
    words = {}
    for f in glob.glob(os.path.join(ML, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if isinstance(v, dict) and v.get("w"):
                words[k.lower()] = v
    return words


def load_root_zh():
    p = os.path.expanduser("~/dict-build/src/index-lite.json")
    if not os.path.exists(p):
        return {}, {}
    d = json.load(open(p, encoding="utf-8"))
    roots, affixes = {}, {}
    for it in d.get("roots", []):
        if len(it) >= 7:
            roots[str(it[0]).lower()] = it[6]
    for it in d.get("affixes", []):
        if len(it) >= 3:
            affixes[str(it[0]).lower()] = it[-1]
    return roots, affixes


def split_parts(parts):
    out = []
    for item in parts or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append((item[0], str(item[1])))
    return out


def trim(s, n):
    s = (s or "").strip()
    s = s.replace("\n", " ").replace("\\n", " ")
    s = re.sub(r"\s+", " ", s)
    if len(s) > n:
        s = s[:n].rstrip() + "…"
    return s


def main():
    print("载入词库 ...")
    words = load_words()
    print(f"  单词 {len(words)}")
    roots_zh, affixes_zh = load_root_zh()
    print(f"  词根释义 {len(roots_zh)}  词缀释义 {len(affixes_zh)}")

    # 同根词索引：词根 -> [单词]
    fam_index = collections.defaultdict(list)
    for w, v in words.items():
        for kind, lemma in split_parts(v.get("p")):
            if kind == "r":
                fam_index[lemma.lower()].append(w)

    used = set()
    n = 0
    skipped = 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<d:dictionary xmlns="http://www.w3.org/1999/xhtml" '
                'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')

        for w in sorted(words):
            v = words[w]
            parts = split_parts(v.get("p"))
            zh = trim(v.get("zh"), MAX_TRANS_CHARS)

            if not parts and not zh:
                skipped += 1
                continue

            # ---- 第一行：构词拆解 ----
            segs = []
            for kind, lemma in parts:
                mean = roots_zh.get(lemma.lower()) if kind == "r" else affixes_zh.get(lemma.lower())
                mean = trim(mean, 28).rstrip('）) ')
                mark = {"r": "词根", "p": "前缀", "s": "后缀"}.get(kind, kind)
                segs.append(f"{lemma}（{mark}{'：' + mean if mean else ''}）")
            split_line = " ＋ ".join(segs)

            # ---- 第二行：中文释义 ----
            lines = [split_line]
            if zh:
                lines.append(zh)

            # ---- 第三行：同根词（限流）----
            fam = []
            for kind, lemma in parts:
                if kind == "r":
                    for other in fam_index.get(lemma.lower(), []):
                        if other != w and other not in fam:
                            fam.append(other)
            if fam:
                fam = sorted(fam, key=lambda x: (len(x), x))[:MAX_FAMILY]
                lines.append("同根词: " + ", ".join(fam))

            body = "<br/>".join(esc(x) for x in lines if x)

            # 超长则逐步砍掉同根词
            if len(body) > MAX_ENTRY and len(lines) == 3:
                body = "<br/>".join(esc(x) for x in lines[:2])
            if len(body) > MAX_ENTRY:
                body = esc(split_line)

            eid = make_uid("m_", w, used)
            f.write(f'\t<d:entry id="{eid}" d:title="{esc(w)}">\n')
            f.write(f'\t\t<d:index d:value="{esc(w)}" d:title="{esc(w)}"/>\n')
            f.write(f'\t\t<h1>{esc(w)}</h1>\n')
            f.write(f'\t\t<p>{body}</p>\n')
            f.write('\t</d:entry>\n')
            n += 1

        f.write('</d:dictionary>\n')

    size = os.path.getsize(OUT) / 1048576
    print(f"[紧凑版词根词典] {n} 条（跳过 {skipped}）-> {OUT} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
