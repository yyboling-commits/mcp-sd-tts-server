"""SD WebUI API wrapper"""

import requests
import base64
from typing import Optional


class SDClient:
    """Stable Diffusion WebUI API wrapper"""

    def __init__(self, base_url: str = "http://127.0.0.1:7860"):
        self.base_url = base_url.rstrip("/")
        self._available_models: list[str] = []

    def txt2img(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 896,
        height: int = 1344,
        steps: int = 20,
        cfg_scale: float = 5.0,
        sampler_name: str = "Euler",
        seed: int = -1,
        model_name: Optional[str] = None,
    ) -> tuple[bytes, int]:
        """Generate image from text prompt. Returns (image_bytes, used_seed)"""
        if model_name:
            self._set_model(model_name)

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler_name,
            "seed": seed,
        }

        resp = requests.post(
            f"{self.base_url}/sdapi/v1/txt2img",
            json=payload,
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()

        img_b64 = data["images"][0]
        img_bytes = base64.b64decode(img_b64)
        used_seed = data.get("seed", seed)

        return img_bytes, used_seed

    def get_models(self) -> list[str]:
        """List available checkpoint models"""
        resp = requests.get(f"{self.base_url}/sdapi/v1/sd-models", timeout=30)
        resp.raise_for_status()
        self._available_models = [m["title"] for m in resp.json()]
        return self._available_models

    def _set_model(self, model_name: str):
        """Switch active model"""
        payload = {"sd_model_checkpoint": model_name}
        requests.post(
            f"{self.base_url}/sdapi/v1/options",
            json=payload,
            timeout=60,
        ).raise_for_status()

    def health_check(self) -> bool:
        """Check if SD WebUI is running"""
        try:
            resp = requests.get(f"{self.base_url}/sdapi/v1/sd-models", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False
