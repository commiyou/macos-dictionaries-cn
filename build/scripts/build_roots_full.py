#!/usr/bin/env python3
"""
词根词缀词典（反查型）构建器
数据源: morphemelexicon.com 的 data/w/<前缀两字母>.json 分片

核心特性: 输入任意单词 → 显示该词的构词拆分（前缀/词根/后缀）+ 同族词

用法:
    python3 build_roots2.py
"""
import json
import os
import re
import glob
import collections

ML = os.path.expanduser("~/dict-build/src/ml")
OUT = os.path.expanduser("~/dict-build/out/rootdict2.xml")

# XML 1.0 非法字符
_ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ud800-\udfff\ufffe\uffff]")


def esc(t):
    if t is None:
        return ""
    if not isinstance(t, str):
        t = str(t)
    t = _ILLEGAL.sub(" ", t)
    return (t.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


PART_CN = {
    "p": "前缀",   # prefix 由 affix 分片给出
    "r": "词根",
    "s": "后缀",
}


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
    """载入所有单词分片"""
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


def load_roots_zh():
    """载入词根/词缀的中文释义（index-lite.json）"""
    p = os.path.expanduser("~/dict-build/src/index-lite.json")
    if not os.path.exists(p):
        return {}, {}
    d = json.load(open(p, encoding="utf-8"))
    roots = {}
    for it in d.get("roots", []):
        # ["log","word; speech",217,"","combining",0.84,"表示“词语；语言；标记”之义"]
        if len(it) >= 7:
            roots[it[0].lower()] = {"en": it[1], "n": it[2],
                                     "origin": it[3], "zh": it[6]}
    affixes = {}
    for it in d.get("affixes", []):
        if len(it) >= 3:
            affixes[str(it[0]).lower()] = {"en": it[1] if len(it) > 1 else "",
                                            "zh": it[-1] if len(it) > 2 else ""}
    return roots, affixes


def split_parts(parts):
    """把 p 字段拆成 (类型, 词元, 说明) 列表"""
    out = []
    for item in parts or []:
        if not isinstance(item, (list, tuple)):
            continue
        if len(item) >= 2:
            kind, lemma = item[0], item[1]
        else:
            continue
        out.append((kind, str(lemma)))
    return out


def main():
    print("载入单词分片 ...")
    words = load_words()
    print(f"  单词总数: {len(words)}")

    print("载入词根词缀中文释义 ...")
    roots_zh, affixes_zh = load_roots_zh()
    print(f"  词根 {len(roots_zh)}  词缀 {len(affixes_zh)}")

    # 词根 -> 该词根下挂的单词（用于「同族词」）
    root_family = collections.defaultdict(list)
    for w, v in words.items():
        for kind, lemma in split_parts(v.get("p")):
            if kind == "r":
                root_family[lemma.lower()].append(w)

    used = set()
    n = 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<d:dictionary xmlns="http://www.w3.org/1999/xhtml" '
                'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')

        for w in sorted(words):
            v = words[w]
            parts = split_parts(v.get("p"))
            zh = (v.get("zh") or "").strip()
            ph = (v.get("ph") or "").strip()
            lem = (v.get("lem") or "").strip()
            defs = v.get("d") or []

            # 至少要有一个构词拆分或中文释义
            if not parts and not zh:
                continue

            eid = make_uid("m_", w, used)
            f.write(f'\t<d:entry id="{eid}" d:title="{esc(w)}">\n')
            f.write(f'\t\t<d:index d:value="{esc(w)}" d:title="{esc(w)}"/>\n')
            if lem and lem.lower() != w:
                # 变形词也能被搜到
                pass

            f.write(f'\t\t<h1>{esc(w)}</h1>\n')

            # ---- 构词拆分（核心）—— 首段纯文本，便于预览抽词 ----
            if parts:
                # 供 DCSElementXPath 抓取的一行纯文本
                plain = []
                for kind, lemma in parts:
                    info = roots_zh.get(lemma.lower(), {}) if kind == "r" else affixes_zh.get(lemma.lower(), {})
                    mean_zh = info.get("zh") or info.get("en") or ""
                    mark = {"r": "词根", "p": "前缀", "s": "后缀"}.get(kind, kind)
                    _m = mean_zh.rstrip('）) ').strip() if mean_zh else ''
                    plain.append(f"{lemma}（{mark}{'：' + _m if _m else ''}）")
                f.write(f'\t\t<div class="split-plain"><p>{esc(" + ".join(plain))}</p></div>\n')

                f.write('\t\t<div class="split">\n')
                rendered = []
                for kind, lemma in parts:
                    info = roots_zh.get(lemma.lower(), {}) if kind == "r" else affixes_zh.get(lemma.lower(), {})
                    mean_zh = info.get("zh") or info.get("en") or ""
                    mark = {"r": "词根", "p": "前缀", "s": "后缀"}.get(kind, kind)
                    rendered.append(
                        f'<span class="piece"><b>{esc(lemma)}</b>'
                        f'<i>{esc(mark)}</i>'
                        + (f'<em>{esc(mean_zh)}</em>' if mean_zh else '')
                        + '</span>'
                    )
                f.write('\t\t\t' + '<span class="plus">+</span>'.join(rendered) + '\n')
                f.write('\t\t</div>\n')

            # ---- 音标 + 词频 ----
            f.write('\t\t<div class="head">\n')
            if ph:
                f.write(f'\t\t\t<span class="phon">/{esc(ph)}/</span>\n')
            _fr = v.get("fr")
            if _fr:
                f.write(f'\t\t\t<span class="freq">词频 # {esc(_fr)}</span>\n')
            f.write('\t\t</div>\n')

            # ---- 中文释义 ----
            if zh:
                f.write(f'\t\t<div class="trans"><p>{esc(zh)}</p></div>\n')

            # ---- 英文释义 ----
            if defs:
                f.write('\t\t<div class="def">\n')
                for item in defs[:6]:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        pos, text = item[0], item[1]
                        f.write(f'\t\t\t<p><span class="pos">{esc(pos)}.</span> {esc(text)}</p>\n')
                f.write('\t\t</div>\n')

            # ---- 同族词（同词根）----
            fam = []
            for kind, lemma in parts:
                if kind == "r":
                    for other in root_family.get(lemma.lower(), []):
                        if other != w and other not in fam:
                            fam.append(other)
            if fam:
                if len(fam) > 40:
                    fam = fam[:40]
                f.write('\t\t<div class="family"><b>同根词</b>\n')
                for other in fam:
                    ov = words.get(other, {})
                    ozh = (ov.get("zh") or "").strip()[:40]
                    f.write(f'\t\t\t<span class="famitem"><b>{esc(other)}</b>'
                            + (f' <em>{esc(ozh)}</em>' if ozh else '')
                            + '</span>\n')
                f.write('\t\t</div>\n')

            f.write('\t</d:entry>\n')
            n += 1

        f.write('</d:dictionary>\n')

    size = os.path.getsize(OUT) / 1048576
    print(f"[词根词缀词典·反查版] {n} 条 -> {OUT} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
