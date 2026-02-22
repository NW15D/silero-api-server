# A simple FastAPI Server and Wyoming TTS Server (Home Assistant) to run Silero TTS on CUDA orCPU
Credit goes to the developers of Silero TTS  
[Silero PyTorch Page](https://pytorch.org/hub/snakers4_silero-models_tts/)  
[Silero GitHub Page](https://github.com/snakers4/silero-models)

*** Для русского языка используется морфинг числительных и конвертация латинницы в кирилицу.

## Installation
`pip install silero-api-server`

## Starting Server
**Python 3.12+ is required.**
`python -m silero_api_server` will run on default ip and port (0.0.0.0:8001)

```
usage: silero_api_server [-h] [-o HOST] [-p PORT]

Run Silero within a FastAPI application

options:
  -h, --help            show this help message and exit
  -o HOST, --host HOST
  -p PORT, --port PORT
  -l LANG, --language LANG
  --show-languages
```

On first run of server, two operations occur automatically. These may take a minute or two.
1. The model will be downloaded 
2. Voice samples will be generated. 

## Deploying server as a container

You can build an image from current source by running `docker build -t silero:latest .` in the top
level of repository. Server can then be deployed as a container with `docker run -p 8001:8001 silero:latest`.

# API Docs
API Docs can be accessed from [http://localhost:8001/docs](http://localhost:8001/docs)

# Voice Samples
Samples are served statically by the web server at `/samples/{speaker}.wav` or callable from the API from `/tts/sample?speaker={speaker}` endpoint.

# Selecting Language
Use command-line options or download and set the desired language using `POST /tts/language` with payload `{"id":"languageId"}`  
List of language ids are available via `GET /tts/language`

# Home Assistant Integration
You can use this server with Home Assistant in two ways:

## 1. Wyoming Protocol (Recommended for Voice Assistant)
The server supports the Wyoming protocol, which allows it to work seamlessly with Home Assistant's local voice control.
To start the server with Wyoming support on port `10200`:
`python -m silero_api_server --wyoming-port 10200`
Then, in Home Assistant, add the **Wyoming Protocol** integration and point it to your server's IP and port `10200`.

## 2. Native TTS Component
A base implementation for a native Home Assistant TTS platform is provided in `ha_tts.py`. You can use this as a reference to create a `custom_component`.

# OpenAI-Compatible API
The server provides an OpenAI-compatible speech endpoint at `/v1/audio/speech`.
Example:
```bash
curl http://localhost:8001/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Привет, мир!",
    "voice": "baya"
  }' --output output.wav
```
