# UVT (Universal Voice Translator)
## Virtual Audio Routing & Device Architecture Specification

- **Document Version:** 1.0.0
- **Primary Audio Server:** Linux PipeWire 1.6+ with WirePlumber Session Manager
- **Virtual Nodes:** `UVT-Mic` (Audio Source) & `UVT-Speaker` (Audio Sink)
- **Audio Engine:** Low-Latency Non-Blocking Ring Buffers (`sounddevice` + `numpy`)

---

## 1. Architectural Overview of Virtual Audio Nodes

In standard operating system audio graphs, physical hardware represents real microphones and speakers. UVT injects two persistent, software-defined **virtual audio nodes** into the graph:

```
+--------------------------------------------------------------------------------------------------+
|                                    OPERATING SYSTEM AUDIO GRAPH                                  |
|                                                                                                  |
|   +--------------------------+                                     +--------------------------+  |
|   |   PHYSICAL MICROPHONE    |                                     |    PHYSICAL HEADPHONES   |  |
|   |  (e.g., HK 2M CAM USB)   |                                     |  (Built-in Stereo Sink)  |  |
|   +------------+-------------+                                     +------------^-------------+  |
|                |                                                                |                |
|                v [Capture Raw]                                                  | [Play Translated]
|   +------------+-------------+                                     +------------+-------------+  |
|   |      UVT DAEMON          |                                     |        UVT DAEMON        |  |
|   |   (TX Audio Engine)      |                                     |    (RX Audio Engine)     |  |
|   +------------+-------------+                                     +------------^-------------+  |
|                |                                                                |                |
|                | [Write Translated]                                             | [Read Monitor] |
|                v                                                                |                |
|   +--------------------------+                                     +------------+-------------+  |
|   |        UVT-MIC           |                                     |       UVT-SPEAKER        |  |
|   |  (Virtual Audio Source)  |                                     |   (Virtual Audio Sink)   |  |
|   +------------+-------------+                                     +------------^-------------+  |
|                |                                                                |                |
|                \-----------------------------\    /-----------------------------/                |
|                                              |    |                                              |
|                                              v    |                                              |
|                           +-------------------------------------+                                |
|                           |      GOOGLE MEET / ZOOM / TEAMS     |                                |
|                           |                                     |                                |
|                           |   Microphone: "UVT-Mic"             |                                |
|                           |   Speaker:    "UVT-Speaker"         |                                |
|                           +-------------------------------------+                                |
+--------------------------------------------------------------------------------------------------+
```

### 1.1 `UVT-Mic` (Virtual Source / Microphone)
- **OS Class:** `Audio/Source`
- **Purpose:** Acts as the microphone for external communication apps (Google Meet, Zoom, Slack, Discord).
- **Audio Source:** Fed directly by UVT's translated Outbound (TX) stream.
- **Experience for Others:** Meeting attendees hear the user speaking fluent, translated English with natural cadence and tone.

### 1.2 `UVT-Speaker` (Virtual Sink / Speaker)
- **OS Class:** `Audio/Sink`
- **Purpose:** Acts as the audio output destination for external communication apps.
- **Audio Capture:** UVT taps into `UVT-Speaker.monitor` (PipeWire's built-in monitor stream) to capture foreign speech before it reaches physical speakers.
- **Audio Destination:** Sent to Gemini Live RX $\rightarrow$ Translated speech is rendered privately to the user's physical headphones.
- **Experience for User:** The user hears all foreign speech translated live into their native language (e.g., Persian).

---

## 2. PipeWire Implementation Details (Linux)

Linux systems running PipeWire (such as Ubuntu 24.04+ with PipeWire 1.6.2 and WirePlumber) manage audio streams through dynamic node graphs. Virtual devices can be registered via two methods:

### Method A: Dynamic Process-Level Nodes via `pw-loopback` (Recommended for UVT)
This method allows the UVT Native Companion to spin up and tear down virtual devices dynamically when a session starts and stops, without modifying system configuration files or requiring `sudo` privileges.

#### 1. Creating `UVT-Speaker` (Virtual Sink)
```bash
pw-loopback \
  --name "UVT-Speaker-Daemon" \
  --capture-props='media.class=Audio/Sink node.name=UVT_Speaker node.description="UVT Meeting Speaker" audio.position=[FL FR]' \
  --playback-props='node.name=UVT_Speaker_Dummy node.description="UVT Speaker Dummy Sink" node.passive=true' &
```
*Properties Explained:*
- `media.class=Audio/Sink`: Instructs WirePlumber to expose this node to the desktop environment and browser as a valid **Speaker/Output** device.
- `node.name=UVT_Speaker`: Canonical identifier for audio routing.
- `node.description="UVT Meeting Speaker"`: The friendly label shown in Google Meet's audio settings dropdown.

#### 2. Creating `UVT-Mic` (Virtual Source)
```bash
pw-loopback \
  --name "UVT-Mic-Daemon" \
  --capture-props='node.name=UVT_Mic_Feed node.description="UVT Mic Feed Input" node.passive=true' \
  --playback-props='media.class=Audio/Source node.name=UVT_Mic node.description="UVT Translated Microphone" audio.position=[FL FR]' &
```
*Properties Explained:*
- `media.class=Audio/Source`: Instructs WirePlumber to expose this node as an **Audio Input / Microphone** device.
- `node.name=UVT_Mic`: Canonical identifier.
- `node.description="UVT Translated Microphone"`: The friendly label shown in Google Meet's microphone dropdown.
- Audio written to `UVT_Mic_Feed` automatically loops through PipeWire and becomes available on `UVT_Mic`!

---

### Method B: Persistent PipeWire Configuration File
For users who prefer permanent virtual devices that survive reboots, a configuration drop-in can be placed in `~/.config/pipewire/pipewire.conf.d/99-uvt-devices.conf`:

```spa-json
# ~/.config/pipewire/pipewire.conf.d/99-uvt-devices.conf
context.modules = [
    {   name = libpipewire-module-loopback
        args = {
            node.name = "UVT_Speaker"
            node.description = "UVT Meeting Speaker"
            capture.props = {
                media.class = "Audio/Sink"
                audio.position = [ "FL", "FR" ]
            }
            playback.props = {
                node.name = "UVT_Speaker_Loop"
                node.passive = true
            }
        }
    }
    {   name = libpipewire-module-loopback
        args = {
            node.name = "UVT_Mic"
            node.description = "UVT Translated Microphone"
            capture.props = {
                node.name = "UVT_Mic_Loop"
                node.passive = true
            }
            playback.props = {
                media.class = "Audio/Source"
                audio.position = [ "FL", "FR" ]
            }
        }
    }
]
```

---

## 3. Audio Stream Hooking & Ring Buffer Architecture

UVT's Native Companion manages four concurrent audio streams with zero-latency thread isolation using Python's `sounddevice` (PortAudio/ALSA/PipeWire backend) and `numpy`:

```
STREAM 1: Capture from Physical Mic (Input Device)
          ==> Buffer A ==> Resample 48k->16k ==> Gemini Live TX WebSocket

STREAM 2: Playback to UVT-Mic (Output Device)
          <== Buffer B <== Resample 24k->48k <== Gemini Live TX WebSocket

STREAM 3: Capture from UVT-Speaker Monitor (Input Device)
          ==> Buffer C ==> Resample 48k->16k ==> Gemini Live RX WebSocket

STREAM 4: Playback to Physical Headphones (Output Device)
          <== Buffer D <== Resample 24k->48k <== Gemini Live RX WebSocket
```

### 3.1 Lock-Free Circular Ring Buffer Design
To avoid audio stuttering during CPU spikes or GC pauses, audio chunks are exchanged through bounded, pre-allocated NumPy ring buffers:

```python
import numpy as np
import threading

class AudioRingBuffer:
    def __init__(self, capacity_samples: int = 48000 * 2, channels: int = 1, dtype=np.int16):
        self.capacity = capacity_samples
        self.channels = channels
        self.dtype = dtype
        self.buffer = np.zeros((self.capacity, self.channels), dtype=dtype)
        self.write_pos = 0
        self.read_pos = 0
        self.lock = threading.Lock()

    def write(self, data: np.ndarray):
        with self.lock:
            n = len(data)
            if n > self.capacity:
                data = data[-self.capacity:]
                n = len(data)
            
            # Wrap-around write
            end_pos = self.write_pos + n
            if end_pos <= self.capacity:
                self.buffer[self.write_pos:end_pos] = data
            else:
                first_part = self.capacity - self.write_pos
                self.buffer[self.write_pos:] = data[:first_part]
                self.buffer[:end_pos - self.capacity] = data[first_part:]
            self.write_pos = end_pos % self.capacity

    def read(self, num_samples: int) -> np.ndarray:
        with self.lock:
            # Check available
            available = (self.write_pos - self.read_pos) % self.capacity
            if available < num_samples:
                # Underrun: return available padded with silence
                out = np.zeros((num_samples, self.channels), dtype=self.dtype)
                if available > 0:
                    read_end = self.read_pos + available
                    if read_end <= self.capacity:
                        out[:available] = self.buffer[self.read_pos:read_end]
                    else:
                        first = self.capacity - self.read_pos
                        out[:first] = self.buffer[self.read_pos:]
                        out[first:available] = self.buffer[:read_end - self.capacity]
                    self.read_pos = (self.read_pos + available) % self.capacity
                return out

            read_end = self.read_pos + num_samples
            if read_end <= self.capacity:
                out = self.buffer[self.read_pos:read_end].copy()
            else:
                first = self.capacity - self.read_pos
                out = np.empty((num_samples, self.channels), dtype=self.dtype)
                out[:first] = self.buffer[self.read_pos:]
                out[first:] = self.buffer[:read_end - self.capacity]
            self.read_pos = read_end % self.capacity
            return out

    def clear(self):
        with self.lock:
            self.write_pos = 0
            self.read_pos = 0
            self.buffer.fill(0)
```

---

## 4. Acoustic Isolation & Anti-Feedback Protocol

A major pitfall in bidirectional voice translation is **acoustic feedback**:
If the translated audio playing out of `UVT-Speaker` leaks into the user's real microphone, the system could translate its own translated speech in an endless feedback loop!

UVT enforces three layers of acoustic isolation:

```
+-----------------------------------------------------------------------------------------------+
|                                    ACOUSTIC ISOLATION LAYERS                                  |
|                                                                                               |
|  [ Layer 1: Device Segregation ]                                                              |
|  UVT-Speaker is mapped EXCLUSIVELY to physical headphones. Output audio is NEVER played      |
|  through open loudspeaker monitors where the physical microphone could pick it up.           |
|                                                                                               |
|  [ Layer 2: Signal Muting During Speech (Half-Duplex Guard Option) ]                           |
|  When user is actively speaking into the physical mic, RX playback gain can be attenuated    |
|  by 12dB (ducking) to prevent bleed.                                                          |
|                                                                                               |
|  [ Layer 3: PipeWire Node Pinning ]                                                           |
|  WirePlumber routing rules explicitly link UVT_Speaker only to UVT's monitor capture stream,  |
|  preventing accidental system-wide broadcast.                                                 |
+-----------------------------------------------------------------------------------------------+
```

---

## 5. Verification & Diagnostics Runbook

To verify that PipeWire has registered the virtual nodes correctly, execute the following commands:

### 5.1 Listing Audio Devices via `wpctl`
```bash
wpctl status
```
*Expected Output:*
```text
Audio
 ├─ Sinks:
 │      59. Built-in Audio Analog Stereo
 │  *   92. UVT Meeting Speaker                 [vol: 1.00]
 │  
 ├─ Sources:
 │      56. HK 2M CAM Digital Stereo
 │  *   93. UVT Translated Microphone           [vol: 1.00]
```

### 5.2 Testing Audio Flow through `UVT-Speaker`
To verify that audio sent to `UVT-Speaker` can be captured from its monitor stream:
```bash
# 1. Play test tone to UVT_Speaker in terminal 1
pw-play --target=UVT_Speaker /usr/share/sounds/alsa/Front_Center.wav

# 2. Record from UVT_Speaker monitor in terminal 2
pw-record --target=UVT_Speaker test_capture.wav
```

### 5.3 Verifying Google Meet Detection
1. Open Google Chrome $\rightarrow$ navigate to `meet.google.com/new`.
2. Click **More options (...) $\rightarrow$ Settings $\rightarrow$ Audio**.
3. Under **Microphone**, confirm `UVT Translated Microphone` is listed and selectable.
4. Under **Speakers**, confirm `UVT Meeting Speaker` is listed and selectable.
