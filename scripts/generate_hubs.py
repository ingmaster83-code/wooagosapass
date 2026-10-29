"""
gosapass 허브 페이지 생성 — 등급(시리즈)·분야·분야×등급·합격률 순위·월별 시험일정
data/stats/*.json + docs/data/exams-compare.json → docs/series|field|rank|schedule/*.html

generate_pages.py(→ exams-compare.json) 실행 뒤에 돌린다. 규칙은 hubs.py 공유.
"""
import json
import statistics
from datetime import date
from pathlib import Path
from urllib.parse import quote, unquote

from jinja2 import Environment, FileSystemLoader

import hubs

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"
TEMPLATES = Path(__file__).parent / "templates"

EVENTS = [
    ("written_reg_start", "written_reg_end", "필기 원서접수"),
    ("written_exam_start", "written_exam_end", "필기시험"),
    ("written_pass", None, "필기 합격자 발표"),
    ("prac_reg_start", "prac_reg_end", "실기 원서접수"),
    ("prac_exam_start", "prac_exam_end", "실기시험"),
    ("prac_pass_start", "prac_pass_end", "최종 합격자 발표"),
]
TODAY = date.today()
YEAR = TODAY.year


def md(s):  # 2026-11-02 → 11월 2일
    return "%d월 %d일" % (int(s[5:7]), int(s[8:10]))


def period(a, b):
    return md(a) if (not b or b == a) else "%s ~ %s" % (md(a), md(b))


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


items = load(DOCS / "data" / "exams-compare.json")["items"]
# 개별 일정이 없는 종목은 정기시험 그룹 일정으로 대체 (generate_pages.py 와 같은 규칙)
GROUP_SCHEDULE = {}
for s_ in load(DOCS / "data" / "schedules.json").get("items", []):
    GROUP_SCHEDULE.setdefault(s_["name"], []).append(s_)
QUAL_GROUP = {"기사": "기사/산업기사", "산업기사": "기사/산업기사", "기술사": "기술사", "기능장": "기능장", "기능사": "기능사"}
for it in items:
    it["grade"] = hubs.grade_of(it["name"], it.get("series"))
    it["fld"] = hubs.field_of(it.get("field"))
    st = DATA / "stats" / ("%s.json" % it["jmcd"])
    own = load(st).get("schedule", []) if st.exists() else []
    it["schedule"] = own or GROUP_SCHEDULE.get(QUAL_GROUP.get(it.get("series") or "", ""), [])

by_series, by_field, by_fg, valid = hubs.build_index(items)
_ms = sorted({v[:7] for it in items for r in it["schedule"] for a, b, _ in EVENTS for v in (r.get(a),) if v})
_cur = "%d-%02d" % (TODAY.year, TODAY.month)
EXTRA_LINKS = [("%d년 %d월 시험일정" % (int(m[:4]), int(m[5:])), hubs.month_url(m)) for m in _ms if m >= _cur][:2] + [("합격률 순위", hubs.rank_url("기사")), ("쉬운 자격증 TOP", "/rank/easy.html")]


def next_event(it):
    best = None
    for r in it["schedule"]:
        for a, b, label in EVENTS:
            v = r.get(a)
            if v and v >= TODAY.isoformat():
                if best is None or v < best[0]:
                    best = (v, label)
    return "%s %s" % (md(best[0]), best[1]) if best else "-"


def fee_txt(it):
    try:
        return "{:,}원".format(int(it["fee_written"]))
    except Exception:
        return "-"


def row(it):
    return {"name": it["name"], "url": quote(it["url"]), "field": it["fld"],
            "wr": ("%s%%" % it["written_rate"]) if it.get("written_rate") is not None else "-",
            "pr": ("%s%%" % it["practical_rate"]) if it.get("practical_rate") is not None else "-",
            "app": "{:,}명".format(it["recent_applicants"]) if it.get("recent_applicants") else "-",
            "fee": fee_txt(it), "next": next_event(it)}


def with_rate(xs, key="written_rate", min_app=30):
    return [x for x in xs if x.get(key) is not None and (x.get("recent_applicants") or 0) >= min_app]


def stat_line(xs):
    rs = with_rate(xs)
    if not rs:
        return ""
    hi = max(rs, key=lambda x: x["written_rate"]); lo = min(rs, key=lambda x: x["written_rate"])
    avg = statistics.mean(x["written_rate"] for x in rs)
    return "필기 합격률은 평균 %.1f%%이며, 가장 높은 곳은 %s(%s%%), 가장 낮은 곳은 %s(%s%%)입니다." % (avg, hi["name"], hi["written_rate"], lo["name"], lo["written_rate"])


def fee_line(xs):
    fs = []
    for x in xs:
        try: fs.append(int(x["fee_written"]))
        except Exception: pass
    if not fs:
        return ""
    return "필기 응시 수수료는 %s ~ %s입니다." % ("{:,}원".format(min(fs)), "{:,}원".format(max(fs)))


env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)
tmpl = env.get_template("hub.html.j2")
WRITTEN = []


def faq_ld(faq):
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                       "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
                      ensure_ascii=False).replace("</", "<\\/")


def write(path, title, description, h1, lead, crumbs, sections, faq=None):
    out = DOCS / unquote(path).lstrip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tmpl.render(title=title, description=description[:155], path=path, h1=h1, lead=lead, crumbs=crumbs,
                               sections=sections, faq=faq, faq_ld=faq_ld(faq) if faq else "", updated=TODAY.isoformat(), year=YEAR, extra_links=EXTRA_LINKS), encoding="utf-8")
    WRITTEN.append(path)


def exams_sec(title, xs, rank=False, sort=None, limit=None):
    xs = sorted(xs, key=sort) if sort else xs
    if limit: xs = xs[:limit]
    return {"kind": "exams", "title": title, "rows": [row(x) for x in xs], "rank": rank}


def links_sec(title, pairs):
    return {"kind": "links", "title": title, "rows": pairs}


by_pop = lambda x: -(x.get("recent_applicants") or 0)
by_rate_desc = lambda x: (-(x.get("written_rate") if x.get("written_rate") is not None else -1))

# ── 등급(시리즈) 허브 ─────────────────────────────────────────────
for g, xs in by_series.items():
    n = len(xs); f_cnt = len({x["fld"] for x in xs})
    lead = "%s 자격증은 국가자격 %d종이 있고 %d개 직무분야에 걸쳐 있습니다. %s %s" % (g, n, f_cnt, stat_line(xs), fee_line(xs))
    chips = [("%s 분야 %s (%d종)" % (f, g, len(v)), hubs.field_grade_url(f, g)) for (f, gg), v in sorted(by_fg.items(), key=lambda kv: -len(kv[1])) if gg == g]
    secs = [exams_sec("%s 자격증 전체 (응시자 많은 순)" % g, xs, sort=by_pop)]
    if chips: secs.append(links_sec("분야별 %s" % g, chips))
    rk = [("%s 합격률 순위" % g, hubs.rank_url(g))] if g in hubs.GRADE_SLUG else []
    if rk: secs.append(links_sec("함께 보기", rk))
    faq = [("%s 자격증은 몇 종이 있나요?" % g, "한국산업인력공단 기준 %s 종목은 %d종입니다." % (g, n)),
           ("%s 중 합격률이 가장 높은 자격증은?" % g, stat_line(xs) or "최근 연도 합격률 데이터가 있는 종목이 부족합니다.")]
    write(hubs.series_url(g), "%s 자격증 종류·시험일정 %d — %d종 합격률·수수료" % (g, YEAR, n), lead, "%s 자격증 종류·시험일정 %d" % (g, YEAR), lead,
          [("자격증 목록", "/list.html"), (g, None)], secs, faq)

# ── 분야 허브 ────────────────────────────────────────────────────
for f, xs in by_field.items():
    n = len(xs); gs = {}
    for x in xs: gs.setdefault(x["grade"], []).append(x)
    lead = "%s 분야 국가자격은 %d종입니다. %s %s" % (f, n, stat_line(xs), fee_line(xs))
    secs = []
    for g in hubs.MAIN_GRADES + sorted(k for k in gs if k not in hubs.MAIN_GRADES):
        if g in gs:
            secs.append(exams_sec("%s %s (%d종)" % (f, g, len(gs[g])), gs[g], sort=by_pop))
    chips = [("%s %s" % (f, g), hubs.field_grade_url(f, g)) for g in hubs.MAIN_GRADES if (f, g) in by_fg]
    if chips: secs.append(links_sec("등급별로 보기", chips))
    faq = [("%s 분야에는 어떤 자격증이 있나요?" % f, "%s 분야 국가자격은 %s 등 %d종이 있습니다." % (f, ", ".join(x["name"] for x in sorted(xs, key=by_pop)[:5]), n))]
    write(hubs.field_url(f), "%s 분야 자격증 시험일정 %d — %d종 합격률 비교" % (f, YEAR, n), lead, "%s 분야 자격증 시험일정 %d" % (f, YEAR), lead,
          [("자격증 목록", "/list.html"), (f, None)], secs, faq)

# ── 분야 × 등급 ──────────────────────────────────────────────────
for (f, g), xs in by_fg.items():
    n = len(xs)
    lead = "%s 분야 %s는 %d종입니다. %s %s" % (f, g, n, stat_line(xs), fee_line(xs))
    secs = [exams_sec("%s %s 시험일정·합격률" % (f, g), xs, sort=by_pop)]
    rel = [("%s 분야 자격증 전체" % f, hubs.field_url(f)), ("%s 자격증 전체" % g, hubs.series_url(g))]
    rel += [("%s %s" % (f, gg), hubs.field_grade_url(f, gg)) for gg in hubs.MAIN_GRADES if gg != g and (f, gg) in by_fg]
    secs.append(links_sec("함께 보기", [(a, b) for a, b in rel if b in valid]))
    faq = [("%s %s에는 어떤 자격증이 있나요?" % (f, g), "%s 등 %d종이 있습니다." % (", ".join(x["name"] for x in sorted(xs, key=by_pop)[:5]), n)),
           ("%s %s 중 합격률이 높은 자격증은?" % (f, g), stat_line(xs) or "합격률 데이터가 있는 종목이 부족합니다.")]
    write(hubs.field_grade_url(f, g), "%s %s 시험일정 %d — %d종 합격률·접수일" % (f, g, YEAR, n), lead, "%s %s 시험일정·합격률 (%d)" % (f, g, YEAR), lead,
          [("자격증 목록", "/list.html"), (f, hubs.field_url(f)), (g, None)], secs, faq)

# ── 합격률 순위 (등급별) ─────────────────────────────────────────
for g in hubs.MAIN_GRADES:
    if g not in by_series: continue
    xs = by_series[g]; rs = sorted(with_rate(xs), key=by_rate_desc)
    if not rs: continue
    yr = max((x.get("recent_year") or "0") for x in rs)
    lead = "%s %d종 중 응시자 30명 이상 %d종의 최근 연도(%s년) 필기 합격률 순위입니다. %s" % (g, len(xs), len(rs), yr, stat_line(xs))
    secs = [exams_sec("%s 필기 합격률 순위 (높은 순)" % g, rs, rank=True), exams_sec("%s 응시자 많은 순 TOP 15" % g, xs, sort=by_pop, limit=15),
            links_sec("함께 보기", [("%s 자격증 전체" % g, hubs.series_url(g)), ("쉬운 자격증 TOP", "/rank/easy.html"), ("어려운 자격증 TOP", "/rank/hard.html"), ("응시자 많은 자격증", "/rank/popular.html")])]
    faq = [("%s 중 합격률이 가장 높은 자격증은?" % g, "%s(필기 %s%%)입니다." % (rs[0]["name"], rs[0]["written_rate"])),
           ("%s 중 합격률이 가장 낮은 자격증은?" % g, "%s(필기 %s%%)입니다." % (rs[-1]["name"], rs[-1]["written_rate"]))]
    write(hubs.rank_url(g), "%s 합격률 순위 %d — 쉬운 %s·어려운 %s" % (g, YEAR, g, g), lead, "%s 합격률 순위 %d" % (g, YEAR), lead,
          [("자격증 목록", "/list.html"), ("%s 합격률 순위" % g, None)], secs, faq)

# ── 전체 순위 3종 ────────────────────────────────────────────────
big = [x for x in items if (x.get("recent_applicants") or 0) >= 200 and x.get("written_rate") is not None]
easy = sorted(big, key=by_rate_desc)[:50]; hard = sorted(big, key=lambda x: x["written_rate"])[:50]
nav = [("등급별 합격률 순위", hubs.rank_url("기사")), ("쉬운 자격증", "/rank/easy.html"), ("어려운 자격증", "/rank/hard.html"), ("응시자 많은 자격증", "/rank/popular.html")]
write("/rank/easy.html", "합격률 높은 쉬운 자격증 TOP 50 %d — 필기 합격률 순위" % YEAR, "응시자 200명 이상 국가자격 중 최근 연도 필기 합격률이 높은 쉬운 자격증 TOP 50.", "합격률 높은 쉬운 자격증 TOP 50 (%d)" % YEAR,
      "응시자 200명 이상 국가자격 %d종 중 필기 합격률이 가장 높은 50종입니다. 1위는 %s(%s%%)입니다." % (len(big), easy[0]["name"], easy[0]["written_rate"]),
      [("자격증 목록", "/list.html"), ("쉬운 자격증", None)], [exams_sec("필기 합격률 높은 순", easy, rank=True), links_sec("함께 보기", nav)])
write("/rank/hard.html", "합격률 낮은 어려운 자격증 TOP 50 %d — 필기 합격률 순위" % YEAR, "응시자 200명 이상 국가자격 중 최근 연도 필기 합격률이 낮은 어려운 자격증 TOP 50.", "합격률 낮은 어려운 자격증 TOP 50 (%d)" % YEAR,
      "응시자 200명 이상 국가자격 %d종 중 필기 합격률이 가장 낮은 50종입니다. 가장 어려운 곳은 %s(%s%%)입니다." % (len(big), hard[0]["name"], hard[0]["written_rate"]),
      [("자격증 목록", "/list.html"), ("어려운 자격증", None)], [exams_sec("필기 합격률 낮은 순", hard, rank=True), links_sec("함께 보기", nav)])
pop = sorted([x for x in items if x.get("recent_applicants")], key=by_pop)[:50]
write("/rank/popular.html", "응시자 많은 인기 자격증 TOP 50 %d" % YEAR, "최근 연도 필기 응시자 수가 많은 국가자격 TOP 50. 합격률·수수료·다음 일정.", "응시자 많은 인기 자격증 TOP 50 (%d)" % YEAR,
      "최근 연도 필기 응시자가 가장 많은 국가자격 50종입니다. 1위는 %s(%s)입니다." % (pop[0]["name"], "{:,}명".format(pop[0]["recent_applicants"])),
      [("자격증 목록", "/list.html"), ("인기 자격증", None)], [exams_sec("응시자 많은 순", pop, rank=True), links_sec("함께 보기", nav)])

# ── 월별 시험일정 ────────────────────────────────────────────────
months = sorted({v[:7] for it in items for r in it["schedule"] for a, b, _ in EVENTS for v in (r.get(a),) if v})
months = [m for m in months if m.startswith(str(YEAR)) or m > "%d-01" % YEAR]
for ym in months:
    y, m = int(ym[:4]), int(ym[5:7])
    secs = []; total_exam = set(); cnt = {}
    for a, b, label in EVENTS:
        groups = {}
        for it in items:
            for r in it["schedule"]:
                v = r.get(a)
                if v and v[:7] == ym:
                    groups.setdefault((v, r.get(b) if b else ""), []).append(it)
        rows = []
        for (s, e), xs in sorted(groups.items()):
            xs = sorted({x["name"]: x for x in xs}.values(), key=by_pop)
            for x in xs: total_exam.add(x["name"])
            cnt[label] = cnt.get(label, 0) + len(xs)
            rows.append({"label": label, "period": period(s, e), "exams": [(x["name"], quote(x["url"])) for x in xs[:14]], "more": max(0, len(xs) - 14)})
        if rows:
            secs.append({"kind": "events", "title": "%s (%d건)" % (label, sum(len(r["exams"]) + r["more"] for r in rows)), "rows": rows})
    if not secs: continue
    nxt = [("%d년 %d월 자격증 시험일정" % (int(p[:4]), int(p[5:])), hubs.month_url(p)) for p in months if p != ym]
    secs.append(links_sec("다른 달 일정", nxt))
    lead = "%d년 %d월에 일정이 있는 국가자격은 %d종입니다. %s" % (y, m, len(total_exam), " ".join("%s %d건" % (k, v) for k, v in cnt.items()) + ".")
    faq = [("%d월 자격증 시험은 언제인가요?" % m, "%s 항목별 날짜는 위 표에서 확인하세요." % lead),
           ("%d월 원서접수 중인 자격증은?" % m, "위 표의 '필기 원서접수'·'실기 원서접수' 항목이 %d월 접수 일정입니다. 접수는 큐넷(Q-Net)에서 합니다." % m)]
    write(hubs.month_url(ym), "%d년 %d월 자격증 시험일정 — 원서접수·필기·실기·합격발표" % (y, m), lead, "%d년 %d월 자격증 시험일정" % (y, m), lead,
          [("시험 캘린더", "/calendar.html"), ("%d년 %d월" % (y, m), None)], secs, faq)

(DATA / "hub-paths.json").write_text(json.dumps(WRITTEN, ensure_ascii=False), encoding="utf-8")
print("허브 페이지 %d개 생성: series %d / field %d / field-grade %d / rank %d / month %d" % (
    len(WRITTEN), len(by_series), len(by_field), len(by_fg), sum(1 for p in WRITTEN if p.startswith("/rank/")), sum(1 for p in WRITTEN if p.startswith("/schedule/"))))
