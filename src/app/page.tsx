import VoiceInterface from "@/components/VoiceInterface";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-100 dark:bg-slate-900 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-3xl mb-8 text-center">
        <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-2">
          Bharat Voice Agent
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400">
          Your AI Assistant for discovering government schemes in your native language.
        </p>
      </div>
      
      <div className="flex-1 w-full flex items-center justify-center">
        <VoiceInterface />
      </div>
    </main>
  );
}
