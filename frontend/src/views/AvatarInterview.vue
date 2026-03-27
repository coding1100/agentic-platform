<template>
  <div class="avatar-page">
    <header class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">Back</button>
        <h1>{{ agent?.name || 'Avatar Interview' }}</h1>
      </div>
      <button class="btn-secondary" @click="disconnectAndExit">End Session</button>
    </header>

    <main class="page-content">
      <section class="video-panel">
        <BrowserAvatar
          :speaking-level="assistantSpeakingLevel"
          :connected="connected"
          :has-remote-audio="hasRemoteAudio"
        />
        <div ref="audioHostEl" class="audio-host"></div>
        <div v-if="!hasRemoteAudio" class="video-placeholder">
          Waiting for interviewer voice...
        </div>
      </section>

      <section class="side-panel">
        <div class="panel-card">
          <h2>Session</h2>
          <p class="status">{{ statusText }}</p>
          <p v-if="roomName"><strong>Room:</strong> {{ roomName }}</p>
          <p v-if="sessionId"><strong>Session ID:</strong> {{ sessionId }}</p>
          <p v-if="tokenExpiresAt"><strong>Token Expires:</strong> {{ formatDate(tokenExpiresAt) }}</p>
          <div v-if="error" class="error-box">{{ error }}</div>
          <div class="actions">
            <button class="btn-secondary" @click="toggleMic" :disabled="!connected">
              {{ micMuted ? 'Unmute Mic' : 'Mute Mic' }}
            </button>
            <button class="btn-primary" @click="reconnect" :disabled="connecting">
              {{ connecting ? 'Connecting...' : 'Reconnect' }}
            </button>
          </div>
        </div>

        <div class="panel-card transcript">
          <h2>Live Transcript</h2>
          <div class="transcript-log">
            <p v-if="transcript.length === 0" class="muted">No transcript yet.</p>
            <p v-for="(line, idx) in transcript" :key="idx">{{ line }}</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Room, RoomEvent, Track, createLocalAudioTrack, type LocalAudioTrack } from 'livekit-client'
import { realtimeApi } from '@/services/api'
import { useAgentsStore } from '@/stores/agents'
import { useAuthStore } from '@/stores/auth'
import type { Agent } from '@/types'
import BrowserAvatar from '@/components/avatar/BrowserAvatar.vue'

const route = useRoute()
const router = useRouter()
const agentsStore = useAgentsStore()
const authStore = useAuthStore()

const agentId = route.params.agentId as string
const agent = ref<Agent | null>(null)
const audioHostEl = ref<HTMLDivElement | null>(null)
const hasRemoteAudio = ref(false)
const assistantSpeakingLevel = ref(0)
const roomName = ref('')
const sessionId = ref('')
const tokenExpiresAt = ref('')
const transcript = ref<string[]>([])
const error = ref('')
const connecting = ref(false)
const connected = ref(false)
const micMuted = ref(false)
const status = ref<'idle' | 'connecting' | 'connected' | 'disconnected' | 'error'>('idle')

let room: Room | null = null
let localAudioTrack: LocalAudioTrack | null = null
let sessionEnded = false
const remoteAudioElements = new Map<string, HTMLAudioElement>()

const statusText = computed(() => {
  if (status.value === 'connecting') return 'Connecting to realtime room...'
  if (status.value === 'connected') return 'Connected'
  if (status.value === 'disconnected') return 'Disconnected'
  if (status.value === 'error') return 'Connection error'
  return 'Idle'
})

function resetRoomState() {
  hasRemoteAudio.value = false
  assistantSpeakingLevel.value = 0
  connected.value = false
  micMuted.value = false
}

function attachRemoteAudioTrack(track: any) {
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

function detachRemoteAudioTrack(track: any) {
  const sid = track?.sid as string | undefined
  if (!sid) return

  const element = remoteAudioElements.get(sid)
  track.detach()
  if (element && element.parentElement) {
    element.parentElement.removeChild(element)
  }
  remoteAudioElements.delete(sid)
  hasRemoteAudio.value = remoteAudioElements.size > 0
  if (!hasRemoteAudio.value) {
    assistantSpeakingLevel.value = 0
  }
}

function clearRemoteAudioTracks() {
  for (const element of remoteAudioElements.values()) {
    element.srcObject = null
    if (element.parentElement) {
      element.parentElement.removeChild(element)
    }
  }
  remoteAudioElements.clear()
  hasRemoteAudio.value = false
  assistantSpeakingLevel.value = 0
}

function attachRoomEvents(activeRoom: Room) {
  activeRoom.on(RoomEvent.TrackSubscribed, (track: any, _pub: any, _participant: any) => {
    if (track.kind === Track.Kind.Audio) {
      attachRemoteAudioTrack(track)
    }
  })

  activeRoom.on(RoomEvent.TrackUnsubscribed, (track: any, _pub: any, _participant: any) => {
    if (track.kind === Track.Kind.Audio) {
      detachRemoteAudioTrack(track)
    }
  })

  activeRoom.on(RoomEvent.ActiveSpeakersChanged, (speakers: any[]) => {
    const localIdentity = activeRoom.localParticipant.identity
    const remotePeak = (speakers || [])
      .filter((speaker) => speaker?.identity && speaker.identity !== localIdentity)
      .reduce((max, speaker) => Math.max(max, Number(speaker.audioLevel || 0)), 0)
    assistantSpeakingLevel.value = Math.max(0, Math.min(1, remotePeak * 3))
  })

  activeRoom.on(RoomEvent.TranscriptionReceived, (segments: any[], participant: any) => {
    for (const segment of segments || []) {
      if (segment?.text) {
        const speaker = participant?.name || participant?.identity || 'speaker'
        transcript.value.push(`${speaker}: ${segment.text}`)
      }
    }
  })

  activeRoom.on(RoomEvent.DataReceived, (payload: Uint8Array, participant: any) => {
    try {
      const text = new TextDecoder().decode(payload)
      if (text) {
        const speaker = participant?.name || participant?.identity || 'assistant'
        transcript.value.push(`${speaker}: ${text}`)
      }
    } catch {
      // Ignore binary data frames.
    }
  })

  activeRoom.on(RoomEvent.Disconnected, () => {
    status.value = 'disconnected'
    clearRemoteAudioTracks()
    resetRoomState()
  })
}

async function disconnectRoom() {
  if (localAudioTrack) {
    localAudioTrack.stop()
    localAudioTrack = null
  }
  if (room) {
    room.disconnect()
    room = null
  }
  clearRemoteAudioTracks()
  resetRoomState()
}

async function endSessionOnBackend() {
  if (!sessionId.value || sessionEnded) return
  try {
    await realtimeApi.endSession(sessionId.value)
  } catch {
    // Ignore backend session-close errors on teardown.
  } finally {
    sessionEnded = true
  }
}

async function connectRoom() {
  if (!agent.value) return
  if (agent.value.interaction_mode !== 'avatar_realtime') {
    error.value = 'This agent is not configured for avatar realtime mode.'
    status.value = 'error'
    return
  }

  connecting.value = true
  error.value = ''
  status.value = 'connecting'

  try {
    await endSessionOnBackend()
    await disconnectRoom()

    const token = await realtimeApi.createAgentToken(agentId, {
      participant_name: authStore.currentUser?.email?.split('@')[0] || 'user'
    })

    roomName.value = token.room_name
    sessionId.value = token.session_id
    tokenExpiresAt.value = token.expires_at
    sessionEnded = false

    room = new Room({
      adaptiveStream: true,
      dynacast: true
    })
    attachRoomEvents(room)

    await room.connect(token.server_url, token.participant_token, {
      autoSubscribe: true
    })

    localAudioTrack = await createLocalAudioTrack()
    await room.localParticipant.publishTrack(localAudioTrack)

    connected.value = true
    status.value = 'connected'
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err?.message || 'Failed to connect to realtime room'
    status.value = 'error'
  } finally {
    connecting.value = false
  }
}

async function reconnect() {
  transcript.value = []
  await connectRoom()
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

async function disconnectAndExit() {
  await endSessionOnBackend()
  await disconnectRoom()
  router.push('/dashboard')
}

function goBack() {
  disconnectAndExit()
}

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

onMounted(async () => {
  const result = await agentsStore.fetchAgent(agentId)
  if (!result.success || !result.agent) {
    error.value = result.error || 'Failed to load agent'
    status.value = 'error'
    return
  }
  agent.value = result.agent
  await connectRoom()
})

onBeforeUnmount(async () => {
  await endSessionOnBackend()
  await disconnectRoom()
})
</script>

<style scoped>
.avatar-page {
  min-height: 100vh;
  background: radial-gradient(circle at 0% 0%, #25436e, #101827 52%, #0a0f1f);
  color: #eef2ff;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 22px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.26);
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(8px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header h1 {
  margin: 0;
  font-size: 22px;
}

.page-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  padding: 16px;
}

.video-panel {
  position: relative;
  min-height: 500px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: linear-gradient(140deg, #0f172a, #1e293b);
  overflow: hidden;
}

.video-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #cbd5e1;
  font-size: 16px;
  pointer-events: none;
}

.audio-host {
  display: none;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.panel-card {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(15, 23, 42, 0.8);
  padding: 14px;
}

.panel-card h2 {
  margin: 0 0 10px;
  font-size: 16px;
}

.status {
  font-weight: 600;
}

.error-box {
  margin-top: 10px;
  padding: 10px;
  border-radius: 8px;
  background: rgba(153, 27, 27, 0.35);
  border: 1px solid rgba(248, 113, 113, 0.45);
}

.actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn-primary,
.btn-secondary,
.btn-back {
  cursor: pointer;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  color: #eef2ff;
  background: rgba(30, 41, 59, 0.9);
  padding: 9px 12px;
}

.btn-primary {
  background: rgba(14, 116, 144, 0.9);
}

.transcript-log {
  max-height: 340px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.45;
}

.muted {
  color: #94a3b8;
}

@media (max-width: 1024px) {
  .page-content {
    grid-template-columns: 1fr;
  }

  .video-panel {
    min-height: 340px;
  }
}
</style>
