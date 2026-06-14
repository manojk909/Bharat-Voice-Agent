"use client";

import { useState, useRef, useEffect } from "react";
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
  const { messages, addMessage, clearMessages, isRecording, isProcessing, setRecording, setProcessing } = useChatStore();
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState("hi-IN");
  const [draftStages, setDraftStages] = useState<string[]>([]);
  const [currentStageIndex, setCurrentStageIndex] = useState<number>(-1);
  const [schemes, setSchemes] = useState<any[]>([]);
  const [activeSchemeId, setActiveSchemeId] = useState<string>("");
  const [verificationResult, setVerificationResult] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [userProfile, setUserProfile] = useState<any>(null);
  const audioChunks = useRef<BlobPart[]>([]);

  useEffect(() => {
    const newId = "user_" + Math.random().toString(36).substring(2, 11);
    setUserId(newId);
  }, []);

  const handleResetSession = () => {
    const newId = "user_" + Math.random().toString(36).substring(2, 11);
    setUserId(newId);
    clearMessages();
    setSchemes([]);
    setDraftStages([]);
    setCurrentStageIndex(-1);
    setActiveSchemeId("");
    setVerificationResult("");
    setUserProfile(null);
  };

  const renderMessageText = (text: string, isUser = false) => {
    if (!text) return "";
    const textClass = isUser ? "text-white" : "text-slate-700 dark:text-slate-300";
    const lines = text.split("\n");
    return lines.map((line, lineIdx) => {
      let currentLine = line;
      
      // Check if it's just underscores
      const isUnderscoreLine = /^[\_\s\-]+$/.test(currentLine);
      if (isUnderscoreLine) {
        return (
          <div key={lineIdx} className={`text-slate-300 dark:text-slate-600 opacity-60 leading-none my-0 overflow-hidden text-ellipsis whitespace-nowrap ${textClass}`}>
            {currentLine}
          </div>
        );
      }

      const isBullet = currentLine.trim().startsWith("* ") || currentLine.trim().startsWith("• ") || currentLine.trim().startsWith("- ");
      if (isBullet) {
        currentLine = currentLine.trim().replace(/^[\*\•\-]\s*/, "");
      }

      const parts: (string | React.ReactNode)[] = [];
      const regex = /\*\*([^*]+)\*\*/g;
      let lastIndex = 0;
      let match;

      while ((match = regex.exec(currentLine)) !== null) {
        const matchIndex = match.index;
        if (matchIndex > lastIndex) {
          parts.push(currentLine.substring(lastIndex, matchIndex));
        }
        parts.push(
          <strong key={matchIndex} className={`font-bold ${isUser ? 'text-white' : 'text-slate-900 dark:text-white'}`}>
            {match[1]}
          </strong>
        );
        lastIndex = regex.lastIndex;
      }

      if (lastIndex < currentLine.length) {
        parts.push(currentLine.substring(lastIndex));
      }

      const content = parts.length > 0 ? parts : currentLine;

      if (isBullet) {
        return (
          <div key={lineIdx} className="flex items-start space-x-2 pl-2 my-1">
            <span className={isUser ? "text-white/80" : "text-slate-400"}>•</span>
            <div className={`flex-1 ${textClass}`}>{content}</div>
          </div>
        );
      }

      return (
        <p key={lineIdx} className={`min-h-[1.2rem] my-0.5 ${textClass}`}>
          {content}
        </p>
      );
    });
  };

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
        const profileResponse = await axios.post(`http://localhost:8000/api/v1/profile/extract?transcript=${encodeURIComponent(transcript)}&user_id=${userId}`);
        
        const extractedData = profileResponse.data.profile;
        setUserProfile(extractedData);

        if (extractedData.document_verified) {
          setVerificationResult("Verification Approved: Verified/Approved verbally by user statement.");
        }

        // Format profile data for clean vertical display
        const formattedProfile = Object.entries(extractedData)
          .filter(([key]) => key.toLowerCase() !== "id" && key.toLowerCase() !== "_id")
          .map(([key, value]) => {
            const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
            const val = value === null || value === "" ? "Not specified" : value;
            return `• ${label}: ${val}`;
          })
          .join("\n");

        // Construct a clean speech text containing ONLY user-specified details
        const specifiedDetails = Object.entries(extractedData)
          .filter(([key, value]) => key.toLowerCase() !== "id" && key.toLowerCase() !== "_id" && value !== null && value !== "" && String(value).toLowerCase() !== "not specified" && String(value).toLowerCase() !== "नहीं")
          .map(([key, value]) => {
            const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
            return `${label} is ${value}`;
          })
          .join(", ");

        const isDrafting = activeSchemeId !== "" || draftStages.length > 0;

        const speechProfileSummary = specifiedDetails.length > 0 
          ? (isDrafting
              ? `I have updated your profile details: ${specifiedDetails}.`
              : `I have extracted your profile details: ${specifiedDetails}. I will now look for relevant schemes.`)
          : (isDrafting
              ? `I have received your update.`
              : `I have received your request and will now look for relevant schemes.`);

        // Clean formatting for TTS read-out
        const cleanTextForSpeech = (rawText: string) => {
          return rawText
            .replace(/[🌟🎁🎯🔗📂•*🎉]/g, "")
            .replace(/http[s]?:\/\/[^\s]+/g, "")
            .replace(/[\n\r]+/g, ". ");
        };

        // Call backend TTS
        const playTTS = (speechText: string): Promise<void> => {
          return new Promise(async (resolve) => {
            try {
              const cleanText = cleanTextForSpeech(speechText);
              const response = await axios.post(`http://localhost:8000/api/v1/tts?text=${encodeURIComponent(cleanText)}&language_code=${selectedLanguage}`);
              const audioBase64 = response.data.audio;
              if (audioBase64) {
                const audioUrl = `data:audio/wav;base64,${audioBase64}`;
                const audio = new Audio(audioUrl);
                audio.onended = () => resolve();
                audio.onerror = () => resolve();
                await audio.play();
              } else {
                resolve();
              }
            } catch (err) {
              console.error("TTS playback error:", err);
              resolve();
            }
          });
        };

        const agentProfileRawMsg = isDrafting
          ? `I have updated your profile details:\n\n${formattedProfile}`
          : `I have extracted your profile details:\n\n${formattedProfile}\n\nI will now look for relevant schemes.`;
        
        let agentProfileMsg = agentProfileRawMsg;
        let voiceProfileMsg = speechProfileSummary;

        if (!selectedLanguage.startsWith("en")) {
          try {
            const transResponse = await axios.post(`http://localhost:8000/api/v1/translate?text=${encodeURIComponent(agentProfileRawMsg)}&target_language_code=${selectedLanguage}`);
            if (transResponse.data.translated) {
              agentProfileMsg = transResponse.data.translated;
            }
          } catch {}
          try {
            const voiceTransResponse = await axios.post(`http://localhost:8000/api/v1/translate?text=${encodeURIComponent(speechProfileSummary)}&target_language_code=${selectedLanguage}`);
            if (voiceTransResponse.data.translated) {
              voiceProfileMsg = voiceTransResponse.data.translated;
            }
          } catch {}
        }

        addMessage({ 
          id: (Date.now() + 1).toString(), 
          role: "agent", 
          text: agentProfileMsg
        });
        await playTTS(voiceProfileMsg);

        if (isDrafting) {
          setProcessing(false);
          return;
        }

        // Call discover schemes endpoint with language code to get translated schemes
        const discoverResponse = await axios.get(`http://localhost:8000/api/v1/schemes/discover?user_id=${userId}&language_code=${selectedLanguage}`);
        const eligibleSchemes = discoverResponse.data.schemes;
        setSchemes(eligibleSchemes || []);

        if (eligibleSchemes && eligibleSchemes.length > 0) {
          const formattedSchemes = eligibleSchemes
            .map((scheme: any, index: number) => {
              const docs = scheme.required_documents && scheme.required_documents.length > 0
                ? scheme.required_documents.join(", ")
                : "Not specified";
              
              // We keep labels in English or standard translated tags, but text remains in target language
              return `${index + 1}. 🌟 **${scheme.title}**\n   🎁 *Benefits*: ${scheme.benefits}\n   🎯 *Reason*: ${scheme.eligibility_reason}\n   📅 *Deadline*: ${scheme.application_deadline || "Open"}\n   📂 *Required Documents*: ${docs}\n   🔗 *Source*: ${scheme.source_url || "N/A"}`;
            })
            .join("\n\n");
          
          const rawSchemesMsg = `🎉 Here are the schemes you are eligible for:\n\n${formattedSchemes}`;
          let agentSchemesMsg = rawSchemesMsg;
          if (!selectedLanguage.startsWith("en")) {
            try {
              // The items inside are already translated, but translate the header "Here are the schemes..."
              const headerTrans = await axios.post(`http://localhost:8000/api/v1/translate?text=${encodeURIComponent("Here are the schemes you are eligible for:")}&target_language_code=${selectedLanguage}`);
              if (headerTrans.data.translated) {
                agentSchemesMsg = `🎉 ${headerTrans.data.translated}\n\n${formattedSchemes}`;
              }
            } catch {}
          }

          addMessage({
            id: (Date.now() + 2).toString(),
            role: "agent",
            text: agentSchemesMsg
          });
          
          // Generate a clean, concise voice summary of the schemes
          const schemeTitles = eligibleSchemes.map((s: any) => s.title).join(", ");
          const ttsText = `I found the following schemes for you: ${schemeTitles}. You can see the details on the screen.`;
          
          let translatedTTSText = ttsText;
          if (!selectedLanguage.startsWith("en")) {
            try {
              const transResponse = await axios.post(`http://localhost:8000/api/v1/translate?text=${encodeURIComponent(ttsText)}&target_language_code=${selectedLanguage}`);
              if (transResponse.data.translated) {
                translatedTTSText = transResponse.data.translated;
              }
            } catch {}
          }
          
          // Play the concise summary aloud
          await playTTS(translatedTTSText);
        } else {
          const rawNoSchemesMsg = `No matching schemes were found for your profile criteria.`;
          let noSchemesMsg = rawNoSchemesMsg;
          if (!selectedLanguage.startsWith("en")) {
            try {
              const transResponse = await axios.post(`http://localhost:8000/api/v1/translate?text=${encodeURIComponent(rawNoSchemesMsg)}&target_language_code=${selectedLanguage}`);
              if (transResponse.data.translated) {
                noSchemesMsg = transResponse.data.translated;
              }
            } catch {}
          }
          addMessage({
            id: (Date.now() + 2).toString(),
            role: "agent",
            text: noSchemesMsg
          });
          await playTTS(noSchemesMsg);
        }
      } else {
         const rawRepeatMsg = "I couldn't hear that clearly. Could you please repeat?";
         let repeatMsg = rawRepeatMsg;
         if (!selectedLanguage.startsWith("en")) {
           try {
             const transResponse = await axios.post(`http://localhost:8000/api/v1/translate?text=${encodeURIComponent(rawRepeatMsg)}&target_language_code=${selectedLanguage}`);
             if (transResponse.data.translated) {
               repeatMsg = transResponse.data.translated;
             }
           } catch {}
         }
         addMessage({ 
          id: (Date.now() + 1).toString(), 
          role: "agent", 
          text: repeatMsg
        });
        // Call local playTTS for repeatMsg
        try {
          const response = await axios.post(`http://localhost:8000/api/v1/tts?text=${encodeURIComponent(repeatMsg)}&language_code=${selectedLanguage}`);
          const audioBase64 = response.data.audio;
          if (audioBase64) {
            const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
            audio.play();
          }
        } catch {}
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

  const handleDraftApplication = async (schemeId: string) => {
    if (isProcessing) return;
    setProcessing(true);
    try {
      addMessage({
        id: Date.now().toString(),
        role: "user",
        text: `Draft application for scheme: ${schemeId}`
      });

      const response = await axios.post(`http://localhost:8000/api/v1/schemes/draft?scheme_id=${schemeId}&user_id=${userId}&language_code=${selectedLanguage}`);
      const stages = response.data.draft_stages;
      if (stages && stages.length > 0) {
        setActiveSchemeId(schemeId);
        setVerificationResult("");
        setDraftStages(stages);
        setCurrentStageIndex(0);
        
        let startMsg = `Starting application draft. I have divided the drafting process into ${stages.length} stages so we stay under the word limits. Let's start with Stage 1.`;
        if (!selectedLanguage.startsWith("en")) {
          try {
            const transResponse = await axios.post(`http://localhost:8000/api/v1/translate?text=${encodeURIComponent(startMsg)}&target_language_code=${selectedLanguage}`);
            if (transResponse.data.translated) {
              startMsg = transResponse.data.translated;
            }
          } catch {}
        }
        
        addMessage({
          id: (Date.now() + 1).toString(),
          role: "agent",
          text: startMsg
        });
        
        // Speak start msg
        // Call backend TTS
        const cleanTextForSpeechLocal = (rawText: string) => {
          return rawText.replace(/[🌟🎁🎯🔗📂•*🎉]/g, "").replace(/http[s]?:\/\/[^\s]+/g, "").replace(/[\n\r]+/g, ". ");
        };
        const playTTSLocal = (speechText: string): Promise<void> => {
          return new Promise(async (resolve) => {
            try {
              const cleanText = cleanTextForSpeechLocal(speechText);
              const res = await axios.post(`http://localhost:8000/api/v1/tts?text=${encodeURIComponent(cleanText)}&language_code=${selectedLanguage}`);
              const audioBase64 = res.data.audio;
              if (audioBase64) {
                const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
                audio.onended = () => resolve();
                audio.onerror = () => resolve();
                await audio.play();
              } else { resolve(); }
            } catch { resolve(); }
          });
        };

        await playTTSLocal(startMsg);
        
        // Immediately present stage 0
        let stageText = stages[0];
        addMessage({
          id: (Date.now() + 2).toString(),
          role: "agent",
          text: stageText
        });
        await playTTSLocal(stageText);
      }
    } catch (err) {
      console.error(err);
    }
    setProcessing(false);
  };

  const handleNextStage = async () => {
    if (isProcessing) return;
    if (draftStages.length === 0 || currentStageIndex === -1) return;
    const nextIdx = currentStageIndex + 1;
    if (nextIdx < draftStages.length) {
      setProcessing(true);
      setCurrentStageIndex(nextIdx);
      
      let stageText = draftStages[nextIdx];
      
      addMessage({
        id: Date.now().toString(),
        role: "agent",
        text: stageText
      });
      
      const cleanTextForSpeechLocal = (rawText: string) => {
        return rawText.replace(/[🌟🎁🎯🔗📂•*🎉]/g, "").replace(/http[s]?:\/\/[^\s]+/g, "").replace(/[\n\r]+/g, ". ");
      };
      const playTTSLocal = (speechText: string): Promise<void> => {
        return new Promise(async (resolve) => {
          try {
            const cleanText = cleanTextForSpeechLocal(speechText);
            const res = await axios.post(`http://localhost:8000/api/v1/tts?text=${encodeURIComponent(cleanText)}&language_code=${selectedLanguage}`);
            const audioBase64 = res.data.audio;
            if (audioBase64) {
              const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
              audio.onended = () => resolve();
              audio.onerror = () => resolve();
              await audio.play();
            } else { resolve(); }
          } catch { resolve(); }
        });
      };

      await playTTSLocal(stageText);
      setProcessing(false);
    } else {
      // Completed all stages
      let endMsg = "We have completed all stages of drafting this application. You are ready to submit it on the official portal!";
      if (!selectedLanguage.startsWith("en")) {
        try {
          const transResponse = await axios.post(`http://localhost:8000/api/v1/translate?text=${encodeURIComponent(endMsg)}&target_language_code=${selectedLanguage}`);
          if (transResponse.data.translated) {
            endMsg = transResponse.data.translated;
          }
        } catch {}
      }
      addMessage({
        id: Date.now().toString(),
        role: "agent",
        text: endMsg
      });
      const cleanTextForSpeechLocal = (rawText: string) => {
        return rawText.replace(/[🌟🎁🎯🔗📂•*🎉]/g, "").replace(/http[s]?:\/\/[^\s]+/g, "").replace(/[\n\r]+/g, ". ");
      };
      const playTTSLocal = (speechText: string): Promise<void> => {
        return new Promise(async (resolve) => {
          try {
            const cleanText = cleanTextForSpeechLocal(speechText);
            const res = await axios.post(`http://localhost:8000/api/v1/tts?text=${encodeURIComponent(cleanText)}&language_code=${selectedLanguage}`);
            const audioBase64 = res.data.audio;
            if (audioBase64) {
              const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
              audio.onended = () => resolve();
              audio.onerror = () => resolve();
              await audio.play();
            } else { resolve(); }
          } catch { resolve(); }
        });
      };
      await playTTSLocal(endMsg);
      // Reset stages
      setDraftStages([]);
      setCurrentStageIndex(-1);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950 p-4 sm:p-8 rounded-2xl shadow-xl max-w-3xl w-full mx-auto border border-slate-200 dark:border-slate-800">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800 mb-4">
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200">Bharat Voice Assistant</h2>
        <button
          onClick={handleResetSession}
          disabled={isRecording || isProcessing}
          className="flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold text-red-600 hover:text-white hover:bg-red-600 border border-red-600 rounded-lg shadow-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>🔄 New User / Reset Session</span>
        </button>
      </div>
      <div className="flex-1 overflow-y-auto mb-4 space-y-4 min-h-[300px]">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <p className="text-center">Start speaking to discover government schemes.</p>
          </div>
        ) : (
          messages.map((msg) => {
            const isSchemesMsg = msg.role === 'agent' && msg.text.includes('🎉') && schemes.length > 0;
            return (
              <div key={msg.id} className="flex flex-col space-y-2">
                <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`p-4 rounded-2xl max-w-[80%] break-words ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-none'}`}>
                    {renderMessageText(msg.text, msg.role === 'user')}
                  </div>
                </div>
                {isSchemesMsg && (
                  <div className="flex flex-wrap gap-2 justify-start px-2">
                    {schemes.map((scheme) => (
                      <button
                        key={scheme.id}
                        onClick={() => handleDraftApplication(scheme.id)}
                        disabled={isProcessing}
                        className="bg-green-600 hover:bg-green-700 text-white text-xs px-3.5 py-2 rounded-full shadow transition-colors duration-200 disabled:bg-slate-400"
                      >
                        📝 Draft {scheme.title.split('(')[0].trim()}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
        {draftStages.length > 0 && currentStageIndex !== -1 && (
          <div className="flex flex-col space-y-4 px-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-sm max-w-[80%]">
            
            {/* Stage 1: Document Verification uploader */}
            {currentStageIndex === 0 && (
              <div className="flex flex-col space-y-2">
                <span className="text-xs font-semibold text-slate-500 uppercase">Document Verification</span>
                <input
                  type="file"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    setProcessing(true);
                    try {
                      const formData = new FormData();
                      formData.append("document", file);
                      formData.append("document_type", "Aadhaar / Income Certificate");
                      formData.append("user_id", userId);
                      
                      const verifyRes = await axios.post(`http://localhost:8000/api/v1/schemes/verify-document`, formData, {
                        headers: { "Content-Type": "multipart/form-data" }
                      });
                      
                      setVerificationResult(verifyRes.data.message);
                      if (verifyRes.data.profile) {
                        setUserProfile(verifyRes.data.profile);
                      }
                      
                      // Speak verification result
                      const cleanTextForSpeechLocal = (rawText: string) => {
                        return rawText.replace(/[🌟🎁🎯🔗📂•*🎉]/g, "").replace(/http[s]?:\/\/[^\s]+/g, "").replace(/[\n\r]+/g, ". ");
                      };
                      const playTTSLocal = (speechText: string): Promise<void> => {
                        return new Promise(async (resolve) => {
                          try {
                            const cleanText = cleanTextForSpeechLocal(speechText);
                            const res = await axios.post(`http://localhost:8000/api/v1/tts?text=${encodeURIComponent(cleanText)}&language_code=${selectedLanguage}`);
                            const audioBase64 = res.data.audio;
                            if (audioBase64) {
                              const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
                              audio.onended = () => resolve();
                              audio.onerror = () => resolve();
                              await audio.play();
                            } else { resolve(); }
                          } catch { resolve(); }
                        });
                      };
                      await playTTSLocal(verifyRes.data.message);
                    } catch (err) {
                      console.error(err);
                    }
                    setProcessing(false);
                  }}
                  disabled={isProcessing}
                  className="block w-full text-xs text-slate-500 file:mr-4 file:py-1 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                />
                {verificationResult && (
                  <p className="text-xs text-green-600 font-medium dark:text-green-400 mt-1">{verificationResult}</p>
                )}
              </div>
            )}

            {/* Stage 2: Form Review */}
            {currentStageIndex === 1 && (
              <div className="flex flex-col space-y-3 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                <span className="text-xs font-semibold text-slate-500 uppercase">Review Pre-filled Form Details</span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <label className="block text-slate-400 font-medium">Name</label>
                    <input
                      type="text"
                      value={userProfile?.name || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, name: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">Age</label>
                    <input
                      type="text"
                      value={userProfile?.age || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, age: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">Gender</label>
                    <input
                      type="text"
                      value={userProfile?.gender || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, gender: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">Annual Income</label>
                    <input
                      type="text"
                      value={userProfile?.annual_income || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, annual_income: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">Caste Category</label>
                    <input
                      type="text"
                      value={userProfile?.caste_category || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, caste_category: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">State</label>
                    <input
                      type="text"
                      value={userProfile?.state || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, state: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">District</label>
                    <input
                      type="text"
                      value={userProfile?.district || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, district: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">Occupation</label>
                    <input
                      type="text"
                      value={userProfile?.occupation || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, occupation: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">Aadhaar Number</label>
                    <input
                      type="text"
                      value={userProfile?.aadhaar_number || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, aadhaar_number: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-medium">Mobile Number</label>
                    <input
                      type="text"
                      value={userProfile?.mobile_number || ""}
                      onChange={(e) => setUserProfile({ ...userProfile, mobile_number: e.target.value })}
                      className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-1 text-slate-800 dark:text-slate-200"
                    />
                  </div>
                </div>
                <button
                  onClick={async () => {
                    setProcessing(true);
                    try {
                      const response = await axios.post(`http://localhost:8000/api/v1/profile/update?user_id=${userId}`, userProfile);
                      if (response.data.profile) {
                        setUserProfile(response.data.profile);
                      }
                      alert("Profile details updated successfully!");
                    } catch (err) {
                      console.error("Error saving manual edits:", err);
                      alert("Failed to save changes. Is the backend running?");
                    }
                    setProcessing(false);
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-[11px] px-3 py-1.5 rounded transition-all mt-1 w-fit cursor-pointer"
                >
                  Save Form Changes
                </button>
              </div>
            )}

            {/* Stage 3: PDF pre-filled download option & Autofill Bookmarklet */}
            {currentStageIndex === 2 && (() => {
              const currentScheme = schemes.find(s => s.id === activeSchemeId) || {};
              const sourceUrl = currentScheme.source_url || "https://pmkisan.gov.in/";
              
              // Generate dynamic bookmarklet code pre-filled with the user details
              const bookmarkletCode = `javascript:(function(){
                const profile = ${JSON.stringify(userProfile || {})};
                alert('Bharat Voice Assistant: Starting Autofill on this page!');
                
                const inputs = document.querySelectorAll('input, select, textarea');
                
                const fillMap = {
                  name: profile.name,
                  age: profile.age,
                  gender: profile.gender,
                  state: profile.state,
                  district: profile.district,
                  income: profile.annual_income,
                  caste: profile.caste_category,
                  occupation: profile.occupation,
                  disability: profile.disability_status,
                  aadhaar: profile.aadhaar_number,
                  mobile: profile.mobile_number
                };

                const regexMap = {
                  name: /name|username|full\\s*name/i,
                  age: /age|dob|birth/i,
                  gender: /gender|sex/i,
                  state: /state|domicile/i,
                  district: /district|city/i,
                  income: /income|annual|salary/i,
                  caste: /caste|category/i,
                  occupation: /occupation|job/i,
                  disability: /disability|handicap/i,
                  aadhaar: /aadhaar|uid|aadhaar_number/i,
                  mobile: /mobile|phone|contact|mobile_number/i
                };

                inputs.forEach(input => {
                  const nameAttr = (input.getAttribute('name') || '').toLowerCase();
                  const idAttr = (input.getAttribute('id') || '').toLowerCase();
                  const placeholder = (input.getAttribute('placeholder') || '').toLowerCase();
                  
                  for (const [key, val] of Object.entries(fillMap)) {
                    if (val && String(val).toLowerCase() !== 'not specified') {
                      const regex = regexMap[key];
                      if (regex.test(nameAttr) || regex.test(idAttr) || regex.test(placeholder)) {
                        input.value = val;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        input.style.backgroundColor = '#dcfce7'; // Highlight filled fields in green
                      }
                    }
                  }
                });
                alert('Autofill complete! Verified fields are highlighted in green.');
              })()`;

              return (
                <div className="flex flex-col space-y-4">
                  <div className="flex flex-col space-y-2">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Pre-filled Application PDF</span>
                    <a
                      href={`http://localhost:8000/api/v1/schemes/pdf-draft?scheme_id=${activeSchemeId}&user_id=${userId}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex justify-center items-center bg-red-600 hover:bg-red-700 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow cursor-pointer transition-colors duration-200 w-fit"
                    >
                      📄 Download Draft PDF
                    </a>
                  </div>

                  <div className="flex flex-col space-y-2 p-3 bg-blue-50 dark:bg-blue-950/40 rounded-lg border border-blue-100 dark:border-blue-900">
                    <span className="text-xs font-bold text-blue-700 dark:text-blue-400 uppercase">🚀 Auto-fill Browser Tool</span>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400">
                      Drag the button below to your bookmarks bar. Then visit the official site and click it to autofill your details automatically!
                    </p>
                    <div className="flex flex-wrap gap-2 pt-1">
                      <a
                        href={bookmarkletCode}
                        onClick={(e) => {
                          e.preventDefault();
                          alert("Drag this button to your Bookmarks Bar (Ctrl+Shift+O) to install it, then click it on the official form page!");
                        }}
                        className="inline-flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-3 py-1.5 rounded shadow cursor-move"
                      >
                        ⚡ Drag to Bookmarks (Autofill)
                      </a>
                      <a
                        href={sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center justify-center bg-slate-700 hover:bg-slate-800 text-white text-xs font-semibold px-3 py-1.5 rounded shadow cursor-pointer"
                      >
                        🔗 Go to Official Portal
                      </a>
                    </div>
                  </div>
                  <button
                    onClick={async () => {
                      setProcessing(true);
                      try {
                        const response = await axios.post(`http://localhost:8000/api/v1/schemes/submit?scheme_id=${activeSchemeId}&user_id=${userId}`);
                        if (response.data.success) {
                          alert("Application process begins");
                          window.open(response.data.pdf_url, '_blank');
                          addMessage({
                            id: Date.now().toString(),
                            role: "agent",
                            text: "🎉 Congratulations! Your application draft has been processed. I have opened the pre-filled PDF in a new tab.\n\n👉 **To submit directly on the Official Government Portal**:\n1. Click the **Go to Official Portal** link.\n2. Click the **Drag to Bookmarks (Autofill)** bookmarklet to populate your details automatically!"
                          });
                        }
                      } catch (err) {
                        console.error(err);
                        alert("Submission failed. Is the backend running?");
                      }
                      setProcessing(false);
                    }}
                    className="inline-flex justify-center items-center bg-green-600 hover:bg-green-700 text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow cursor-pointer transition-all duration-200 w-full mt-3"
                  >
                    🚀 Submit Application
                  </button>
                </div>
              );
            })()}

            <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700">
              <span className="text-xs font-medium text-slate-400">Stage {currentStageIndex + 1}/{draftStages.length}</span>
              <button
                onClick={handleNextStage}
                disabled={isProcessing}
                className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-4.5 py-2 rounded-full shadow transition-all disabled:bg-slate-400"
              >
                <span>➡️ {currentStageIndex + 1 < draftStages.length ? 'Next Stage' : 'Finish Draft'}</span>
              </button>
            </div>
          </div>
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
