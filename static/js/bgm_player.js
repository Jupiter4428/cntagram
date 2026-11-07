/**
 * CNTAGRAM 2000s Retro BGM Player (Winamp / Hi5 Vibe)
 * Supports full playback, seekable progress bar, playlist tracklist, and track switching.
 */
document.addEventListener("DOMContentLoaded", () => {
    const audio = document.getElementById("bgm-audio");
    if (!audio) return;

    const playPauseBtn = document.getElementById("bgm-play-pause");
    const prevBtn = document.getElementById("bgm-prev");
    const nextBtn = document.getElementById("bgm-next");
    const toggleListBtn = document.getElementById("bgm-toggle-list");
    const muteBtn = document.getElementById("bgm-mute");
    const volumeSlider = document.getElementById("bgm-volume");
    const seekbar = document.getElementById("bgm-seekbar");
    const timeDisplay = document.getElementById("bgm-time-display");
    const titleDisplay = document.getElementById("bgm-track-title");
    const statusDisplay = document.getElementById("bgm-track-status");
    const disc = document.getElementById("bgm-disc");
    const tracklistContainer = document.getElementById("bgm-tracklist");

    const playlist = Array.from(document.querySelectorAll("#bgm-playlist li"), (li) => ({
        title: li.textContent.trim(),
        artist: li.dataset.artist,
        src: li.dataset.src,
    }));

    let currentTrackIndex = 0;
    let isSeeking = false;

    function formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return "00:00";
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    }

    function renderTracklist() {
        if (!tracklistContainer) return;
        tracklistContainer.innerHTML = "";
        playlist.forEach((track, index) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = `music-widget__track-item ${index === currentTrackIndex ? "is-active" : ""}`;

            const iconSpan = document.createElement("span");
            iconSpan.setAttribute("aria-hidden", "true");
            iconSpan.textContent = index === currentTrackIndex ? "▶" : "♫";

            btn.appendChild(iconSpan);
            btn.append(` ${index + 1}. ${track.title}`);
            btn.setAttribute("aria-label", `เล่นเพลง ${track.title}`);
            btn.addEventListener("click", () => {
                selectTrack(index, true);
            });
            tracklistContainer.appendChild(btn);
        });
    }

    function selectTrack(index, playImmediately = false) {
        currentTrackIndex = (index + playlist.length) % playlist.length;
        const track = playlist[currentTrackIndex];
        audio.src = track.src;
        const trackNum = (currentTrackIndex + 1).toString().padStart(2, "0");
        if (titleDisplay) titleDisplay.textContent = `[${trackNum}] ${track.title}`;
        if (statusDisplay) statusDisplay.textContent = track.artist;
        renderTracklist();

        if (playImmediately) {
            audio.play().catch(() => {
                updatePlayState(false);
            });
        } else {
            updatePlayState(false);
        }
    }

    function updatePlayState(isPlaying) {
        if (isPlaying) {
            if (playPauseBtn) {
                playPauseBtn.innerHTML = "⏸";
                playPauseBtn.setAttribute("aria-label", "หยุดเพลง");
                playPauseBtn.title = "Pause (หยุดเพลง)";
            }
            if (disc) disc.classList.add("is-playing");
            if (statusDisplay) statusDisplay.textContent = `PLAYING · ${playlist[currentTrackIndex].artist}`;
        } else {
            if (playPauseBtn) {
                playPauseBtn.innerHTML = "▶";
                playPauseBtn.setAttribute("aria-label", "เล่นเพลง");
                playPauseBtn.title = "Play (เล่นเพลง)";
            }
            if (disc) disc.classList.remove("is-playing");
            if (statusDisplay) statusDisplay.textContent = `PAUSED · ${playlist[currentTrackIndex].artist}`;
        }
    }

    // Keep play/pause button and spinning disc in sync with actual audio playback state
    audio.addEventListener("play", () => updatePlayState(true));
    audio.addEventListener("pause", () => updatePlayState(false));

    // Play / Pause toggle
    if (playPauseBtn) {
        playPauseBtn.addEventListener("click", () => {
            if (audio.paused) {
                audio.play().catch((err) => {
                    console.warn("Playback error:", err);
                    updatePlayState(false);
                });
            } else {
                audio.pause();
            }
        });
    }

    // Prev / Next buttons
    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            selectTrack(currentTrackIndex - 1, !audio.paused);
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            selectTrack(currentTrackIndex + 1, !audio.paused);
        });
    }

    // Toggle tracklist visibility
    if (toggleListBtn && tracklistContainer) {
        toggleListBtn.addEventListener("click", () => {
            const isHidden = tracklistContainer.style.display === "none";
            tracklistContainer.style.display = isHidden ? "flex" : "none";
            toggleListBtn.classList.toggle("is-active", isHidden);
            toggleListBtn.setAttribute("aria-expanded", isHidden ? "true" : "false");
        });
    }

    // Audio timeupdate -> seekbar & time display
    audio.addEventListener("timeupdate", () => {
        if (!isSeeking && audio.duration) {
            const progressPercent = (audio.currentTime / audio.duration) * 100;
            if (seekbar) seekbar.value = progressPercent;
        }
        if (timeDisplay) {
            timeDisplay.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
        }
    });

    audio.addEventListener("loadedmetadata", () => {
        if (timeDisplay) {
            timeDisplay.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
        }
    });

    audio.addEventListener("seeking", () => {
        isSeeking = true;
    });

    audio.addEventListener("seeked", () => {
        isSeeking = false;
        if (audio.duration && timeDisplay) {
            timeDisplay.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
        }
    });

    // Seek bar interaction
    if (seekbar) {
        const applySeek = () => {
            if (audio.duration) {
                const targetTime = (parseFloat(seekbar.value) / 100) * audio.duration;
                audio.currentTime = targetTime;
                if (timeDisplay) {
                    timeDisplay.textContent = `${formatTime(targetTime)} / ${formatTime(audio.duration)}`;
                }
            }
        };

        seekbar.addEventListener("input", () => {
            isSeeking = true;
            if (audio.duration && timeDisplay) {
                const targetTime = (parseFloat(seekbar.value) / 100) * audio.duration;
                timeDisplay.textContent = `${formatTime(targetTime)} / ${formatTime(audio.duration)}`;
            }
        });

        seekbar.addEventListener("change", () => {
            applySeek();
            setTimeout(() => { isSeeking = false; }, 300);
        });
    }

    // Volume & Mute control
    if (volumeSlider) {
        // Restore saved volume
        let savedVolume = NaN;
        try {
            savedVolume = parseFloat(localStorage.getItem("cntagram_bgm_volume"));
        } catch (e) {
            // storage blocked (private mode / disabled): fall back to default
        }
        audio.volume = Number.isFinite(savedVolume) ? Math.min(Math.max(savedVolume, 0), 1) : 0.7;
        volumeSlider.value = audio.volume;

        volumeSlider.addEventListener("input", (e) => {
            audio.volume = parseFloat(e.target.value);
            audio.muted = false;
            try {
                localStorage.setItem("cntagram_bgm_volume", audio.volume.toString());
            } catch (e) {
                // storage blocked: volume still applies for this page
            }
            updateMuteButton();
        });
    }

    function updateMuteButton() {
        if (!muteBtn) return;
        if (audio.muted || audio.volume === 0) {
            muteBtn.innerHTML = "🔇";
            muteBtn.title = "Unmute (เปิดเสียง)";
            muteBtn.setAttribute("aria-label", "เปิดเสียง");
        } else {
            muteBtn.innerHTML = "🔊";
            muteBtn.title = "Mute (ปิดเสียง)";
            muteBtn.setAttribute("aria-label", "ปิดเสียง");
        }
    }

    if (muteBtn) {
        muteBtn.addEventListener("click", () => {
            audio.muted = !audio.muted;
            updateMuteButton();
        });
    }

    // Auto next track when current ends
    audio.addEventListener("ended", () => {
        selectTrack(currentTrackIndex + 1, true);
    });

    // Initialize track
    selectTrack(0, false);
});

