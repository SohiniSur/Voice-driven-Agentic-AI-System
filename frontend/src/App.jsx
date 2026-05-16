import React, { useState, useRef, useEffect } from 'react';

const App = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [status, setStatus] = useState('Ready');

// NEW: State for the AI Agent
  const [agentQuestion, setAgentQuestion] = useState("Hello! I am ready to help you fill out the form. Press record to begin.");
  const [formData, setFormData] = useState({});
  const [isComplete, setIsComplete] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // NEW: Fetch the first question from the backend when the page loads
  useEffect(() => {
    const fetchInitialState = async () => {
      try {
        const response = await fetch('https://blearier-lenita-unrevertible.ngrok-free.dev/api/v1/init', {
            method: 'GET', 
            headers: {
                "ngrok-skip-browser-warning": "true" // This bypasses the Ngrok warning page!
            }
          });
    
        // Check if the response is actually OK before trying to parse JSON
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
      }

        const data = await response.json();
        setAgentQuestion(data.agent_question);
        setFormData(data.form_state); 

      } catch (error) {
        console.error('Could not connect to backend:', error);
        setAgentQuestion('Error connecting to AI backend. Is the server running?');
      }
    };
    
    fetchInitialState();
  }, []); // The empty bracket means this only runs ONCE when the page loads

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          noiseSuppression: true,
          echoCancellation: true,
          autoGainControl: true,
        }
      });

      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = sendAudioToBackend;
      mediaRecorder.start();
      setIsRecording(true);
      setStatus('Recording... Please speak clearly.');
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setStatus('Microphone access denied. Please allow permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus('Processing your voice...');
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const sendAudioToBackend = async () => {
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');

    try {
      const response = await fetch('https://blearier-lenita-unrevertible.ngrok-free.dev/api/v1/transcribe', {
        method: 'POST',
        headers: {
            "ngrok-skip-browser-warning": "true" // This bypasses the Ngrok warning page!
        },
        body: formData,
      });
      // Check if the response is actually OK before trying to parse JSON
      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      if (data.needs_rerecord) {
        setStatus(`I didn't quite catch that. Could you please say it again?`);
        setTranscript(`(Heard: ${data.text})`);
      } else {
        setStatus(`Detected Language: ${data.language} (Confidence: ${data.confidence_score})`);
        setTranscript(data.text);

        // NEW: Update the UI with the Agent's brain
        setAgentQuestion(data.agent_question);
        setFormData(data.form_state);
        setIsComplete(data.is_complete);

        // --- NEW PHASE 6 CODE: Autoplay the Agent's Voice ---
        if (data.audio_base64) {
          const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
          // We use .catch() just in case the browser blocks the audio
          audio.play().catch(err => console.error("Audio playback blocked by browser:", err));
        }
        
      }
    } catch (error) {
      console.error('Error sending audio:', error);
      setStatus('Network error. Is the Python server running?');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '40px auto', fontFamily: 'sans-serif' }}>
      
      {/* 1. The Agent's Question Box */}
      <div style={{ backgroundColor: isComplete ? '#d4edda' : '#e2e3e5', padding: '20px', borderRadius: '8px', marginBottom: '20px', color: 'black' }}>
        <h2 style={{ margin: '0 0 10px 0' }}>🤖 Agent:</h2>
        <h3 style={{ margin: 0 }}>{agentQuestion}</h3>
      </div>

      {/* 2. Recording Controls */}
      {!isComplete && (
        <button 
          onClick={isRecording ? stopRecording : startRecording}
          style={{ width: '100%', padding: '15px', fontSize: '18px', fontWeight: 'bold', backgroundColor: isRecording ? '#dc3545' : '#0d6efd', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
        >
          {isRecording ? '🛑 Stop Recording' : '🎤 Tap to Answer'}
        </button>
      )}

      <div style={{ marginTop: '10px', textAlign: 'center', color: '#6c757d' }}>
        {status}
      </div>

      {/* 3. The Live Database View */}
      <div style={{ display: 'flex', gap: '20px', marginTop: '30px' }}>
        
        {/* Left Side: What the user just said */}
        <div style={{ flex: 1, padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', color: 'black' }}>
          <h4 style={{ margin: '0 0 10px 0' }}>You Said:</h4>
          <p style={{ margin: 0, fontStyle: 'italic' }}>{transcript || "Waiting for input..."}</p>
        </div>

        {/* Right Side: The extracted JSON state */}
        <div style={{ flex: 1, padding: '15px', backgroundColor: '#212529', borderRadius: '8px', color: '#20c997' }}>
          <h4 style={{ margin: '0 0 10px 0', color: 'white' }}>Live Form Data:</h4>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
            {JSON.stringify(formData, null, 2)}
          </pre>
        </div>
        
      </div>
    </div>
  );
};

/*
  return (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '50px auto', fontFamily: 'sans-serif', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>Government Form Assistant</h2>
      
      <button 
        onClick={isRecording ? stopRecording : startRecording}
        style={{
          padding: '12px 24px',
          fontSize: '16px',
          backgroundColor: isRecording ? '#dc3545' : '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          width: '100%'
        }}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>

      <div style={{ marginTop: '15px', fontWeight: 'bold' }}>
        Status: <span style={{ fontWeight: 'normal' }}>{status}</span>
      </div>

      {transcript && (
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px', color: 'black' }}>
          <strong>Extracted Text:</strong> <br/>
          {transcript}
        </div>
      )}
    </div>
  );
};
*/
export default App;