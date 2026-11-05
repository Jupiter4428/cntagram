(() => {
  const form = document.getElementById("upload-form");
  if (!form) return;

  const batchSelect = document.getElementById("id_batch");
  const courseSelect = document.getElementById("id_batch_course");
  const courseStatus = document.getElementById("course-status");
  const docTypeSelect = document.getElementById("id_doc_type");
  const examFields = document.getElementById("exam-fields");
  const examPeriod = document.getElementById("id_exam_period");
  const examYear = document.getElementById("id_exam_year_be");
  const fileInput = document.getElementById("id_file");
  const fileError = document.getElementById("file-error");
  const disclaimer = document.getElementById("id_disclaimer");
  const submitButton = document.getElementById("upload-submit");
  const maxMb = Number(form.dataset.maxMb || "50");

  // 1) Cascading dropdown: เลือกรุ่น -> ดึงวิชา
  let requestId = 0;
  batchSelect.addEventListener("change", async () => {
    const current = ++requestId;
    courseSelect.disabled = true;
    courseStatus.textContent = "";
    courseSelect.replaceChildren(new Option("เลือกรุ่นก่อน", ""));

    if (!batchSelect.value) return;

    courseSelect.replaceChildren(new Option("กำลังโหลดวิชา...", ""));
    const url = batchSelect.dataset.coursesUrl.replace("/0/", `/${encodeURIComponent(batchSelect.value)}/`);
    try {
      const response = await fetch(url, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(String(response.status));
      const { courses } = await response.json();
      if (current !== requestId) return;
      courseSelect.replaceChildren(new Option(courses.length ? "เลือกวิชา" : "ไม่มีวิชาในรุ่นนี้", ""));
      for (const course of courses) {
        courseSelect.add(new Option(`${course.code} ${course.name}`, course.id));
      }
      courseSelect.disabled = courses.length === 0;
    } catch {
      if (current !== requestId) return;
      courseSelect.replaceChildren(new Option("โหลดวิชาไม่สำเร็จ", ""));
      courseStatus.textContent = "โหลดรายวิชาไม่สำเร็จ ลองเลือกรุ่นอีกครั้ง";
    }
  });

  // 2) แสดง/ซ่อนช่วงสอบ + ปี พ.ศ. ตามประเภทเอกสาร (ตรวจ data-vault === "exam")
  const syncExamFields = () => {
    const option = docTypeSelect.selectedOptions[0];
    const isExam = Boolean(option) && option.dataset.vault === "exam";
    examFields.hidden = !isExam;
    examPeriod.required = isExam;
    examYear.required = isExam;
    if (!isExam) {
      examPeriod.value = "";
      examYear.value = "";
    }
  };
  docTypeSelect.addEventListener("change", syncExamFields);
  syncExamFields();

  // 3) เช็คชนิดและขนาดไฟล์เบื้องต้น
  const showFileError = (message) => {
    fileError.replaceChildren();
    if (message) {
      const item = document.createElement("li");
      item.textContent = message;
      fileError.append(item);
    }
    fileError.hidden = !message;
    fileInput.setAttribute("aria-invalid", message ? "true" : "false");
  };

  fileInput.addEventListener("change", () => {
    showFileError("");
    const file = fileInput.files[0];
    if (!file) return;
    const isPdf = file.name.toLowerCase().endsWith(".pdf") && (file.type === "" || file.type === "application/pdf");
    if (!isPdf) {
      showFileError("รับเฉพาะไฟล์ PDF เท่านั้น");
    } else if (file.size > maxMb * 1024 * 1024) {
      showFileError(`ไฟล์ใหญ่เกินไป (สูงสุด ${maxMb} MB)`);
    } else if (file.size === 0) {
      showFileError("ไฟล์ว่างเปล่า");
    }
    if (!fileError.hidden) fileInput.value = "";
  });

  // 4) Disclaimer ควบคุมปุ่ม Submit
  const syncSubmit = () => {
    submitButton.disabled = !disclaimer.checked;
  };
  disclaimer.addEventListener("change", syncSubmit);
  syncSubmit();

  // ตรวจสอบความถูกต้องก่อน submit
  form.addEventListener("submit", (event) => {
    if (!form.checkValidity()) {
      event.preventDefault();
      form.reportValidity();
    }
  });
})();