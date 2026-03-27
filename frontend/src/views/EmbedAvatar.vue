<template>
  <div class="embed-page">
    <div class="video-wrap">
      <BrowserAvatar
        :speaking-level="assistantSpeakingLevel"
        :connected="connected"
        :has-remote-audio="hasRemoteAudio"
      />
      <div ref="audioHostEl" class="audio-host"></div>
      <div v-if="!hasRemoteAudio" class="placeholder">Connecting to interviewer voice...</div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div class="footer">
      <span>{{ statusText }}</span>
      <button class="btn" @click="toggleMic" :disabled="!connected">
        {{ micMuted ? 'Unmute Mic' : 'Mute Mic' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Room, RoomEvent, Track, createLocalAudioTrack, type LocalAudioTrack } from 'livekit-client'
import BrowserAvatar from '@/components/avatar/BrowserAvatar.vue'

const route = useRoute()
const embedId = route.params.embedId as string
const defaultBaseUrl = import.meta.env.DEV ? 'http://localhost:8009' : window.location.origin
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || defaultBaseUrl

const audioHostEl = ref<HTMLDivElement | null>(null)
const hasRemoteAudio = ref(false)
const assistantSpeakingLevel = ref(0)
const error = ref('')
const status = ref<'idle' | 'connecting' | 'connected' | 'disconnected' | 'error'>('idle')
const connected = ref(false)
const micMuted = ref(false)
const sessionId = ref<string | null>(null)
const sessionEnded = ref(false)

let room: Room | null = null
let localAudioTrack: LocalAudioTrack | null = null
const remoteAudioElements = new Map<string, HTMLAudioElement>()

const statusText = computed(() => {
  if (status.value === 'connecting') return 'Connecting...'
  if (status.value === 'connected') return 'Connected'
  if (status.value === 'disconnected') return 'Disconnected'
  if (status.value === 'error') return 'Connection error'
  return 'Idle'
})

function getOriginHint(): string | null {
  try {
    if (document.referrer) {
      return new URL(document.referrer).origin
    }
  } catch {
    // Ignore malformed referrer.
  }
  return null
}

function buildSessionEndUrl(): string {
  if (!sessionId.value) return ''
  return `${API_BASE_URL}/api/v1/public/realtime/embed/${embedId}/sessions/${sessionId.value}/end`
}

async function endSessionWithFetch(keepalive: boolean = false) {
  if (!sessionId.value || sessionEnded.value) return
  try {
    await fetch(buildSessionEndUrl(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ origin_hint: getOriginHint() }),
      keepalive
    })
  } catch {
    // Ignore end-session errors during teardown.
  } finally {
    sessionEnded.value = true
    sessionId.value = null
  }
}

function endSessionWithBeacon() {
  if (!sessionId.value || sessionEnded.value || typeof navigator.sendBeacon !== 'function') return
  try {
    const body = JSON.stringify({ origin_hint: getOriginHint() })
    const payload = new Blob([body], { type: 'application/json' })
    const accepted = navigator.sendBeacon(buildSessionEndUrl(), payload)
    if (accepted) {
      sessionEnded.value = true
      sessionId.value = null
    }
  } catch {
    // Ignore beacon failures and rely on normal cleanup path.
  }
}

function handleBeforeUnload() {
  endSessionWithBeacon()
}

async function fetchToken() {
  const participantName =
    (new URLSearchParams(window.location.search).get('name') || 'candidate').slice(0, 120)
  const response = await fetch(`${API_BASE_URL}/api/v1/public/realtime/embed/${embedId}/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      participant_name: participantName,
      origin_hint: getOriginHint()
    })
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body?.detail || `Token request failed (${response.status})`)
  }
  return response.json()
}

async function disconnectRoom() {
  await endSessionWithFetch(true)
  if (localAudioTrack) {
    localAudioTrack.stop()
    localAudioTrack = null
  }
  if (room) {
    room.disconnect()
    room = null
  }
  connected.value = false
  assistantSpeakingLevel.value = 0
  for (const element of remoteAudioElements.values()) {
    element.srcObject = null
    if (element.parentElement) {
      element.parentElement.removeChild(element)
    }
  }
  remoteAudioElements.clear()
  hasRemoteAudio.value = false
}

async function connectRoom() {
  status.value = 'connecting'
  error.value = ''

  try {
    await disconnectRoom()

    const token = await fetchToken()
    sessionId.value = token.session_id
    sessionEnded.value = false
    room = new Room({
      adaptiveStream: true,
      dynacast: true
    })

    room.on(RoomEvent.TrackSubscribed, (track: any) => {
      if (track.kind === Track.Kind.Audio) {
        const sid = track?.sid as string | undefined
        if (!sid || remoteAudioElements.has(sid)) return

        const attached = track.attach() as HTMLAudioElement
        attached.autoplay = true
        attached.playsInline = true
        attached.style.display = 'none'
        audioHostEl.value?.appendChild(attached)
        void attached.play().catch(() => {
          // Autoplay can be blocked until user gesture in some browsers.
        })

        remoteAudioElements.set(sid, attached)
        hasRemoteAudio.value = remoteAudioElements.size > 0
      }
    })

    room.on(RoomEvent.TrackUnsubscribed, (track: any) => {
      if (track.kind === Track.Kind.Audio) {
        const sid = track?.sid as string | undefined
        if (!sid) return
        track.detach()
        const element = remoteAudioElements.get(sid)
        if (element && element.parentElement) {
          element.parentElement.removeChild(element)
        }
        remoteAudioElements.delete(sid)
        hasRemoteAudio.value = remoteAudioElements.size > 0
        if (!hasRemoteAudio.value) {
          assistantSpeakingLevel.value = 0
        }
      }
    })

    room.on(RoomEvent.ActiveSpeakersChanged, (speakers: any[]) => {
      const localIdentity = room?.localParticipant.identity
      const remotePeak = (speakers || [])
        .filter((speaker) => speaker?.identity && speaker.identity !== localIdentity)
        .reduce((max, speaker) => Math.max(max, Number(speaker.audioLevel || 0)), 0)
      assistantSpeakingLevel.value = Math.max(0, Math.min(1, remotePeak * 3))
    })

    room.on(RoomEvent.Disconnected, () => {
      status.value = 'disconnected'
      connected.value = false
      assistantSpeakingLevel.value = 0
      endSessionWithFetch(true)
    })

    await room.connect(token.server_url, token.participant_token, {
      autoSubscribe: true
    })
    localAudioTrack = await createLocalAudioTrack()
    await room.localParticipant.publishTrack(localAudioTrack)

    connected.value = true
    status.value = 'connected'
  } catch (err: any) {
    error.value = err?.message || 'Failed to connect'
    status.value = 'error'
  }
}

async function toggleMic() {
  if (!localAudioTrack) return
  micMuted.value = !micMuted.value
  if (micMuted.value) {
    await localAudioTrack.mute()
  } else {
    await localAudioTrack.unmute()
  }
}

onMounted(async () => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  await connectRoom()
})

onBeforeUnmount(async () => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  await disconnectRoom()
})
</script>

<style scoped>
.embed-page {
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  color: #e2e8f0;
}

.video-wrap {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #cbd5e1;
  pointer-events: none;
}

.audio-host {
  display: none;
}

.error {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 12px;
  background: rgba(127, 29, 29, 0.88);
  border: 1px solid rgba(248, 113, 113, 0.5);
  padding: 10px;
  border-radius: 8px;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(15, 23, 42, 0.9);
}

.btn {
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(30, 41, 59, 0.9);
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
}
</style>
