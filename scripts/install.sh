#!/bin/bash
# install.sh —— 安装本仓库的成品词典到当前用户
# 用法: ./scripts/install.sh [词典压缩包路径...]
set -euo pipefail

DEST="$HOME/Library/Dictionaries"
mkdir -p "$DEST"

if [ $# -eq 0 ]; then
    echo "用法: $0 <词典.zip> [更多.zip ...]"
    echo
    echo "示例:"
    echo "  $0 ~/Downloads/英语词根词缀反查词典.dictionary.zip"
    exit 1
fi

for zip in "$@"; do
    [ -f "$zip" ] || { echo "跳过（不存在）: $zip"; continue; }
    echo "▶ 安装: $(basename "$zip")"

    tmp=$(mktemp -d)
    ditto -x -k "$zip" "$tmp"

    found=0
    for d in "$tmp"/*.dictionary; do
        [ -d "$d" ] || continue
        found=1
        name=$(basename "$d")
        target="$DEST/$name"
        if [ -d "$target" ]; then
            echo "  已存在，先备份为 $name.bak"
            rm -rf "$target.bak"
            mv "$target" "$target.bak"
        fi
        ditto --noextattr --norsrc "$d" "$target"
        echo "  ✅ $target"
    done

    [ $found -eq 1 ] || echo "  ⚠️ 压缩包里没找到 .dictionary"
    rm -rf "$tmp"
done

touch "$DEST"

echo
echo "完成。接下来："
echo "  1. 打开「词典」app（⌘Q 完全退出后再开，确保刷新）"
echo "  2. 按 ⌘, 打开设置"
echo "  3. 勾选刚装的词典"
echo "  4. ⚠️ 必须至少保留一本系统自带词典处于勾选状态"
echo "     否则三指查词只会显示「更多」"
