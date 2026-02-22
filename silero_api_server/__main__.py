import uvicorn
import asyncio
from silero_api_server.server import app, tts_service
from silero_api_server.wyoming_server import run_wyoming_server

import argparse

parser = argparse.ArgumentParser(
                    prog='silero_api_server',
                    description='Run Silero within a FastAPI application')
parser.add_argument('-o','--host', action='store', dest='host', default='0.0.0.0')
parser.add_argument('-p','--port', action='store', dest='port', type=int, default=8001)
parser.add_argument('-s','--session_path', action='store', dest='session_path', type=str, default="sessions")
parser.add_argument('-l','--language', action='store', dest='language', type=str, default="v5_ru.pt")
parser.add_argument('--show-languages', action='store_true', dest='show_languages')
parser.add_argument('--wyoming-port', type=int, dest='wyoming_port', help='Start Wyoming protocol server on this port')

args = parser.parse_args()

if help not in args:
    if args.show_languages:
        for lang in tts_service.langs.keys():
            print(lang)
    else:
        tts_service.load_model(args.language)
        
        async def main():
            tasks = []
            
            # FastAPI task
            config = uvicorn.Config(app, host=args.host, port=args.port)
            server = uvicorn.Server(config)
            tasks.append(server.serve())
            
            # Wyoming task
            if args.wyoming_port:
                tasks.append(run_wyoming_server(args.host, args.wyoming_port, tts_service))
            
            await asyncio.gather(*tasks)

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            pass
