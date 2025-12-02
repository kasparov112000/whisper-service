# Whisper Transcription Service

Self-hosted speech-to-text transcription service using OpenAI's Whisper model. Provides a REST API for transcribing audio files without any external API costs.

## Features

- **Free & Self-hosted**: No API costs, runs entirely on your infrastructure
- **Multiple Models**: Support for tiny, base, small, medium, and large models
- **GPU Support**: Automatic GPU acceleration when available
- **Multiple Formats**: Supports WAV, MP3, M4A, MP4, OGG, FLAC, WebM
- **Production Ready**: Docker support, health checks, Kubernetes deployment

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

### Docker

```bash
# Build
docker build -t whisper-service .

# Run
docker run -p 5000:5000 whisper-service
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `WHISPER_MODEL` | `base` | Model size: tiny, base, small, medium, large |
| `WHISPER_DEVICE` | `cpu` | Device: cpu or cuda |
| `PRELOAD_MODEL` | `false` | Preload model on startup |

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "ok",
  "service": "whisper-transcription",
  "model": "base",
  "device": "cpu"
}
```

### Transcribe Audio

```bash
POST /transcribe
Content-Type: multipart/form-data
```

Parameters:
- `audio` (required): Audio file
- `language` (optional): Language code (e.g., 'en', 'es', 'pt')

Example:
```bash
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@audio.mp3" \
  -F "language=en"
```

Response:
```json
{
  "transcript": "Hello world, this is a test.",
  "language": "en",
  "model": "base"
}
```

## Model Sizes

| Model | Parameters | VRAM | Relative Speed |
|-------|------------|------|----------------|
| tiny | 39M | ~1GB | ~32x |
| base | 74M | ~1GB | ~16x |
| small | 244M | ~2GB | ~6x |
| medium | 769M | ~5GB | ~2x |
| large | 1550M | ~10GB | 1x |

## Production Deployment

### Kubernetes with Helm

```bash
cd helm
helm install whisper-service . -f values.yaml
```

### Resource Recommendations

- **CPU Mode**: 2+ CPU cores, 4GB+ RAM
- **GPU Mode**: NVIDIA GPU with 4GB+ VRAM, CUDA 11.x+

## Architecture

```
┌─────────────────────────────────────┐
│         Video Transcription         │
│            Service                  │
│         (port 3016)                 │
└──────────────┬──────────────────────┘
               │
               │ POST /transcribe
               │ (audio file)
               ▼
┌─────────────────────────────────────┐
│         Whisper Service             │
│         (port 5000)                 │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   faster-whisper / whisper  │   │
│  │      (Whisper Model)        │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## License

MIT License - Part of LearnByTesting.ai platform
