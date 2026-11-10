import asyncio
import os
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
import edge_tts

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from noise_lab.generate_noise import (
    apply_telephony_channel,
    generate_fan_hum,
    generate_traffic_noise,
    generate_market_babble,
    mix_speech_and_noise
)

def generate_synthetic_noise(noise_type: str, duration: float, sr: int):
    if noise_type == "traffic":
        return generate_traffic_noise(duration, sample_rate=sr)
    elif noise_type == "fan":
        return generate_fan_hum(duration, sample_rate=sr)
    elif noise_type == "market":
        return generate_market_babble(duration, sample_rate=sr)
    else:
        return np.zeros(int(duration * sr), dtype=np.float32)

AUDIO_DIR = PROJECT_ROOT / "audio_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

TEST_UTTERANCES = [
    {
        "id": "clip_1_brand_keyterms",
        "text": "भैया 2 किलो बासमती चावल, 1 Maggi masala, 2 Kurkure और 1 litre Arogyam oil लिख लो, बस इतना ही।",
        "voice": "hi-IN-MadhurNeural",
        "snr_db": 5,
        "noise_type": "traffic"
    },
    {
        "id": "clip_2_ambiguous_rice",
        "text": "भैया 5 किलो आशीर्वाद आटा, ढाई किलो चावल और 2 almond oil भेज देना।",
        "voice": "hi-IN-SwaraNeural",
        "snr_db": 20,
        "noise_type": "fan"
    },
    {
        "id": "clip_3_colloquial_fractions",
        "text": "नमस्ते गुप्ता जी, सवा दो किलो आशीर्वाद आटा, आधा किलो तूर दाल, 1 Tata नमक, बस इतना ही।",
        "voice": "hi-IN-MadhurNeural",
        "snr_db": 0,
        "noise_type": "market"
    },
    {
        "id": "clip_4_dairy_snacks",
        "text": "भैया 2 packet अमूल ताज़ा दूध, 1 Amul butter, 2 Parle-G बिस्कुट और 1 Vim bar, हो गया।",
        "voice": "hi-IN-SwaraNeural",
        "snr_db": 10,
        "noise_type": "fan"
    },
    {
        "id": "clip_5_kannada_hinglish",
        "text": "नमस्ते, 2 किलो इंडिया गेट बासमती चावल, 1 किलो तूर दाल और 1 पैकेट टाटा नमक पैक कर दो, बस इतना ही।",
        "voice": "hi-IN-MadhurNeural",
        "snr_db": 20,
        "noise_type": "clean"
    }
]

async def synthesize_clip(text: str, voice: str, out_path: Path):
    communicate = edge_tts.Communicate(text, voice)
    temp_mp3 = out_path.with_suffix(".mp3")
    await communicate.save(str(temp_mp3))
    
    # Read with soundfile and resample to 16 kHz float32
    data, sr = sf.read(str(temp_mp3))
    if len(data.shape) > 1:
        data = np.mean(data, axis=1) # Mono
    
    # Save clean 16 kHz WAV
    sf.write(str(out_path), data, sr)
    if temp_mp3.exists():
        temp_mp3.unlink()
    return data, sr

async def main():
    print("Generating 5 Test Audio Clips & Telephony Noisy Variants...")
    
    for item in TEST_UTTERANCES:
        clean_wav = AUDIO_DIR / f"{item['id']}_clean_16khz.wav"
        print(f"\nSynthesizing Clean Audio -> {clean_wav.name}...")
        speech_data, sr = await synthesize_clip(item["text"], item["voice"], clean_wav)
        
        # 1. Apply 8 kHz downsampler + ITU-T G.711 mu-law codec
        telephony_audio, target_sr = apply_telephony_channel(speech_data, orig_sr=sr)
        
        # 2. Generate environmental noise matching the tier
        duration = len(telephony_audio) / target_sr
        noise = generate_synthetic_noise(item["noise_type"], duration, sr=target_sr)
        
        # 3. Mix at specified SNR
        noisy_telephony_audio = mix_speech_and_noise(telephony_audio, noise, target_snr_db=item["snr_db"])
        
        # Save noisy telephony file
        noisy_wav = AUDIO_DIR / f"{item['id']}_telephony_{item['noise_type']}_{item['snr_db']}db.wav"
        sf.write(str(noisy_wav), noisy_telephony_audio, target_sr)
        print(f"Generated Noisy Telephony -> {noisy_wav.name} (8 kHz μ-Law, {item['snr_db']} dB SNR)")
        
    print("\nAll 5 test audio clips and telephony noise variants generated successfully in audio_samples/!")

if __name__ == "__main__":
    asyncio.run(main())
