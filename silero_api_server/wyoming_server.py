import asyncio
import logging
from pathlib import Path
from typing import Optional

from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.event import Event
from wyoming.info import Describe, Info, TtsVoice, TtsProgram, Attribution
from wyoming.server import AsyncTcpServer, AsyncEventHandler
from wyoming.tts import Synthesize

from silero_api_server.tts import SileroTtsService
from pydub import AudioSegment

_LOGGER = logging.getLogger(__name__)

class SileroWyomingHandler(AsyncEventHandler):
    def __init__(self, tts_service: SileroTtsService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tts_service = tts_service

    async def handle_event(self, event: Event) -> bool:
        if Describe.is_type(event.type):
            voices = []
            attribution = Attribution(name="Silero", url="https://github.com/snakers4/silero-models")
            for speaker in self.tts_service.get_speakers():
                voices.append(TtsVoice(
                    name=speaker,
                    description=f"Silero speaker {speaker}",
                    languages=["ru"],
                    attribution=attribution,
                    installed=True
                ))
            
            info = Info(tts=[TtsProgram(voices=voices)])
            await self.write_event(info.event())
            return True

        if Synthesize.is_type(event.type):
            synthesize = Synthesize.from_event(event)
            _LOGGER.info(f"Synthesizing: {synthesize.text} with voice {synthesize.voice.name}")
            
            voice = synthesize.voice.name if synthesize.voice else "baya"
            # Generate audio using the service
            audio_path = self.tts_service.generate(voice, synthesize.text)
            
            # Load and convert to PCM 16-bit 22050Hz Mono (standard for Wyoming)
            audio = AudioSegment.from_file(audio_path)
            audio = audio.set_frame_rate(22050).set_channels(1).set_sample_width(2)
            raw_data = audio.raw_data
            
            # Send AudioStart
            await self.write_event(AudioStart(rate=22050, width=2, channels=1).event())
            
            # Send AudioChunks
            chunk_size = 2048
            for i in range(0, len(raw_data), chunk_size):
                chunk_data = raw_data[i:i+chunk_size]
                await self.write_event(AudioChunk(rate=22050, width=2, channels=1, audio=chunk_data).event())
                
            # Send AudioStop
            await self.write_event(AudioStop().event())
            return False # Close connection after synthesis

        return True

class SileroWyomingServer(AsyncTcpServer):
    def __init__(self, host: str, port: int, tts_service: SileroTtsService):
        super().__init__(host, port)
        self.tts_service = tts_service

    def create_handler(self, reader, writer):
        return SileroWyomingHandler(self.tts_service, reader, writer)

async def run_wyoming_server(host: str, port: int, tts_service: SileroTtsService):
    server = SileroWyomingServer(host, port, tts_service)
    _LOGGER.info(f"Wyoming server started on {host}:{port}")
    await server.run(server.create_handler)

if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=10200)
    parser.add_argument("--uri", help="tcp://host:port")
    parser.add_argument("--language", default="v5_ru.pt")
    parser.add_argument("--samples", default="samples")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    
    # Initialize service
    module_path = Path(__file__).resolve().parent
    tts_service = SileroTtsService(args.samples, lang=args.language)
    
    if args.uri:
        # Example tcp://0.0.0.0:10200
        host, port = args.uri.split("://")[1].split(":")
        args.host = host
        args.port = int(port)

    asyncio.run(run_wyoming_server(args.host, args.port, tts_service))
