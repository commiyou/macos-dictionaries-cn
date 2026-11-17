# macOS 原生词典：制作、排错与成品分享

[![Release](https://img.shields.io/github/v/release/commiyou/macos-dictionaries-cn?label=release)](https://github.com/commiyou/macos-dictionaries-cn/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS-black.svg)]()

把第三方词库做成 macOS「词典.app」原生词典，支持**三指轻点 / 右键查询 / Spotlight**，并附上两本可直接安装的成品：

| 成品 | 规模 | 说明 |
|---|---|---|
| **英语词根词缀反查词典** | 67,521 词 | 输入任意单词，拆出它的前缀 / 词根 / 后缀 + 同根词 |
| **牛津柯林斯英中词典** | 770,611 词 | 英中双解，含 OXFORD 标记、柯林斯星级、考纲标签 |

> 全部离线、无账号、无常驻进程。

---

## 目录

- [一、先说最重要的坑](#一先说最重要的坑)
- [二、安装成品词典](#二安装成品词典)
- [三、macOS 词典的三种扩展方式](#三macos-词典的三种扩展方式)
- [四、从零构建一本 .dictionary](#四从零构建一本-dictionary)
- [五、查词浮窗（三指轻点）为什么只显示「更多」](#五查词浮窗三指轻点为什么只显示更多)
- [六、CSS 定制：宽度、字号、深色模式](#六css-定制宽度字号深色模式)
- [七、常见问题排查](#七常见问题排查)
- [八、数据来源与许可](#八数据来源与许可)

---

## 一、先说最重要的坑

如果你只勾选了第三方词典、把系统自带词典全部取消，**三指查词浮窗会只显示词头和一个「更多」链接，点开才能看到释义**。

这不是你的词典做错了，也不是 CSS 写错了。

**规则：至少保留一本 macOS 系统自带词典处于勾选状态。**

原因：查词浮窗的内容渲染依赖系统词典链路，只挂第三方词典时该链路拿不到内容。这是 macOS 的系统行为，与词典本身无关。

配置位置：**词典.app → 设置（`⌘,`）→ 勾选顺序**

```
① 你的第三方词典        ← 排最前，优先显示
② 至少一本系统词典      ← 例如「简体中文–英语」/「Apple Dictionary」
```

拖动列表可以调整顺序，靠前的词典先显示。

---

## 二、安装成品词典

### 2.1 下载

到本仓库的 **Releases** 页面下载：

| 文件 | 内容 | 体积 |
|---|---|---|
| [`EnglishWordRoots.dictionary.zip`](https://github.com/commiyou/macos-dictionaries-cn/releases/latest/download/EnglishWordRoots.dictionary.zip) | 词根词缀反查词典 | 13 MB |
| [`OxfordCollinsEnZh.dictionary.zip`](https://github.com/commiyou/macos-dictionaries-cn/releases/latest/download/OxfordCollinsEnZh.dictionary.zip) | 牛津柯林斯英中词典 | 52 MB |
| [`SHA256SUMS.txt`](https://github.com/commiyou/macos-dictionaries-cn/releases/latest/download/SHA256SUMS.txt) | 校验值 | — |

压缩包内是中文名的 `.dictionary` 文件夹。解压后整个文件夹放进 `~/Library/Dictionaries/`。

### 2.2 安装（三步）

1. 解压，得到 `xxx.dictionary` 文件夹（**注意是文件夹，不要只拷里面的 Contents**）
2. 整个文件夹放进：

   ```
   ~/Library/Dictionaries/
   ```

   这个目录可能不存在，新建即可。

   > 小技巧：访达里按 `⇧⌘G`，粘贴 `~/Library/Dictionaries` 直接跳转。

3. 打开「词典.app」，按 `⌘,` 打开设置，在列表里**勾选**新词典。
   同时在列表里**保留至少一本系统词典**（见[第一节](#一先说最重要的坑)）。

### 2.3 验证

在词典.app 里搜 `telephone`，应看到：

```
telephone
tele（词根：远；电信） ＋ phon（词根：声音）
n. 电话, 电话机 / v. 打电话
```

三指轻点任意英文单词，应直接在浮窗里看到拆解，无需点击「更多」。

### 2.4 卸载

1. 词典.app 设置里取消勾选
2. 删除 `~/Library/Dictionaries/xxx.dictionary`
3. 完全退出词典.app（`⌘Q`）后重开

---

## 三、macOS 词典的三种扩展方式

| 方式 | 做法 | 能装什么 | 难度 |
|---|---|---|---|
| **A. 直接放入词典目录** | 把 `.dictionary` 放进 `~/Library/Dictionaries/` | 任何已构建好的 Apple 词典 | ★ |
| **B. 自己构建** | 用 Dictionary Development Kit 把 XML 编译成 `.dictionary` | 自建、MDX 转换、任意词库 | ★★★ |
| **C. 第三方词典 App** | Easydict / GoldenDict / 欧路 | MDX/MDD 原生支持 | ★ |

**关键限制**：词典.app **不支持 `.mdx`（MDict）格式**。想用 MDX 词库，必须先转换（方式 B 或 C）。

### 目录与生效机制

| 路径 | 作用域 | 说明 |
|---|---|---|
| `~/Library/Dictionaries/` | 当前用户 | **推荐**，不需要管理员权限 |
| `/Library/Dictionaries/` | 全机所有用户 | 需要 sudo |
| `~/Library/Containers/com.apple.Dictionary/Data/Library/Dictionaries` | — | 这是指向 `~/Library/Dictionaries` 的软链接，不用单独处理 |

放入后需要：**完全退出词典.app（`⌘Q`）再打开**，设置里才会出现新词典。

---

## 四、从零构建一本 `.dictionary`

### 4.1 准备工具

需要 Apple 的 **Dictionary Development Kit**（随 Xcode 附加工具提供，也可用社区镜像）。

```bash
# 社区镜像（内容与官方一致）
git clone --depth 1 https://github.com/SebastianSzturo/Dictionary-Development-Kit.git devkit
```

目录说明：

```
devkit/
├── bin/build_dict.sh          # 构建入口
├── project_templates/         # 模板（Makefile / plist / css）
└── samples/                   # 官方示例 XML
```

### 4.2 词典源文件格式

一个 `.xml`，根节点是 `d:dictionary`，每个词条是 `d:entry`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<d:dictionary xmlns="http://www.w3.org/1999/xhtml"
              xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">

<d:entry id="telephone" d:title="telephone">
    <d:index d:value="telephone" d:title="telephone"/>
    <h1>telephone</h1>
    <p>tele（词根：远；电信） ＋ phon（词根：声音）<br/>n. 电话, 电话机</p>
</d:entry>

</d:dictionary>
```

要点：

- `d:entry/@id` **必须全局唯一**，重复会导致构建报 `Duplicate entry_id`
- `d:index/@d:value` 决定能被搜到哪些词；一个词条可以有多个 `d:index`（用于复数、变形、别名）
- 正文可以用 XHTML 标签（`p` `span` `div` `br` `b` `i` 等），由 CSS 控制外观

### 4.3 构建

```bash
export DICT_BUILD_TOOL_DIR="$PWD/devkit"

sh "$DICT_BUILD_TOOL_DIR/bin/build_dict.sh" \
   -v 10.11 \
   "我的词典" \
   我的词典.xml \
   样式.css \
   Info.plist
```

产物在 `objects/我的词典.dictionary`。

`-v 10.11` 会生成 `Contents/Resources/` 结构（现代格式），**建议始终加上**。

### 4.4 安装

```bash
ditto --noextattr --norsrc "objects/我的词典.dictionary" ~/Library/Dictionaries/"我的词典.dictionary"
touch ~/Library/Dictionaries
```

### 4.5 `Info.plist` 关键字段

```xml
<key>CFBundleIdentifier</key>        <string>local.dictionary.MyDict</string>
<key>CFBundleName</key>              <string>我的词典</string>
<key>CFBundleDisplayName</key>       <string>我的词典</string>
<key>DCSDictionaryCSS</key>          <string>DefaultStyle.css</string>
<key>DCSElementXPath</key>
<dict>
    <key>definitions</key>  <string>//p</string>
</dict>
```

| 字段 | 作用 |
|---|---|
| `CFBundleIdentifier` | 唯一标识，设置里记录的就是它 |
| `CFBundleName` / `CFBundleDisplayName` | 设置列表里显示的名字 |
| `DCSDictionaryCSS` | 指向包内样式文件名 |
| `DCSElementXPath` | 查词浮窗从哪个元素取内容 |
| `DCSDictionaryCopyright` | 版权说明（设置里可查） |

**不要**写 `DCSDictionaryXSL` 除非你确实放了这个文件——指向不存在的文件会让渲染走降级路径。

---

## 五、查词浮窗（三指轻点）为什么只显示「更多」

三种可能，按概率排序：

### 5.1 没有勾选任何系统词典 ← 最常见

见[第一节](#一先说最重要的坑)。系统词典必须至少勾一本。

### 5.2 词条太长，超出浮窗高度

浮窗高度固定，内容过高就折叠。参考基准：

| 词典 | 单条长度 |
|---|---|
| Apple Dictionary（系统） | 300–700 字符，**每条 1 个 `<p>`** |
| 本仓库词根词典 | 平均 255，最长 417 |

**做法**：把词条压短。最稳的是**每条只用 1 个 `<p>`**，用 `<br/>` 换行，把次要内容（完整释义、词形变化、同根词列表）限制条数。

### 5.3 CSS 需要在浮窗语境下单独收窄

浮窗渲染时，根元素带 `apple_client-panel` 类。可以只针对浮窗写规则：

```css
html.apple_client-panel h1 { font-size: 100% !important; margin: 0 0 0.15em 0 !important; }
html.apple_client-panel body { margin: 0 !important; line-height: 120% !important; }
html.apple_client-panel .secondary { display: none !important; }  /* 浮窗里隐藏次要内容 */
```

这是系统词典自己用的写法，可参考 `/System/Library/AssetsV2/.../Apple Dictionary.dictionary/Contents/Resources/AppleDictionary.css`。

> 注意：CSS 只影响**浮窗渲染**，不能弥补「没勾系统词典」的问题。

---

## 六、CSS 定制：宽度、字号、深色模式

### 6.1 基本结构

```css
body { font-family: "Helvetica Neue", "PingFang SC", sans-serif; font-size: 13px; }
h1   { font-size: 17px; border-bottom: 1px solid #ddd; }
p    { margin: 3px 0; line-height: 1.6; }
```

### 6.2 调整显示宽度

词典.app 内容区宽度由阅读栏设置决定；若想让内容不那么宽，给根容器限宽：

```css
body { max-width: 720px; }
```

浮窗里则写：

```css
html.apple_client-panel body { max-width: none; padding: 2px 6px; }
```

### 6.3 深色模式

```css
@media (prefers-color-scheme: dark) {
    body { background: #1e1e1e; color: #e8e8e8; }
    h1   { color: #f2f2f2; border-bottom-color: #444; }
    p    { color: #d8d8d8; }
}
```

或直接在 plist 里加：

```xml
<key>DCSDictionaryUseSystemAppearance</key><true/>
```

### 6.4 改完 CSS 要重启

CSS 在构建时被复制进包里。改包内的 `Contents/Resources/DefaultStyle.css` 后：

```bash
killall Dictionary
```

再打开词典.app。若没变化，清理缓存：

```bash
rm -rf ~/Library/Containers/com.apple.Dictionary/Data/Library/Caches/com.apple.DictionaryApp/*
```

---

## 七、常见问题排查

| 现象 | 原因 | 处理 |
|---|---|---|
| 设置里看不到新词典 | 没完全退出应用；目录不对 | `⌘Q` 退出后重开；确认是 `~/Library/Dictionaries/` 且放的是整个 `.dictionary` 文件夹 |
| 三指查词只有词头 + 「更多」 | 未勾选系统词典 / 词条太长 | 勾一本系统词典；压缩词条长度 |
| 搜不到某个词 | 缺 `d:index` | 补 `<d:index d:value="词"/>`，变形词也要单独加 index |
| 搜索变体（复数、过去式）搜不到 | 同上 | 给同一词条加多条 `d:index` |
| 构建报 `Duplicate entry_id` | `id` 重复 | id 生成时加去重序号 |
| 构建报 `PCDATA invalid Char` | XML 里混入控制字符 | 转义时过滤 `\x00-\x08` `\x0b` `\x0c` `\x0e-\x1f` |
| 构建报 `Opening and ending tag mismatch` | 内容未转义（如 `<法>`） | 所有文本走 XML 转义函数 |
| 词条内容里的 `\n` 没换行 | 源数据是字面量反斜杠n | `s.replace("\\n", "\n")` 后再按行拆 |
| 改了 CSS 没生效 | 缓存 | `killall Dictionary` + 清缓存 |
| 词典.app 打不开 `.dictionary`（提示 folder 格式） | 不支持双击导入 | 只能放进词典目录，不能靠「打开方式」 |

### 检查词典是否被系统认可

```bash
defaults read com.apple.DictionaryServices DCSActiveDictionaries
```

这里列出当前激活的词典。

---

## 八、数据来源与许可

### 成品词典的数据来源

| 数据 | 来源 | 许可 |
|---|---|---|
| 英中词条、音标、柯林斯/牛津标记、考纲 | [ECDICT](https://github.com/skywind3000/ECDICT) | MIT |
| 词根词缀拆分、词族、词根释义 | [Morpheme Lexicon](https://morphemelexicon.com/)（数据源自 MorphoLEX-en、Wiktionary/kaikki.org、WordNet 3.0、MorphyNet 等公开学术语料） | 见其站点说明 |

本项目仅做格式转换与排版，**不主张对上述数据的任何权利**。仅供个人学习研究使用，请勿商用。

### 本仓库代码

[MIT](LICENSE)

---

## 附：从源码重建

```bash
# 1. 取 ECDICT 数据
curl -L -o ecdict.csv https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv

# 2. 生成英中词典 XML
python3 build/scripts/pipeline_enzh.py enzh

# 3. 构建
export DICT_BUILD_TOOL_DIR="$PWD/devkit"
sh "$DICT_BUILD_TOOL_DIR/bin/build_dict.sh" -v 10.11 \
   "牛津柯林斯英中词典" out/enzh.xml build/css/enzh.css build/plists/enzh.plist
```

词根词典需要先从 Morpheme Lexicon 抓取 `data/w/<两字母>.json` 分片（共 676 个），再运行 `build_roots_compact.py`（紧凑版）或 `build_roots_full.py`（完整版）。
