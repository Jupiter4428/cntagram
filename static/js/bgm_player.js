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

    const playlist = [
        {
            title: "เบาเบา",
            artist: "Singular",
            src: "/audio/singular_bao_bao.mp3"
        },
        {
            title: "ลอง",
            artist: "Singular",
            src: "/audio/singular_long.mp3"
        },
        {
            title: "ให้ฉันดูแลเธอ",
            artist: "แหนม รณเดช",
            src: "/audio/hai_chan_doolae_ter.mp3"
        },
        {
            title: "สาบานได้เลย",
            artist: "ฮันเตอร์",
            src: "/audio/saban_dai_loei.mp3"
        },
        {
            title: "วิชามาร",
            artist: "เท่ห์ อุเทน พรหมมินทร์",
            src: "/audio/wicha_marn.mp3"
        },
        {
            title: "TSE Cyber Campus (8-Bit)",
            artist: "CNTAGRAM BGM",
            src: "/audio/tse_cyber_campus.wav"
        },
        {
            title: "Midnight Study (Lofi)",
            artist: "Lofi Engineer",
            src: "/audio/midnight_study_lofi.wav"
        },
        {
            title: "Final Exam Rush (Chiptune)",
            artist: "Retro Chiptune",
            src: "/audio/final_exam_rush.wav"
        }
    ];

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
            btn.innerHTML = `<span aria-hidden="true">${index === currentTrackIndex ? "▶" : "♫"}</span> ${index + 1}. ${track.title}`;
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
        if (titleDisplay) titleDisplay.textContent = `[0${currentTrackIndex + 1}] ${track.title}`;
        if (statusDisplay) statusDisplay.textContent = track.artist;
        renderTracklist();

        if (playImmediately) {
            audio.play().then(() => {
                updatePlayState(true);
            }).catch(() => {
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

    // Play / Pause toggle
    if (playPauseBtn) {
        playPauseBtn.addEventListener("click", () => {
            if (audio.paused) {
                audio.play().then(() => {
                    updatePlayState(true);
                }).catch((err) => {
                    console.warn("Playback error:", err);
                });
            } else {
                audio.pause();
                updatePlayState(false);
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
        const savedVolume = localStorage.getItem("cntagram_bgm_volume");
        if (savedVolume !== null) {
            audio.volume = parseFloat(savedVolume);
            volumeSlider.value = audio.volume;
        } else {
            audio.volume = 0.7;
        }

        volumeSlider.addEventListener("input", (e) => {
            audio.volume = parseFloat(e.target.value);
            audio.muted = false;
            localStorage.setItem("cntagram_bgm_volume", audio.volume.toString());
            updateMuteButton();
        });
    }

    function updateMuteButton() {
        if (!muteBtn) return;
        if (audio.muted || audio.volume === 0) {
            muteBtn.innerHTML = "🔇";
            muteBtn.title = "Unmute (เปิดเสียง)";
        } else {
            muteBtn.innerHTML = "🔊";
            muteBtn.title = "Mute (ปิดเสียง)";
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

