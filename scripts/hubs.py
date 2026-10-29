"""
허브 페이지 공통 규칙 (generate_pages.py 의 상세 페이지 링크 + generate_hubs.py 가 공유)
  /series/{등급}.html          예) /series/기사.html
  /field/{분야}.html           예) /field/건설.html
  /field/{분야}-{등급}.html    예) /field/건설-기사.html
  /rank/{등급}-pass-rate.html  예) /rank/gisa-pass-rate.html
  /schedule/{YYYY-MM}.html     예) /schedule/2026-11.html
"""
from urllib.parse import quote

MAIN_GRADES = ["기술사", "기능장", "기사", "산업기사", "기능사"]
GRADE_SLUG = {"기술사": "gisulsa", "기능장": "gineungjang", "기사": "gisa", "산업기사": "sanupgisa", "기능사": "gineungsa"}
MIN_SERIES = 5   # 등급(시리즈) 허브 최소 종목 수
MIN_FIELD = 3    # 분야 허브·분야×등급 허브 최소 종목 수


def grade_of(name, series):
    for g in ["기술사", "기능장", "산업기사", "기능사", "기사"]:
        if name.endswith(g):
            return g
    return series or "기타"


def field_of(field):
    f = (field or "").strip()
    return f if f else "기타"


def safe(s):
    return s.replace("/", "-").replace("\\", "-").replace(":", "-")


def series_url(g): return "/series/%s.html" % quote(safe(g))
def field_url(f): return "/field/%s.html" % quote(safe(field_of(f)))
def field_grade_url(f, g): return "/field/%s-%s.html" % (quote(safe(field_of(f))), quote(safe(g)))
def rank_url(g): return "/rank/%s-pass-rate.html" % GRADE_SLUG[g]
def month_url(ym): return "/schedule/%s.html" % ym


def hub_links_for(exam_name, series, field, valid):
    """valid: set of 생성된 URL 경로. 이 종목 상세 페이지에서 걸 허브 링크 목록 [(라벨, url)]"""
    g = grade_of(exam_name, series); f = field_of(field); out = []
    for label, url in [
        ("%s 분야 %s 전체" % (f, g), field_grade_url(f, g)),
        ("%s 분야 자격증 전체" % f, field_url(f)),
        ("%s 자격증 종류·시험일정" % g, series_url(g)),
    ] + ([("%s 합격률 순위" % g, rank_url(g))] if g in GRADE_SLUG else []):
        if url in valid:
            out.append((label, url))
    return out


def build_index(items):
    """items: [{name, series, field}] → (series 그룹, 분야 그룹, 분야×등급 그룹, valid URL 집합)"""
    by_series, by_field, by_fg = {}, {}, {}
    for it in items:
        g = grade_of(it["name"], it.get("series")); f = field_of(it.get("field"))
        by_series.setdefault(g, []).append(it)
        by_field.setdefault(f, []).append(it)
        if g in MAIN_GRADES:
            by_fg.setdefault((f, g), []).append(it)
    by_series = {g: v for g, v in by_series.items() if len(v) >= MIN_SERIES}
    by_field = {f: v for f, v in by_field.items() if len(v) >= MIN_FIELD}
    by_fg = {k: v for k, v in by_fg.items() if len(v) >= MIN_FIELD}
    valid = {series_url(g) for g in by_series} | {field_url(f) for f in by_field} | {field_grade_url(f, g) for f, g in by_fg}
    valid |= {rank_url(g) for g in MAIN_GRADES if g in by_series}
    return by_series, by_field, by_fg, valid
