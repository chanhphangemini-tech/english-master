"""
Script để test và xác thực các giọng Edge TTS có sẵn.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import edge_tts
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List các giọng tiếng Anh tự nhiên để test
TEST_VOICES = [
    "en-US-AriaNeural",  # Hiện tại
    "en-US-JennyNeural",  # Nữ, Mỹ, rất tự nhiên
    "en-US-MichelleNeural",  # Nữ, Mỹ
    "en-US-ChristopherNeural",  # Nam, Mỹ
    "en-US-GuyNeural",  # Nam, Mỹ
    "en-GB-SoniaNeural",  # Nữ, Anh
    "en-GB-RyanNeural",  # Nam, Anh
    "en-AU-NatashaNeural",  # Nữ, Úc
]

TEST_TEXT = "Hello, this is a test of the text to speech system. The voice should sound natural and clear."

async def list_all_voices():
    """List tất cả voices có sẵn trong Edge TTS."""
    print("=" * 60)
    print("Available Edge TTS Voices")
    print("=" * 60)
    try:
        voices = await edge_tts.list_voices()
        english_voices = [v for v in voices if v['Locale'].startswith('en-')]
        
        print(f"\nTotal English voices: {len(english_voices)}\n")
        
        # Group by locale
        by_locale = {}
        for voice in english_voices:
            locale = voice['Locale']
            if locale not in by_locale:
                by_locale[locale] = []
            by_locale[locale].append(voice)
        
        for locale in sorted(by_locale.keys()):
            print(f"\n{locale}:")
            for voice in by_locale[locale]:
                gender = voice.get('Gender', 'Unknown')
                name = voice.get('ShortName', voice.get('Name', 'Unknown'))
                print(f"  - {name} ({gender})")
        
        return english_voices
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        return []

async def test_voice(voice_name, text):
    """Test một voice cụ thể."""
    try:
        communicate = edge_tts.Communicate(text, voice_name)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        if audio_data and len(audio_data) > 0:
            return True, len(audio_data)
        else:
            return False, 0
    except Exception as e:
        logger.error(f"Error testing voice {voice_name}: {e}")
        return False, 0

async def verify_voices():
    """Verify các voices trong TEST_VOICES có tồn tại và hoạt động không."""
    print("\n" + "=" * 60)
    print("Voice Verification")
    print("=" * 60)
    
    # Get all available voices
    all_voices = await edge_tts.list_voices()
    available_names = {v.get('ShortName') or v.get('Name'): v for v in all_voices}
    
    print(f"\nTesting {len(TEST_VOICES)} voices...\n")
    
    verified_voices = []
    for voice_name in TEST_VOICES:
        if voice_name in available_names:
            voice_info = available_names[voice_name]
            success, size = await test_voice(voice_name, TEST_TEXT)
            status = "OK" if success else "FAIL"
            gender = voice_info.get('Gender', 'Unknown')
            locale = voice_info.get('Locale', 'Unknown')
            
            print(f"{voice_name}: {status} ({gender}, {locale})")
            if success:
                verified_voices.append({
                    'name': voice_name,
                    'gender': gender,
                    'locale': locale,
                    'info': voice_info
                })
        else:
            print(f"{voice_name}: NOT FOUND")
    
    print(f"\nVerified voices: {len(verified_voices)}/{len(TEST_VOICES)}")
    
    # Recommend best voice for comprehension
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    
    # Prefer female US voices for comprehension (clearer, more natural)
    recommended = None
    for voice in verified_voices:
        if voice['locale'] == 'en-US' and voice['gender'] == 'Female':
            if voice['name'] == 'en-US-JennyNeural':
                recommended = voice
                break
    
    if not recommended and verified_voices:
        # Fallback to first female US voice
        for voice in verified_voices:
            if voice['locale'] == 'en-US' and voice['gender'] == 'Female':
                recommended = voice
                break
    
    if recommended:
        print(f"\nRecommended voice for comprehension: {recommended['name']}")
        print(f"  Gender: {recommended['gender']}")
        print(f"  Locale: {recommended['locale']}")
        print(f"\nReason: Female US voices are generally clearer and more natural")
        print(f"for educational content, especially for listening comprehension.")
    else:
        print("\nCould not find suitable voice. Using current: en-US-AriaNeural")
    
    return verified_voices, recommended

async def main():
    print("Edge TTS Voice Test Script")
    print("=" * 60)
    
    # List all voices
    await list_all_voices()
    
    # Verify test voices
    verified, recommended = await verify_voices()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
