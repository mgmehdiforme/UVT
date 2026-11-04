"""
pipewire_devices.py - Dynamic PipeWire Virtual Node Manager for UVT
"""
import logging
import subprocess
import time
from typing import Optional

logger = logging.getLogger("UVT.PipeWire")

class PipeWireDeviceManager:
    """
    Manages creation and teardown of UVT-Mic (Audio Source) and
    UVT-Speaker (Audio Sink) using Linux PipeWire pw-loopback.
    """
    def __init__(self):
        self.speaker_proc: Optional[subprocess.Popen] = None
        self.mic_proc: Optional[subprocess.Popen] = None

    def start_devices(self) -> bool:
        """Initializes both UVT-Speaker and UVT-Mic virtual nodes."""
        logger.info("Starting UVT PipeWire virtual devices...")

        # 1. Start UVT-Speaker (Audio Sink for Meeting Output)
        speaker_cmd = [
            "pw-loopback",
            "--name", "UVT-Speaker-Daemon",
            "--capture-props=media.class=Audio/Sink node.name=UVT_Speaker node.description=\"UVT Meeting Speaker\" audio.position=[FL FR]",
            "--playback-props=node.name=UVT_Speaker_Dummy node.description=\"UVT Speaker Dummy Sink\" node.passive=true"
        ]
        
        # 2. Start UVT-Mic (Audio Source for Meeting Microphone Input)
        mic_cmd = [
            "pw-loopback",
            "--name", "UVT-Mic-Daemon",
            "--capture-props=node.name=UVT_Mic_Feed node.description=\"UVT Mic Feed Input\" node.passive=true",
            "--playback-props=media.class=Audio/Source node.name=UVT_Mic node.description=\"UVT Translated Microphone\" audio.position=[FL FR]"
        ]

        try:
            self.speaker_proc = subprocess.Popen(speaker_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.mic_proc = subprocess.Popen(mic_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)  # Allow WirePlumber to register nodes
            logger.info("UVT-Speaker and UVT-Mic virtual nodes are active!")
            return True
        except Exception as e:
            logger.error(f"Failed to start PipeWire virtual devices: {e}", exc_info=True)
            self.stop_devices()
            return False

    def stop_devices(self):
        """Terminates virtual device processes and cleans up PipeWire graph."""
        logger.info("Stopping UVT PipeWire virtual devices...")
        for proc in (self.speaker_proc, self.mic_proc):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self.speaker_proc = None
        self.mic_proc = None
        logger.info("PipeWire virtual nodes destroyed.")

    def __enter__(self):
        self.start_devices()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_devices()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = PipeWireDeviceManager()
    try:
        manager.start_devices()
        print("Devices active! Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_devices()
