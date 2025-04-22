"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import requests
from pydub import AudioSegment
import io
import urllib.parse
import base64

def generate_tts(
    text: str,
    service: str = "StreamElements",
    voice: str = "Brian",
    lang: str = "English",
    g_param: str = "A",
    headers: dict = None,
    api_url: str = "https://lazypy.ro/tts/request_ts.php",
) -> dict:
    """
    Convert text to speech and return MP3/WAV bytes.
    
    Args:
        text: Input text to convert
        service: TTS service provider (default: StreamElements)
        voice: Voice to use (default: Brian)
        lang: Language (default: English)
        g_param: Mystery parameter from original request (default: A)
        headers: Custom headers (optional)
        api_url: TTS endpoint URL
    
    Returns:
        Dictionary with 'mp3' and 'wav' keys containing bytes
    
    Requires:
        - requests
        - pydub
        - ffmpeg (system installation)
    """
    # Prepare POST data
    data = {
        "service": service,
        "voice": voice,
        "text": text,
        "lang": lang,
    }

    # Build referrer URL
    referrer_params = {
        "voice": voice,
        "service": service,
        "text": text,
        "lang": lang,
        "g": g_param,
    }
    query_string = "&".join(
        [f"{urllib.parse.quote(k)}={urllib.parse.quote(v)}" for k, v in referrer_params.items()]
    )
    referrer_url = f"https://lazypy.ro/tts/?{query_string}"

    # Set default headers
    if headers is None:
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,de-DE;q=0.8,de;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
        }
    headers["Referer"] = referrer_url

    # Make TTS request
    response = requests.post(api_url, data=data, headers=headers)
    response.raise_for_status()
    result = response.json()

    if not result.get("success"):
        raise RuntimeError(f"TTS failed: {result.get('error_msg', 'Unknown error')}")

    # Download audio
    mp3_response = requests.get(result["audio_url"])
    mp3_response.raise_for_status()
    mp3_bytes = mp3_response.content

    # Convert to WAV
    with io.BytesIO(mp3_bytes) as mp3_buffer:
        audio = AudioSegment.from_file(mp3_buffer, format="mp3")
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_bytes = wav_buffer.getvalue()

    return {
        "mp3": base64.b64encode(mp3_bytes).decode(),
        "wav": base64.b64encode(wav_bytes).decode()
    }

# Example usage
if __name__ == "__main__":
    result = generate_tts("Hello, this is a test!")
    print(f"MP3 size: {len(result['mp3'])} bytes")
    print(f"WAV size: {len(result['wav'])} bytes")