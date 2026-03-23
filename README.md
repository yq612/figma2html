# figma2html

将 Figma 导出的 JSON 转换为可预览的单文件 HTML，用于验证设计稿还原度。

支持本地 CLI 和 [Vercel 在线预览](https://figma2html.vercel.app)。

## 目录结构

```
figma2html/
├── main.py                      # ⭐ 一键 Pipeline 入口（simplify → style → render）
│
├── api/
│   └── render.py                # Vercel Serverless Function（POST /api/render）
│
├── public/
│   ├── index.html               # Web 预览界面（粘贴 JSON → 实时渲染 → 下载 HTML）
│   └── figma.svg                # Figma logo
│
├── simplify/                    # 第一步：精简 Figma JSON，去除渲染无关字段
│   ├── utils.py                 # null 清理、字段裁剪、fills/strokes 精简
│   ├── nodes.py                 # 各类型字段白名单、处理器 + simplify_node()
│   └── main.py                  # CLI 入口
│
├── style/                       # 第二步：遍历节点树，为每个节点生成 CSS style
│   ├── utils.py                 # _set()、_normalize_num()
│   ├── transform.py             # 2x3 仿射矩阵：生成、组合、求逆、转 CSS
│   ├── layout.py                # 定位与 Flex 布局（_style_common、_apply_flex_child）
│   ├── effects.py               # 阴影与滤镜（box-shadow、backdrop-filter、filter）
│   ├── border.py                # 背景色、边框、圆角（_style_background_border）
│   ├── typography.py            # 字体权重解析与 TEXT 节点完整样式
│   ├── image.py                 # 图片节点识别（isImage/locked）与样式计算
│   ├── nodes.py                 # FRAME/GROUP/RECTANGLE/LINE 节点处理器
│   └── main.py                  # add_style()、minimize_node()、CLI 入口
│
├── render/                      # 第三步：将附带 style 的 JSON 渲染为 HTML
│   ├── css_utils.py             # CSS 值规范化、build_inline_style()
│   ├── text.py                  # TEXT 节点渲染（纯文本、segments、列表项）
│   ├── fonts.py                 # 字体名收集与 Google Fonts link 生成
│   ├── node.py                  # 节点递归渲染为 HTML 标签
│   └── builder.py               # build_html()、CLI 入口
│
├── __result__/                  # Pipeline 产物（自动创建）
│   ├── <timestamp>_simplified.json
│   ├── <timestamp>_styled.json
│   └── <timestamp>.html
│
├── __test__/                    # 测试样例（8 个页面）
│   ├── test_1.json ~ test_8.json
│
├── vercel.json                  # Vercel 部署配置
├── pyproject.toml               # Python 包配置（>=3.12）
└── requirements.txt             # 无第三方依赖
```

## 模块依赖

```
main.py
 ├── simplify/nodes.py  ←  simplify/utils.py
 ├── style/main.py      ←  style/nodes.py
 │                           ├── style/layout.py   ← style/transform.py ← style/utils.py
 │                           ├── style/border.py   ← style/effects.py
 │                           └── style/typography.py
 │                      ←  style/image.py
 │                           └── style/transform.py, style/layout.py
 └── render/builder.py  ←  render/node.py
                              ├── render/css_utils.py
                              └── render/text.py    ← render/css_utils.py
                         ←  render/fonts.py
```

所有包均为 Python 3 namespace package，无 `__init__.py`，使用绝对路径导入。

## 处理流程

```
Figma 原始 JSON
       │
       ▼  simplify_node()          去除 parent 引用、冗余字段，按节点类型裁剪白名单
精简后 JSON
       │
       ▼  add_style()              递归为每个节点挂载 CSS 键值对（style 字段）
       ▼  minimize_node()          再次裁剪，只保留渲染所需字段
带 style 的最小 JSON
       │
       ▼  build_html()             递归渲染为 HTML 标签，引入 Google Fonts
单文件 HTML
```

## 快速上手

### 在线预览

访问 [figma2html.vercel.app](https://figma2html.vercel.app)，在左侧粘贴 Figma JSON，点击「渲染」即可在右侧预览 HTML 效果，支持缩放（25%/50%/75%/100%）和下载。

### 本地预览

使用 [Vercel CLI](https://vercel.com/docs/cli) 在本地启动开发服务器，模拟线上环境：

```bash
# 安装 Vercel CLI（如未安装）
npm i -g vercel

# 启动本地开发服务器
vercel dev
```

访问 `http://localhost:3000`，体验与线上一致的预览界面。

### 本地 Pipeline

自动依序执行三步，产物写入 `__result__/`，文件名使用毫秒时间戳：

```bash
python3 main.py __test__/test_1.json
```

输出：
```
[1/3] simplify  →  __result__/1741234567890_simplified.json
[2/3] style     →  __result__/1741234567890_styled.json
[3/3] render    →  __result__/1741234567890.html

Done  →  __result__/1741234567890.html
```

### 分步执行

```bash
# 1. 精简 Figma JSON
python3 -m simplify.main input.json simplified.json

# 2. 生成带 style 的 JSON（--keep-all 保留全部原始字段，调试用）
python3 -m style.main simplified.json styled.json
python3 -m style.main simplified.json styled.json --keep-all

# 3. 渲染为 HTML
python3 -m render.builder styled.json output.html
```

## Vercel 部署

项目已适配 Vercel Serverless 架构：

- `public/` 下的静态文件直接托管
- `api/render.py` 作为 Serverless Function 处理 `POST /api/render` 请求
- 请求体为精简后的 Figma JSON（最大 10 MB），返回完整 HTML 字符串

```
客户端
 ├─ GET /           → public/index.html（Web 预览界面）
 └─ POST /api/render → api/render.py（style → minimize → render）
      请求: Figma JSON
      响应: HTML string (text/html)
```

## 节点类型支持

| Figma 类型 | HTML 标签 | 主要特性 |
|---|---|---|
| `FRAME` | `<div>` | Flex 布局（row/column/wrap）、clipsContent（overflow:hidden）、圆角、阴影 |
| `GROUP` | `<div>` | 绝对定位，GROUP 子节点坐标系 rebasing |
| `TEXT` | `<div>` / `<ul>` / `<ol>` | textSegments 分段（span）、列表样式、textAutoResize |
| `RECTANGLE` | `<div>` | 背景色、渐变、边框、圆角 |
| `LINE` | `<div>` | border-top / border-left，0°/90° 旋转自动切换方向 |
| 图片节点 | `<img>` | `isImage=true` 或 `locked=true` 均视为图片 |

## 依赖

仅使用 Python 标准库，无需安装第三方包。要求 **Python 3.12+**。
