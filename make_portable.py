#!/usr/bin/env python3
"""สร้างไฟล์ Portable HTML ไฟล์เดียวจบ (Single-File Standalone App)
สามารถก๊อปปี้ไปวางเครื่อง PC (Windows / Mac) เครื่องอื่นแล้วดับเบิลคลิกเปิดในเบราว์เซอร์
(Chrome / Microsoft Edge) เพื่อแก้ไขจังหวัดและสั่งสร้างรูป PNG (2160x2700 px) หรือดาวน์โหลดเป็น ZIP ได้ทันที
โดยไม่ต้องติดตั้ง Python หรือโปรแกรมเสริมใดๆ
"""
import base64
import json
import os
import shutil
import zipfile

import build
from provinces import TH2EN

ROOT = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(ROOT, *p)


def b64_data_uri(rel_path, mime):
    raw = open(A(rel_path), "rb").read()
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def build_portable_bundle():
    # 1. Pre-project Thailand 77 provinces map paths & centroids at (430, 760) and (400, 760)
    map_data = {}
    for w, h in [(430, 760), (400, 760)]:
        P = build.Proj(w, h)
        paths = {}
        cents = {}
        for name, f in build.FEAT.items():
            paths[name] = "".join(build.ring_path(r, P) for poly in build.rings_of(f) for r in poly)
            cx, cy = P(*build.CENT[name])
            cents[name] = [round(cx, 1), round(cy, 1)]
        map_data[f"{w}x{h}"] = {"paths": paths, "cents": cents}

    # 2. Embed fonts & images as base64 data URIs
    fonts_css = []
    for wname, wt in [("Regular", 400), ("Medium", 500), ("SemiBold", 600), ("Bold", 700), ("ExtraBold", 800)]:
        uri = b64_data_uri(f"assets/Kanit-{wname}.ttf", "font/ttf")
        fonts_css.append(f"@font-face{{font-family:'Kanit';font-weight:{wt};src:url('{uri}') format('truetype')}}")
    fonts_css_str = "\n".join(fonts_css)

    bg_uri = b64_data_uri("assets/bg.jpg", "image/jpeg")
    logo_uri = b64_data_uri("assets/logo.png", "image/png")
    wps_uri = b64_data_uri("assets/wps-lockup.svg", "image/svg+xml")
    m4_uri = b64_data_uri("assets/m4.png", "image/png")
    m5_uri = b64_data_uri("assets/m5.png", "image/png")

    poster_css = open(A("poster.css"), encoding="utf8").read()
    poster_css = poster_css.replace(".poster{", ".poster{font-family:'Kanit',sans-serif;color:#0e254c;background:#d8f1ff;")
    poster_css = poster_css.replace("url('assets/m5.png')", f"url('{m5_uri}')")
    poster_css = poster_css.replace("url('assets/m4.png')", f"url('{m4_uri}')")

    default_data = json.load(open(A("data.default.json"), encoding="utf8"))
    current_data = json.load(open(A("data.json"), encoding="utf8"))
    provinces_sorted = sorted(k for k in TH2EN.keys() if k != "กรุงเทพฯ")

    bundle = {
        "defaultData": default_data,
        "initialData": current_data,
        "th2en": TH2EN,
        "provinces": provinces_sorted,
        "mapData": map_data,
        "assets": {
            "bg": bg_uri,
            "logo": logo_uri,
            "wps": wps_uri,
            "m4": m4_uri,
            "m5": m5_uri,
        },
        "posterCss": fonts_css_str + "\n" + poster_css,
    }
    return bundle, fonts_css_str


PORTABLE_HTML_TEMPLATE = r"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MWA Poster Studio (Portable) — ระบบแก้ไขจังหวัดและสร้างโปสเตอร์ประปาสัญจร</title>
<style>
__FONTS_CSS__

  :root{
    --bg:#0f172a;
    --panel:#1e293b;
    --panel2:#26354d;
    --border:#334155;
    --accent:#0ea5e9;
    --accent2:#2563eb;
    --text:#f8fafc;
    --muted:#94a3b8;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{
    font-family:'Kanit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background:var(--bg);
    color:var(--text);
    height:100vh;
    display:flex;
    flex-direction:column;
    overflow:hidden;
  }

  .topbar{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:10px 18px;
    background:linear-gradient(90deg,#0b2545,#133b6e);
    border-bottom:1px solid #1e4976;
    gap:12px;
    flex-shrink:0;
    flex-wrap:wrap;
  }
  .brand{display:flex;align-items:center;gap:12px}
  .brand img{width:42px;height:42px;border-radius:50%;border:2px solid #fff;background:#fff}
  .brand h1{font-size:18px;font-weight:700;line-height:1.15;color:#fff;display:flex;align-items:center;gap:8px}
  .badge-port{background:#22c55e;color:#052e16;font-size:11px;font-weight:800;padding:2px 8px;border-radius:999px}
  .brand small{display:block;font-size:12px;font-weight:400;color:#93c5fd}

  .actions{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
  .btn{
    font-family:inherit;
    font-size:13px;
    font-weight:600;
    padding:7px 13px;
    border-radius:10px;
    border:1px solid transparent;
    cursor:pointer;
    display:inline-flex;
    align-items:center;
    gap:6px;
    transition:.15s;
    text-decoration:none;
    color:#fff;
    background:#334155;
  }
  .btn:hover{filter:brightness(1.1)}
  .btn:disabled{opacity:.5;cursor:not-allowed}
  .btn.primary{background:linear-gradient(135deg,#22c55e,#15803d);border-color:#4ade80;box-shadow:0 4px 12px rgba(22,163,74,.35);font-size:13.5px;padding:8px 15px}
  .btn.blue{background:linear-gradient(135deg,#0ea5e9,#2563eb);border-color:#38bdf8}
  .btn.amber{background:linear-gradient(135deg,#f59e0b,#d97706);border-color:#fbbf24}
  .btn.ghost{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.18)}

  .workspace{
    display:grid;
    grid-template-columns:550px 1fr;
    flex:1;
    min-height:0;
  }
  @media (max-width: 1100px){
    .workspace{grid-template-columns:460px 1fr;}
  }

  .editor{
    background:var(--panel);
    border-right:1px solid var(--border);
    display:flex;
    flex-direction:column;
    min-height:0;
  }
  .tabs{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    background:#0f172a;
    padding:6px;
    gap:6px;
    border-bottom:1px solid var(--border);
  }
  .tab{
    font-family:inherit;
    padding:8px 10px;
    border-radius:8px;
    border:none;
    background:transparent;
    color:var(--muted);
    font-size:13px;
    font-weight:600;
    cursor:pointer;
  }
  .tab.active{background:var(--accent2);color:#fff;box-shadow:0 2px 8px rgba(37,99,235,.35)}

  .toolbar{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:9px 14px;
    background:rgba(15,23,42,.55);
    border-bottom:1px solid var(--border);
    gap:8px;
    flex-wrap:wrap;
  }
  .qfilters{display:flex;gap:4px;flex-wrap:wrap}
  .qbtn{
    font-family:inherit;
    font-size:12px;
    font-weight:600;
    padding:4px 10px;
    border-radius:999px;
    border:1px solid var(--border);
    background:#1e293b;
    color:#cbd5e1;
    cursor:pointer;
  }
  .qbtn.active{background:#38bdf8;color:#0f172a;border-color:#38bdf8}

  .scroll-area{
    flex:1;
    overflow-y:auto;
    padding:12px 14px 28px;
    display:flex;
    flex-direction:column;
    gap:10px;
  }

  .s-card{
    background:var(--panel2);
    border:1px solid #3b4f6b;
    border-left:5px solid var(--cc,#38bdf8);
    border-radius:12px;
    padding:10px 12px;
    display:flex;
    flex-direction:column;
    gap:8px;
  }
  .s-top{display:flex;align-items:center;justify-content:space-between;gap:8px}
  .s-badges{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
  .qpill{background:#fef08a;color:#0f172a;font-size:11.5px;font-weight:800;padding:1px 8px;border-radius:999px}
  .cpill{background:var(--cc,#0ea5e9);color:#fff;font-size:11.5px;font-weight:700;padding:1px 8px;border-radius:999px}
  .s-title{font-size:13px;font-weight:600;color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:270px}
  .del-btn{background:transparent;border:none;color:#f87171;font-size:12px;font-family:inherit;cursor:pointer;padding:2px 6px;border-radius:6px}
  .del-btn:hover{background:rgba(239,68,68,.2)}

  .grid-row{display:grid;grid-template-columns:1.35fr 1.05fr 0.65fr 0.95fr;gap:6px}
  .grid-row2{display:grid;grid-template-columns:1.3fr 0.6fr 1.1fr;gap:6px}
  label.fld{display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:#94a3b8;font-weight:500;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  label.fld.hi{color:#7dd3fc;font-weight:700}
  input, select, textarea{
    font-family:inherit;
    font-size:12.5px;
    font-weight:600;
    color:#f8fafc;
    background:#0f172a;
    border:1px solid #475569;
    border-radius:8px;
    padding:5px 6px;
    outline:none;
    width:100%;
    min-width:0;
  }
  label.fld.hi select{background:#0c2d48;border-color:#38bdf8;color:#fff;font-size:13.5px}
  input:focus, select:focus, textarea:focus{border-color:#38bdf8;box-shadow:0 0 0 2px rgba(56,189,248,.25)}

  .viewer{display:flex;flex-direction:column;background:#0b1120;min-height:0}
  .v-bar{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:10px 18px;
    background:#111c33;
    border-bottom:1px solid var(--border);
    gap:10px;
    flex-wrap:wrap;
  }
  .poster-tabs{display:flex;gap:6px;flex-wrap:wrap}
  .ptab{
    font-family:inherit;
    font-size:13px;
    font-weight:600;
    padding:6px 12px;
    border-radius:9px;
    border:1px solid #334155;
    background:#1e293b;
    color:#cbd5e1;
    cursor:pointer;
  }
  .ptab.active{background:#0ea5e9;color:#fff;border-color:#38bdf8}

  .canvas-wrap{
    flex:1;
    overflow:auto;
    display:flex;
    align-items:flex-start;
    justify-content:center;
    padding:20px;
    position:relative;
  }

  .frame-holder{display:flex;flex-direction:column;align-items:center;gap:10px}
  .scale-box{
    width:540px;
    height:675px;
    position:relative;
    border-radius:16px;
    overflow:hidden;
    box-shadow:0 20px 50px rgba(0,0,0,.6);
    border:2px solid #334155;
    background:#d8f1ff;
  }
  .scale-inner{
    width:1080px;
    height:1350px;
    transform:scale(0.5);
    transform-origin:top left;
    pointer-events:none;
  }

  .grid-all{
    display:grid;
    grid-template-columns:repeat(auto-fit, minmax(340px, 1fr));
    gap:20px;
    width:100%;
    max-width:1400px;
    justify-items:center;
  }
  .mini-card{
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:8px;
    background:#162238;
    padding:12px;
    border-radius:16px;
    border:1px solid #2d3f5e;
  }
  .mini-head{
    width:100%;
    display:flex;
    justify-content:space-between;
    align-items:center;
    font-size:13px;
    font-weight:700;
    color:#e2e8f0;
  }
  .mini-scale{
    width:345.6px;
    height:432px;
    position:relative;
    border-radius:10px;
    overflow:hidden;
    border:1px solid #475569;
    background:#d8f1ff;
    cursor:pointer;
  }
  .mini-inner{
    width:1080px;
    height:1350px;
    transform:scale(0.32);
    transform-origin:top left;
    pointer-events:none;
  }

  .status-bar{
    padding:8px 18px;
    background:#09101f;
    border-top:1px solid var(--border);
    display:flex;
    justify-content:space-between;
    align-items:center;
    font-size:12.5px;
    color:#94a3b8;
    flex-wrap:wrap;
    gap:8px;
  }
  .toast{
    position:fixed;
    bottom:46px;
    right:24px;
    background:#15803d;
    color:#fff;
    padding:10px 18px;
    border-radius:12px;
    font-weight:600;
    font-size:14px;
    box-shadow:0 10px 25px rgba(0,0,0,.45);
    border:1px solid #4ade80;
    z-index:999;
    display:none;
  }
</style>
<!-- Scoped Poster Styles for Live Preview & Export -->
<style id="posterStyleTag"></style>
</head>
<body>

<header class="topbar">
  <div class="brand">
    <img id="brandLogo" alt="MWA">
    <div>
      <h1>MWA Poster Studio <span class="badge-port">PORTABLE ใช้งานได้ทุกเครื่อง</span></h1>
      <small>แก้ไขจังหวัด วันเวลา หรือหลักสูตร แล้วสั่งสร้างไฟล์รูป PNG (2160×2700 px) หรือ ZIP ได้ทันทีโดยไม่ต้องลงโปรแกรม</small>
    </div>
  </div>
  <div class="actions">
    <button class="btn ghost" onclick="exportJSON()" title="บันทึกข้อมูลที่แก้ไขเก็บไว้เป็นไฟล์ .json">💾 บันทึกข้อมูล (.json)</button>
    <button class="btn ghost" onclick="document.getElementById('importFile').click()" title="เปิดไฟล์ข้อมูล .json ที่บันทึกไว้">📂 โหลดข้อมูล (.json)</button>
    <input type="file" id="importFile" accept=".json" style="display:none" onchange="importJSON(event)">
    <button class="btn ghost" onclick="resetDefault()" title="คืนค่าเริ่มต้นปีงบประมาณ 2570">↺ คืนค่าเริ่มต้น</button>
    <button class="btn blue" id="btnDlOne" onclick="downloadCurrentPNG()">🖼️ สร้างรูปหน้านี้ (.PNG)</button>
    <button class="btn primary" id="btnDlAll" onclick="downloadAllPNGs()">⚡ สร้างและดาวน์โหลดครบ 5 ภาพ (.PNG)</button>
    <button class="btn amber" id="btnDlZip" onclick="downloadAllZIP()">📦 สร้างไฟล์ .ZIP (ครบ 5 ภาพ)</button>
  </div>
</header>

<div class="workspace">
  <aside class="editor">
    <div class="tabs">
      <button class="tab active" id="tabBtn-sessions" onclick="switchTab('sessions')">📍 รุ่นและจังหวัด (<span id="sessCount">11</span>)</button>
      <button class="tab" id="tabBtn-courses" onclick="switchTab('courses')">📚 หลักสูตร (7)</button>
      <button class="tab" id="tabBtn-general" onclick="switchTab('general')">⚙️ ข้อมูลติดต่อ/หัวกระดาษ</button>
    </div>

    <div id="tab-sessions" style="display:flex;flex-direction:column;flex:1;min-height:0">
      <div class="toolbar">
        <div class="qfilters">
          <button class="qbtn active" data-q="all" onclick="setQFilter('all')">ทั้งหมด</button>
          <button class="qbtn" data-q="1" onclick="setQFilter(1)">Q1 (ต.ค.–ธ.ค.)</button>
          <button class="qbtn" data-q="2" onclick="setQFilter(2)">Q2 (ม.ค.–มี.ค.)</button>
          <button class="qbtn" data-q="3" onclick="setQFilter(3)">Q3 (เม.ย.–มิ.ย.)</button>
          <button class="qbtn" data-q="4" onclick="setQFilter(4)">Q4 (ก.ค.–ก.ย.)</button>
        </div>
        <button class="btn blue" style="padding:4px 10px;font-size:12px" onclick="addSession()">+ เพิ่มรุ่นอบรม</button>
      </div>
      <div class="scroll-area" id="sessionsList"></div>
    </div>

    <div id="tab-courses" style="display:none;flex-direction:column;flex:1;min-height:0">
      <div class="scroll-area" id="coursesList"></div>
    </div>

    <div id="tab-general" style="display:none;flex-direction:column;flex:1;min-height:0">
      <div class="scroll-area" id="generalForm"></div>
    </div>
  </aside>

  <main class="viewer">
    <div class="v-bar">
      <div class="poster-tabs">
        <button class="ptab active" data-idx="0" onclick="selectPoster(0)">🗺️ ภาพรวมทั้งปี</button>
        <button class="ptab" data-idx="1" onclick="selectPoster(1)">ไตรมาส 1</button>
        <button class="ptab" data-idx="2" onclick="selectPoster(2)">ไตรมาส 2</button>
        <button class="ptab" data-idx="3" onclick="selectPoster(3)">ไตรมาส 3</button>
        <button class="ptab" data-idx="4" onclick="selectPoster(4)">ไตรมาส 4</button>
        <button class="ptab" data-idx="all" onclick="selectPoster('all')">🪟 ดูทั้ง 5 ภาพพร้อมกัน</button>
      </div>
      <div style="font-size:12.5px;color:#93c5fd">✨ แสดงผลสดทันทีเมื่อเปลี่ยนจังหวัด (บันทึกข้อมูลอัตโนมัติในเครื่อง)</div>
    </div>

    <div class="canvas-wrap" id="canvasWrap"></div>

    <div class="status-bar">
      <div id="statusText">พร้อมใช้งาน — เลือกเปลี่ยนจังหวัดทางด้านซ้าย แล้วกดปุ่มสร้างรูป PNG หรือ ZIP ด้านบน</div>
      <div>ความละเอียดภาพส่งออก: <b>2160 × 2700 px (4:5 Facebook Carousel)</b></div>
    </div>
  </main>
</div>

<!-- Hidden offscreen renderer container -->
<div id="offscreenHost" style="position:fixed;left:-99999px;top:0;width:1080px;height:1350px;overflow:hidden;pointer-events:none"></div>
<div class="toast" id="toast"></div>

<script>
const BUNDLE = __BUNDLE_JSON__;

const M_FULL = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"];
const M_ABBR = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];
const MONTHS = [
  {v:10, name:"ตุลาคม (Q1)"},
  {v:11, name:"พฤศจิกายน (Q1)"},
  {v:12, name:"ธันวาคม (Q1)"},
  {v:1,  name:"มกราคม (Q2)"},
  {v:2,  name:"กุมภาพันธ์ (Q2)"},
  {v:3,  name:"มีนาคม (Q2)"},
  {v:4,  name:"เมษายน (Q3)"},
  {v:5,  name:"พฤษภาคม (Q3)"},
  {v:6,  name:"มิถุนายน (Q3)"},
  {v:7,  name:"กรกฎาคม (Q4)"},
  {v:8,  name:"สิงหาคม (Q4)"},
  {v:9,  name:"กันยายน (Q4)"},
];
const ICON_CAL = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"><rect x="3" y="5" width="18" height="16" rx="3" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M3 10h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>';
const ICON_PIN = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"><path d="M12 22s7-7.2 7-12.5A7 7 0 0 0 5 9.5C5 14.8 12 22 12 22z" fill="currentColor"/><circle cx="12" cy="9.5" r="2.7" fill="#fff"/></svg>';

const STORAGE_KEY = "MWA_POSTER_STUDIO_FY2570_STATE_V1";
let STATE = null;
let currentQFilter = 'all';
let currentPoster = 0;

function quarterOf(m){
  m = Number(m);
  if ([10,11,12].includes(m)) return 1;
  if ([1,2,3].includes(m)) return 2;
  if ([4,5,6].includes(m)) return 3;
  return 4;
}
function fmtMoney(n){ return Number(n).toLocaleString('en-US'); }
function yy(y){ return String(y).slice(-2); }

function showToast(msg, bg="#15803d"){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = bg;
  t.style.display = 'block';
  clearTimeout(t._tm);
  t._tm = setTimeout(()=>{ t.style.display = 'none'; }, 3500);
}
function setStatus(msg){
  document.getElementById('statusText').innerHTML = msg;
}

function saveLocal(){
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(STATE));
  } catch (e) {}
}

// ---------------- Poster HTML Builder (Client-side equivalent of build.py) ----------------
function buildMapHTML(w, h, sessions, faded=[], showLabels=true, labelMode="full", pin=30){
  const mdata = BUNDLE.mapData[`${w}x${h}`];
  const pathsObj = mdata.paths;
  const centsObj = mdata.cents;
  const hi = {};
  sessions.forEach(s => { if (!hi[s.en]) hi[s.en] = s.cat.color; });

  const bgPaths = [];
  const hiPaths = [];
  for (const [name, d] of Object.entries(pathsObj)){
    if (hi[name]){
      hiPaths.push(`<path d="${d}" fill="${hi[name]}" fill-opacity=".9" stroke="#fff" stroke-width="1.4"/>`);
    } else {
      bgPaths.push(`<path d="${d}" fill="#ffffff" fill-opacity=".92" stroke="#8cc8ee" stroke-width=".8"/>`);
    }
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" class="map-svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">` +
              `<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#3a8fd0" flood-opacity=".35"/></filter></defs>` +
              `<g filter="url(#sh)">${bgPaths.join('')}${hiPaths.join('')}</g></svg>`;

  const els = [];
  const activeEn = new Set(sessions.map(s => s.en));
  faded.forEach(s => {
    if (activeEn.has(s.en)) return;
    const [x, y] = centsObj[s.en] || [0,0];
    els.push(`<div class="dot" style="left:${Math.round(x)}px;top:${Math.round(y)}px"></div>`);
  });

  const groups = {};
  sessions.forEach(s => {
    if (!groups[s.en]) groups[s.en] = [];
    groups[s.en].push(s);
  });

  for (const [en, ss] of Object.entries(groups)){
    const [x, y] = centsObj[en] || [0,0];
    const s0 = ss[0];
    const lbl = s0.label || "";
    const side = ["left","right","top","bottom"].includes(lbl) ? lbl : (x > w * 0.54 ? "left" : "right");
    const col = s0.cat.color;
    const pinTxt = ss.length === 1 ? String(ss[0].c.no) : String(ss.length);
    els.push(
      `<div class="pin" style="left:${Math.round(x)}px;top:${Math.round(y)}px;--pc:${col};--ps:${pin}px">` +
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-20 -52 40 54" width="${pin}" height="${Math.round(pin*1.35)}"><path d="M0,0 L-13.4,-24.6 A19 19 0 1 1 13.4,-24.6 Z" fill="${col}" stroke="#fff" stroke-width="3.2"/></svg>` +
      `<b>${pinTxt}</b></div>`
    );
    if (showLabels){
      let inner = `<em>${s0.prov_short}</em>`;
      if (labelMode === "full"){
        const sub = ss.map(s => `${ss.length > 1 ? '#'+s.c.no+' ' : ''}${M_ABBR[s.month]} ${yy(s.year)}`).join(" / ");
        inner += `<small>${sub}</small>`;
      }
      els.push(`<div class="plabel ${side}" style="left:${Math.round(x)}px;top:${Math.round(y)}px;--pc:${col}">${inner}</div>`);
    }
  }
  return `<div class="map" style="width:${w}px;height:${h}px">${svg}${els.join('')}</div>`;
}

function buildAllPages(D){
  const courses = {};
  D.courses.forEach(c => courses[Number(c.no)] = c);
  const cats = D.categories;
  const fy = String(D.fiscal_year || "2570");
  const fyi = Number(fy) || 2570;
  const qRange = {
    1: `ต.ค. – ธ.ค. ${fyi-1}`,
    2: `ม.ค. – มี.ค. ${fyi}`,
    3: `เม.ย. – มิ.ย. ${fyi}`,
    4: `ก.ค. – ก.ย. ${fyi}`,
  };
  const qRangeFull = {
    1: `ตุลาคม – ธันวาคม ${fyi-1}`,
    2: `มกราคม – มีนาคม ${fyi}`,
    3: `เมษายน – มิถุนายน ${fyi}`,
    4: `กรกฎาคม – กันยายน ${fyi}`,
  };

  const sess = D.sessions.map(s => {
    const prov = (s.province || "กรุงเทพมหานคร").trim();
    const en = BUNDLE.th2en[prov] || "Bangkok Metropolis";
    const c = courses[Number(s.course)] || D.courses[0];
    const cat = cats[c.cat] || Object.values(cats)[0];
    return {
      ...s,
      course: Number(s.course),
      month: Number(s.month),
      year: Number(s.year),
      run: Number(s.run),
      q: quarterOf(s.month),
      en,
      c,
      cat,
      prov_short: prov === "กรุงเทพมหานคร" ? "กรุงเทพฯ" : prov
    };
  }).sort((a,b) => (a.year - b.year) || (a.month - b.month) || (a.course - b.course) || (a.run - b.run));

  function headerHTML(quarter=null){
    const logo = `<div class="logos"><img class="logo" src="${BUNDLE.assets.logo}" alt="logo"/><div class="sep"></div><img class="wps" src="${BUNDLE.assets.wps}" alt="กวช. WPS"/></div>`;
    if (quarter === null){
      return `<header class="hd"><h1>${D.title}<br/><span>ปีงบประมาณ ${fy}</span></h1>${logo}</header>` +
             `<div class="banner"><div>สำหรับองค์กรปกครองส่วนท้องถิ่น</div><div>หน่วยงานราชการ และภาคเอกชน</div></div>`;
    }
    return `<header class="hd q"><div class="kicker">${D.title} <span>ปีงบประมาณ ${fy}</span></div>` +
           `<div class="qline"><div class="qbadge">ไตรมาส <b>${quarter}</b></div><div class="qrange">${qRangeFull[quarter]}</div></div>${logo}</header>` +
           `<div class="banner thin"><div>${D.subtitle}</div></div>`;
  }

  function footerHTML(){
    const c = D.contact || {};
    return `<footer class="ft"><div class="mascot m5"></div><div class="ct">` +
           `<div class="ct-h">ติดต่อสอบถาม / สมัครอบรม</div>` +
           `<div>${c.org || ''}</div><div>${c.tel || ''}</div>` +
           `<div class="ct-sm"><span class="line">${c.line || ''}</span> &#160; <span class="fb">${c.fb || ''}</span></div>` +
           `</div></footer><div class="note">${D.note || ''}</div>`;
  }

  function catChip(c){
    const k = cats[c.cat];
    return `<span class="chip" style="--cc:${k.color};--cd:${k.dark}">${c.cat} ${k.short}</span>`;
  }

  function overviewPage(){
    const nCourse = D.courses.length;
    const nSess = sess.length;
    const nProv = new Set(sess.map(s => s.en)).size;
    const seats = sess.reduce((acc, s) => acc + Number(s.c.seats || 0), 0);
    const mp = buildMapHTML(430, 760, sess, [], true, "full", 28);
    const legend = Object.entries(cats).map(([code, k]) => `<div><i style="background:${k.color}"></i>${code} ${k.short}</div>`).join('');

    const qblocks = [1,2,3,4].map(q => {
      const qss = sess.filter(x => x.q === q);
      const rows = qss.length ? qss.map(s => {
        const c = s.c;
        const newBadge = c.is_new ? '<span class="new-s">NEW</span>' : '';
        return `<div class="qrow"><div class="mon">${M_ABBR[s.month]} ${yy(s.year)}</div>` +
               `<div class="num" style="background:${s.cat.color}">${c.no}</div>` +
               `<div class="qtxt"><div class="qt">${c.short}${newBadge}</div>` +
               `<div class="qp">${ICON_PIN}<span>จ.${s.prov_short}</span> <small>· รุ่นที่ ${s.run}</small></div></div></div>`;
      }).join('') : `<div class="qrow"><div class="mon">-</div><div class="num" style="background:#94a3b8">-</div><div class="qtxt"><div class="qt" style="color:#64748b">ไม่มีกำหนดการจัดอบรมในไตรมาสนี้</div></div></div>`;
      return `<div class="qblk"><div class="qhd"><b>ไตรมาส ${q}</b><span>${qRange[q]}</span></div>${rows}</div>`;
    }).join('');

    return `<div class="poster overview"><img class="bg" src="${BUNDLE.assets.bg}" alt="bg"/>${headerHTML(null)}` +
           `<section class="ov"><div class="mapcard glass"><div class="mapttl">แผนที่จังหวัดที่จัดอบรม</div>${mp}<div class="legend">${legend}</div></div>` +
           `<div class="ovright"><div class="stats">` +
           `<div><b>${nCourse}</b><span>หลักสูตร</span></div><div><b>${nSess}</b><span>รุ่น</span></div>` +
           `<div><b>${nProv}</b><span>จังหวัด</span></div><div><b>${seats}</b><span>ที่นั่ง</span></div>` +
           `</div>${qblocks}</div></section>${footerHTML()}</div>`;
  }

  function sessionCard(s, big=false, compact=false){
    const c = s.c, k = s.cat;
    const newB = c.is_new ? '<span class="newb">NEW<small>หลักสูตรใหม่</small></span>' : '';
    const feeNote = c.fee_note ? `<div class="feenote">* ${c.fee_note}</div>` : '';
    const venue = s.venue ? ` (${s.venue})` : '';
    const cls = "card" + (big ? " big" : "") + (compact ? " compact" : "");
    return `<div class="${cls}" style="--cc:${k.color};--cd:${k.dark}">` +
           `<div class="cnum">${c.no}</div><div class="cbody">` +
           `<div class="ctop">${catChip(c)}${newB}</div>` +
           `<div class="ctitle">${c.title}</div>` +
           `<div class="cinfo">อบรม ${c.days} วัน &#160;|&#160; ค่าลงทะเบียน <b>${fmtMoney(c.fee)}</b> บาท &#160;|&#160; รับ ${c.seats} คน</div>` +
           `${feeNote}` +
           `<div class="cwhen"><span class="run">รุ่นที่ ${s.run}</span><span>${ICON_CAL}${M_FULL[s.month]} ${s.year}</span><span>${ICON_PIN}จ.${s.prov_short}${venue}</span></div>` +
           `</div></div>`;
  }

  function quarterPage(q){
    const ss = sess.filter(s => s.q === q);
    const others = sess.filter(s => s.q !== q);
    const mp = buildMapHTML(400, 760, ss, others, true, "full", 34);
    const cards = ss.length
      ? ss.map(s => sessionCard(s, ss.length <= 2, ss.length >= 5)).join('')
      : '<div class="card big"><div class="cbody"><div class="ctitle" style="text-align:center;color:#64748b">ไม่มีกำหนดการจัดอบรมในไตรมาสนี้</div></div></div>';
    let extra = "";
    if (ss.length <= 2){
      const nq = q < 4 ? q + 1 : null;
      if (nq){
        const nxt = sess.filter(s => s.q === nq);
        const items = nxt.map(s => `<div><span class="mon">${M_ABBR[s.month]} ${yy(s.year)}</span><span class="num" style="background:${s.cat.color}">${s.c.no}</span>${s.c.short} <small>· จ.${s.prov_short}</small></div>`).join('');
        extra = `<div class="next glass"><div class="nhd">เตรียมพบกับ ไตรมาส ${nq} <span>${qRange[nq]}</span></div>${items}</div>`;
      } else {
        extra = `<div class="next glass cta"><div class="mascot m4"></div><div style="display:block"><div class="nhd">ปิดท้ายปีงบประมาณ ${fy}</div><div class="ctatxt">ที่นั่งมีจำนวนจำกัด สมัครได้ตั้งแต่วันนี้!<small>ติดตามหลักสูตรปีงบประมาณถัดไปได้ที่เพจ ประปามืออาชีพ</small></div></div></div>`;
      }
    }
    return `<div class="poster quarter q${q}"><img class="bg" src="${BUNDLE.assets.bg}" alt="bg"/>${headerHTML(q)}` +
           `<section class="qs"><div class="mapcard glass small"><div class="mapttl">จังหวัดที่จัดอบรม</div>${mp}` +
           `<div class="legend sm"><div><i class="pinmini"></i>ไตรมาสนี้</div><div><i class="dotmini"></i>ไตรมาสอื่น</div></div></div>` +
           `<div class="cards n${ss.length}">${cards}${extra}</div></section>${footerHTML()}</div>`;
  }

  return [
    { name: `00_overview_FY${fy}`, title: "ภาพที่ 1: ภาพรวมทั้งปี (Overview)", html: overviewPage() },
    { name: `01_Q1_FY${fy}`,       title: "ภาพที่ 2: ไตรมาส 1 (ต.ค. – ธ.ค.)",  html: quarterPage(1) },
    { name: `02_Q2_FY${fy}`,       title: "ภาพที่ 3: ไตรมาส 2 (ม.ค. – มี.ค.)",  html: quarterPage(2) },
    { name: `03_Q3_FY${fy}`,       title: "ภาพที่ 4: ไตรมาส 3 (เม.ย. – มิ.ย.)",  html: quarterPage(3) },
    { name: `04_Q4_FY${fy}`,       title: "ภาพที่ 5: ไตรมาส 4 (ก.ค. – ก.ย.)",  html: quarterPage(4) },
  ];
}

// ---------------- High-Res 2160x2700 PNG Renderer (100% Client-Side) ----------------
async function renderPosterToPNGBlob(posterHTML){
  await document.fonts.ready;
  const host = document.getElementById('offscreenHost');
  host.innerHTML = `<div xmlns="http://www.w3.org/1999/xhtml" style="width:1080px;height:1350px;font-family:'Kanit',sans-serif"><style>${BUNDLE.posterCss}</style>${posterHTML}</div>`;
  const node = host.firstElementChild;
  const serialized = new XMLSerializer().serializeToString(node);
  const svgStr = `<svg xmlns="http://www.w3.org/2000/svg" width="2160" height="2700" viewBox="0 0 1080 1350"><foreignObject width="1080" height="1350">${serialized}</foreignObject></svg>`;
  const dataUrl = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svgStr);

  const img = new Image();
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = reject;
    img.src = dataUrl;
  });
  // Allow embedded @font-face inside SVG image to finish decoding
  await new Promise(r => setTimeout(r, 250));

  const canvas = document.createElement('canvas');
  canvas.width = 2160;
  canvas.height = 2700;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0, 2160, 2700);

  return await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
}

function triggerDownload(blob, filename){
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

// ---------------- Pure JS ZIP Creator (Store Mode, Zero Dependencies) ----------------
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++){
    let c = i;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[i] = c >>> 0;
  }
  return t;
})();

function crc32(u8){
  let c = 0xFFFFFFFF;
  for (let i = 0; i < u8.length; i++){
    c = CRC_TABLE[(c ^ u8[i]) & 0xFF] ^ (c >>> 8);
  }
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function createZipBlob(files){
  // files: [{name: string, data: Uint8Array}]
  const enc = new TextEncoder();
  const localParts = [];
  const centralParts = [];
  let offset = 0;

  for (const f of files){
    const nameBytes = enc.encode(f.name);
    const crc = crc32(f.data);
    const size = f.data.length;

    const lhdr = new Uint8Array(30 + nameBytes.length);
    const lv = new DataView(lhdr.buffer);
    lv.setUint32(0, 0x04034b50, true);
    lv.setUint16(4, 20, true);
    lv.setUint16(6, 0x0800, true); // UTF-8
    lv.setUint16(8, 0, true);      // STORE
    lv.setUint16(10, 0, true);
    lv.setUint16(12, 0x21, true);
    lv.setUint32(14, crc, true);
    lv.setUint32(18, size, true);
    lv.setUint32(22, size, true);
    lv.setUint16(26, nameBytes.length, true);
    lv.setUint16(28, 0, true);
    lhdr.set(nameBytes, 30);

    const chdr = new Uint8Array(46 + nameBytes.length);
    const cv = new DataView(chdr.buffer);
    cv.setUint32(0, 0x02014b50, true);
    cv.setUint16(4, 20, true);
    cv.setUint16(6, 20, true);
    cv.setUint16(8, 0x0800, true);
    cv.setUint16(10, 0, true);
    cv.setUint16(12, 0, true);
    cv.setUint16(14, 0x21, true);
    cv.setUint32(16, crc, true);
    cv.setUint32(20, size, true);
    cv.setUint32(24, size, true);
    cv.setUint16(28, nameBytes.length, true);
    cv.setUint16(30, 0, true);
    cv.setUint16(32, 0, true);
    cv.setUint16(34, 0, true);
    cv.setUint16(36, 0, true);
    cv.setUint32(38, 0, true);
    cv.setUint32(42, offset, true);
    chdr.set(nameBytes, 46);

    localParts.push(lhdr, f.data);
    centralParts.push(chdr);
    offset += lhdr.length + size;
  }

  const centralSize = centralParts.reduce((a, b) => a + b.length, 0);
  const eocd = new Uint8Array(22);
  const ev = new DataView(eocd.buffer);
  ev.setUint32(0, 0x06054b50, true);
  ev.setUint16(8, files.length, true);
  ev.setUint16(10, files.length, true);
  ev.setUint32(12, centralSize, true);
  ev.setUint32(16, offset, true);

  return new Blob([...localParts, ...centralParts, eocd], {type: 'application/zip'});
}

// ---------------- UI Actions & Editors ----------------
function setBusy(busy){
  ['btnDlOne','btnDlAll','btnDlZip'].forEach(id => {
    document.getElementById(id).disabled = busy;
  });
}

async function downloadCurrentPNG(){
  const pages = buildAllPages(STATE);
  const idx = currentPoster === 'all' ? 0 : Number(currentPoster);
  const p = pages[idx];
  setBusy(true);
  setStatus(`⏳ กำลังสร้างไฟล์รูป <b>${p.name}.png</b> (2160×2700 px)...`);
  showToast(`กำลังสร้างรูป ${p.name}.png...`, '#0284c7');
  try {
    const blob = await renderPosterToPNGBlob(p.html);
    triggerDownload(blob, `${p.name}.png`);
    setStatus(`✅ ดาวน์โหลดไฟล์ <b>${p.name}.png</b> (2160×2700 px) เรียบร้อย!`);
    showToast(`✓ ดาวน์โหลด ${p.name}.png สำเร็จ!`);
  } catch (e) {
    setStatus(`❌ เกิดข้อผิดพลาด: ${e.message}`);
    showToast('เกิดข้อผิดพลาดในการสร้างรูป', '#dc2626');
  } finally {
    setBusy(false);
  }
}

async function downloadOneByIndex(idx){
  const prev = currentPoster;
  currentPoster = idx;
  await downloadCurrentPNG();
  currentPoster = prev;
}

async function downloadAllPNGs(){
  const pages = buildAllPages(STATE);
  setBusy(true);
  try {
    for (let i = 0; i < pages.length; i++){
      const p = pages[i];
      setStatus(`⏳ กำลังสร้างรูปที่ ${i+1}/5: <b>${p.name}.png</b> (2160×2700 px)...`);
      showToast(`กำลังสร้างรูปที่ ${i+1}/5 (${p.name}.png)...`, '#0284c7');
      const blob = await renderPosterToPNGBlob(p.html);
      triggerDownload(blob, `${p.name}.png`);
      await new Promise(r => setTimeout(r, 250));
    }
    setStatus(`✅ สร้างและดาวน์โหลดรูป PNG ครบทั้ง 5 ภาพ เรียบร้อย!`);
    showToast(`✓ ดาวน์โหลดครบทั้ง 5 ภาพสำเร็จ!`);
  } catch (e) {
    setStatus(`❌ เกิดข้อผิดพลาด: ${e.message}`);
  } finally {
    setBusy(false);
  }
}

async function downloadAllZIP(){
  const pages = buildAllPages(STATE);
  setBusy(true);
  try {
    const zipEntries = [];
    for (let i = 0; i < pages.length; i++){
      const p = pages[i];
      setStatus(`⏳ กำลังสร้างรูปที่ ${i+1}/5 สำหรับแพ็กลง ZIP: <b>${p.name}.png</b>...`);
      showToast(`กำลังสร้างรูปที่ ${i+1}/5...`, '#0284c7');
      const blob = await renderPosterToPNGBlob(p.html);
      const buf = await blob.arrayBuffer();
      zipEntries.push({ name: `${p.name}.png`, data: new Uint8Array(buf) });
    }
    const fy = STATE.fiscal_year || "2570";
    const zipBlob = createZipBlob(zipEntries);
    triggerDownload(zipBlob, `MWA_Posters_FY${fy}.zip`);
    setStatus(`✅ สร้างและดาวน์โหลดไฟล์ <b>MWA_Posters_FY${fy}.zip</b> (ครบทั้ง 5 ภาพ) เรียบร้อย!`);
    showToast(`✓ ดาวน์โหลดไฟล์ ZIP ครบ 5 ภาพสำเร็จ!`);
  } catch (e) {
    setStatus(`❌ เกิดข้อผิดพลาด: ${e.message}`);
  } finally {
    setBusy(false);
  }
}

function exportJSON(){
  const fy = STATE.fiscal_year || "2570";
  const blob = new Blob([JSON.stringify(STATE, null, 2)], {type: 'application/json;charset=utf-8'});
  triggerDownload(blob, `MWA_Poster_Data_FY${fy}.json`);
  showToast('บันทึกไฟล์ข้อมูล .json เรียบร้อย');
}

function importJSON(ev){
  const f = ev.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const obj = JSON.parse(reader.result);
      if (!obj.sessions || !obj.courses) throw new Error('รูปแบบไฟล์ไม่ถูกต้อง');
      STATE = obj;
      saveLocal();
      renderAllEditors();
      renderViewer();
      showToast('โหลดข้อมูลจากไฟล์ .json สำเร็จ!');
    } catch (e) {
      alert('ไม่สามารถอ่านไฟล์ JSON ได้: ' + e.message);
    }
  };
  reader.readAsText(f);
  ev.target.value = '';
}

function resetDefault(){
  if (!confirm('ต้องการคืนค่าจังหวัดและหลักสูตรทั้งหมดกลับเป็นค่าเริ่มต้นของปีงบประมาณ 2570 ใช่หรือไม่?')) return;
  STATE = JSON.parse(JSON.stringify(BUNDLE.defaultData));
  saveLocal();
  renderAllEditors();
  renderViewer();
  showToast('คืนค่าเริ่มต้นปีงบประมาณ 2570 เรียบร้อย');
}

function switchTab(tab){
  for (const k of ['sessions','courses','general']){
    document.getElementById('tab-'+k).style.display = (k === tab) ? 'flex' : 'none';
    document.getElementById('tabBtn-'+k).classList.toggle('active', k === tab);
  }
}

function setQFilter(q){
  currentQFilter = q;
  document.querySelectorAll('.qbtn').forEach(b=>{
    b.classList.toggle('active', String(b.dataset.q) === String(q));
  });
  renderSessionsEditor();
  if (q !== 'all') selectPoster(Number(q));
}

function selectPoster(idx){
  currentPoster = idx;
  document.querySelectorAll('.ptab').forEach(b => {
    b.classList.toggle('active', String(b.dataset.idx) === String(idx));
  });
  renderViewer();
}

function renderAllEditors(){
  renderSessionsEditor();
  renderCoursesEditor();
  renderGeneralEditor();
}

function renderSessionsEditor(){
  const wrap = document.getElementById('sessionsList');
  document.getElementById('sessCount').textContent = STATE.sessions.length;
  const cmap = {};
  STATE.courses.forEach(c => cmap[c.no] = c);
  const cats = STATE.categories || {};

  let html = '';
  STATE.sessions.forEach((s, idx) => {
    const q = quarterOf(s.month);
    if (currentQFilter !== 'all' && q !== Number(currentQFilter)) return;
    const c = cmap[s.course] || STATE.courses[0];
    const cat = cats[c.cat] || {color:'#0ea5e9'};

    const provOptions = BUNDLE.provinces.map(p =>
      `<option value="${p}" ${p === s.province ? 'selected' : ''}>${p}</option>`
    ).join('');
    const courseOptions = STATE.courses.map(co =>
      `<option value="${co.no}" ${Number(co.no) === Number(s.course) ? 'selected' : ''}>#${co.no} ${co.short}</option>`
    ).join('');
    const monthOptions = MONTHS.map(mo =>
      `<option value="${mo.v}" ${Number(mo.v) === Number(s.month) ? 'selected' : ''}>${mo.name}</option>`
    ).join('');
    const lbl = s.label || 'auto';

    html += `
    <div class="s-card" style="--cc:${cat.color}">
      <div class="s-top">
        <div class="s-badges">
          <span class="qpill">ไตรมาส ${q}</span>
          <span class="cpill">หลักสูตร #${c.no} (${c.cat})</span>
          <span class="s-title" title="${c.title}">${c.short}</span>
        </div>
        <button class="del-btn" onclick="removeSession(${idx})">✕ ลบ</button>
      </div>
      <div class="grid-row">
        <label class="fld hi">
          📍 จังหวัดที่จัดอบรม
          <select onchange="updateSessionProvince(${idx}, this.value)">${provOptions}</select>
        </label>
        <label class="fld">
          🗓️ เดือนที่จัด
          <select onchange="updateSessionMonth(${idx}, this.value)">${monthOptions}</select>
        </label>
        <label class="fld">
          ปี พ.ศ.
          <input type="number" value="${s.year}" onchange="updateSessionField(${idx}, 'year', Number(this.value))">
        </label>
        <label class="fld">
          ป้ายชื่อบนแผนที่
          <select onchange="updateSessionField(${idx}, 'label', this.value)">
            <option value="auto" ${lbl==='auto'?'selected':''}>อัตโนมัติ</option>
            <option value="right" ${lbl==='right'?'selected':''}>ขวา (Right)</option>
            <option value="left" ${lbl==='left'?'selected':''}>ซ้าย (Left)</option>
            <option value="top" ${lbl==='top'?'selected':''}>บน (Top)</option>
            <option value="bottom" ${lbl==='bottom'?'selected':''}>ล่าง (Bottom)</option>
          </select>
        </label>
      </div>
      <div class="grid-row2">
        <label class="fld">
          📚 หลักสูตร
          <select onchange="updateSessionField(${idx}, 'course', Number(this.value))">${courseOptions}</select>
        </label>
        <label class="fld">
          🔢 รุ่นที่
          <input type="number" min="1" max="20" value="${s.run}" onchange="updateSessionField(${idx}, 'run', Number(this.value))">
        </label>
        <label class="fld">
          🏢 สถานที่เพิ่มเติม (ถ้ามี)
          <input type="text" placeholder="เช่น สำนักงานใหญ่ กปน." value="${s.venue || ''}" onchange="updateSessionField(${idx}, 'venue', this.value)">
        </label>
      </div>
    </div>`;
  });

  wrap.innerHTML = html || `<div style="text-align:center;padding:30px;color:#94a3b8">ไม่มีรุ่นอบรมในไตรมาสนี้ กดปุ่ม "+ เพิ่มรุ่นอบรม" ด้านบนได้</div>`;
}

function renderCoursesEditor(){
  const wrap = document.getElementById('coursesList');
  const cats = STATE.categories || {};
  wrap.innerHTML = STATE.courses.map((c, idx) => {
    const cat = cats[c.cat] || {color:'#0ea5e9'};
    return `
    <div class="s-card" style="--cc:${cat.color}">
      <div class="s-top">
        <div class="s-badges">
          <span class="cpill">หลักสูตรที่ ${c.no}</span>
          <span style="font-size:12.5px;color:#cbd5e1">หมวด ${c.cat}</span>
        </div>
        <label style="font-size:12.5px;display:flex;align-items:center;gap:5px;cursor:pointer">
          <input type="checkbox" ${c.is_new ? 'checked' : ''} onchange="updateCourseField(${idx}, 'is_new', this.checked)">
          ติดป้าย NEW (หลักสูตรใหม่)
        </label>
      </div>
      <label class="fld">
        ชื่อหลักสูตรเต็ม
        <textarea rows="2" onchange="updateCourseField(${idx}, 'title', this.value)">${c.title}</textarea>
      </label>
      <div class="grid-row">
        <label class="fld" style="grid-column:span 2">
          ชื่อย่อ (แสดงในหน้าภาพรวม)
          <input type="text" value="${c.short}" onchange="updateCourseField(${idx}, 'short', this.value)">
        </label>
        <label class="fld">
          ค่าลงทะเบียน (บาท)
          <input type="number" value="${c.fee}" onchange="updateCourseField(${idx}, 'fee', Number(this.value))">
        </label>
        <label class="fld">
          จำนวนรับ (คน)
          <input type="number" value="${c.seats}" onchange="updateCourseField(${idx}, 'seats', Number(this.value))">
        </label>
      </div>
      <div class="grid-row2">
        <label class="fld">
          หมวดวิชา
          <select onchange="updateCourseField(${idx}, 'cat', this.value)">
            <option value="2.1" ${c.cat==='2.1'?'selected':''}>2.1 ไฟฟ้า IoT & พลังงานทดแทน</option>
            <option value="2.2" ${c.cat==='2.2'?'selected':''}>2.2 ระบบส่งและจ่ายน้ำ</option>
            <option value="2.3" ${c.cat==='2.3'?'selected':''}>2.3 น้ำดิบ & ระบบผลิตน้ำ</option>
          </select>
        </label>
        <label class="fld">
          จำนวนวันอบรม
          <input type="number" value="${c.days}" onchange="updateCourseField(${idx}, 'days', Number(this.value))">
        </label>
        <label class="fld">
          หมายเหตุค่าลงทะเบียน (ถ้ามี)
          <input type="text" value="${c.fee_note || ''}" onchange="updateCourseField(${idx}, 'fee_note', this.value)">
        </label>
      </div>
    </div>`;
  }).join('');
}

function renderGeneralEditor(){
  const wrap = document.getElementById('generalForm');
  const ct = STATE.contact || {};
  wrap.innerHTML = `
  <div class="s-card" style="--cc:#38bdf8">
    <label class="fld">ปีงบประมาณ (พ.ศ.)<input type="text" value="${STATE.fiscal_year}" onchange="updateRootField('fiscal_year', this.value)"></label>
    <label class="fld">หัวข้อหลักโปสเตอร์<input type="text" value="${STATE.title}" onchange="updateRootField('title', this.value)"></label>
    <label class="fld">คำโปรยกลุ่มเป้าหมาย<input type="text" value="${STATE.subtitle}" onchange="updateRootField('subtitle', this.value)"></label>
    <label class="fld">หน่วยงานติดต่อ<input type="text" value="${ct.org || ''}" onchange="updateContactField('org', this.value)"></label>
    <label class="fld">เบอร์โทรศัพท์<input type="text" value="${ct.tel || ''}" onchange="updateContactField('tel', this.value)"></label>
    <label class="fld">LINE Official<input type="text" value="${ct.line || ''}" onchange="updateContactField('line', this.value)"></label>
    <label class="fld">Facebook Page<input type="text" value="${ct.fb || ''}" onchange="updateContactField('fb', this.value)"></label>
    <label class="fld">หมายเหตุท้ายโปสเตอร์<input type="text" value="${STATE.note || ''}" onchange="updateRootField('note', this.value)"></label>
  </div>`;
}

function updateSessionProvince(idx, prov){
  STATE.sessions[idx].province = prov;
  saveLocal();
  renderViewer();
  showToast(`เปลี่ยนจังหวัดเป็น "${prov}" เรียบร้อย`);
}
function updateSessionMonth(idx, monthVal){
  const m = Number(monthVal);
  const fy = Number(STATE.fiscal_year) || 2570;
  STATE.sessions[idx].month = m;
  STATE.sessions[idx].year = [10,11,12].includes(m) ? (fy - 1) : fy;
  saveLocal();
  renderSessionsEditor();
  renderViewer();
  showToast(`เปลี่ยนเดือนเป็น ${M_FULL[m]} (ไตรมาส ${quarterOf(m)})`);
}
function updateSessionField(idx, key, val){
  if (key === 'venue' && !String(val).trim()) delete STATE.sessions[idx].venue;
  else if (key === 'label' && val === 'auto') delete STATE.sessions[idx].label;
  else STATE.sessions[idx][key] = val;
  saveLocal();
  if (key === 'course') renderSessionsEditor();
  renderViewer();
}
function addSession(){
  const fy = Number(STATE.fiscal_year) || 2570;
  const defMonth = currentQFilter === 1 ? 11 : currentQFilter === 2 ? 2 : currentQFilter === 3 ? 5 : currentQFilter === 4 ? 8 : 1;
  const defYear = [10,11,12].includes(defMonth) ? (fy - 1) : fy;
  STATE.sessions.push({ course: 1, run: 1, month: defMonth, year: defYear, province: "เชียงใหม่" });
  saveLocal();
  renderSessionsEditor();
  renderViewer();
  showToast('เพิ่มรุ่นอบรมใหม่เรียบร้อย');
}
function removeSession(idx){
  const s = STATE.sessions[idx];
  if (!confirm(`ต้องการลบรุ่นอบรม จ.${s.province} ใช่หรือไม่?`)) return;
  STATE.sessions.splice(idx, 1);
  saveLocal();
  renderSessionsEditor();
  renderViewer();
}
function updateCourseField(idx, key, val){
  if (key === 'fee_note' && !String(val).trim()) delete STATE.courses[idx].fee_note;
  else STATE.courses[idx][key] = val;
  saveLocal();
  renderSessionsEditor();
  renderViewer();
}
function updateRootField(key, val){
  STATE[key] = val;
  saveLocal();
  renderViewer();
}
function updateContactField(key, val){
  STATE.contact[key] = val;
  saveLocal();
  renderViewer();
}

function renderViewer(){
  const wrap = document.getElementById('canvasWrap');
  const pages = buildAllPages(STATE);

  if (currentPoster === 'all'){
    wrap.innerHTML = `<div class="grid-all">` + pages.map((p, idx) => `
      <div class="mini-card">
        <div class="mini-head">
          <span>${p.title}</span>
          <button class="btn blue" style="padding:3px 9px;font-size:11.5px" onclick="downloadOneByIndex(${idx})">⬇ สร้าง PNG</button>
        </div>
        <div class="mini-scale" onclick="selectPoster(${idx})" title="คลิกเพื่อขยายดูภาพนี้">
          <div class="mini-inner">${p.html}</div>
        </div>
      </div>`).join('') + `</div>`;
    return;
  }

  const idx = Number(currentPoster);
  const p = pages[idx] || pages[0];
  wrap.innerHTML = `
    <div class="frame-holder">
      <div style="display:flex;gap:12px;align-items:center">
        <span style="font-size:13.5px;color:#cbd5e1"><b>${p.title}</b> (${p.name}.png)</span>
        <button class="btn blue" style="padding:5px 12px;font-size:12.5px" onclick="downloadCurrentPNG()">🖼️ สร้างและดาวน์โหลดรูปนี้ (.PNG 2160×2700)</button>
      </div>
      <div class="scale-box">
        <div class="scale-inner">${p.html}</div>
      </div>
    </div>`;
}

function init(){
  document.getElementById('brandLogo').src = BUNDLE.assets.logo;
  // Inject poster CSS rules without body override affecting outer page
  const scopedCss = BUNDLE.posterCss.replace(/body\{[^}]+\}/g, "");
  document.getElementById('posterStyleTag').textContent = scopedCss;

  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    STATE = saved ? JSON.parse(saved) : JSON.parse(JSON.stringify(BUNDLE.initialData));
  } catch (e) {
    STATE = JSON.parse(JSON.stringify(BUNDLE.initialData));
  }
  renderAllEditors();
  renderViewer();
}

init();
</script>
</body>
</html>
"""


def main():
    bundle, fonts_css_str = build_portable_bundle()
    bundle_json = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    html_out = PORTABLE_HTML_TEMPLATE.replace("__FONTS_CSS__", fonts_css_str).replace("__BUNDLE_JSON__", bundle_json)

    # 1. Write standalone portable HTML in project root
    portable_file = A("MWA_Poster_Portable.html")
    with open(portable_file, "w", encoding="utf8") as f:
        f.write(html_out)

    # 2. Create a clean portable distribution folder & ZIP for copying to any PC
    dist_dir = A("MWA_Poster_Portable_สำหรับก๊อปวางเครื่องอื่น")
    os.makedirs(dist_dir, exist_ok=True)
    main_html_in_dist = os.path.join(dist_dir, "เปิดใช้งานทันที_MWA_Poster_Studio.html")
    with open(main_html_in_dist, "w", encoding="utf8") as f:
        f.write(html_out)

    shutil.copy2(A("data.json"), os.path.join(dist_dir, "ข้อมูลหลักสูตร_FY2570.json"))

    readme_txt = """======================================================================
  ระบบแก้ไขจังหวัดและสร้างโปสเตอร์ "ประปาสัญจร" (รุ่น Portable)
  การประปานครหลวง (กปน.)
======================================================================

วิธีใช้งานบนเครื่อง PC อื่น (Windows หรือ Mac) — ไม่ต้องติดตั้งโปรแกรมใดๆ:

1. ก๊อปปี้โฟลเดอร์นี้ (หรือก๊อปปี้เฉพาะไฟล์ "เปิดใช้งานทันที_MWA_Poster_Studio.html" เพียงไฟล์เดียวก็ได้)
   ไปวางไว้ที่เครื่อง PC เครื่องใดก็ได้

2. ดับเบิลคลิกไฟล์ "เปิดใช้งานทันที_MWA_Poster_Studio.html"
   (แนะนำให้เปิดด้วยเบราว์เซอร์ Google Chrome หรือ Microsoft Edge)

3. การแก้ไขจังหวัดและข้อมูล:
   - แท็บ "รุ่นและจังหวัด": เลือกเปลี่ยนจังหวัดได้ครบทั้ง 77 จังหวัด, เปลี่ยนเดือน/ปี/รุ่น
     แผนที่ประเทศไทยและการ์ดหลักสูตรทางด้านขวาจะเปลี่ยนตามทันที
   - แท็บ "หลักสูตร": แก้ไขชื่อหลักสูตร ค่าลงทะเบียน จำนวนรับ หรือป้าย NEW ได้
   - ข้อมูลที่แก้ไขจะถูกจำไว้ในเบราว์เซอร์อัตโนมัติ และสามารถกดปุ่ม
     "บันทึกข้อมูล (.json)" เพื่อเก็บเป็นไฟล์สำรองหรือส่งต่อให้เครื่องอื่นกด "โหลดข้อมูล (.json)" ได้

4. การสั่งสร้างรูปภาพโปสเตอร์ความละเอียดสูง (2160 x 2700 px):
   - กดปุ่ม "สร้างรูปหน้านี้ (.PNG)" เพื่อดาวน์โหลดเฉพาะหน้าที่กำลังดูอยู่
   - กดปุ่ม "สร้างและดาวน์โหลดครบ 5 ภาพ (.PNG)" เพื่อดาวน์โหลดแยกทั้ง 5 ภาพ
   - กดปุ่ม "สร้างไฟล์ .ZIP (ครบ 5 ภาพ)" เพื่อรวมรูป PNG ทั้ง 5 ภาพเป็นไฟล์ .ZIP เดียว
======================================================================
"""
    with open(os.path.join(dist_dir, "วิธีใช้งาน_อ่านฉัน.txt"), "w", encoding="utf8") as f:
        f.write(readme_txt)

    # 3. Also package a single .zip file ready to send via Line / Email / USB
    zip_path = A("MWA_Poster_Portable_สำหรับก๊อปวางเครื่องอื่น.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(dist_dir):
            fpath = os.path.join(dist_dir, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, arcname=os.path.join("MWA_Poster_Portable", fname))

    print("✓ สร้างไฟล์ Portable สำเร็จ:")
    print(f"  1) ไฟล์เดียวจบ: {portable_file} ({os.path.getsize(portable_file)/1024/1024:.2f} MB)")
    print(f"  2) โฟลเดอร์พร้อมก๊อปวาง: {dist_dir}")
    print(f"  3) ไฟล์ ZIP พร้อมส่งต่อ: {zip_path} ({os.path.getsize(zip_path)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
