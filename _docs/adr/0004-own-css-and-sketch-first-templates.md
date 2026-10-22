# ADR 0004: ใช้ CSS ของทีมแทน Bootstrap และทำ template แบบวาดเส้นก่อนลงสี

- **Status:** Proposed
- **Date:** 2026-10-23
- **Issue:** #38

## Context
เอกสารเดิมกำหนดให้ UI ใช้ Bootstrap 5 ผ่าน CDN แต่ FE-1 (#38) เขียนธีม Retro Webboard เองใน `static/css/retro.css` ถ้าใช้ทั้งสองอย่างพร้อมกัน style จะตีกัน และต้องคอยเขียนทับค่าของ Bootstrap
lecture ของวิชาไม่ได้กำหนด CSS framework ไว้
งาน frontend ของทุก story ค้างอยู่ เพราะ AC เอางานโครงหน้ากับงานแต่งหน้าตาไว้ด้วยกัน จึงต้องรอธีมเสร็จก่อนทุกครั้ง
ขณะที่ story ต้องเป็น vertical slice ที่มี UI ใช้งานได้จริงเมื่อ Done ([`lecture-notes/05`](../lecture-notes/05-agile-scrum-sprints.md))

## Decision
- ไม่ใช้ Bootstrap ใช้ CSS ของทีม (`retro.css` จาก FE-1) เป็นที่เดียว ถอด Bootstrap CDN ออกจาก `base.html` ใน PR ที่ merge FE-1
- template ทำเป็นสองขั้น
  - **วาดเส้น** ทำไปพร้อมกับฟีเจอร์ใน story นั้น: HTML ที่ใช้ tag ตรงความหมาย ใส่ class ตามความหมาย และพฤติกรรมครบ (error ของฟอร์ม, CSRF, escape, ซ่อนปุ่มที่ไม่มีสิทธิ์, หน้า 403) ไม่ใส่ style
  - **ลงสี** ทำทีหลังใน issue แยก: เขียน CSS ให้ class เหล่านั้นใน `retro.css` โดยแตะ HTML ให้น้อยที่สุด
- กติกาละเอียดอยู่ใน [CONTRIBUTING: Templates](../../CONTRIBUTING.md#templates)

## Alternatives considered
- **ใช้ Bootstrap ต่อแล้วเอา retro ทับ**: ต้องสู้กับ specificity ของ Bootstrap ทุกหน้า และโหลด CSS สองชุด
- **ใช้ Bootstrap อย่างเดียว ทิ้ง retro**: ทิ้งงาน FE-1 ที่เสร็จเกือบหมดแล้ว และหน้าตาไม่ตรงกับธีมที่ทีมเลือก
- **ทำ HTML กับ CSS เสร็จพร้อมกันในแต่ละ story**: story ต้องรอธีม และหลายคนแก้ `retro.css` พร้อมกันจน merge conflict

## Consequences
- story ส่งมอบได้โดยไม่ต้องรอธีม หน้าตาเหมือนกันทั้งระบบเพราะลงสีจากที่เดียว
- template ใน `develop` ที่ใช้ class ของ Bootstrap อยู่ (`home`, `login`, หน้า `catalog/*`, `_navbar`) จะดูเป็นหน้าเปล่าหลังถอด CDN ต้องเปลี่ยน class ให้ตรงความหมายในงานลงสี
- งานลงสีต้องมี issue และ sprint ชัดเจน ไม่อย่างนั้นจะค้างไม่มีคนแต่ง
- ต้องดูแลให้ responsive (~360px) เองโดยไม่มี grid ของ Bootstrap ช่วย
