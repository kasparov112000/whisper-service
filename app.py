"""
Self-hosted Whisper Transcription Service
Uses OpenAI's Whisper model locally - completely free, no API costs.

Endpoints:
- GET /health - Health check
- POST /transcribe - Transcribe audio file

Requires:
- Python 3.8+
- pip install flask faster-whisper
"""

import os
import sys
import tempfile
from flask import Flask, request, jsonify
import warnings
import time

# Suppress warnings
warnings.filterwarnings("ignore")

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

app = Flask(__name__)

# Configuration
MODEL_SIZE = os.environ.get('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large

# Global model instance
model = None
model_type = None  # 'faster-whisper' or 'openai-whisper'


def load_model():
    """Load Whisper model (lazy loading on first request)"""
    global model, model_type
    if model is not None:
        return model, model_type

    print(f"Loading Whisper model: {MODEL_SIZE}")

    # Try faster-whisper first (more efficient)
    try:
        from faster_whisper import WhisperModel
        # Use CPU by default, change to "cuda" if you have GPU
        device = os.environ.get('WHISPER_DEVICE', 'cpu')
        compute_type = 'int8' if device == 'cpu' else 'float16'
        model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
        model_type = 'faster-whisper'
        print(f"[OK] Loaded faster-whisper model ({MODEL_SIZE}) on {device}")
        return model, model_type
    except ImportError as e:
        print(f"faster-whisper not installed: {e}")
    except Exception as e:
        print(f"faster-whisper failed to load: {e}")

    # Fallback to OpenAI Whisper
    try:
        import whisper
        model = whisper.load_model(MODEL_SIZE)
        model_type = 'openai-whisper'
        print(f"[OK] Loaded openai-whisper model ({MODEL_SIZE})")
        return model, model_type
    except ImportError as e:
        print(f"openai-whisper not installed: {e}")
        raise RuntimeError("No whisper implementation available. Install faster-whisper or openai-whisper.")
    except Exception as e:
        print(f"openai-whisper failed to load: {e}")
        raise


def transcribe_audio(audio_path: str, language: str = None) -> dict:
    """Transcribe audio using the loaded model"""
    loaded_model, loaded_model_type = load_model()

    print(f"Transcribing with {loaded_model_type}...")
    start_time = time.time()
    duration = 0
    detected_language = language

    if loaded_model_type == 'faster-whisper':
        # faster-whisper API
        segments, info = loaded_model.transcribe(
            audio_path,
            language=language if language else None,
            beam_size=5,
            vad_filter=True  # Filter out silence
        )

        # Combine all segments
        transcript_parts = []
        for segment in segments:
            transcript_parts.append(segment.text.strip())

        transcript = ' '.join(transcript_parts)
        duration = info.duration if hasattr(info, 'duration') else 0
        detected_language = info.language if hasattr(info, 'language') else language
    else:
        # openai-whisper API
        result = loaded_model.transcribe(
            audio_path,
            language=language if language else None,
            fp16=False  # Use fp32 for CPU
        )
        transcript = result['text'].strip()
        detected_language = result.get('language', language)

    elapsed = time.time() - start_time
    print(f"[OK] Transcription completed in {elapsed:.1f}s: {len(transcript)} characters")

    return {
        'transcript': transcript,
        'processing_time': elapsed,
        'duration': duration,
        'language': detected_language
    }


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    global model_type
    return jsonify({
        'status': 'ok',
        'service': 'whisper-transcription',
        'model': MODEL_SIZE,
        'device': os.environ.get('WHISPER_DEVICE', 'cpu'),
        'timestamp': time.time()
    })


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe audio file

    Expects multipart/form-data with:
    - audio: Audio file (wav, mp3, m4a, mp4, ogg, flac, webm)
    - language: Optional language code (e.g., 'en', 'es', 'pt')

    Returns:
    - transcript: Transcribed text
    """
    try:
        # Check if audio file was provided
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        language = request.form.get('language', None)

        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400

        print(f"Received audio file: {audio_file.filename}")
        print(f"Content type: {audio_file.content_type}")
        print(f"Language: {language}")

        # Get file extension
        original_ext = os.path.splitext(audio_file.filename)[1].lower()
        if not original_ext:
            # Try to determine from content type
            content_type_map = {
                'audio/wav': '.wav',
                'audio/mpeg': '.mp3',
                'audio/mp4': '.m4a',
                'audio/mp3': '.mp3',
                'audio/ogg': '.ogg',
                'audio/flac': '.flac',
                'audio/webm': '.webm',
                'audio/x-wav': '.wav',
                'audio/x-m4a': '.m4a'
            }
            original_ext = content_type_map.get(audio_file.content_type, '.wav')

        # Save to temporary file in a simple path (avoid Windows path issues)
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        temp_path = os.path.join(temp_dir, f'audio_{int(time.time())}{original_ext}')
        audio_file.save(temp_path)
        print(f"Saved to temp file: {temp_path}")

        # Get file size
        file_size = os.path.getsize(temp_path)
        print(f"File size: {file_size / (1024*1024):.2f} MB")

        try:
            # Transcribe
            result = transcribe_audio(temp_path, language)

            return jsonify({
                'transcript': result['transcript'],
                'language': result['language'],
                'duration': result['duration'],
                'processing_time': result['processing_time'],
                'model': MODEL_SIZE
            })

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"Transcription error ({error_type}): {error_msg}")
        traceback.print_exc()
        return jsonify({'error': error_msg, 'error_type': error_type}), 500


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API info"""
    return jsonify({
        'service': 'Whisper Transcription Service',
        'version': '1.0.0',
        'endpoints': {
            'GET /health': 'Health check',
            'POST /transcribe': 'Transcribe audio (multipart form with audio file)'
        },
        'model': MODEL_SIZE
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Whisper service on port {port}")
    print(f"Model: {MODEL_SIZE}")
    print(f"Device: {os.environ.get('WHISPER_DEVICE', 'cpu')}")

    # Pre-load model on startup (optional, can comment out for faster startup)
    if os.environ.get('PRELOAD_MODEL', 'false').lower() == 'true':
        load_model()

    app.run(host='0.0.0.0', port=port, debug=False)
