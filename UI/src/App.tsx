import React, { useEffect, useState, useRef } from "react";
import { Send, Book, Brain, Sparkles } from "lucide-react";
import { ChatMessage } from "./components/ChatMessage";

export function App() {
  const [messages, setMessages] = useState([{
    isAi: true,
    message: "Welcome! I can help you explore knowledge about various topics related to India. What would you like to know?"
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
      const response = await fetch('/query', {
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
    <div className="flex flex-col w-full h-screen bg-gradient-to-b from-orange-100 via-yellow-100 to-pink-100">
      <header className="w-full bg-white/50 backdrop-blur-sm shadow-lg border-b border-orange-200/50 flex-none">
        <div className="max-w-6xl mx-auto p-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="relative">
              <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-orange-400 to-pink-500 opacity-75 blur"></div>
              <div className="relative bg-white rounded-full p-2">
                <Book className="w-10 h-10 text-orange-400" />
              </div>
            </div>
            <h1 className="text-3xl font-semibold bg-gradient-to-r from-orange-400 to-pink-500 text-transparent bg-clip-text">
              Knowledge Graph Explorer
            </h1>
          </div>
          <p className="text-orange-600">
            Your personal AI-powered knowledge retriever
          </p>
        </div>
      </header>
      <main className="flex-1 w-full max-w-6xl mx-auto p-4 relative min-h-0">
        <div className="absolute top-20 right-8 opacity-10">
          <Brain className="w-24 h-24 text-orange-400" />
        </div>
        <div className="absolute bottom-20 left-8 opacity-10">
          <Sparkles className="w-20 h-20 text-pink-400" />
        </div>
        <div className="relative z-10 bg-white/50 backdrop-blur-sm rounded-2xl shadow-lg border border-orange-200/50 p-6 h-full flex flex-col">
          <div className="flex-1 min-h-0">
            <div className="h-full overflow-y-auto pr-2">
              <div className="space-y-4">
                {messages.map((msg, index) => (
                  <ChatMessage key={index} isAi={msg.isAi} message={msg.message} />
                ))}
                {isLoading && (
                  <div className="flex items-center justify-center p-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>
          <form onSubmit={handleSubmit} className="flex gap-2 pt-4 border-t border-orange-200/50 flex-none">
            <input 
              type="text" 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              placeholder="Ask me anything..." 
              className="flex-1 p-4 rounded-xl border border-orange-200 focus:outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-400/20 transition-all bg-white/50 text-orange-900 placeholder-orange-400" 
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="p-4 bg-gradient-to-r from-orange-400 to-pink-500 text-white rounded-xl hover:opacity-90 transition-all hover:shadow-lg hover:shadow-orange-500/20 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
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