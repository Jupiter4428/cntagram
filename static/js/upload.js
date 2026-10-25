// static/js/upload.js
document.addEventListener("DOMContentLoaded", function () {
  const batchSelect = document.getElementById("id_batch");
  const courseSelect = document.getElementById("id_batch_course");
  const docTypeSelect = document.querySelector('[name="doc_type"]');
  const examPeriodWrapper = document.getElementById("wrapper_exam_period");
  const academicYearWrapper = document.getElementById("wrapper_academic_year");
  const fileInput = document.querySelector('input[type="file"]');
  const fileError = document.getElementById("file-client-error");
  const disclaimerCheck = document.getElementById("disclaimerCheck");
  const submitBtn = document.getElementById("submitBtn");

  // 1. Cascading Dropdown: เลือกรุ่น -> โหลดวิชาแบบ AJAX
  if (batchSelect && courseSelect) {
    batchSelect.addEventListener("change", function () {
      const batchId = this.value;
      const baseUrl = batchSelect.getAttribute("data-courses-url");

      if (!batchId) {
        courseSelect.innerHTML = '<option value="">เลือกรุ่นก่อน</option>';
        courseSelect.disabled = true;
        return;
      }

      courseSelect.disabled = true;
      courseSelect.innerHTML = '<option value="">กำลังโหลดวิชา...</option>';

      const fetchUrl = baseUrl.replace(/0\/?$/, batchId + "/");

      fetch(fetchUrl)
        .then((res) => {
          if (!res.ok) throw new Error("Network response was not ok");
          return res.json();
        })
        .then((data) => {
          courseSelect.innerHTML = '<option value="">-- เลือกวิชา --</option>';
          if (data.courses && data.courses.length > 0) {
            data.courses.forEach((c) => {
              const opt = document.createElement("option");
              opt.value = c.id;
              opt.textContent = `${c.code} - ${c.name}`;
              courseSelect.appendChild(opt);
            });
            courseSelect.disabled = false;
          } else {
            courseSelect.innerHTML = '<option value="">ไม่มีวิชาในรุ่นนี้</option>';
          }
        })
        .catch(() => {
          courseSelect.innerHTML = '<option value="">โหลดข้อมูลไม่สำเร็จ</option>';
        });
    });
  }

  // 2. Client-side File Validation: เช็คนามสกุล .pdf และขนาดไม่เกิน 50MB (ตามรูป)
  const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB ตามข้อความในแบบ UI

  if (fileInput) {
    fileInput.addEventListener("change", function () {
      if (fileError) {
        fileError.style.display = "none";
        fileError.textContent = "";
      }

      if (this.files && this.files[0]) {
        const file = this.files[0];
        const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

        if (!isPdf) {
          showError("รับเฉพาะไฟล์ PDF เท่านั้น");
          this.value = "";
          return;
        }

        if (file.size > MAX_FILE_SIZE) {
          showError("ขนาดไฟล์ต้องไม่เกิน 50 MB");
          this.value = "";
          return;
        }
      }
    });
  }

  function showError(msg) {
    if (fileError) {
      fileError.textContent = msg;
      fileError.style.display = "block";
    }
  }

  // 3. Dynamic Fields: แสดง/ซ่อน ช่องช่วงสอบและปีการศึกษา ตามประเภทเอกสาร
  function toggleExamFields() {
    if (!docTypeSelect) return;
    const selectedText = docTypeSelect.options[docTypeSelect.selectedIndex]?.text || "";
    const isExam = selectedText.includes("ข้อสอบ") || docTypeSelect.value.toLowerCase().includes("exam");

    if (examPeriodWrapper) examPeriodWrapper.style.display = isExam ? "" : "none";
    if (academicYearWrapper) academicYearWrapper.style.display = isExam ? "" : "none";
  }

  if (docTypeSelect) {
    docTypeSelect.addEventListener("change", toggleExamFields);
    toggleExamFields();
  }

  // 4. Disclaimer Checkbox: คุมปุ่ม Submit ไม่ให้กดได้จนกว่าจะยอมรับเงื่อนไข
  if (disclaimerCheck && submitBtn) {
    disclaimerCheck.addEventListener("change", function () {
      submitBtn.disabled = !this.checked;
    });
  }
});