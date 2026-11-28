"""Tactical 60fps JS Radar + 360-Degree Voice-Reactive Holographic Spectrum & Ripples (CCv2)."""

from __future__ import annotations

import streamlit as st

_RADAR_HTML = """
<div class="j-tactical-stage" id="j-stage">
  <div class="j-radar-wrap" id="j-wrap">
    <canvas id="j-radar-canvas"></canvas>
    <div class="j-face-layer" id="j-face-layer">
      <img id="j-face-img" alt="JARVIS" />
    </div>
  </div>
  <canvas id="j-eq-canvas"></canvas>
  <div class="j-status-pill" id="j-status-pill">
    <span class="j-mic-dot" id="j-mic-dot"></span>
    <span id="j-status-text">AWAITING COMMAND...</span>
  </div>
  <audio id="j-audio" preload="auto"></audio>
</div>
"""

_RADAR_CSS = """
.j-tactical-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4px;
  font-family: 'JetBrains Mono', monospace;
  user-select: none;
}
.j-radar-wrap {
  position: relative;
  width: 400px;
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 900px;
}
#j-radar-canvas {
  position: absolute;
  inset: 0;
  width: 400px;
  height: 400px;
  pointer-events: none;
}
.j-face-layer {
  position: relative;
  width: 288px;
  height: 288px;
  border-radius: 50%;
  overflow: hidden;
  will-change: transform, filter;
  -webkit-mask-image: radial-gradient(circle, rgba(0,0,0,1) 62%, rgba(0,0,0,0) 98%);
  mask-image: radial-gradient(circle, rgba(0,0,0,1) 62%, rgba(0,0,0,0) 98%);
}
#j-face-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.16);
  display: block;
  mix-blend-mode: screen;
  pointer-events: none;
}
#j-eq-canvas {
  margin-top: 4px;
  display: block;
}
.j-status-pill {
  margin-top: 6px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 20px;
  border-radius: 999px;
  background: rgba(4, 22, 33, 0.88);
  border: 1px solid rgba(0, 229, 255, 0.36);
  color: #5eeeff;
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.j-mic-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #00e5ff;
  box-shadow: 0 0 8px #00e5ff;
}
#j-audio {
  display: none;
}
"""

_RADAR_JS = """
export default function (component) {
  const { data, parentElement } = component;
  const stage = parentElement.querySelector("#j-stage");
  const wrap = parentElement.querySelector("#j-wrap");
  const radarCanvas = parentElement.querySelector("#j-radar-canvas");
  const eqCanvas = parentElement.querySelector("#j-eq-canvas");
  const faceLayer = parentElement.querySelector("#j-face-layer");
  const faceImg = parentElement.querySelector("#j-face-img");
  const statusText = parentElement.querySelector("#j-status-text");
  const audioEl = parentElement.querySelector("#j-audio");

  if (!stage || !radarCanvas || !eqCanvas || !faceLayer || !faceImg || !audioEl) return;

  const avatarUri = (data && data.avatar_uri) || "";
  const audioUri = (data && data.audio_uri) || "";
  const audioId = (data && data.audio_id) || "";

  if (!stage._state) {
    stage._state = {
      lastAudioId: "",
      isPlaying: false,
      audioCtx: null,
      analyser: null,
      timeData: null,
      freqData: null,
      smoothLevel: 0,
      ripples: [],
      lastRippleAt: 0,
      curRx: 0,
      curRy: 0,
      targetRx: 0,
      targetRy: 0,
    };
  }
  const st = stage._state;

  if (avatarUri && faceImg.src !== avatarUri) {
    faceImg.src = avatarUri;
  }

  if (audioUri && audioId && audioId !== st.lastAudioId) {
    st.lastAudioId = audioId;
    try {
      if (!st.audioCtx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          st.audioCtx = new AudioCtx();
          const srcNode = st.audioCtx.createMediaElementSource(audioEl);
          st.analyser = st.audioCtx.createAnalyser();
          st.analyser.fftSize = 256;
          st.analyser.smoothingTimeConstant = 0.65;
          srcNode.connect(st.analyser);
          st.analyser.connect(st.audioCtx.destination);
          st.timeData = new Uint8Array(st.analyser.fftSize);
          st.freqData = new Uint8Array(st.analyser.frequencyBinCount);
        }
      }
      if (st.audioCtx && st.audioCtx.state === "suspended") {
        st.audioCtx.resume().catch(() => {});
      }
      audioEl.src = audioUri;
      audioEl.currentTime = 0;
      const playPromise = audioEl.play();
      if (playPromise && typeof playPromise.catch === "function") {
        playPromise.catch(() => { st.isPlaying = false; });
      }
    } catch (_err) {
      st.isPlaying = false;
    }
  }

  audioEl.onplay = () => {
    st.isPlaying = true;
    statusText.textContent = "VOICE TRANSMISSION...";
  };
  audioEl.onended = () => {
    st.isPlaying = false;
    statusText.textContent = "AWAITING COMMAND...";
  };
  audioEl.onpause = () => {
    if (audioEl.ended || audioEl.currentTime === 0) {
      st.isPlaying = false;
      statusText.textContent = "AWAITING COMMAND...";
    }
  };

  if (stage._jarvisCleanup) {
    stage._jarvisCleanup();
  }

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const size = 400;
  radarCanvas.width = size * dpr;
  radarCanvas.height = size * dpr;
  const rctx = radarCanvas.getContext("2d");
  rctx.scale(dpr, dpr);

  const eqW = 210;
  const eqH = 34;
  eqCanvas.width = eqW * dpr;
  eqCanvas.height = eqH * dpr;
  eqCanvas.style.width = `${eqW}px`;
  eqCanvas.style.height = `${eqH}px`;
  const ectx = eqCanvas.getContext("2d");
  ectx.scale(dpr, dpr);

  const onMouseMove = (e) => {
    const rect = wrap.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = Math.max(-1, Math.min(1, (e.clientX - cx) / 420));
    const dy = Math.max(-1, Math.min(1, (e.clientY - cy) / 420));
    st.targetRy = dx * 9;
    st.targetRx = -dy * 8;
  };
  const onMouseLeave = () => {
    st.targetRx = 0;
    st.targetRy = 0;
  };
  window.addEventListener("mousemove", onMouseMove, { passive: true });
  window.addEventListener("mouseleave", onMouseLeave, { passive: true });

  let rafId = 0;
  const startTime = performance.now();

  const renderFrame = (now) => {
    const t = (now - startTime) * 0.001;
    const mid = size / 2;
    const speaking = st.isPlaying && !audioEl.paused && !audioEl.ended;

    // 1. Measure real-time voice level (0..1)
    let targetLevel = 0;
    let hasLiveSignal = false;
    if (speaking && st.analyser && st.timeData && st.freqData) {
      st.analyser.getByteTimeDomainData(st.timeData);
      st.analyser.getByteFrequencyData(st.freqData);
      let sumSq = 0;
      for (let i = 0; i < st.timeData.length; i++) {
        const v = (st.timeData[i] - 128) / 128;
        sumSq += v * v;
      }
      const rms = Math.sqrt(sumSq / st.timeData.length);
      if (rms > 0.006) {
        hasLiveSignal = true;
        targetLevel = Math.min(1, Math.max(0, (rms - 0.01) * 4.8));
      }
    }
    if (speaking && !hasLiveSignal) {
      targetLevel = 0.25 + 0.75 * Math.abs(Math.sin(t * 9.5) * Math.cos(t * 4.3));
    }

    st.smoothLevel += (targetLevel - st.smoothLevel) * (targetLevel > st.smoothLevel ? 0.35 : 0.18);

    // Spawn expanding acoustic shockwave ripples on speech peaks
    if (speaking && st.smoothLevel > 0.28 && now - st.lastRippleAt > 260) {
      st.lastRippleAt = now;
      st.ripples.push({ r: 140, alpha: 0.55 });
    }

    // 2. Smooth 3D tilt + subtle voice-synced holographic brightness pulse (face stays 100% crisp!)
    st.curRx += (st.targetRx - st.curRx) * 0.08;
    st.curRy += (st.targetRy - st.curRy) * 0.08;
    const scale = 1 + Math.sin(t * 1.8) * 0.007 + st.smoothLevel * 0.022;
    const bright = (1.04 + st.smoothLevel * 0.28).toFixed(2);
    faceLayer.style.transform =
      `rotateX(${st.curRx.toFixed(2)}deg) rotateY(${st.curRy.toFixed(2)}deg) scale(${scale.toFixed(4)})`;
    faceLayer.style.filter = `brightness(${bright}) contrast(1.06)`;

    // 3. Draw Tactical Radar + 360-degree Radial Voice Spectrum + Expanding Ripples
    rctx.clearRect(0, 0, size, size);

    // Expanding acoustic ripple rings
    for (let i = st.ripples.length - 1; i >= 0; i--) {
      const rp = st.ripples[i];
      rp.r += 1.65;
      rp.alpha -= 0.014;
      if (rp.alpha <= 0 || rp.r > 196) {
        st.ripples.splice(i, 1);
        continue;
      }
      rctx.beginPath();
      rctx.arc(mid, mid, rp.r, 0, Math.PI * 2);
      rctx.strokeStyle = `rgba(0, 229, 255, ${rp.alpha.toFixed(2)})`;
      rctx.lineWidth = 1.6;
      rctx.stroke();
    }

    // Outer rotating dashed perimeter ring
    rctx.save();
    rctx.translate(mid, mid);
    rctx.rotate(t * (speaking ? 0.45 : 0.14));
    rctx.beginPath();
    rctx.setLineDash([7, 7]);
    rctx.arc(0, 0, 190, 0, Math.PI * 2);
    rctx.strokeStyle = "rgba(0, 229, 255, 0.36)";
    rctx.lineWidth = 1.4;
    rctx.stroke();
    rctx.restore();

    // Concentric solid thin rings
    for (const rs of [{ r: 174, a: 0.24 }, { r: 146, a: 0.22 }]) {
      rctx.beginPath();
      rctx.arc(mid, mid, rs.r, 0, Math.PI * 2);
      rctx.strokeStyle = `rgba(0, 229, 255, ${rs.a})`;
      rctx.lineWidth = 1.0;
      rctx.stroke();
    }

    // 360-Degree Radial Voice Spectrum Ring (48 crisp cyan bars around face perimeter!)
    const radialBars = 48;
    const innerR = 148;
    for (let i = 0; i < radialBars; i++) {
      const angle = (i / radialBars) * Math.PI * 2 - Math.PI / 2;
      let mag = 0.08;
      if (speaking) {
        if (hasLiveSignal && st.freqData) {
          const bin = 2 + (i % 24);
          mag = (st.freqData[bin] || 0) / 255;
        } else {
          mag = 0.2 + 0.8 * Math.abs(Math.sin(t * 9 + i * 0.5)) * st.smoothLevel;
        }
      } else {
        mag = 0.08 + 0.08 * Math.sin(t * 2.2 + i * 0.4);
      }
      const barLen = 3 + mag * (speaking ? 22 : 6);
      const x1 = mid + Math.cos(angle) * innerR;
      const y1 = mid + Math.sin(angle) * innerR;
      const x2 = mid + Math.cos(angle) * (innerR + barLen);
      const y2 = mid + Math.sin(angle) * (innerR + barLen);

      rctx.beginPath();
      rctx.moveTo(x1, y1);
      rctx.lineTo(x2, y2);
      rctx.strokeStyle = speaking
        ? `rgba(0, 229, 255, ${(0.35 + mag * 0.65).toFixed(2)})`
        : "rgba(0, 229, 255, 0.25)";
      rctx.lineWidth = 2.0;
      rctx.lineCap = "round";
      rctx.stroke();
    }

    // Two glowing cyan rotating radar sweep bars
    const sweepAngle = t * (speaking ? 1.5 : 0.48) - 0.9;
    for (const offset of [0, Math.PI]) {
      const a = sweepAngle + offset;
      rctx.save();
      rctx.beginPath();
      rctx.moveTo(mid + Math.cos(a) * 150, mid + Math.sin(a) * 150);
      rctx.lineTo(mid + Math.cos(a) * 180, mid + Math.sin(a) * 180);
      rctx.strokeStyle = "#00E5FF";
      rctx.lineWidth = 4.2;
      rctx.lineCap = "round";
      rctx.shadowColor = "#00E5FF";
      rctx.shadowBlur = 14;
      rctx.stroke();
      rctx.restore();
    }

    // 4. Vertical-bar cyan audio equalizer below
    ectx.clearRect(0, 0, eqW, eqH);
    const barCount = 19;
    const barW = 4;
    const bgap = 5;
    const totalW = barCount * barW + (barCount - 1) * bgap;
    const startX = (eqW - totalW) / 2;

    for (let i = 0; i < barCount; i++) {
      const norm = i / (barCount - 1);
      const env = Math.sin(norm * Math.PI);
      let level = 0;
      if (speaking && hasLiveSignal && st.freqData) {
        const bin = 2 + Math.floor(Math.abs(i - 9) * 2.5);
        level = (st.freqData[Math.min(bin, st.freqData.length - 1)] || 0) / 255;
      } else if (speaking) {
        level = 0.2 + 0.8 * Math.abs(Math.sin(t * 10 + i * 0.65)) * (0.4 + 0.6 * st.smoothLevel);
      } else {
        level = 0.22 + 0.30 * Math.abs(Math.sin(t * 2.4 + i * 0.55));
      }
      const h = Math.max(4, (speaking ? 30 : 12) * env * (0.25 + 0.95 * level));
      const x = startX + i * (barW + bgap);
      const y = (eqH - h) / 2;
      ectx.fillStyle = speaking ? "#00E5FF" : "rgba(0, 229, 255, 0.72)";
      ectx.fillRect(x, y, barW, h);
    }

    rafId = requestAnimationFrame(renderFrame);
  };

  rafId = requestAnimationFrame(renderFrame);

  const cleanup = () => {
    cancelAnimationFrame(rafId);
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseleave", onMouseLeave);
  };
  stage._jarvisCleanup = cleanup;
  return cleanup;
}
"""

_JARVIS_VOICE_AURA_V8 = st.components.v2.component(
    "jarvis_voice_aura_v8",
    html=_RADAR_HTML,
    css=_RADAR_CSS,
    js=_RADAR_JS,
)


def render_jarvis_voice_aura(
    *,
    avatar_uri: str,
    audio_uri: str = "",
    audio_id: str = "",
) -> None:
    """Mount the 60fps JS Tactical Radar with 360-degree Voice Spectrum & Ripples."""
    _JARVIS_VOICE_AURA_V8(
        data={
            "avatar_uri": avatar_uri,
            "audio_uri": audio_uri,
            "audio_id": audio_id,
        },
        key="jarvis_voice_aura_v8",
    )
