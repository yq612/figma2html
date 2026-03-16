"""TEXT 节点内容渲染：纯文本、分段 span、列表项。"""
import html

from render.css_utils import build_inline_style


def _html_escape_and_br(text):
    """转义 <>&" 并将 \\n 替换为 <br>。"""
    if text is None:
        return ""
    s = str(text)
    s = html.escape(s)
    s = s.replace("\n", "<br>")
    return s


def _text_node_full_characters(node):
    """TEXT 节点完整纯文本：优先 characters，否则拼接 textSegments。"""
    if node.get("characters") is not None:
        return node.get("characters") or ""
    parts = []
    for seg in node.get("textSegments") or []:
        if isinstance(seg, dict):
            parts.append(seg.get("characters") or "")
    return "".join(parts)


def _seg_span_style(seg, node_fills):
    """
    从 textSegment 提取 inline style 字符串。
    当前处理：fills → color（取第一个 SOLID fill 的 rgba）。
    若 segment 无 fills 或 fills 为空，退回到 node 级 fills。
    """
    fills = seg.get("fills") or []
    if not fills:
        fills = node_fills or []
    parts = []
    for fill in fills:
        if isinstance(fill, dict) and fill.get("type") == "SOLID":
            rgba = fill.get("rgba")
            if rgba:
                parts.append(f"color:{rgba}")
            break
    return ";".join(parts)


def render_text_content(node):
    """
    处理 TEXT 节点的 characters / textSegments。
    有 textSegments 时用 span 包每段；否则用 node.characters；换行 → <br>。
    """
    segments = node.get("textSegments") or []
    if segments:
        node_fills = node.get("fills") or []
        out = []
        for seg in segments:
            if not isinstance(seg, dict):
                continue
            chars = seg.get("characters", "")
            span_style = _seg_span_style(seg, node_fills)
            span_attr = f' style="{span_style}"' if span_style else ""
            out.append(f"<span{span_attr}>{_html_escape_and_br(chars)}</span>")
        return "".join(out)
    chars = node.get("characters") or ""
    return _html_escape_and_br(chars)


def _render_line_with_segments(line_text, line_start, seg_map):
    """
    给定一行文本（已去掉 \\n）及其在全文中的起始偏移 line_start，
    根据 seg_map（[(seg_start, seg_end, style), ...]，已按 seg_start 排序）
    生成带颜色 span 的 HTML 字符串。
    """
    if not seg_map:
        return html.escape(line_text)

    line_end = line_start + len(line_text)
    parts = []   # [(style, text), ...]
    cursor = 0   # 在 line_text 内的游标

    for seg_start, seg_end, style in seg_map:
        # 转为行内坐标
        local_start = max(0, seg_start - line_start)
        local_end = min(len(line_text), seg_end - line_start)
        if local_start >= local_end:
            continue
        # 补齐空隙（正常情况下 segments 无缝衔接，以防万一）
        if local_start > cursor:
            parts.append(("", line_text[cursor:local_start]))
        parts.append((style, line_text[local_start:local_end]))
        cursor = local_end

    # 补齐尾部
    if cursor < len(line_text):
        parts.append(("", line_text[cursor:]))

    out = []
    for style, text in parts:
        escaped = html.escape(text)
        if style:
            out.append(f'<span style="{style}">{escaped}</span>')
        else:
            out.append(escaped)
    return "".join(out)


def render_text_content_as_list(node):
    """
    当 TEXT 为列表（hasListStyle + listType）时：
    按 \\n 拆分为 <li>，同时应用 textSegments 的颜色。
    segment 的 start/end 是在完整文本中的字符偏移，\\n 可能落在 segment 内部，
    因此必须按位置切割而非直接使用 segment.characters。
    """
    segments = node.get("textSegments") or []
    node_fills = node.get("fills") or []
    raw = _text_node_full_characters(node)
    lines = raw.split("\n")

    # 构建 seg_map，按 start 排序
    seg_map = []
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        style = _seg_span_style(seg, node_fills)
        seg_map.append((start, end, style))
    seg_map.sort(key=lambda x: x[0])

    # listSpacing：取第一个 segment 的值，作为相邻 li 之间的间距
    list_spacing = 0
    for seg in segments:
        if isinstance(seg, dict):
            list_spacing = seg.get("listSpacing") or 0
            break

    out = []
    line_start = 0
    for i, line in enumerate(lines):
        li_content = _render_line_with_segments(line, line_start, seg_map)
        is_last = (i == len(lines) - 1)
        li_style = ""
        if list_spacing and not is_last:
            li_style = f' style="margin-bottom:{round(list_spacing, 2)}px"'
        out.append(f"<li{li_style}>{li_content}</li>")
        line_start += len(line) + 1  # +1 for the \n

    return "".join(out)
