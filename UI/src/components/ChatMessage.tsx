import React from "react";
import { Bot, User } from "lucide-react";
interface ChatMessageProps {
  isAi: boolean;
  message: string;
}
export const ChatMessage: React.FC<ChatMessageProps> = ({
  isAi,
  message
}) => {
  return <div className={`flex ${isAi ? "justify-start" : "justify-end"} mb-4 items-start gap-2`}>
      {isAi && <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500/20 to-indigo-500/20 flex items-center justify-center border border-blue-400/20">
          <Bot size={18} className="text-blue-400" />
        </div>}
      <div className={`max-w-[80%] p-4 rounded-xl shadow-lg ${isAi ? "bg-gradient-to-r from-slate-700/50 to-slate-800/50 text-slate-200 border border-slate-700/50" : "bg-gradient-to-r from-blue-500 to-indigo-600 text-white"}`}>
        <p className="text-sm md:text-base">{message}</p>
      </div>
      {!isAi && <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center">
          <User size={18} className="text-white" />
        </div>}
    </div>;
};