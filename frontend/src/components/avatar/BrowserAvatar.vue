<template>
  <div class="avatar-stage" :class="{ online: connected }" :style="avatarStyle">
    <div class="orbital orbital-a"></div>
    <div class="orbital orbital-b"></div>
    <div class="orbital orbital-c"></div>

    <div class="avatar-shell">
      <div class="halo"></div>
      <div class="head">
        <div class="glow"></div>
        <div class="eyes">
          <span class="eye left"></span>
          <span class="eye right"></span>
        </div>
        <div class="mouth-wrap">
          <span class="mouth"></span>
        </div>
      </div>

      <div class="voice-bars" aria-hidden="true">
        <span v-for="idx in 5" :key="idx"></span>
      </div>

      <p class="state">
        {{ connected ? (hasRemoteAudio ? "Interviewer connected" : "Connecting audio stream...") : "Disconnected" }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    speakingLevel: number;
    connected: boolean;
    hasRemoteAudio: boolean;
  }>(),
  {
    speakingLevel: 0,
    connected: false,
    hasRemoteAudio: false,
  }
);

const normalizedLevel = computed(() => Math.max(0, Math.min(props.speakingLevel, 1)));

const avatarStyle = computed(() => {
  const level = normalizedLevel.value;
  return {
    "--speech-open": (0.28 + level * 0.95).toFixed(3),
    "--speech-energy": (0.2 + level * 0.8).toFixed(3),
    "--speech-halo": (0.18 + level * 0.72).toFixed(3),
  };
});
</script>

<style scoped>
.avatar-stage {
  --speech-open: 0.28;
  --speech-energy: 0.2;
  --speech-halo: 0.2;
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 320px;
  background: radial-gradient(circle at 20% 15%, rgba(56, 189, 248, 0.22), transparent 45%),
    radial-gradient(circle at 82% 82%, rgba(14, 165, 233, 0.22), transparent 42%),
    linear-gradient(140deg, #0b1220 8%, #101b35 58%, #14213d 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.orbital {
  position: absolute;
  border-radius: 999px;
  filter: blur(0.2px);
  opacity: 0.35;
  animation: orbit 14s linear infinite;
}

.orbital-a {
  width: 420px;
  height: 420px;
  border: 1px solid rgba(56, 189, 248, 0.34);
}

.orbital-b {
  width: 320px;
  height: 320px;
  border: 1px dashed rgba(129, 140, 248, 0.28);
  animation-duration: 18s;
  animation-direction: reverse;
}

.orbital-c {
  width: 520px;
  height: 520px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  animation-duration: 24s;
}

.avatar-shell {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.halo {
  position: absolute;
  width: 220px;
  height: 220px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.52), transparent 70%);
  opacity: var(--speech-halo);
  transform: scale(calc(0.86 + var(--speech-energy) * 0.22));
  transition: transform 120ms linear, opacity 120ms linear;
}

.head {
  position: relative;
  width: 172px;
  height: 208px;
  border-radius: 88px;
  background: linear-gradient(170deg, #dbeafe 0%, #bfdbfe 35%, #93c5fd 74%, #60a5fa 100%);
  border: 2px solid rgba(219, 234, 254, 0.88);
  box-shadow: 0 18px 56px rgba(14, 165, 233, 0.28), inset 0 -18px 28px rgba(30, 64, 175, 0.2);
  overflow: hidden;
  animation: floaty 3.8s ease-in-out infinite;
}

.glow {
  position: absolute;
  top: 14px;
  left: 12px;
  width: 108px;
  height: 68px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.36);
  filter: blur(7px);
}

.eyes {
  position: absolute;
  top: 78px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 38px;
}

.eye {
  width: 18px;
  height: 14px;
  border-radius: 12px;
  background: #0f172a;
  animation: blink 4.7s infinite;
}

.eye.right {
  animation-delay: 140ms;
}

.mouth-wrap {
  position: absolute;
  left: 50%;
  bottom: 48px;
  transform: translateX(-50%);
  width: 54px;
  height: 40px;
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mouth {
  width: 34px;
  height: 10px;
  border-radius: 999px;
  background: #111827;
  transform: scaleY(var(--speech-open));
  transform-origin: center;
  transition: transform 90ms linear;
}

.voice-bars {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 28px;
}

.voice-bars span {
  width: 6px;
  border-radius: 6px;
  background: rgba(125, 211, 252, 0.92);
  height: calc(8px + var(--speech-energy) * 16px);
  animation: equalize 880ms ease-in-out infinite;
}

.voice-bars span:nth-child(2) {
  animation-delay: 120ms;
}

.voice-bars span:nth-child(3) {
  animation-delay: 240ms;
}

.voice-bars span:nth-child(4) {
  animation-delay: 360ms;
}

.voice-bars span:nth-child(5) {
  animation-delay: 480ms;
}

.state {
  margin: 0;
  color: rgba(226, 232, 240, 0.95);
  font-size: 13px;
  letter-spacing: 0.2px;
}

.avatar-stage:not(.online) .head {
  filter: grayscale(0.35);
}

.avatar-stage:not(.online) .voice-bars span {
  opacity: 0.42;
}

@keyframes orbit {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes floaty {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-8px);
  }
}

@keyframes blink {
  0%,
  45%,
  47%,
  100% {
    transform: scaleY(1);
  }
  46% {
    transform: scaleY(0.1);
  }
}

@keyframes equalize {
  0%,
  100% {
    transform: scaleY(0.65);
  }
  40% {
    transform: scaleY(1.22);
  }
  70% {
    transform: scaleY(0.8);
  }
}
</style>
