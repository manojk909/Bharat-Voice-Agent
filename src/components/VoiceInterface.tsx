"use client";

import { useState, useRef } from "react";
import { Mic, Square, Loader2, Volume2, Globe } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import axios from "axios";

const LANGUAGES = [
  { code: "hi-IN", name: "Hindi (हिन्दी)" },
  { code: "te-IN", name: "Telugu (తెలుగు)" },
  { code: "ta-IN", name: "Tamil (தமிழ்)" },
  { code: "kn-IN", name: "Kannada (ಕನ್ನಡ)" },
  { code: "ml-IN", name: "Malayalam (മലയാളം)" },
  { code: "mr-IN", name: "Marathi (मराठी)" },
  { code: "gu-IN", name: "Gujarati (ગુજરાતી)" },
  { code: "bn-IN", name: "Bengali (বাংলা)" },
  { code: "en-IN", name: "English" }
];

export default function VoiceInterface() {
  const { messages, addMessage, isRecording, isProcessing, setRecording, setProcessing } = useChatStore();
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState("hi-IN");
  const audioChunks = useRef<BlobPart[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
        audioChunks.current = [];
        await handleAudioSubmission(audioBlob);
      };

      setMediaRecorder(recorder);
      recorder.start();
      setRecording(true);
    } catch (err) {
      console.error("Error accessing mic:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setRecording(false);
    }
  };

  const handleAudioSubmission = async (audioBlob: Blob) => {
    setProcessing(true);
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      formData.append("language_code", selectedLanguage);

      // In a real browser this adds a mock message before the server replies
      addMessage({ id: Date.now().toString(), role: "user", text: "🎤 [Audio Sent]" });

      // Call FastAPI STT endpoint
      const sttResponse = await axios.post("http://localhost:8000/api/v1/stt", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      const transcript = sttResponse.data.transcript;
      
      if (transcript) {
        addMessage({ id: Date.now().toString() + "_tr", role: "user", text: `Transcript: ${transcript}` });
        
        // Then extract profile based on the transcript
        const profileResponse = await axios.post(`http://localhost:8000/api/v1/profile/extract?transcript=${encodeURIComponent(transcript)}&user_id=test_user_123`);
        
        const extractedData = profileResponse.data.profile;

        // Format profile data for clean vertical display
        const formattedProfile = Object.entries(extractedData)
          .map(([key, value]) => {
            const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
            const val = value === null || value === "" ? "Not specified" : value;
            return `• ${label}: ${val}`;
          })
          .join("\n");
        
        addMessage({ 
          id: (Date.now() + 1).toString(), 
          role: "agent", 
          text: `I have extracted your profile details:\n\n${formattedProfile}\n\nI will now look for relevant schemes.` 
        });
      } else {
         addMessage({ 
          id: (Date.now() + 1).toString(), 
          role: "agent", 
          text: "I couldn't hear that clearly. Could you please repeat?" 
        });
      }
      setProcessing(false);

    } catch (error) {
      console.error(error);
      addMessage({ 
        id: (Date.now() + 1).toString(), 
        role: "agent", 
        text: "Sorry, there was an error connecting to the server. Is the backend running?" 
      });
      setProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950 p-4 sm:p-8 rounded-2xl shadow-xl max-w-3xl w-full mx-auto border border-slate-200 dark:border-slate-800">
      <div className="flex-1 overflow-y-auto mb-4 space-y-4 min-h-[300px]">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <p className="text-center">Start speaking to discover government schemes.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`p-4 rounded-2xl max-w-[80%] whitespace-pre-wrap break-words ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-none'}`}>
                {msg.text}
              </div>
            </div>
          ))
        )}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center space-x-2">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
              <span className="text-sm text-slate-500">Processing...</span>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col items-center space-y-4 py-4 border-t border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1.5 rounded-full shadow-sm">
          <Globe className="w-4 h-4 text-slate-500 dark:text-slate-400" />
          <select 
            value={selectedLanguage} 
            onChange={(e) => setSelectedLanguage(e.target.value)}
            disabled={isRecording || isProcessing}
            className="bg-transparent text-sm text-slate-700 dark:text-slate-200 focus:outline-none cursor-pointer"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code} className="dark:bg-slate-800">
                {lang.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex justify-center items-center">
          {!isRecording ? (
            <button 
              onClick={startRecording}
              disabled={isProcessing}
              className="flex items-center justify-center w-16 h-16 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white rounded-full shadow-lg transition-transform hover:scale-105 active:scale-95"
            >
              <Mic className="w-8 h-8" />
            </button>
          ) : (
            <button 
              onClick={stopRecording}
              className="flex items-center justify-center w-16 h-16 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-lg transition-transform hover:scale-105 active:scale-95 animate-pulse"
            >
              <Square className="w-6 h-6 fill-current" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
