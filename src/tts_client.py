"""TTS (GPT-SoVITS) API client - fully configurable via config.yaml"""

import requests
from typing import Optional


class TTSClient:
    """GPT-SoVITS TTS API wrapper"""

    def __init__(self, base_url: str = "http://127.0.0.1:9880"):
        self.base_url = base_url.rstrip("/")

    def synthesize(
        self,
        text: str,
        speed: float = 0.85,
        temperature: float = 1.0,
        top_k: int = 12,
        top_p: float = 0.9,
    ) -> bytes:
        """Synthesize speech from text. Returns WAV audio bytes."""
        params = {
            "text": text,
            "text_lang": "zh",
            "ref_audio_path": "",
            "prompt_text": "",
            "prompt_lang": "zh",
            "text_split_method": "cut0",
            "speed_factor": speed,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
        }
        resp = requests.get(
            f"{self.base_url}/tts",
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.content

    def get_voices(self) -> list[str]:
        """List available voice roles"""
        try:
            resp = requests.get(f"{self.base_url}/voice_list", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return [v["name"] for v in data if "name" in v]
        except (requests.RequestException, ValueError, KeyError):
            pass
        return []

    def set_voice(self, voice_name: str) -> bool:
        """Switch active voice"""
        try:
            payload = {"voice": voice_name}
            resp = requests.post(
                f"{self.base_url}/set_voice",
                json=payload,
                timeout=10,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def health_check(self) -> bool:
        """Check if TTS server is running"""
        try:
            resp = requests.get(f"{self.base_url}/status", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False
