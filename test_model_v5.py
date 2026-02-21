import torch
import sys

try:
    print('Testing Device Selection')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Device:', device)

    print('Testing v5 download')
    local_file = 'model_v5.pt'
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v5_ru.pt', local_file)
    model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    model.to(device)

    print('Model loaded successfully')

except Exception as e:
    print('Error loading model:', e)
    sys.exit(1)
