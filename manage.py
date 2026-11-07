#!/usr/bin/env python3
"""CLI สำหรับดู/แก้ไขจังหวัดและสั่งสร้างรูปโปสเตอร์จาก Terminal
ตัวอย่างการใช้งาน:
  python3 manage.py list
  python3 manage.py set --id 1 --province เชียงใหม่ --build
  python3 manage.py set --course 5 --run 1 --province อุบลราชธานี --month 11 --build
  python3 manage.py build
"""
import argparse
import json
import os
import sys

import build
from provinces import TH2EN

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(ROOT, "data.json")


def load_data():
    return json.load(open(DATA_FILE, encoding="utf8"))


def save_data(d):
    with open(DATA_FILE, "w", encoding="utf8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def cmd_list(args):
    d = load_data()
    courses = {c["no"]: c for c in d["courses"]}
    print(f"=== แผนจัดอบรมประปาสัญจร ปีงบประมาณ {d['fiscal_year']} ({len(d['sessions'])} รุ่น) ===")
    print(f"{'ID':>3} | {'ไตรมาส':<6} | {'เดือน/ปี':<10} | {'หลักสูตร':<8} | {'รุ่น':<4} | {'จังหวัด':<16} | ชื่อหลักสูตรย่อ")
    print("-" * 88)
    for idx, s in enumerate(d["sessions"], 1):
        q = build.quarter_of(s["month"])
        m_str = f"{build.M_ABBR[s['month']]} {s['year']}"
        c = courses.get(s["course"], {})
        print(f"{idx:>3} | Q{q:<5} | {m_str:<10} | #{s['course']:<7} | {s['run']:<4} | {s['province']:<16} | {c.get('short','')}")


def cmd_set(args):
    d = load_data()
    target = None
    if args.id is not None:
        idx = args.id - 1
        if not (0 <= idx < len(d["sessions"])):
            sys.exit(f"ไม่พบลำดับ ID {args.id} (มีทั้งหมด {len(d['sessions'])} รุ่น)")
        target = d["sessions"][idx]
    elif args.course is not None:
        run_no = args.run or 1
        for s in d["sessions"]:
            if int(s["course"]) == args.course and int(s["run"]) == run_no:
                target = s
                break
        if not target:
            sys.exit(f"ไม่พบหลักสูตร #{args.course} รุ่นที่ {run_no}")
    else:
        sys.exit("กรุณาระบุ --id <ลำดับรุ่น> หรือ --course <เลขหลักสูตร> [--run <รุ่นที่>]")

    if args.province:
        if args.province not in TH2EN:
            sys.exit(f"ไม่พบจังหวัด '{args.province}' ในระบบ (ตรวจสอบตัวสะกดภาษาไทย)")
        old_p = target["province"]
        target["province"] = args.province
        print(f"✓ เปลี่ยนจังหวัด: {old_p} -> {args.province}")

    if args.month:
        target["month"] = args.month
        fy = int(d.get("fiscal_year", 2570))
        target["year"] = (fy - 1) if args.month in (10, 11, 12) else fy
        print(f"✓ เปลี่ยนเดือนเป็น: {build.M_FULL[args.month]} {target['year']} (Q{build.quarter_of(args.month)})")

    if args.label:
        if args.label == "auto":
            target.pop("label", None)
        else:
            target["label"] = args.label
        print(f"✓ ตั้งตำแหน่งป้ายชื่อ: {args.label}")

    save_data(d)
    if args.build:
        cmd_build(args)


def cmd_build(args):
    pages = build.build_pages(DATA_FILE)
    os.makedirs(os.path.join(ROOT, "html"), exist_ok=True)
    for name, htm in pages.items():
        with open(os.path.join(ROOT, "html", name + ".html"), "w", encoding="utf8") as f:
            f.write(htm)
    print("✓ อัปเดตไฟล์ HTML ทั้ง 5 หน้าเรียบร้อย")
    if not getattr(args, "no_png", False):
        build.render_pngs(pages, only=getattr(args, "only", None))


def main():
    p = argparse.ArgumentParser(description="จัดการข้อมูลจังหวัดและสั่งสร้างรูปโปสเตอร์ประปาสัญจร")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list", help="แสดงรายการรุ่นอบรมและจังหวัดทั้งหมด")

    ps = sub.add_parser("set", help="แก้ไขจังหวัดหรือเดือนของรุ่นอบรม")
    ps.add_argument("--id", type=int, help="ลำดับรุ่นอบรม (ดูจากคำสั่ง list เริ่มที่ 1)")
    ps.add_argument("--course", type=int, help="หมายเลขหลักสูตร (1-7)")
    ps.add_argument("--run", type=int, help="รุ่นที่ของหลักสูตรนั้น (เช่น 1, 2, 3)")
    ps.add_argument("--province", type=str, help="ชื่อจังหวัดภาษาไทย เช่น เชียงใหม่, ขอนแก่น, ภูเก็ต")
    ps.add_argument("--month", type=int, choices=range(1, 13), help="เลขเดือน (1-12)")
    ps.add_argument("--label", choices=["auto", "left", "right", "top", "bottom"], help="ตำแหน่งป้ายบนแผนที่")
    ps.add_argument("--build", action="store_true", help="สั่งสร้างรูป PNG ใหม่ทันทีหลังแก้ไข")
    ps.add_argument("--only", type=str, help="ระบุชื่อภาพที่ต้องการสร้างเฉพาะหน้า เช่น 01_Q1")

    pb = sub.add_parser("build", help="สั่งสร้างไฟล์ HTML และรูป PNG ทั้ง 5 ภาพ")
    pb.add_argument("--no-png", action="store_true", help="สร้างเฉพาะ HTML ไม่สร้าง PNG")
    pb.add_argument("--only", type=str, help="สร้างเฉพาะภาพที่ระบุ เช่น 00_overview หรือ 02_Q2")

    args = p.parse_args()
    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "set":
        cmd_set(args)
    elif args.cmd == "build":
        cmd_build(args)
    else:
        cmd_list(args)


if __name__ == "__main__":
    main()
