/**
 * CNTAGRAM Interactive Home Widgets (AJAX Shoutbox & Weekly Poll)
 * Handles smooth non-refresh submissions for Shoutbox and Weekly Poll.
 */
document.addEventListener("DOMContentLoaded", () => {
    // ----------------------------------------------------
    // 1. Shoutbox Non-refresh Submission
    // ----------------------------------------------------
    const shoutboxForm = document.querySelector(".shoutbox-controls");
    const shoutboxLog = document.querySelector(".shoutbox-log");

    if (shoutboxLog) {
        // Auto scroll to bottom of log on load
        shoutboxLog.scrollTop = shoutboxLog.scrollHeight;
    }

    if (shoutboxForm && shoutboxLog) {
        shoutboxForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const input = shoutboxForm.querySelector('input[name="message"]');
            const submitBtn = shoutboxForm.querySelector('button[type="submit"]');
            const message = (input ? input.value : "").trim();

            if (!message) return;

            const formData = new FormData(shoutboxForm);
            const actionUrl = shoutboxForm.getAttribute("action");

            if (submitBtn) submitBtn.disabled = true;

            try {
                const response = await fetch(actionUrl, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }

                const data = await response.json();
                if (data.ok && Array.isArray(data.messages)) {
                    shoutboxLog.innerHTML = "";
                    data.messages.forEach((item) => {
                        const p = document.createElement("p");
                        const b = document.createElement("b");
                        b.textContent = `${item.author}: `;
                        p.appendChild(b);
                        p.appendChild(document.createTextNode(item.text));
                        shoutboxLog.appendChild(p);
                    });
                    if (input) {
                        input.value = "";
                        input.focus();
                    }
                    shoutboxLog.scrollTop = shoutboxLog.scrollHeight;
                } else {
                    shoutboxForm.submit();
                }
            } catch (err) {
                console.error("Shoutbox AJAX post failed, submitting normally:", err);
                shoutboxForm.submit();
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }

    // ----------------------------------------------------
    // 2. Weekly Poll Non-refresh Submission
    // ----------------------------------------------------
    const pollWidget = document.querySelector(".poll-widget");
    if (!pollWidget) return;

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text || "";
        return div.innerHTML;
    }

    function renderPollResults(data) {
        const pollBody = pollWidget.querySelector(".retro-widget__body");
        const statusBadge = pollWidget.querySelector(".retro-widget__titlebar small");
        if (statusBadge) {
            statusBadge.textContent = "โหวตแล้ว";
        }

        if (!pollBody) return;

        const poll = (data && data.poll) ? data.poll : data;
        const question = (poll && poll.question) ? poll.question : "";
        const questionHtml = `<p class="mb-1"><strong>${escapeHtml(question)}</strong></p>`;

        if (data && data.html) {
            pollBody.innerHTML = questionHtml + data.html;
            return;
        }

        let resultsHtml = questionHtml;
        resultsHtml += `<div class="poll-results" aria-label="ผลโหวตล่าสุด">`;

        if (poll && Array.isArray(poll.choices)) {
            poll.choices.forEach((choice) => {
                resultsHtml += `
                    <div class="poll-result-row">
                        <div class="poll-result-label">
                            <span>${escapeHtml(choice.label)}</span>
                            <b>${choice.percent}% (${choice.votes})</b>
                        </div>
                        <div class="poll-bar-wrap">
                            <div class="poll-bar-fill" style="width: ${choice.percent}%;"></div>
                        </div>
                    </div>
                `;
            });
        }

        const total = (poll && poll.total !== undefined) ? poll.total : 0;
        resultsHtml += `</div>`;
        resultsHtml += `<p class="demo-note mb-1 text-center">ผลโหวตทั้งหมด ${total} เสียง</p>`;
        resultsHtml += `<a href="?poll_view=form" class="chrome-button chrome-button--quiet w-100 text-center d-block">ดูตัวเลือก / โหวตใหม่</a>`;

        pollBody.innerHTML = resultsHtml;
    }

    const pollForm = pollWidget.querySelector(".poll-form");
    if (pollForm) {
        pollForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(pollForm);
            const actionUrl = pollForm.getAttribute("action");
            const submitBtn = pollForm.querySelector('button[type="submit"]');

            if (submitBtn) submitBtn.disabled = true;

            try {
                const response = await fetch(actionUrl, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }

                const data = await response.json();
                if (data.ok && data.poll) {
                    renderPollResults(data);
                } else {
                    pollForm.submit();
                }
            } catch (err) {
                console.error("Poll AJAX vote failed, submitting normally:", err);
                pollForm.submit();
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }
});
