# UVT (Universal Voice Translator)

<p align="center">
  <b>Invisible Real-Time Speech-to-Speech Voice Translation in Chrome Side Panel</b><br>
  Powered by Google Gemini Multimodal Live API, Google Cloud Application Default Credentials (ADC), and OS Virtual Audio Routing.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Chrome-Extension_MV3-4285F4?logo=googlechrome&logoColor=white" alt="Chrome MV3"/>
  <img src="https://img.shields.io/badge/Gemini-Live_Multimodal_API-8E75C4?logo=google&logoColor=white" alt="Gemini Live"/>
  <img src="https://img.shields.io/badge/Google_Cloud-ADC_OAuth2-34A853?logo=googlecloud&logoColor=white" alt="Google Cloud ADC"/>
  <img src="https://img.shields.io/badge/Audio-PipeWire_Virtual_Nodes-E95420?logo=linux&logoColor=white" alt="PipeWire"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+"/>
</p>

---

## 🌟 Overview

**UVT (Universal Voice Translator)** is an invisible, real-time, bidirectional voice translation companion built into Google Chrome as a **Side Panel application**. It enables natural, full-duplex verbal conversations across language barriers in Google Meet, Zoom, Microsoft Teams, Slack, and Discord.

Unlike traditional translation tools that rely on reading captions or waiting for delayed text-to-speech cascades, UVT integrates directly into the **operating system audio graph** by creating two virtual audio devices:
1. **`UVT-Mic`**: A virtual microphone that streams your real-time translated voice into the meeting (e.g., you speak Persian, attendees hear fluent English).
2. **`UVT-Speaker`**: A virtual audio output that receives meeting audio, translates it live into your native language, and plays it privately into your physical headphones.

---

## 🚀 Key Features

- **Sub-Second Latency ($\le 700\text{ ms}$):** Direct Speech-to-Speech (S2S) processing through Google's Gemini Multimodal Live API bypasses the slow 3-stage cascade (ASR $\rightarrow$ MT $\rightarrow$ TTS).
- **Expressive Human Prosody:** Maintains vocal pacing, emotional intensity, and inflection instead of robotic monotone playback.
- **Enterprise Security via Google ADC:** Authenticates natively using **Google Application Default Credentials (ADC)** with auto-refreshing OAuth2 bearer tokens.
- **Dual-Session Isolation:** Independent Outbound (TX) and Inbound (RX) WebSocket sessions prevent conversational cross-talk and context contamination.
- **Native Barge-In / Interruption:** Automatically purges audio playback buffers when user interrupts, mimicking natural human conversation pacing.
- **Docked Chrome Side Panel UI:** Stays pinned alongside your Google Meet tab with real-time bilingual transcripts, VU volume meters, and one-click pass-through controls.

---

## 🏗️ System Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                      HOST OPERATING SYSTEM                                         |
|                                                                                                    |
|  +----------------------------------+          IPC          +-----------------------------------+  |
|  |     CHROME SIDE PANEL (MV3)      |  <----------------->  |       UVT NATIVE ENGINE           |  |
|  |                                  |   (Native Messaging   |                                   |  |
|  |  * Persistent UI & Controls      |    or Local WS RPC)   |  * Google ADC Token Refresher     |  |
|  |  * Live Dual Subtitle Feed       |                       |  * PipeWire Virtual Node Manager  |  |
|  |  * Language & Voice Settings     |                       |  * Dual Gemini Live WS Clients    |  |
|  |  * Audio VU Meters & Latency HUD |                       |  * 16k <-> 24k <-> 48k Resampler  |  |
|  +----------------------------------+                       +-----------------+-----------------+  |
|                                                                               |                    |
|                                               +-------------------------------+                    |
|                                               v                                                    |
|  +----------------------------------------------------------------------------------------------+  |
|  |                                PIPEWIRE 1.6+ AUDIO SUBSYSTEM                                 |  |
|  |                                                                                              |  |
|  |   [ Physical Mic ]                                                  [ Physical Headphones ]  |  |
|  |          |                                                                    ^              |  |
|  |          v [Capture 16kHz]                                                    | [Play 48kHz] |  |
|  |   ( Gemini Live TX )                                                ( Gemini Live RX )       |  |
|  |          | [Translated 24kHz]                                                 ^              |  |
|  |          v                                                                    | [Monitor]    |  |
|  |   [ UVT-Mic ] -----------------------------------------------\                |              |  |
|  |   (Virtual Source Node)                                       |      [ UVT-Speaker ]         |  |
|  |                                                               |   (Virtual Sink Node)        |  |
|  |                                                               v               ^              |  |
|  |                     +-------------------------------------------------+       |              |  |
|  |                     |        CONFERENCING APPLICATION (Meet / Zoom)   |       |              |  |
|  |                     |  * Microphone Input = "UVT-Mic"                 |-------/              |  |
|  |                     |  * Audio Output     = "UVT-Speaker"             |                      |  |
|  |                     +-------------------------------------------------+                      |  |
|  +----------------------------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------------------------+
```

---

## 🔐 Google ADC (Application Default Credentials) Setup

UVT leverages Google Cloud ADC for enterprise authentication, allowing access to Gemini Live models on Vertex AI and Google Cloud without hardcoding API keys.

### 1. Authenticate with Google Cloud
Ensure you have authenticated your local environment:
```bash
gcloud auth application-default login
```
This generates credentials at `~/.config/gcloud/application_default_credentials.json`.

### 2. Verify Your ADC Quota Project
```bash
gcloud auth application-default set-quota-project mehdigolzari
```

### 3. Verify Access Token Generation
```bash
gcloud auth application-default print-access-token
```

---

## 🎛️ PipeWire Virtual Audio Nodes (Linux)

UVT creates and manages two non-destructive virtual nodes dynamically using `pw-loopback`:

```bash
# 1. Create UVT-Speaker (Conferencing apps output audio here)
pw-loopback \
  --name "UVT-Speaker-Daemon" \
  --capture-props='media.class=Audio/Sink node.name=UVT_Speaker node.description="UVT Meeting Speaker" audio.position=[FL FR]' \
  --playback-props='node.name=UVT_Speaker_Dummy node.description="UVT Speaker Dummy Sink" node.passive=true' &

# 2. Create UVT-Mic (Conferencing apps pick this up as their microphone)
pw-loopback \
  --name "UVT-Mic-Daemon" \
  --capture-props='node.name=UVT_Mic_Feed node.description="UVT Mic Feed Input" node.passive=true' \
  --playback-props='media.class=Audio/Source node.name=UVT_Mic node.description="UVT Translated Microphone" audio.position=[FL FR]' &
```

---

## 📚 Documentation Index

Detailed engineering and product documentation is available in the [`docs/`](./docs) folder:

- [**`docs/01_PRODUCT_SPECIFICATION.md`**](./docs/01_PRODUCT_SPECIFICATION.md): Complete PRD, user personas, functional requirements, and UX specifications.
- [**`docs/02_TECHNICAL_SPECIFICATION.md`**](./docs/02_TECHNICAL_SPECIFICATION.md): System architecture, hybrid browser-native bridge, IPC message schemas, and failure recovery.
- [**`docs/03_GEMINI_TRANSLATION_MODEL_GUIDE.md`**](./docs/03_GEMINI_TRANSLATION_MODEL_GUIDE.md): Gemini Multimodal Live API (`BidiGenerateContent`), S2S latency budget, strict zero-commentary system prompts, and Python reference implementation.
- [**`docs/04_VIRTUAL_AUDIO_ROUTING_ARCHITECTURE.md`**](./docs/04_VIRTUAL_AUDIO_ROUTING_ARCHITECTURE.md): PipeWire 1.6+ audio graphs, ring buffers, sample rate conversion, and anti-feedback acoustic isolation.

---

## 📁 Repository Structure

```
UVT/
├── docs/                              # Architecture, PRD, AI model, and audio specs
│   ├── 01_PRODUCT_SPECIFICATION.md
│   ├── 02_TECHNICAL_SPECIFICATION.md
│   ├── 03_GEMINI_TRANSLATION_MODEL_GUIDE.md
│   ├── 04_VIRTUAL_AUDIO_ROUTING_ARCHITECTURE.md
│   └── README.md
├── native-engine/                     # Native Audio Engine (PipeWire + Gemini Live with ADC)
│   ├── auth.py                        # Google ADC OAuth2 token manager
│   ├── gemini_live.py                 # Bidirectional Gemini Live WebSocket client
│   ├── pipewire_devices.py            # Automatic UVT-Mic & UVT-Speaker manager
│   └── daemon.py                      # Core audio orchestration daemon
├── chrome-extension/                  # Chrome Side Panel Extension (Manifest V3)
│   ├── manifest.json                  # Manifest V3 extension configuration
│   ├── background/
│   │   └── service-worker.js          # Background service worker & IPC
│   └── sidepanel/
│       ├── sidepanel.html             # Side Panel UI layout
│       ├── sidepanel.css              # Styling & VU meters
│       └── sidepanel.js               # Side panel controller
├── pyproject.toml                     # Python dependencies & build configuration
├── .gitignore                         # Git ignore configuration
└── README.md                          # Project documentation
```

---

## 👤 Author

**Mehdi Golzari**
- GitHub: [@mgmehdiforme](https://github.com/mgmehdiforme)
- Email: `i.entersoft@gmail.com`
