"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, FileText, CheckCircle, Upload } from "lucide-react";

export default function VoiceCanvas() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [profileData, setProfileData] = useState<any>(null);
  const [showHITL, setShowHITL] = useState(false);
  const [approved, setApproved] = useState(false);

  // Mock Voice Interaction Loop
  const handleOrbClick = () => {
    if (isRecording) {
      setIsRecording(false);
      setIsProcessing(true);
      // Simulate backend processing
      setTimeout(() => {
        setIsProcessing(false);
        setProfileData({
          name: "Ramesh Kumar",
          occupation: "Farmer",
          land: "3 Acres",
          location: "Maharashtra",
          schemes: ["PM-Kisan Samman Nidhi", "Fasal Bima Yojana"],
          status: "eligible"
        });
        
        // Simulate n8n hitting HITL after 2 seconds
        setTimeout(() => setShowHITL(true), 2000);

      }, 3000);
    } else {
      setIsRecording(true);
      setProfileData(null);
      setShowHITL(false);
      setApproved(false);
    }
  };

  const handleApprove = () => {
    setApproved(true);
    setShowHITL(false);
    // In real app, call /handle-hitl-approval endpoint
  };

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center bg-slate-900 overflow-hidden">
      
      {/* Background ambient light */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="absolute top-8 w-full text-center z-10">
        <h1 className="text-3xl font-light tracking-widest text-white/90">BHARAT VOICE AGENT</h1>
      </header>

      {/* Main Canvas Area */}
      <div className="flex w-full max-w-7xl px-8 items-center justify-between z-10">
        
        {/* Left Side: Dynamic Profile Card */}
        <div className="w-1/3 min-h-[400px] flex items-center justify-start">
          <AnimatePresence>
            {profileData && (
              <motion.div
                initial={{ opacity: 0, x: -50, scale: 0.9 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: -50, scale: 0.9 }}
                transition={{ duration: 0.5, type: "spring" }}
                className="glass-panel p-6 rounded-2xl w-full"
              >
                <div className="flex items-center gap-4 mb-6 border-b border-white/10 pb-4">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <FileText className="text-blue-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-white">{profileData.name}</h2>
                    <p className="text-blue-200/60 text-sm">Profile Extracted</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <ProfileBadge label="Occupation" value={profileData.occupation} delay={0.2} />
                  <ProfileBadge label="Land" value={profileData.land} delay={0.4} />
                  <ProfileBadge label="Location" value={profileData.location} delay={0.6} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Center: The Voice Orb */}
        <div className="w-1/3 flex flex-col items-center justify-center cursor-pointer" onClick={handleOrbClick}>
          <motion.div
            animate={{
              scale: isRecording ? [1, 1.2, 1] : isProcessing ? [1, 1.1, 1] : [1, 1.05, 1],
              boxShadow: isRecording 
                ? ["0px 0px 40px rgba(239, 68, 68, 0.4)", "0px 0px 80px rgba(239, 68, 68, 0.6)", "0px 0px 40px rgba(239, 68, 68, 0.4)"]
                : isProcessing
                ? ["0px 0px 40px rgba(59, 130, 246, 0.4)", "0px 0px 60px rgba(59, 130, 246, 0.8)", "0px 0px 40px rgba(59, 130, 246, 0.4)"]
                : ["0px 0px 20px rgba(255,255,255,0.1)", "0px 0px 30px rgba(255,255,255,0.2)", "0px 0px 20px rgba(255,255,255,0.1)"]
            }}
            transition={{
              duration: isRecording ? 1 : isProcessing ? 0.8 : 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className={`w-40 h-40 rounded-full flex items-center justify-center transition-colors duration-500 ${
              isRecording ? "bg-red-500/20 border-red-500/50" : "bg-blue-500/10 border-blue-500/30"
            } border backdrop-blur-md`}
          >
            <Mic className={`w-12 h-12 ${isRecording ? "text-red-400" : "text-blue-300"}`} />
          </motion.div>
          <p className="mt-8 text-white/50 text-sm tracking-wide">
            {isRecording ? "Listening..." : isProcessing ? "Synthesizing Profile..." : "Tap to Speak"}
          </p>
        </div>

        {/* Right Side: Eligible Schemes & HITL */}
        <div className="w-1/3 min-h-[400px] flex items-center justify-end relative">
          <AnimatePresence>
            {profileData && (
              <motion.div
                initial={{ opacity: 0, x: 50, scale: 0.9 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 50, scale: 0.9 }}
                transition={{ duration: 0.5, delay: 0.8, type: "spring" }}
                className="w-full flex flex-col gap-4"
              >
                <h3 className="text-lg text-emerald-400 font-medium mb-2 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" /> Eligible Schemes
                </h3>
                {profileData.schemes.map((scheme: string, idx: number) => (
                  <motion.div
                    key={scheme}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1 + idx * 0.2 }}
                    className="glass-panel p-4 rounded-xl border-emerald-500/20"
                  >
                    <p className="text-white/90">{scheme}</p>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* HITL Overlay */}
          <AnimatePresence>
            {showHITL && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8, y: -20 }}
                className="absolute inset-0 z-20 flex items-center justify-center"
              >
                <div className="glass-panel p-8 rounded-2xl w-full text-center border-yellow-500/30 bg-slate-900/80 backdrop-blur-xl">
                  <h3 className="text-xl font-bold text-yellow-400 mb-2">Human Verification</h3>
                  <p className="text-white/70 text-sm mb-6">n8n workflow is paused. Approve scheme application for {profileData?.name}?</p>
                  <div className="flex gap-4 justify-center">
                    <button className="px-6 py-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition">Reject</button>
                    <button onClick={handleApprove} className="px-6 py-2 rounded-full bg-yellow-500 text-slate-900 font-semibold hover:bg-yellow-400 transition shadow-[0_0_20px_rgba(234,179,8,0.4)]">Approve Submission</button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Final Approval State */}
          <AnimatePresence>
            {approved && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="absolute inset-0 z-30 flex items-center justify-center pointer-events-none"
              >
                <div className="text-center">
                  <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/50 shadow-[0_0_40px_rgba(16,185,129,0.5)]">
                    <Upload className="w-10 h-10 text-emerald-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-emerald-400">Submitted</h3>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

      </div>
    </div>
  );
}

function ProfileBadge({ label, value, delay }: { label: string, value: string, delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="flex justify-between items-center bg-black/20 p-3 rounded-lg border border-white/5"
    >
      <span className="text-white/50 text-sm">{label}</span>
      <span className="text-white font-medium">{value}</span>
    </motion.div>
  );
}
