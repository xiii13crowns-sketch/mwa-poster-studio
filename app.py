#!/usr/bin/env python3
"""ระบบเว็บสตูดิโอแก้ไขจังหวัดและสั่งสร้างโปสเตอร์ ประปาสัญจร (MWA Poster Studio)
รันคำสั่ง:
  python3 app.py          -> เปิดเซิร์ฟเวอร์ที่ http://127.0.0.1:8765
  python3 app.py --open   -> เปิดเซิร์ฟเวอร์พร้อมเปิดเบราว์เซอร์อัตโนมัติ
"""
import io
import json
import os
import shutil
import subprocess
import sys
import time
import webbrowser
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import build
from provinces import TH2EN

ROOT = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(ROOT, *p)
PORT = int(os.environ.get("PORT", "8765"))

# รายชื่อ 77 จังหวัดภาษาไทย (ตัดชื่อซ้ำ กรุงเทพฯ ออกเพื่อให้เหลือ 77 จังหวัดมาตรฐาน)
PROVINCE_LIST = sorted(k for k in TH2EN.keys() if k != "กรุงเทพฯ")


def list_outputs(fy):
    out_dir = A("output")
    os.makedirs(out_dir, exist_ok=True)
    expected = [
        f"00_overview_FY{fy}",
        f"01_Q1_FY{fy}",
        f"02_Q2_FY{fy}",
        f"03_Q3_FY{fy}",
        f"04_Q4_FY{fy}",
    ]
    res = []
    for name in expected:
        png_path = os.path.join(out_dir, name + ".png")
        exists = os.path.isfile(png_path)
        mtime = int(os.path.getmtime(png_path) * 1000) if exists else 0
        size_kb = round(os.path.getsize(png_path) / 1024, 1) if exists else 0
        res.append({
            "name": name,
            "html_url": f"/html/{name}.html",
            "png_url": f"/output/{name}.png?t={mtime}" if exists else None,
            "exists": exists,
            "mtime": mtime,
            "size_kb": size_kb,
        })
    return res


def save_and_build_html(data_obj):
    with open(A("data.json"), "w", encoding="utf8") as f:
        json.dump(data_obj, f, ensure_ascii=False, indent=2)
    os.makedirs(A("html"), exist_ok=True)
    pages = build.build_pages(A("data.json"))
    for name, htm in pages.items():
        with open(A("html", name + ".html"), "w", encoding="utf8") as f:
            f.write(htm)
    return pages


class StudioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[Studio] {self.address_string()} - {fmt % args}\n")

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def send_json(self, payload, status=200):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(body.decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.path = "/studio.html"
            return super().do_GET()

        if parsed.path == "/api/state":
            data = json.load(open(A("data.json"), encoding="utf8"))
            fy = str(data.get("fiscal_year", "2570"))
            return self.send_json({
                "ok": True,
                "data": data,
                "provinces": PROVINCE_LIST,
                "outputs": list_outputs(fy),
            })

        if parsed.path == "/api/download-zip":
            data = json.load(open(A("data.json"), encoding="utf8"))
            fy = str(data.get("fiscal_year", "2570"))
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for item in list_outputs(fy):
                    p = A("output", item["name"] + ".png")
                    if os.path.isfile(p):
                        zf.write(p, arcname=item["name"] + ".png")
            raw = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="MWA_Posters_FY{fy}.zip"')
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/preview":
                body = self.read_json()
                data_obj = body.get("data")
                if not data_obj:
                    return self.send_json({"ok": False, "error": "ไม่พบข้อมูล data"}, 400)
                save_and_build_html(data_obj)
                fy = str(data_obj.get("fiscal_year", "2570"))
                return self.send_json({
                    "ok": True,
                    "outputs": list_outputs(fy),
                })

            if parsed.path == "/api/generate":
                t0 = time.time()
                body = self.read_json()
                data_obj = body.get("data")
                only = body.get("only")
                if data_obj:
                    pages = save_and_build_html(data_obj)
                else:
                    data_obj = json.load(open(A("data.json"), encoding="utf8"))
                    pages = save_and_build_html(data_obj)
                rendered = build.render_pngs(pages, only=only)
                fy = str(data_obj.get("fiscal_year", "2570"))
                return self.send_json({
                    "ok": True,
                    "rendered": [os.path.basename(x) for x in rendered],
                    "elapsed_sec": round(time.time() - t0, 2),
                    "outputs": list_outputs(fy),
                })

            if parsed.path == "/api/reset":
                src = A("data.default.json") if os.path.isfile(A("data.default.json")) else A("data.json")
                data_obj = json.load(open(src, encoding="utf8"))
                save_and_build_html(data_obj)
                fy = str(data_obj.get("fiscal_year", "2570"))
                return self.send_json({
                    "ok": True,
                    "data": data_obj,
                    "outputs": list_outputs(fy),
                })

            if parsed.path == "/api/open-folder":
                subprocess.Popen(["open", A("output")])
                return self.send_json({"ok": True})

            return self.send_json({"ok": False, "error": "Unknown endpoint"}, 404)
        except Exception as e:
            return self.send_json({"ok": False, "error": str(e)}, 500)


def main():
    os.makedirs(A("html"), exist_ok=True)
    os.makedirs(A("output"), exist_ok=True)
    # Ensure HTML previews exist on startup
    try:
        d = json.load(open(A("data.json"), encoding="utf8"))
        save_and_build_html(d)
    except Exception as e:
        print("Warning building initial HTML:", e)

    server = ThreadingHTTPServer(("127.0.0.1", PORT), StudioHandler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"============================================================")
    print(f" 🚀 MWA Poster Studio พร้อมใช้งานที่: {url}")
    print(f"============================================================")
    if "--open" in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nปิดเซิร์ฟเวอร์เรียบร้อย")


if __name__ == "__main__":
    main()
