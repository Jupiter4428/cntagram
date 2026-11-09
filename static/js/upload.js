(() => {
  const form = document.getElementById("upload-form");
  if (!form) return;

  const batchSelect = document.getElementById("id_batch");
  const courseSelect = document.getElementById("id_batch_course");
  const courseSearch = document.getElementById("id_course_search");
  const courseToggle = document.getElementById("id_course_toggle");
  const courseMenu = document.getElementById("id_batch_course_menu");
  const comboboxContainer = document.getElementById("batch-course-combobox");
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

  // State สำหรับวิชาที่ query มาในรุ่น
  let currentCourses = [];
  let activeIndex = -1;

  const closeMenu = () => {
    if (!courseMenu) return;
    courseMenu.hidden = true;
    if (courseSearch) courseSearch.setAttribute("aria-expanded", "false");
    if (courseToggle) courseToggle.setAttribute("aria-expanded", "false");
    activeIndex = -1;
  };

  const openMenu = () => {
    if (!courseMenu || !courseSearch || courseSearch.disabled) return;
    renderOptions(courseSearch.value.trim());
    courseMenu.hidden = false;
    courseSearch.setAttribute("aria-expanded", "true");
    if (courseToggle) courseToggle.setAttribute("aria-expanded", "true");
  };

  const renderOptions = (filterQuery = "") => {
    if (!courseMenu) return;
    courseMenu.replaceChildren();
    activeIndex = -1;

    const query = filterQuery.toLowerCase();
    const filtered = currentCourses.filter((course) => {
      if (!query) return true;
      const text = `${course.code} ${course.name}`.toLowerCase();
      return text.includes(query);
    });

    if (filtered.length === 0) {
      const li = document.createElement("li");
      li.className = "retro-combobox__item retro-combobox__item--empty";
      li.textContent = currentCourses.length === 0 ? "ไม่มีวิชาในรุ่นนี้" : "ไม่พบวิชาที่ค้นหา";
      courseMenu.append(li);
      return;
    }

    filtered.forEach((course) => {
      const li = document.createElement("li");
      li.className = "retro-combobox__item";
      li.setAttribute("role", "option");
      li.setAttribute("data-id", course.id);
      li.setAttribute("data-label", `${course.code} ${course.name}`);
      li.textContent = `${course.code} ${course.name}`;
      if (String(courseSelect.value) === String(course.id)) {
        li.classList.add("is-selected");
        li.setAttribute("aria-selected", "true");
      }

      li.addEventListener("mousedown", (e) => {
        e.preventDefault();
        selectCourse(course);
        closeMenu();
      });

      courseMenu.append(li);
    });
  };

  const selectCourse = (course) => {
    courseSelect.value = course ? course.id : "";
    if (courseSearch) {
      courseSearch.value = course ? `${course.code} ${course.name}` : "";
    }
    validateCourseInput();
  };

  // ตรวจสอบความถูกต้องของค่าที่พิมพ์ (Validation logic)
  const validateCourseInput = () => {
    if (!courseSearch) return;
    const val = courseSearch.value.trim();
    if (!val) {
      courseSelect.value = "";
      courseSearch.setCustomValidity("กรุณาเลือกวิชา");
      return;
    }

    const upper = val.toUpperCase();
    const matched = currentCourses.find(
      (c) =>
        c.code.toUpperCase() === upper ||
        `${c.code} ${c.name}`.toLowerCase() === val.toLowerCase()
    );

    if (matched) {
      courseSelect.value = matched.id;
      courseSearch.setCustomValidity("");
    } else {
      courseSelect.value = "";
      courseSearch.setCustomValidity("วิชาที่เลือกไม่ถูกต้อง หรือไม่มีในรุ่นนี้");
    }
  };

  if (courseSearch && courseToggle && courseMenu) {
    courseSearch.addEventListener("focus", () => {
      openMenu();
    });

    courseSearch.addEventListener("input", () => {
      openMenu();
      validateCourseInput();
    });

    courseSearch.addEventListener("change", () => {
      validateCourseInput();
    });

    courseSearch.addEventListener("blur", () => {
      validateCourseInput();
      closeMenu();
    });

    courseToggle.addEventListener("click", (e) => {
      e.preventDefault();
      if (courseMenu.hidden) {
        courseSearch.focus();
        openMenu();
      } else {
        closeMenu();
      }
    });

    // Keyboard navigation
    courseSearch.addEventListener("keydown", (e) => {
      const items = Array.from(courseMenu.querySelectorAll(".retro-combobox__item:not(.retro-combobox__item--empty)"));
      if (courseMenu.hidden && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
        openMenu();
        return;
      }

      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (items.length === 0) return;
        activeIndex = (activeIndex + 1) % items.length;
        items.forEach((it, idx) => it.classList.toggle("is-active", idx === activeIndex));
        items[activeIndex].scrollIntoView({ block: "nearest" });
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (items.length === 0) return;
        activeIndex = (activeIndex - 1 + items.length) % items.length;
        items.forEach((it, idx) => it.classList.toggle("is-active", idx === activeIndex));
        items[activeIndex].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter") {
        if (!courseMenu.hidden && activeIndex >= 0 && items[activeIndex]) {
          e.preventDefault();
          const targetId = items[activeIndex].dataset.id;
          const course = currentCourses.find((c) => String(c.id) === String(targetId));
          if (course) selectCourse(course);
          closeMenu();
        }
      } else if (e.key === "Escape") {
        closeMenu();
      }
    });

    document.addEventListener("click", (e) => {
      if (comboboxContainer && !comboboxContainer.contains(e.target)) {
        closeMenu();
      }
    });
  }

  // 1) Cascading dropdown: เลือกรุ่น -> ดึงวิชา
  let requestId = 0;
  batchSelect.addEventListener("change", async () => {
    const current = ++requestId;
    courseSelect.disabled = true;
    courseSelect.value = "";
    if (courseSearch) {
      courseSearch.disabled = true;
      courseSearch.value = "";
      courseSearch.placeholder = "เลือกรุ่นก่อน";
      courseSearch.setCustomValidity("");
    }
    if (courseToggle) courseToggle.disabled = true;
    courseStatus.textContent = "";
    courseSelect.replaceChildren(new Option("เลือกรุ่นก่อน", ""));
    currentCourses = [];
    closeMenu();

    if (!batchSelect.value) return;

    if (courseSearch) courseSearch.placeholder = "กำลังโหลดวิชา...";
    courseSelect.replaceChildren(new Option("กำลังโหลดวิชา...", ""));
    const url = batchSelect.dataset.coursesUrl.replace("/0/", `/${encodeURIComponent(batchSelect.value)}/`);
    try {
      const response = await fetch(url, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(String(response.status));
      const { courses } = await response.json();
      if (current !== requestId) return;

      currentCourses = courses;
      courseSelect.replaceChildren(new Option(courses.length ? "เลือกวิชา" : "ไม่มีวิชาในรุ่นนี้", ""));
      for (const course of courses) {
        courseSelect.add(new Option(`${course.code} ${course.name}`, course.id));
      }
      const hasCourses = courses.length > 0;
      courseSelect.disabled = !hasCourses;
      if (courseSearch) {
        courseSearch.disabled = !hasCourses;
        courseSearch.placeholder = hasCourses ? "เลือกวิชา หรือพิมพ์ค้นหา เช่น CN200" : "ไม่มีวิชาในรุ่นนี้";
      }
      if (courseToggle) courseToggle.disabled = !hasCourses;
    } catch {
      if (current !== requestId) return;
      courseSelect.replaceChildren(new Option("โหลดวิชาไม่สำเร็จ", ""));
      if (courseSearch) courseSearch.placeholder = "โหลดวิชาไม่สำเร็จ";
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