#!/usr/bin/env python3
"""สร้างโปสเตอร์ infographic หลักสูตรประปาสัญจร (หมวดที่ 2) จาก data.json
ใช้งาน:
  python3 build.py                  -> สร้าง html/*.html และ output/*.png ทั้ง 5 ภาพ
  python3 build.py --no-png         -> สร้างเฉพาะ html/*.html (สำหรับ Live Preview)
  python3 build.py --only 01_Q1     -> สร้างเฉพาะภาพที่ระบุ
"""
import json, math, os, shutil, subprocess, sys
from provinces import TH2EN

ROOT = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(ROOT, *p)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ARTIFACT_DIR = "/Users/ipondjong/.gemini/antigravity/brain/22210a26-7ac1-4cd7-b4d9-d1a210ad2cc8"
W, H = 1080, 1350

GEO = json.load(open(A("assets", "thailand.json"), encoding="utf8"))

M_FULL = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
          "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
M_ABBR = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
QUARTERS = {1: (10, 11, 12), 2: (1, 2, 3), 3: (4, 5, 6), 4: (7, 8, 9)}


def quarter_of(m):
    return next(q for q, ms in QUARTERS.items() if int(m) in ms)


def fmt_money(n):
    return f"{int(n):,}"


def yy(y):
    return str(y)[-2:]


# ---------------------------------------------------------------- map geometry
def rings_of(feat):
    g = feat["geometry"]
    return g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]


ALL_LON = [p[0] for f in GEO["features"] for poly in rings_of(f) for r in poly for p in r]
ALL_LAT = [p[1] for f in GEO["features"] for poly in rings_of(f) for r in poly for p in r]
LON0, LON1, LAT0, LAT1 = min(ALL_LON), max(ALL_LON), min(ALL_LAT), max(ALL_LAT)
KX = math.cos(math.radians(13))


class Proj:
    def __init__(self, w, h, pad=6):
        gw, gh = (LON1 - LON0) * KX, (LAT1 - LAT0)
        self.s = min((w - 2 * pad) / gw, (h - 2 * pad) / gh)
        self.ox = (w - gw * self.s) / 2
        self.oy = (h - gh * self.s) / 2
        self.w, self.h = w, h

    def __call__(self, lon, lat):
        return self.ox + (lon - LON0) * KX * self.s, self.oy + (LAT1 - lat) * self.s


def ring_path(ring, P):
    out, last = [], None
    for lon, lat in ring:
        x, y = P(lon, lat)
        if last and abs(x - last[0]) < 0.9 and abs(y - last[1]) < 0.9:
            continue
        out.append((x, y))
        last = (x, y)
    if len(out) < 3:
        return ""
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in out) + "Z"


def centroid(feat):
    best = max((poly[0] for poly in rings_of(feat)), key=len)
    a = cx = cy = 0
    for (x0, y0), (x1, y1) in zip(best, best[1:] + best[:1]):
        cr = x0 * y1 - x1 * y0
        a += cr
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    a *= 0.5
    return cx / (6 * a), cy / (6 * a)


FEAT = {f["properties"]["name"]: f for f in GEO["features"]}
CENT = {k: centroid(v) for k, v in FEAT.items()}


def map_html(w, h, sessions, faded=(), show_labels=True, label_mode="full", pin=30):
    """sessions: sessions to highlight with pins; faded: other sessions to show as small dots"""
    P = Proj(w, h)
    hi = {}
    for s in sessions:
        hi.setdefault(s["en"], s["cat"]["color"])
    paths = []
    for name, f in FEAT.items():
        d = "".join(ring_path(r, P) for poly in rings_of(f) for r in poly)
        if name in hi:
            paths.append(f'<path d="{d}" fill="{hi[name]}" fill-opacity=".9" stroke="#fff" stroke-width="1.4"/>')
        else:
            paths.append(f'<path d="{d}" fill="#ffffff" fill-opacity=".92" stroke="#8cc8ee" stroke-width=".8"/>')
    paths.sort(key=lambda p: 'fill-opacity=".9"' in p)
    svg = (f'<svg class="map-svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
           f'<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#3a8fd0" flood-opacity=".35"/></filter></defs>'
           f'<g filter="url(#sh)">{"".join(paths)}</g></svg>')
    els = []
    active_en = {s["en"] for s in sessions}
    for s in faded:
        if s["en"] in active_en:
            continue
        x, y = P(*CENT[s["en"]])
        els.append(f'<div class="dot" style="left:{x:.0f}px;top:{y:.0f}px"></div>')
    groups = {}
    for s in sessions:
        groups.setdefault(s["en"], []).append(s)
    for en, ss in groups.items():
        x, y = P(*CENT[en])
        s0 = ss[0]
        lbl = s0.get("label", "")
        side = lbl if lbl in ("left", "right", "top", "bottom") else ("left" if x > w * 0.54 else "right")
        col = s0["cat"]["color"]
        pin_txt = str(ss[0]["c"]["no"]) if len(ss) == 1 else f'{len(ss)}'
        els.append(
            f'<div class="pin" style="left:{x:.0f}px;top:{y:.0f}px;--pc:{col};--ps:{pin}px">'
            f'<svg viewBox="-20 -52 40 54" width="{pin}" height="{pin*1.35:.0f}"><path d="M0,0 L-13.4,-24.6 A19 19 0 1 1 13.4,-24.6 Z" fill="{col}" stroke="#fff" stroke-width="3.2"/></svg>'
            f'<b>{pin_txt}</b></div>')
        if show_labels:
            if label_mode == "full":
                sub = " / ".join(
                    f'{"#" + str(s["c"]["no"]) + " " if len(ss) > 1 else ""}{M_ABBR[s["month"]]} {yy(s["year"])}'
                    for s in ss
                )
                inner = f'<em>{s0["prov_short"]}</em><small>{sub}</small>'
            else:
                inner = f'<em>{s0["prov_short"]}</em>'
            els.append(f'<div class="plabel {side}" style="left:{x:.0f}px;top:{y:.0f}px;--pc:{col}">{inner}</div>')
    return f'<div class="map" style="width:{w}px;height:{h}px">{svg}{"".join(els)}</div>'


def font_face():
    out = []
    for wname, wt in [("Regular", 400), ("Medium", 500), ("SemiBold", 600), ("Bold", 700), ("ExtraBold", 800)]:
        out.append(f"@font-face{{font-family:Kanit;font-weight:{wt};src:url('../assets/Kanit-{wname}.ttf')}}")
    return "\n".join(out)


ICON_CAL = '<svg viewBox="0 0 24 24" width="22" height="22"><rect x="3" y="5" width="18" height="16" rx="3" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M3 10h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>'
ICON_PIN = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 22s7-7.2 7-12.5A7 7 0 0 0 5 9.5C5 14.8 12 22 12 22z" fill="currentColor"/><circle cx="12" cy="9.5" r="2.7" fill="#fff"/></svg>'


def load_context(data_path=None):
    d = json.load(open(data_path or A("data.json"), encoding="utf8"))
    courses = {int(c["no"]): c for c in d["courses"]}
    cats = d["categories"]
    fy = str(d["fiscal_year"])
    fyi = int(fy)
    q_range = {1: f"ต.ค. – ธ.ค. {fyi-1}", 2: f"ม.ค. – มี.ค. {fyi}", 3: f"เม.ย. – มิ.ย. {fyi}", 4: f"ก.ค. – ก.ย. {fyi}"}
    q_range_full = {
        1: f"ตุลาคม – ธันวาคม {fyi-1}",
        2: f"มกราคม – มีนาคม {fyi}",
        3: f"เมษายน – มิถุนายน {fyi}",
        4: f"กรกฎาคม – กันยายน {fyi}",
    }
    sess = []
    for s in d["sessions"]:
        sc = dict(s)
        sc["course"] = int(sc["course"])
        sc["month"] = int(sc["month"])
        sc["year"] = int(sc["year"])
        sc["run"] = int(sc["run"])
        sc["q"] = quarter_of(sc["month"])
        prov = sc["province"].strip()
        if prov not in TH2EN:
            raise ValueError(f"ไม่พบชื่อจังหวัด '{prov}' ในระบบแผนที่ (กรุณาตรวจสอบตัวสะกด)")
        sc["en"] = TH2EN[prov]
        sc["c"] = courses[sc["course"]]
        sc["cat"] = cats[sc["c"]["cat"]]
        sc["prov_short"] = "กรุงเทพฯ" if prov == "กรุงเทพมหานคร" else prov
        sess.append(sc)
    sess.sort(key=lambda x: (x["year"], x["month"], x["course"], x["run"]))
    return d, courses, cats, fy, q_range, q_range_full, sess


def build_pages(data_path=None):
    D, COURSES, CATS, FY, Q_RANGE, Q_RANGE_FULL, SESS = load_context(data_path)

    def header(quarter=None):
        logo = '<div class="logos"><img class="logo" src="../assets/logo.png"><div class="sep"></div><img class="wps" src="../assets/wps-lockup.svg"></div>'
        if quarter is None:
            return f'''
<header class="hd">
  <h1>{D["title"]}<br><span>ปีงบประมาณ {FY}</span></h1>{logo}
</header>
<div class="banner"><div>สำหรับองค์กรปกครองส่วนท้องถิ่น</div><div>หน่วยงานราชการ และภาคเอกชน</div></div>'''
        return f'''
<header class="hd q">
  <div class="kicker">{D["title"]} <span>ปีงบประมาณ {FY}</span></div>
  <div class="qline"><div class="qbadge">ไตรมาส <b>{quarter}</b></div><div class="qrange">{Q_RANGE_FULL[quarter]}</div></div>
  {logo}
</header>
<div class="banner thin"><div>{D["subtitle"]}</div></div>'''

    def footer():
        c = D["contact"]
        return f'''
<footer class="ft">
  <div class="mascot m5"></div>
  <div class="ct">
    <div class="ct-h">ติดต่อสอบถาม / สมัครอบรม</div>
    <div>{c["org"]}</div>
    <div>{c["tel"]}</div>
    <div class="ct-sm"><span class="line">{c["line"]}</span> &nbsp; <span class="fb">{c["fb"]}</span></div>
  </div>
</footer>
<div class="note">{D["note"]}</div>'''

    def page(body, cls):
        return f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<style>{font_face()}</style><link rel="stylesheet" href="../poster.css"></head>
<body><div class="poster {cls}">{body}</div></body></html>'''

    def cat_chip(c):
        k = CATS[c["cat"]]
        return f'<span class="chip" style="--cc:{k["color"]};--cd:{k["dark"]}">{c["cat"]} {k["short"]}</span>'

    def overview():
        n_course = len(D["courses"])
        n_sess = len(SESS)
        n_prov = len({s["en"] for s in SESS})
        seats = sum(COURSES[s["course"]]["seats"] for s in SESS)
        mp = map_html(430, 760, SESS, pin=28)
        legend = "".join(f'<div><i style="background:{k["color"]}"></i>{code} {k["short"]}</div>' for code, k in CATS.items())
        qblocks = []
        for q in (1, 2, 3, 4):
            rows = []
            for s in [x for x in SESS if x["q"] == q]:
                c = s["c"]
                new = '<span class="new-s">NEW</span>' if c.get("is_new") else ""
                rows.append(f'''<div class="qrow">
  <div class="mon">{M_ABBR[s["month"]]} {yy(s["year"])}</div>
  <div class="num" style="background:{s["cat"]["color"]}">{c["no"]}</div>
  <div class="qtxt"><div class="qt">{c["short"]}{new}</div><div class="qp">{ICON_PIN}<span>จ.{s["prov_short"]}</span> <small>· รุ่นที่ {s["run"]}</small></div></div>
</div>''')
            if not rows:
                rows.append('<div class="qrow"><div class="mon">-</div><div class="num" style="background:#94a3b8">-</div><div class="qtxt"><div class="qt" style="color:#64748b">ไม่มีกำหนดการจัดอบรมในไตรมาสนี้</div></div></div>')
            qblocks.append(f'<div class="qblk"><div class="qhd"><b>ไตรมาส {q}</b><span>{Q_RANGE[q]}</span></div>{"".join(rows)}</div>')
        body = f'''<img class="bg" src="../assets/bg.jpg">
{header()}
<section class="ov">
  <div class="mapcard glass">
    <div class="mapttl">แผนที่จังหวัดที่จัดอบรม</div>
    {mp}
    <div class="legend">{legend}</div>
  </div>
  <div class="ovright">
    <div class="stats">
      <div><b>{n_course}</b><span>หลักสูตร</span></div>
      <div><b>{n_sess}</b><span>รุ่น</span></div>
      <div><b>{n_prov}</b><span>จังหวัด</span></div>
      <div><b>{seats}</b><span>ที่นั่ง</span></div>
    </div>
    {"".join(qblocks)}
  </div>
</section>
{footer()}'''
        return page(body, "overview")

    def session_card(s, big=False, compact=False):
        c = s["c"]
        k = s["cat"]
        new = '<span class="newb">NEW<small>หลักสูตรใหม่</small></span>' if c.get("is_new") else ""
        fee_note = f'<div class="feenote">* {c["fee_note"]}</div>' if c.get("fee_note") else ""
        venue = f' ({s["venue"]})' if s.get("venue") else ""
        cls = "card" + (" big" if big else "") + (" compact" if compact else "")
        return f'''<div class="{cls}" style="--cc:{k["color"]};--cd:{k["dark"]}">
  <div class="cnum">{c["no"]}</div>
  <div class="cbody">
    <div class="ctop">{cat_chip(c)}{new}</div>
    <div class="ctitle">{c["title"]}</div>
    <div class="cinfo">อบรม {c["days"]} วัน &nbsp;|&nbsp; ค่าลงทะเบียน <b>{fmt_money(c["fee"])}</b> บาท &nbsp;|&nbsp; รับ {c["seats"]} คน</div>
    {fee_note}
    <div class="cwhen"><span class="run">รุ่นที่ {s["run"]}</span><span>{ICON_CAL}{M_FULL[s["month"]]} {s["year"]}</span><span>{ICON_PIN}จ.{s["prov_short"]}{venue}</span></div>
  </div>
</div>'''

    def quarter_page(q):
        ss = [s for s in SESS if s["q"] == q]
        others = [s for s in SESS if s["q"] != q]
        mp = map_html(400, 760, ss, faded=others, pin=34)
        cards = "".join(session_card(s, big=len(ss) <= 2, compact=len(ss) >= 5) for s in ss)
        if not ss:
            cards = '<div class="card big"><div class="cbody"><div class="ctitle" style="text-align:center;color:#64748b">ไม่มีกำหนดการจัดอบรมในไตรมาสนี้</div></div></div>'
        extra = ""
        if len(ss) <= 2:
            nq = q + 1 if q < 4 else None
            if nq:
                nxt = [s for s in SESS if s["q"] == nq]
                items = "".join(
                    f'<div><span class="mon">{M_ABBR[s["month"]]} {yy(s["year"])}</span><span class="num" style="background:{s["cat"]["color"]}">{s["c"]["no"]}</span>{s["c"]["short"]} <small>· จ.{s["prov_short"]}</small></div>'
                    for s in nxt
                )
                extra = f'<div class="next glass"><div class="nhd">เตรียมพบกับ ไตรมาส {nq} <span>{Q_RANGE[nq]}</span></div>{items}</div>'
            else:
                extra = (
                    '<div class="next glass cta"><div class="mascot m4"></div><div style="display:block"><div class="nhd">ปิดท้ายปีงบประมาณ '
                    + FY
                    + '</div><div class="ctatxt">ที่นั่งมีจำนวนจำกัด สมัครได้ตั้งแต่วันนี้!<small>ติดตามหลักสูตรปีงบประมาณถัดไปได้ที่เพจ ประปามืออาชีพ</small></div></div></div>'
                )
        body = f'''<img class="bg" src="../assets/bg.jpg">
{header(q)}
<section class="qs">
  <div class="mapcard glass small">
    <div class="mapttl">จังหวัดที่จัดอบรม</div>
    {mp}
    <div class="legend sm"><div><i class="pinmini"></i>ไตรมาสนี้</div><div><i class="dotmini"></i>ไตรมาสอื่น</div></div>
  </div>
  <div class="cards n{len(ss)}">{cards}{extra}</div>
</section>
{footer()}'''
        return page(body, f"quarter q{q}")

    pages = {f"00_overview_FY{FY}": overview()}
    for q in (1, 2, 3, 4):
        pages[f"0{q}_Q{q}_FY{FY}"] = quarter_page(q)
    return pages


def render_pngs(pages, only=None):
    os.makedirs(A("output"), exist_ok=True)
    rendered = []
    for name in pages:
        if only and only not in name:
            continue
        out = A("output", name + ".png")
        subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--user-data-dir=/tmp/chr",
                "--force-device-scale-factor=2",
                f"--window-size={W},{H}",
                "--virtual-time-budget=3000",
                "--allow-file-access-from-files",
                f"--screenshot={out}",
                "file://" + A("html", name + ".html"),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if os.path.isdir(ARTIFACT_DIR):
            try:
                shutil.copy2(out, os.path.join(ARTIFACT_DIR, name + ".png"))
            except Exception:
                pass
        print("✓", out)
        rendered.append(out)
    return rendered


def main():
    os.makedirs(A("html"), exist_ok=True)
    os.makedirs(A("output"), exist_ok=True)
    pages = build_pages()
    for name, htm in pages.items():
        open(A("html", name + ".html"), "w", encoding="utf8").write(htm)
    if "--no-png" in sys.argv:
        return
    only = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        if idx + 1 < len(sys.argv):
            only = sys.argv[idx + 1]
    render_pngs(pages, only=only)


if __name__ == "__main__":
    main()
