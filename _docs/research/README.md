# ข้อมูลสำหรับเขียนเล่มรายงานโครงงาน (Research Report) — CNtagram

โฟลเดอร์นี้รวบรวม**วัตถุดิบสำหรับเขียนเล่มรายงาน/เล่มวิจัย** ของโปรเจค แยกไฟล์ตามบทของเล่มมาตรฐาน 5 บท
แต่ละบทมี (1) **ร่างเนื้อหา** ที่เรียบเรียงจากเอกสารในโปรเจคแล้ว (2) **แหล่งข้อมูล** ที่ลิงก์กลับไปยังเอกสารต้นทาง และ (3) **ช่องที่ต้องเติม** เมื่อมีข้อมูลจริงจาก Sprint

> โฟลเดอร์นี้**ไม่ใช่แหล่งความจริงของสเปก** ถ้าข้อมูลขัดกัน ให้ยึดเอกสารต้นทาง ([`requirements.md`](../requirements.md), [`database-design.md`](../database-design.md), [ADR](../adr/), [C4](../architecture/c4.md)) แล้วค่อยแก้ร่างในนี้ตาม

---

## โครงเล่มและไฟล์

| ไฟล์ | ส่วนของเล่ม | สถานะร่าง | แหล่งข้อมูลหลัก |
|---|---|---|---|
| [00-front-matter.md](./00-front-matter.md) | ปก, บทคัดย่อ (ไทย/อังกฤษ), กิตติกรรมประกาศ, สารบัญ | ร่างบทคัดย่อแล้ว รอผลลัพธ์ | ทุกบท |
| [01-introduction.md](./01-introduction.md) | บทที่ 1 บทนำ | ร่างครบ | `requirements.md` §2–4, SRS v1 |
| [02-literature-review.md](./02-literature-review.md) | บทที่ 2 ทฤษฎีและงานที่เกี่ยวข้อง | ร่างทฤษฎีครบ, งานที่เกี่ยวข้องรอค้นเพิ่ม | `lecture-notes/`, ADR |
| [03-methodology.md](./03-methodology.md) | บทที่ 3 วิธีดำเนินงาน (การวิเคราะห์และออกแบบระบบ) | ร่างครบ | `requirements.md`, `database-design.md`, ADR, C4, `CONTRIBUTING.md` |
| [04-results.md](./04-results.md) | บทที่ 4 ผลการดำเนินงาน | **โครง + ตารางรอเติมข้อมูลจริง** | GitHub Project, ผลเทสต์, Retro |
| [05-conclusion.md](./05-conclusion.md) | บทที่ 5 สรุป อภิปรายผล และข้อเสนอแนะ | โครง + ประเด็นอภิปราย | บทที่ 4, Retro |
| [references.md](./references.md) | บรรณานุกรม | ร่างรายการอ้างอิงหลัก | — |
| [appendices.md](./appendices.md) | ภาคผนวก | รายการสิ่งที่ต้องแนบ | `database-design.md`, ADR, README |

## สัญลักษณ์ในร่าง

| สัญลักษณ์ | ความหมาย |
|---|---|
| **[เติม: …]** | ข้อมูลที่ยังไม่มี ต้องเก็บจาก GitHub / การทดสอบ / ทีม |
| **[ตรวจ: …]** | ข้อมูลที่ร่างไว้แล้วแต่ต้องยืนยันกับทีมหรืออาจารย์ก่อนใช้ |
| **[อ้างอิง: X]** | ตำแหน่งที่ต้องใส่การอ้างอิง (รหัส X อยู่ใน [references.md](./references.md)) |
| `รูปที่ 3.x` / `ตารางที่ 3.x` | เลขรูป/ตาราง ตามบท (ดูรายการด้านล่าง) |

---

## ข้อมูลที่ต้องเก็บระหว่างทำโปรเจค (Checklist)

เก็บ**ทันทีเมื่อเกิดขึ้น** ย้อนเก็บทีหลังยากมาก โดยเฉพาะตัวเลข Sprint

**ทุก Sprint**
- [ ] Sprint Goal ที่ตั้งจริง และวันที่เริ่ม/จบ (จาก GitHub Milestone)
- [ ] Story ที่ commit เข้า Sprint และ Story Points (แผน vs เสร็จจริง → Velocity)
- [ ] ภาพ Burndown Chart (capture จาก GitHub Project Insights ก่อนปิด Sprint)
- [ ] ผล Sprint Review: PO รับงานไหน ไม่รับงานไหน เพราะอะไร
- [ ] ผล Retrospective (`_docs/sprintN_retro.md` ตาม CONTRIBUTING) และ Action Items
- [ ] จำนวน PR / commit / issue ที่ปิด (`gh pr list --state merged --search "milestone:..."`)
- [ ] สัดส่วนแต้ม Tech Debt (เป้า ≥ 20% ตั้งแต่ Sprint 2)

**ผลลัพธ์ทางเทคนิค**
- [ ] ภาพหน้าจอทุกหน้าที่เสร็จ (เดสก์ท็อป + มือถือกว้าง ~360px)
- [ ] ผล `python manage.py test` (จำนวนเทสต์, ผ่าน/ไม่ผ่าน) และ `coverage report` (เป้า > 80%)
- [ ] เวลาตอบของหน้าค้นหา (เป้า ~2 วินาที) พร้อมวิธีวัดและขนาดข้อมูลทดสอบ
- [ ] จำนวน query ต่อหน้าที่แสดงรายการ (`assertNumQueries` / Django Debug Toolbar) ก่อน–หลังปรับ
- [ ] ผลตรวจ OWASP Top 10 (Sprint 3)
- [ ] URL / สภาพแวดล้อมที่ deploy จริง (SP-4)

**ผลจากผู้ใช้ (ถ้ามีการทดลองใช้)**
- [ ] จำนวนผู้ทดลองใช้, แบบสอบถามความพึงพอใจ (แนะนำ SUS 10 ข้อ) และข้อเสนอแนะ
- [ ] จำนวนเอกสาร/รายวิชาที่นำเข้าได้ (สัดส่วนรายวิชา CN21–CN25 ที่มีเอกสาร)

---

## รายการรูปและตาราง (วางแผนไว้)

| เลข | ชื่อ | แหล่ง |
|---|---|---|
| รูปที่ 2.1 | วงรอบ Scrum ของทีม | `CONTRIBUTING.md` (mermaid) |
| รูปที่ 3.1 | C4 Level 1 System Context | [`architecture/c4.md`](../architecture/c4.md) |
| รูปที่ 3.2 | C4 Level 2 Container | [`architecture/c4.md`](../architecture/c4.md) |
| รูปที่ 3.3 | ทิศทาง dependency ระหว่าง Django apps | [ADR 0001](../adr/0001-modular-monolith-and-app-boundaries.md) |
| รูปที่ 3.4 | การแยกชั้นโค้ด views → services/selectors → models | [ADR 0002](../adr/0002-service-layer-and-selectors.md) |
| รูปที่ 3.5 | ERD (3NF) | [`database-design.md` §2](../database-design.md#2-erd) |
| รูปที่ 3.6 | Activity/Sequence ของการอัปโหลดและอนุมัติเอกสาร | **[เติม: วาดเมื่อ US-5/US-6 เสร็จ]** |
| รูปที่ 4.x | ภาพหน้าจอระบบ, Burndown Chart แต่ละ Sprint | **[เติม]** |
| ตารางที่ 3.1 | บทบาทผู้ใช้ | `requirements.md` §3 |
| ตารางที่ 3.2 | Epic และ Product Backlog | `requirements.md` §5–6 |
| ตารางที่ 3.3 | การตัดสินใจออกแบบฐานข้อมูล | `database-design.md` §1 |
| ตารางที่ 3.4 | Definition of Ready / Done | `CONTRIBUTING.md` |
| ตารางที่ 4.x | Velocity, ผลเทสต์, ผลวัดประสิทธิภาพ | **[เติม]** |

> แปลง mermaid เป็นรูปสำหรับเล่ม: วางโค้ดใน <https://mermaid.live> แล้ว export เป็น PNG/SVG เก็บไว้ที่ `_docs/research/figures/` ตั้งชื่อตามเลขรูป เช่น `fig-3-5-erd.png`

## ข้อตกลงการเขียน

- ภาษาไทยทางการ ศัพท์เทคนิคใส่ภาษาอังกฤษในวงเล็บครั้งแรกที่ใช้ เช่น "สถาปัตยกรรมแบบโมโนลิทเชิงโมดูล (Modular Monolith)"
- อ้างอิงรูปแบบ **[ตรวจ: APA 7 หรือ IEEE ตามที่ภาค/อาจารย์กำหนด]** ร่างในนี้ใช้รหัสอ้างอิงชั่วคราว เช่น [อ้างอิง: SCRUM2020]
- ห้ามคัดลอกเนื้อหาจาก lecture notes ทั้งย่อหน้า ให้เรียบเรียงใหม่และอ้างอิงแหล่งต้นทาง
- ถ้าใช้ AI ช่วยเรียบเรียง ต้องตรวจข้อเท็จจริงกับโค้ดและเอกสารต้นทางทุกครั้ง (กติกาเดียวกับโค้ดใน `CONTRIBUTING.md`)
