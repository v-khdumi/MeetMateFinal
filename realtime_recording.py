import azure.cognitiveservices.speech as speechsdk
import json
from datetime import datetime
from upstash_redis import Redis
import os

# Load credentials from environment variables
UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://fine-swift-52766.upstash.io")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "Ac4eAAIjcDE2NzI4ZmMzYmU1NmU0NmM3ODIxY2YzYWI2ZTAyMzdhNXAxMA")
redis_client = Redis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)

subscription_key = os.getenv("AZURE_SPEECH_KEY", "7D6sNCVfG0raLGtt31oF5fEtyu7FOkT521wmvwR9LMlWmc3rhNNyJQQJ99ALACHYHv6XJ3w3AAAAACOGvMWd")
service_region = os.getenv("AZURE_SPEECH_REGION", "eastus2")

class RealtimeRecorder:
    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)
        self.speech_config.speech_recognition_language = "en-US"
        self.speech_config.enable_dictation()
        
        # Enable speaker diarization
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_SpeakerIdMode, 
            "Dependent"
        )
        
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.conversation_transcriber = None
        self.transcription_results = []
        self.is_recording = False
        
    def start_recording(self):
        """Start real-time recording and transcription from microphone"""
        self.is_recording = True
        self.transcription_results = []
        
        # Create conversation transcriber for speaker diarization
        self.conversation_transcriber = speechsdk.transcription.ConversationTranscriber(
            speech_config=self.speech_config, 
            audio_config=self.audio_config
        )
        
        # Connect callbacks
        self.conversation_transcriber.transcribing.connect(self._handle_transcribing)
        self.conversation_transcriber.transcribed.connect(self._handle_transcribed)
        self.conversation_transcriber.session_started.connect(self._handle_session_started)
        self.conversation_transcriber.session_stopped.connect(self._handle_session_stopped)
        self.conversation_transcriber.canceled.connect(self._handle_canceled)
        
        # Start transcription
        self.conversation_transcriber.start_transcribing_async().get()
        
        return {"status": "started", "message": "Recording started"}
    
    def stop_recording(self):
        """Stop recording and return transcription"""
        if self.conversation_transcriber and self.is_recording:
            self.conversation_transcriber.stop_transcribing_async().get()
            self.is_recording = False
            
            # Format transcription
            formatted_transcript = self._format_transcript()
            
            # Store in Redis
            redis_client.set("realtime-transcript", formatted_transcript)
            redis_client.set("realtime-results", json.dumps(self.transcription_results))
            
            return {
                "status": "stopped", 
                "message": "Recording stopped",
                "transcript": formatted_transcript,
                "speakers": len(set([r['speaker'] for r in self.transcription_results if 'speaker' in r]))
            }
        
        return {"status": "error", "message": "No active recording"}
    
    def _handle_transcribing(self, evt):
        """Handle interim transcription results"""
        if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            # Send interim results to client via Redis
            interim_result = {
                "type": "interim",
                "text": evt.result.text,
                "speaker": getattr(evt.result, 'speaker_id', 'Unknown'),
                "timestamp": datetime.now().isoformat()
            }
            redis_client.set("realtime-interim", json.dumps(interim_result))
    
    def _handle_transcribed(self, evt):
        """Handle final transcription results"""
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            result = {
                "type": "final",
                "text": evt.result.text,
                "speaker": getattr(evt.result, 'speaker_id', 'Unknown'),
                "timestamp": datetime.now().isoformat(),
                "offset": evt.result.offset,
                "duration": evt.result.duration
            }
            self.transcription_results.append(result)
            
            # Update Redis with latest results
            redis_client.set("realtime-results", json.dumps(self.transcription_results))
    
    def _handle_session_started(self, evt):
        """Handle session started event"""
        print(f"Session started: {evt}")
        redis_client.set("recording-status", "started")
    
    def _handle_session_stopped(self, evt):
        """Handle session stopped event"""
        print(f"Session stopped: {evt}")
        redis_client.set("recording-status", "stopped")
    
    def _handle_canceled(self, evt):
        """Handle cancellation event"""
        print(f"Canceled: {evt}")
        if evt.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {evt.error_details}")
            redis_client.set("recording-error", evt.error_details)
    
    def _format_transcript(self):
        """Format transcription results for display"""
        formatted = ""
        speaker_map = {}
        speaker_counter = 1
        
        for result in self.transcription_results:
            if result['type'] == 'final' and result['text']:
                speaker_id = result.get('speaker', 'Unknown')
                
                # Map speaker IDs to Speaker 1, Speaker 2, etc.
                if speaker_id not in speaker_map:
                    speaker_map[speaker_id] = f"Speaker {speaker_counter}"
                    speaker_counter += 1
                
                speaker_label = speaker_map[speaker_id]
                timestamp = result.get('timestamp', '')
                text = result['text']
                
                formatted += f"[{speaker_label}]\n{text}\n\n"
        
        return formatted if formatted else "No transcription available"
    
    def get_current_transcript(self):
        """Get the current transcription state"""
        results = redis_client.get("realtime-results")
        if results:
            return json.loads(results)
        return []

# Global recorder instance
recorder = None

def get_recorder():
    """Get or create recorder instance"""
    global recorder
    if recorder is None:
        recorder = RealtimeRecorder()
    return recorder
