# Real-time Recording Feature - Testing Documentation

## Overview
This document describes the newly added real-time microphone recording and transcription feature.

## New Features

### 1. Real-time Microphone Recording
- Users can now record meetings directly through their microphone
- Real-time transcription with speaker diarization
- Live display of transcription as the meeting progresses

### 2. API Endpoints

#### `/start_recording` (POST)
Starts real-time recording from the microphone.

**Response:**
```json
{
    "status": "started",
    "message": "Recording started"
}
```

#### `/stop_recording` (POST)
Stops the recording and returns the transcript.

**Response:**
```json
{
    "status": "stopped",
    "message": "Recording stopped",
    "transcript": "Formatted transcript with speaker labels",
    "speakers": 3
}
```

#### `/get_realtime_transcript` (GET)
Gets the current real-time transcription status.

**Response:**
```json
{
    "results": [...],
    "interim": {...},
    "status": "success"
}
```

#### `/process_recording` (POST)
Processes the recorded audio and generates Minutes of Meeting.

**Response:**
```json
{
    "status": "success",
    "meeting_info": {...}
}
```

### 3. Frontend UI Components

- **Start Recording Button**: Red button (🎤 Start Recording) to begin recording
- **Stop Recording Button**: Gray button (⏹️ Stop Recording) to end recording
- **Generate Minutes Button**: Green button that appears after stopping recording
- **Recording Status**: Real-time status indicator showing recording state
- **Live Transcript Display**: Updates every 2 seconds during recording

### 4. Technical Implementation

#### Backend (`realtime_recording.py`)
- Uses Azure Cognitive Services Speech SDK
- Implements `RealtimeRecorder` class
- Handles speaker diarization automatically
- Stores results in Redis for real-time access

#### Frontend (JavaScript in `index.html`)
- Polls for transcript updates every 2 seconds during recording
- Displays interim and final transcription results
- Auto-scrolls to show latest transcript
- Smooth UI state transitions

### 5. Integration with Existing Features

The recording functionality seamlessly integrates with existing features:
- Generated transcripts follow the same format as uploaded files
- MoM generation works identically for recorded and uploaded audio
- Download options (transcript and minutes) work the same way
- Google Calendar integration for follow-up meetings is maintained

## Usage Flow

1. User clicks "Start Recording" button
2. Browser requests microphone access (if not already granted)
3. Recording begins and transcript appears in real-time
4. User clicks "Stop Recording" when meeting ends
5. Final transcript is displayed with speaker count
6. User clicks "Generate Minutes" to create MoM
7. System processes recording and generates meeting information
8. Page reloads with complete meeting details

## Requirements

- Microphone access in the browser
- Azure Speech Services API key (configured in the code)
- Active internet connection for transcription
- Redis for state management

## Browser Compatibility

The feature uses standard Web APIs and should work on:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Other modern browsers with microphone support

## Testing Notes

To test the feature in a production environment:
1. Ensure Azure Speech Services credentials are valid
2. Ensure Redis connection is properly configured
3. Grant microphone permissions in browser
4. Test with multiple speakers for diarization
5. Verify MoM generation matches uploaded file workflow
