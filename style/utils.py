"""通用辅助函数。"""


def _set(d, k, v, default=None):
    """仅当值非默认时才加入 style。"""
    if v is None:
        return
    if default is not None and v == default:
        return
    d[k] = v


def _normalize_num(v, precision=6):
    if abs(v) < 1e-9:
        return 0.0
    if abs(v - round(v)) < 1e-9:
        return int(round(v))
    return round(v, precision)
