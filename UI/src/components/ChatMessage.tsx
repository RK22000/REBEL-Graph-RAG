import React from "react";
import { Bot, User } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  isAi: boolean;
  message: string;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  isAi,
  message
}) => {
  return <div className={`flex ${isAi ? "justify-start" : "justify-end"} mb-4 items-start gap-2`}>
      {isAi && <div className="w-8 h-8 rounded-full bg-gradient-to-r from-orange-500/20 to-pink-500/20 flex items-center justify-center border border-orange-400/20">
          <Bot size={18} className="text-orange-400" />
        </div>}
      <div className={`max-w-[80%] p-4 rounded-xl shadow-lg ${isAi ? "bg-gradient-to-r from-orange-500/50 to-pink-500/50 text-black border border-orange-400/50" : "bg-gradient-to-r from-yellow-200 to-orange-200 text-black"}`}>
        <div className="prose prose-sm md:prose-base max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message}
          </ReactMarkdown>
        </div>
      </div>
      {!isAi && <div className="w-8 h-8 rounded-full bg-gradient-to-r from-yellow-200 to-orange-200 flex items-center justify-center">
          <User size={18} className="text-black" />
        </div>}
    </div>;
};