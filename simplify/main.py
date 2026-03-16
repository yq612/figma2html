"""CLI 入口：读取 Figma JSON，精简后写出。"""
import json
import sys

from simplify.nodes import simplify_node  # noqa: F401 — 重新导出，供 pipeline 使用


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 -m simplify.main input.json output.json", file=sys.stderr)
        sys.exit(1)
    inp_path, out_path = sys.argv[1], sys.argv[2]
    with open(inp_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    result = simplify_node(data)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
