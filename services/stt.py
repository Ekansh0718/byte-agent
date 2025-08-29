# services/stt.py
import logging
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingParameters,
    StreamingSessionParameters,
    StreamingEvents,
    BeginEvent,
    TurnEvent,
    TerminationEvent,
    StreamingError,
)

logger = logging.getLogger(__name__)

def _on_begin(client, event: BeginEvent):
    logger.info("AAI session started: %s", event.id)

def _on_termination(client, event: TerminationEvent):
    logger.info("AAI session terminated after %s s", event.audio_duration_seconds)

def _on_error(client, error: StreamingError):
    logger.error("AAI error: %s", error)

class AssemblyAIStreamingTranscriber:
    def __init__(self, sample_rate=16000, on_partial_callback=None, on_final_callback=None, api_key=None):
        self.on_partial_callback = on_partial_callback
        self.on_final_callback = on_final_callback
        opts = StreamingClientOptions(api_key=api_key, api_host="streaming.assemblyai.com")
        self.client = StreamingClient(opts)

        self.client.on(StreamingEvents.Begin, _on_begin)
        self.client.on(StreamingEvents.Error, _on_error)
        self.client.on(StreamingEvents.Termination, _on_termination)
        self.client.on(StreamingEvents.Turn, lambda client, event: self._on_turn(client, event))

        self.client.connect(StreamingParameters(sample_rate=sample_rate, format_turns=False))

    def _on_turn(self, client, event: TurnEvent):
        text = (event.transcript or "").strip()
        if not text:
            return
        if event.end_of_turn:
            if self.on_final_callback:
                self.on_final_callback(text)
            if not event.turn_is_formatted:
                try:
                    client.set_params(StreamingSessionParameters(format_turns=True))
                except Exception as e:
                    logger.exception("set_params error")
        else:
            if self.on_partial_callback:
                self.on_partial_callback(text)

    def stream_audio(self, audio_chunk: bytes):
        try:
            self.client.stream(audio_chunk)
        except Exception:
            logger.exception("stream_audio failed")

    def close(self):
        try:
            self.client.disconnect(terminate=True)
        except Exception:
            pass
