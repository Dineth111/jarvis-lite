"""Interactive 60fps JavaScript Canvas + 3D Parallax Hero Face component (Streamlit CCv2)."""

from __future__ import annotations

import streamlit as st

_HERO_HTML = """
<div class="j-stage" id="j-stage">
  <div class="j-canvas-wrap" id="j-wrap">
    <canvas id="j-orbit-canvas"></canvas>
    <div class="j-face-shell" id="j-face-shell">
      <img id="j-face-img" alt="Jarvis" />
      <div class="j-face-sheen" id="j-face-sheen"></div>
    </div>
  </div>
  <canvas id="j-wave-canvas" width="320" height="44"></canvas>
  <div class="j-copy" id="j-copy">
    <h1 class="j-heading" id="j-heading"></h1>
    <p class="j-sub" id="j-sub"></p>
  </div>
</div>
"""

_HERO_CSS = """
.j-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 6px 8px 4px 8px;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  user-select: none;
}
.j-canvas-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 900px;
}
#j-orbit-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.j-face-shell {
  position: relative;
  border-radius: 50%;
  overflow: hidden;
  background: #090a0f;
  border: 1.5px solid rgba(148, 163, 184, 0.24);
  box-shadow:
    0 24px 64px rgba(0, 0, 0, 0.72),
    0 0 48px rgba(56, 189, 248, 0.18);
  will-change: transform;
  transition: border-color 0.35s ease, box-shadow 0.35s ease;
}
.j-face-shell.is-speaking {
  border-color: rgba(56, 189, 248, 0.65);
  box-shadow:
    0 24px 72px rgba(0, 0, 0, 0.75),
    0 0 70px rgba(56, 189, 248, 0.38),
    0 0 110px rgba(99, 102, 241, 0.28);
}
#j-face-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.42);
  display: block;
  pointer-events: none;
}
.j-face-sheen {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 25%, rgba(255, 255, 255, 0.12), transparent 55%);
  pointer-events: none;
}
#j-wave-canvas {
  margin-top: 6px;
  display: block;
}
.j-copy {
  margin-top: 4px;
}
.j-heading {
  font-size: 1.55rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #f8fafc;
  margin: 4px 0 6px 0;
}
.j-sub {
  font-size: 0.92rem;
  color: #94a3b8;
  max-width: 540px;
  line-height: 1.5;
  margin: 0 auto;
}
"""

_HERO_JS = """
export default function (component) {
  const { data, parentElement } = component;
  const stage = parentElement.querySelector("#j-stage");
  const wrap = parentElement.querySelector("#j-wrap");
  const orbitCanvas = parentElement.querySelector("#j-orbit-canvas");
  const waveCanvas = parentElement.querySelector("#j-wave-canvas");
  const faceShell = parentElement.querySelector("#j-face-shell");
  const faceImg = parentElement.querySelector("#j-face-img");
  const headingEl = parentElement.querySelector("#j-heading");
  const subEl = parentElement.querySelector("#j-sub");
  const copyEl = parentElement.querySelector("#j-copy");

  if (!stage || !orbitCanvas || !waveCanvas || !faceShell || !faceImg) return;

  const avatarUri = (data && data.avatar_uri) || "";
  const speaking = Boolean(data && data.speaking);
  const compact = Boolean(data && data.compact);
  const heading = (data && data.heading) || "";
  const subtitle = (data && data.subtitle) || "";

  // Sizing: extra-large centerpiece face (420px default, 300px compact)
  const faceSize = compact ? 300 : 420;
  const canvasSize = faceSize + 64;
  wrap.style.width = `${canvasSize}px`;
  wrap.style.height = `${canvasSize}px`;
  faceShell.style.width = `${faceSize}px`;
  faceShell.style.height = `${faceSize}px`;
  faceShell.classList.toggle("is-speaking", speaking);

  if (avatarUri && faceImg.src !== avatarUri) {
    faceImg.src = avatarUri;
  }

  if (heading || subtitle) {
    copyEl.style.display = "block";
    headingEl.textContent = heading;
    subEl.textContent = subtitle;
  } else {
    copyEl.style.display = "none";
  }

  // Cancel any prior animation loop on rerun
  if (stage._jarvisCleanup) {
    stage._jarvisCleanup();
  }

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  orbitCanvas.width = canvasSize * dpr;
  orbitCanvas.height = canvasSize * dpr;
  const octx = orbitCanvas.getContext("2d");
  octx.scale(dpr, dpr);

  const wWidth = 320;
  const wHeight = 42;
  waveCanvas.width = wWidth * dpr;
  waveCanvas.height = wHeight * dpr;
  waveCanvas.style.width = `${wWidth}px`;
  waveCanvas.style.height = `${wHeight}px`;
  const wctx = waveCanvas.getContext("2d");
  wctx.scale(dpr, dpr);

  // Smooth 3D mouse-follow parallax state
  let targetRx = 0;
  let targetRy = 0;
  let curRx = 0;
  let curRy = 0;

  const onMouseMove = (e) => {
    const rect = wrap.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = Math.max(-1, Math.min(1, (e.clientX - cx) / 420));
    const dy = Math.max(-1, Math.min(1, (e.clientY - cy) / 420));
    targetRy = dx * 11;
    targetRx = -dy * 10;
  };
  const onMouseLeave = () => {
    targetRx = 0;
    targetRy = 0;
  };
  window.addEventListener("mousemove", onMouseMove, { passive: true });
  window.addEventListener("mouseleave", onMouseLeave, { passive: true });

  // Floating orbital light particles
  const particles = Array.from({ length: 24 }, (_, i) => ({
    angle: (Math.PI * 2 * i) / 24 + Math.random() * 0.4,
    radiusOffset: 10 + Math.random() * 24,
    speed: (0.0025 + Math.random() * 0.004) * (i % 2 === 0 ? 1 : -1),
    size: 1.2 + Math.random() * 1.8,
    alpha: 0.25 + Math.random() * 0.55,
  }));

  let rafId = 0;
  const startTime = performance.now();

  const renderFrame = (now) => {
    const t = (now - startTime) * 0.001;

    // 1. Lerp 3D tilt + subtle breathing scale on face shell
    curRx += (targetRx - curRx) * 0.08;
    curRy += (targetRy - curRy) * 0.08;
    const breathe = 1 + Math.sin(t * (speaking ? 4.4 : 1.7)) * (speaking ? 0.018 : 0.008);
    faceShell.style.transform =
      `rotateX(${curRx.toFixed(2)}deg) rotateY(${curRy.toFixed(2)}deg) scale(${breathe.toFixed(4)})`;

    // 2. Draw fluid harmonic ambient rings + orbiting particles
    octx.clearRect(0, 0, canvasSize, canvasSize);
    const mid = canvasSize / 2;
    const baseR = faceSize / 2 + 12;

    for (let ring = 0; ring < 2; ring++) {
      octx.beginPath();
      const steps = 96;
      const amp = speaking ? (ring === 0 ? 7.5 : 5.0) : (ring === 0 ? 2.4 : 1.6);
      const freq = ring === 0 ? 5 : 3;
      const speed = speaking ? (ring === 0 ? 4.2 : -3.2) : (ring === 0 ? 1.1 : -0.8);

      for (let i = 0; i <= steps; i++) {
        const theta = (i / steps) * Math.PI * 2;
        const wobble =
          Math.sin(theta * freq + t * speed) * amp +
          Math.cos(theta * (freq + 2) - t * speed * 0.7) * (amp * 0.45);
        const r = baseR + ring * 10 + wobble;
        const x = mid + Math.cos(theta) * r;
        const y = mid + Math.sin(theta) * r;
        if (i === 0) octx.moveTo(x, y);
        else octx.lineTo(x, y);
      }
      octx.closePath();
      octx.strokeStyle =
        ring === 0
          ? speaking
            ? "rgba(56, 189, 248, 0.55)"
            : "rgba(56, 189, 248, 0.24)"
          : speaking
          ? "rgba(129, 140, 248, 0.45)"
          : "rgba(129, 140, 248, 0.16)";
      octx.lineWidth = ring === 0 ? 1.6 : 1.1;
      octx.stroke();
    }

    // Orbiting soft light particles
    for (const p of particles) {
      p.angle += p.speed * (speaking ? 2.1 : 1.0);
      const pr = faceSize / 2 + p.radiusOffset + Math.sin(t * 2 + p.angle * 3) * 3;
      const px = mid + Math.cos(p.angle) * pr;
      const py = mid + Math.sin(p.angle) * pr;
      octx.beginPath();
      octx.arc(px, py, p.size, 0, Math.PI * 2);
      octx.fillStyle = `rgba(125, 211, 252, ${(p.alpha * (speaking ? 1.0 : 0.65)).toFixed(2)})`;
      octx.fill();
    }

    // 3. Draw smooth fluid JS sine-wave voice visualizer below the face
    wctx.clearRect(0, 0, wWidth, wHeight);
    const cy = wHeight / 2;
    const waveGrad = wctx.createLinearGradient(0, 0, wWidth, 0);
    waveGrad.addColorStop(0, "rgba(56, 189, 248, 0)");
    waveGrad.addColorStop(0.25, speaking ? "rgba(56, 189, 248, 0.9)" : "rgba(148, 163, 184, 0.4)");
    waveGrad.addColorStop(0.5, speaking ? "rgba(129, 140, 248, 1)" : "rgba(129, 140, 248, 0.55)");
    waveGrad.addColorStop(0.75, speaking ? "rgba(56, 189, 248, 0.9)" : "rgba(148, 163, 184, 0.4)");
    waveGrad.addColorStop(1, "rgba(56, 189, 248, 0)");

    for (let layer = 0; layer < 2; layer++) {
      wctx.beginPath();
      const maxAmp = speaking ? (layer === 0 ? 14 : 9) : (layer === 0 ? 4.5 : 2.8);
      const speed = speaking ? (layer === 0 ? 7.5 : -5.5) : (layer === 0 ? 2.0 : -1.4);
      const freq = layer === 0 ? 0.045 : 0.068;

      for (let x = 0; x <= wWidth; x += 2) {
        // Taper smoothly to 0 at left/right edges
        const norm = x / wWidth;
        const envelope = Math.sin(norm * Math.PI);
        const y =
          cy +
          Math.sin(x * freq + t * speed) *
            maxAmp *
            envelope *
            (0.75 + 0.25 * Math.sin(t * 3.1 + layer));
        if (x === 0) wctx.moveTo(x, y);
        else wctx.lineTo(x, y);
      }
      wctx.strokeStyle = waveGrad;
      wctx.lineWidth = layer === 0 ? 2.2 : 1.3;
      wctx.stroke();
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

_JARVIS_HERO_FACE = st.components.v2.component(
    "jarvis_hero_face_v2",
    html=_HERO_HTML,
    css=_HERO_CSS,
    js=_HERO_JS,
)


def render_jarvis_hero(
    *,
    avatar_uri: str,
    speaking: bool = False,
    compact: bool = False,
    heading: str = "",
    subtitle: str = "",
) -> None:
    """Mount the 60fps JS Canvas + 3D Parallax Jarvis face component."""
    _JARVIS_HERO_FACE(
        data={
            "avatar_uri": avatar_uri,
            "speaking": speaking,
            "compact": compact,
            "heading": heading,
            "subtitle": subtitle,
        },
        key="jarvis_hero_face",
    )
