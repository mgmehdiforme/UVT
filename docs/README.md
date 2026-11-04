# UVT (Universal Voice Translator) Documentation Suite
## Real-Time Speech-to-Speech Translation in Chrome Side Panel with Virtual Audio Routing

Welcome to the architectural and product documentation for **UVT (Universal Voice Translator)**.

UVT is a next-generation real-time voice translation application designed as a **Google Chrome Side Panel Extension** coupled with a high-performance **Native Audio Companion**. It allows users to conduct natural, fluent conversations across language barriers in Google Meet, Zoom, Microsoft Teams, Discord, and Slack without external meeting bots, high cascade latency, or robotic TTS speech.

---

## 📚 Documentation Index

| Document | Purpose & Summary |
| :--- | :--- |
| **[01_PRODUCT_SPECIFICATION.md](./01_PRODUCT_SPECIFICATION.md)** | **Product Requirements Document (PRD):** Vision, user personas, functional requirements (FR-01 to FR-15), user journeys, non-functional requirements (latency $\le 750\text{ms}$), and UI/UX design. |
| **[02_TECHNICAL_SPECIFICATION.md](./02_TECHNICAL_SPECIFICATION.md)** | **System Architecture & IPC:** Hybrid architecture (Chrome Side Panel MV3 + Native Engine), audio stream topology, IPC protocol, Manifest V3 blueprint, and failure recovery. |
| **[03_GEMINI_TRANSLATION_MODEL_GUIDE.md](./03_GEMINI_TRANSLATION_MODEL_GUIDE.md)** | **AI Model Deep Dive:** Gemini 2.0 Multimodal Live API (`BidiGenerateContent` WebSocket), Speech-to-Speech (S2S) streaming, strict zero-commentary system prompts, barge-in interruption handling, audio framing (16kHz PCM $\leftrightarrow$ 24kHz PCM), and complete Python client implementation. |
| **[04_VIRTUAL_AUDIO_ROUTING_ARCHITECTURE.md](./04_VIRTUAL_AUDIO_ROUTING_ARCHITECTURE.md)** | **Virtual Devices & OS Audio:** Creating and managing `UVT-Mic` (Virtual Source) and `UVT-Speaker` (Virtual Sink) on Linux PipeWire 1.6+ / WirePlumber, ring buffers, anti-feedback isolation, and verification commands. |

---

## 🚀 Architectural Blueprint at a Glance

```mermaid
graph TD
    subgraph Host_OS [Host OS & User Peripherals]
        PhysicalMic[Physical Microphone]
        PhysicalSpeaker[Physical Headphones / Speaker]
    end

    subgraph Native_Audio_Bridge [UVT Native Engine (PipeWire / Python 3.12)]
        RingBufTX[TX Resampler 48k to 16k]
        RingBufRX[RX Resampler 24k to 48k]
        VirtualMicNode["UVT-Mic (Virtual Audio Source)"]
        VirtualSpeakerNode["UVT-Speaker (Virtual Audio Sink)"]
    end

    subgraph Chrome_Browser [Google Chrome]
        SidePanel["UVT Side Panel (HTML5 / JS / VU Meters)"]
        MeetingTab["Google Meet / Zoom Web Tab"]
    end

    subgraph Google_Cloud [Google Gemini Infrastructure]
        GeminiTX["Gemini Live API (TX Session: fa -> en)"]
        GeminiRX["Gemini Live API (RX Session: en -> fa)"]
    end

    %% Outbound Audio Flow
    PhysicalMic -->|Raw 48kHz PCM| RingBufTX
    RingBufTX -->|16kHz PCM Base64| GeminiTX
    GeminiTX -->|24kHz Translated Audio| VirtualMicNode
    VirtualMicNode -->|Input Microphone| MeetingTab

    %% Inbound Audio Flow
    MeetingTab -->|Meeting Audio Output| VirtualSpeakerNode
    VirtualSpeakerNode -->|Capture Monitor 16kHz| GeminiRX
    GeminiRX -->|24kHz Translated Audio| RingBufRX
    RingBufRX -->|Playback 48kHz| PhysicalSpeaker

    %% IPC & Control
    SidePanel <-->|Native Messaging / Local RPC| Native_Audio_Bridge
```

---

## 🌟 Key Highlights & Engineering Breakthroughs

1. **Direct Speech-to-Speech (S2S):** Eliminates the traditional 3-stage cascade (Whisper + MT + TTS) which incurs 2.5s+ latency. Gemini 2.0 Flash S2S delivers translated speech in **sub-second latency ($< 700\text{ms}$)** with natural prosody and emotional cadence.
2. **Dual-Session Isolation:** Running two dedicated Gemini Multimodal Live WebSocket connections (one for Outbound TX, one for Inbound RX) completely prevents conversational context bleeding and self-answering hallucinations.
3. **OS-Level Virtual Nodes (`UVT-Mic` & `UVT-Speaker`):** Works with any meeting platform out-of-the-box. Google Meet or Zoom simply selects `UVT-Mic` as the microphone and `UVT-Speaker` as the speaker.
4. **Native Barge-In / Interruption:** If you interrupt or speak over a translation, Gemini's `interrupted: true` signal automatically purges outdated audio from the output ring buffer instantly.
5. **Chrome Side Panel Ergonomics:** Designed to stay pinned right beside your Google Meet tab with live dual-language subtitles, volume meters, and one-click pass-through controls.

---

## 📅 Next Steps & Implementation Path

- **Phase 1 (Complete):** Architecture, PRD, Technical Specs, Audio Routing & Gemini Live Model Guides.
- **Phase 2:** Implement the Native Companion script (`uvt_bridge.py`) and verify PipeWire virtual node creation.
- **Phase 3:** Implement the Gemini Live dual-session client and test real-time speech translation with physical audio devices.
- **Phase 4:** Scaffold and build the Chrome Extension Side Panel UI (Manifest V3) and link with Native Messaging.
- **Phase 5:** End-to-end testing with Google Meet and Zoom.
