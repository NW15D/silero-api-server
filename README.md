# API Server and Wyoming (Home Assistant) to run Silero TTS on CUDA or CPU
Fast as real on GPU , only 550MB VRAM required
*** Для русского и украинского языка используется морфинг числительных и конвертация латинницы в кирилицу. Для украинского не тестировалось



Credit goes to the developers of Silero TTS  
[Silero PyTorch Page](https://pytorch.org/hub/snakers4_silero-models_tts/)  
[Silero GitHub Page](https://github.com/snakers4/silero-models)

## Installation
`pip install silero-api-server`

## Starting Server
**Python <= 3.12 is required.**
`python -m silero_api_server` will run on default ip and port (0.0.0.0:8001)

```
usage: silero_api_server [-h] [-o HOST] [-p PORT]

Run Silero within a FastAPI application

options:
  -h, --help            show this help message and exit
  -o HOST, --host HOST
  -p PORT, --port PORT
  -m MODEL, --model MODEL
  --show-models
```

On first run of server, two operations occur automatically. These may take a minute or two.
1. The model will be downloaded 
2. Voice samples will be generated. 

## Deploying server as a container

You can build an image from current source by running `docker build -t silero:latest .` in the top
level of repository. Server can then be deployed as a container with `docker run -p 8001:8001 silero:latest`.

# API Docs
API Docs can be accessed from [http://localhost:8001/docs](http://localhost:8001/docs)

# Default model
By default, the server uses the `v5_ru.pt` model.
You can change the model via command-line options or change it at runtime using `POST /tts/model` with payload `{"id":"model_id"}`.
List of available models is available via `GET /tts/model`.

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
