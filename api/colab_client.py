# api/colab_client.py
import os
import requests

COLAB_API_URL = os.environ.get("COLAB_API_URL", "")

class ColabNotConfigured(Exception):
    pass

def call_colab_compare(description: str, seed: int = 42, controlnet_scale: float = 0.75) -> dict:
    """Calls the Colab-hosted ControlNet+LoRA API (scripts/colab_server.py).
    Raises ColabNotConfigured if COLAB_API_URL isn't set, or requests
    exceptions on network/timeout failure -- let the caller in main.py
    decide how to surface those to the frontend."""
    url = os.environ.get("COLAB_API_URL", "") or COLAB_API_URL
    if not url:
        raise ColabNotConfigured(
            "COLAB_API_URL is not set in .env. Start scripts/colab_server.py "
            "in Colab and paste the printed ngrok URL into .env."
        )
    resp = requests.post(
        f"{url.rstrip('/')}/compare",
        json={"description": description, "seed": seed, "controlnet_scale": controlnet_scale},
        headers={"ngrok-skip-browser-warning": "1"},
        timeout=900,  # ControlNet baseline+refine often >5 min on Colab
    )
    resp.raise_for_status()
    return resp.json()
