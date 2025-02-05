<script lang="ts">
  import { browser } from '$app/environment';
  import Scene from '../lib/3d/Scene.svelte';
  import { onMount } from 'svelte';

  let websocket: WebSocket;
  let isRecording = false;
  let mediaRecorder: MediaRecorder;
  let audioChunks: Blob[] = [];
  let audioElement: HTMLAudioElement;

  // Websocket init
  onMount(() => {
    websocket = new WebSocket('ws://localhost:8000/ws');
    
    websocket.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        const audioBlob = new Blob([event.data], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Create audio element and play
        audioElement = new Audio(audioUrl);
        audioElement.play();
      }
    };

    // Key handlers
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'm' && !isRecording) {
        startRecording();
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'm' && isRecording) {
        stopRecording();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    return () => {
      websocket?.close();
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
    };
  });

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      isRecording = true;

      mediaRecorder.ondataavailable = (e) => {
        audioChunks.push(e.data);
      };

      mediaRecorder.start();
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  }

  async function stopRecording() {
    if (!mediaRecorder) return;

    mediaRecorder.stop();
    isRecording = false;

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      audioChunks = [];
      
      // Convert audio to text (you'll need a speech-to-text service here)
      const text = await convertAudioToText(audioBlob);
      
      // Send text to WebSocket
      websocket.send(JSON.stringify({ text }));
    };
  }

  async function blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  async function convertAudioToText(audioBlob: Blob): Promise<string> {
  try {
    // Add silence detection
    const audioContext = new AudioContext();
    const buffer = await audioContext.decodeAudioData(await audioBlob.arrayBuffer());
    
    // Check for silent audio
    const isSilent = buffer.getChannelData(0).every(sample => Math.abs(sample) < 0.01);
    if (isSilent) {
      console.log('Silent audio detected');
      return '';
    }

    // Proceed with conversion
    const resampledBlob = await convertToWav(audioBlob);
      const base64Audio = await blobToBase64(resampledBlob);

      const response = await fetch('http://localhost:8000/transcribe', {  
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio: base64Audio.split(',')[1] })
      });

      if (!response.ok) throw new Error(await response.text());
      
      const { text } = await response.json();
      return text || ''; // Ensure empty string on failure

    } catch (error) {
      console.error('Transcription failed:', error);
      return '';
    }
  }

// Updated convertToWav function with proper WAV encoding
async function convertToWav(blob: Blob): Promise<Blob> {
  try {
    const audioContext = new AudioContext();
    const buffer = await audioContext.decodeAudioData(await blob.arrayBuffer());
    
    // Force 16kHz sample rate
    const offlineContext = new OfflineAudioContext(
      1, // Mono
      Math.floor(buffer.duration * 16000), // Sample count
      16000 // Sample rate
    );

    const source = offlineContext.createBufferSource();
    source.buffer = buffer;
    source.connect(offlineContext.destination);
    source.start(0);

    const resampledBuffer = await offlineContext.startRendering();
    
    // Convert AudioBuffer to WAV 
    const wavBuffer = audioBufferToWav(resampledBuffer);
    return new Blob([wavBuffer], { type: 'audio/wav' });

  } catch (error) {
    console.error('Audio conversion failed:', error);
    throw error;
  }
}

// Helper function to convert AudioBuffer to WAV format
function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
  const numChannels = buffer.numberOfChannels;
  const sampleRate = buffer.sampleRate;
  const length = buffer.getChannelData(0).length;
  
  const header = new ArrayBuffer(44);
  const view = new DataView(header);

  // RIFF identifier
  writeString(view, 0, 'RIFF');
  // File length
  view.setUint32(4, 32 + length * 2, true);
  // WAVE identifier
  writeString(view, 8, 'WAVE');
  // Format chunk identifier
  writeString(view, 12, 'fmt ');
  // Format chunk length
  view.setUint32(16, 16, true);
  // Sample format (1 = PCM)
  view.setUint16(20, 1, true);
  // Channel count
  view.setUint16(22, numChannels, true);
  // Sample rate
  view.setUint32(24, sampleRate, true);
  // Byte rate (sampleRate * blockAlign)
  view.setUint32(28, sampleRate * 2, true);
  // Block align (channelCount * bytesPerSample)
  view.setUint16(32, 2, true);
  // Bits per sample
  view.setUint16(34, 16, true);
  // Data chunk identifier
  writeString(view, 36, 'data');
  // Data chunk length
  view.setUint32(40, length * 2, true);

  // Combine header and PCM data
  const data = new Float32Array(length);
  data.set(buffer.getChannelData(0));
  const pcm = new Int16Array(length);
  for (let i = 0; i < length; i++) {
    const s = Math.max(-1, Math.min(1, data[i]));
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }

  const wav = new Uint8Array(header.byteLength + pcm.byteLength);
  wav.set(new Uint8Array(header), 0);
  wav.set(new Uint8Array(pcm.buffer), header.byteLength);

  return wav.buffer;
}

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

</script>

<div class="scene-container">
  {#if browser}
    <Scene />
  {/if}
  
  {#if isRecording}
    <div class="recording-indicator">
      ● Recording
    </div>
  {/if}
</div>

<style>
  .scene-container {
    position: absolute;
    inset: 0;
    background: radial-gradient(hsl(220 14% 20%), hsl(220 20% 10%));
  }

  .recording-indicator {
    position: fixed;
    bottom: 20px;
    right: 20px;
    color: #ff4444;
    font-family: monospace;
    font-size: 1.2rem;
    text-shadow: 0 0 8px rgba(255, 68, 68, 0.5);
  }
</style>
