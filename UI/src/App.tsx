import React, { useEffect, useState, useRef } from "react";
import { Send, Book, Brain, Sparkles } from "lucide-react";
import { ChatMessage } from "./components/ChatMessage";

export function App() {
  const [messages, setMessages] = useState([{
    isAi: true,
    message: "Welcome to GraphRAG! I can help you explore knowledge about India, including its history, geography, culture, and more. What would you like to know?"
  }]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth"
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    // Add user message
    setMessages(prev => [...prev, {
      isAi: false,
      message: input
    }]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch('https://1742-204-52-16-125.ngrok-free.app/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input
        })
      });

      const data = await response.json();
      
      // Add AI response
      setMessages(prev => [...prev, {
        isAi: true,
        message: data.result
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        isAi: true,
        message: "Sorry, I encountered an error while processing your request. Please try again."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full h-screen bg-gradient-to-b from-slate-800 via-blue-900 to-slate-900">
      <header className="w-full bg-slate-800/50 backdrop-blur-sm shadow-lg border-b border-slate-700/50 flex-none">
        <div className="max-w-3xl mx-auto p-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="relative">
              <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 opacity-75 blur"></div>
              <div className="relative bg-slate-900 rounded-full p-2">
                <Book className="w-10 h-10 text-blue-400" />
              </div>
            </div>
            <h1 className="text-3xl font-semibold bg-gradient-to-r from-blue-400 to-indigo-400 text-transparent bg-clip-text">
              GraphRAG
            </h1>
          </div>
          <p className="text-slate-400">
            Your AI-powered knowledge explorer for Indian history and culture
          </p>
        </div>
      </header>
      <main className="flex-1 w-full max-w-3xl mx-auto p-4 relative min-h-0">
        <div className="absolute top-20 right-8 opacity-10">
          <Brain className="w-24 h-24 text-blue-400" />
        </div>
        <div className="absolute bottom-20 left-8 opacity-10">
          <Sparkles className="w-20 h-20 text-indigo-400" />
        </div>
        <div className="relative z-10 bg-slate-800/50 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-700/50 p-6 h-full flex flex-col">
          <div className="flex-1 min-h-0">
            <div className="h-full overflow-y-auto pr-2">
              <div className="space-y-4">
                {messages.map((msg, index) => (
                  <ChatMessage key={index} isAi={msg.isAi} message={msg.message} />
                ))}
                {isLoading && (
                  <div className="flex items-center justify-center p-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>
          <form onSubmit={handleSubmit} className="flex gap-2 pt-4 border-t border-slate-700/50 flex-none">
            <input 
              type="text" 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              placeholder="Ask about India's history, geography, culture..." 
              className="flex-1 p-4 rounded-xl border border-slate-700 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all bg-slate-800/50 text-slate-200 placeholder-slate-400" 
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="p-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl hover:opacity-90 transition-all hover:shadow-lg hover:shadow-blue-500/20 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              <Send size={20} />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}