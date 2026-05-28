"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, BookOpen } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatUI() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sources, setSources] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setSources([]);

    // Add empty AI message to stream into
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        
        // SSE parsing
        const lines = chunk.split("\n\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "");
            if (!dataStr.trim()) continue;
            
            try {
              const data = JSON.parse(dataStr);
              if (data.type === "token") {
                setMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMessage = { ...newMessages[newMessages.length - 1] };
                  lastMessage.content += data.content;
                  newMessages[newMessages.length - 1] = lastMessage;
                  return newMessages;
                });
              } else if (data.type === "sources") {
                setSources(data.sources);
              } else if (data.type === "error") {
                console.error("Stream error:", data.content);
              }
            } catch (e) {
              console.error("Error parsing JSON:", dataStr);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-4xl mx-auto glass-panel rounded-2xl overflow-hidden shadow-2xl relative">
      
      {/* Header */}
      <div className="p-5 border-b border-white/10 bg-black/20 flex items-center justify-between z-10 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/20 rounded-xl">
            <Bot className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white tracking-tight">RAG Assistant</h1>
            <p className="text-xs text-blue-300/70">Psychology & Dating Knowledge Base</p>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
            <Bot className="w-16 h-16 mb-4 text-blue-400 opacity-50" />
            <h2 className="text-xl font-medium mb-2 text-white">How can I help you today?</h2>
            <p className="text-sm max-w-md">Ask me anything about dating and psychology based on my trained knowledge base.</p>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((m, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex gap-4 ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {m.role === "assistant" && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center mt-1 border border-blue-500/30">
                    <Bot className="w-4 h-4 text-blue-400" />
                  </div>
                )}
                
                <div
                  className={`px-5 py-3.5 rounded-2xl max-w-[85%] leading-relaxed ${
                    m.role === "user"
                      ? "bg-blue-600/80 text-white rounded-tr-sm border border-blue-500/50 shadow-lg shadow-blue-500/10"
                      : "bg-[var(--ai-msg-bg)] border border-white/5 text-gray-200 rounded-tl-sm shadow-xl backdrop-blur-md"
                  }`}
                >
                  <div className="prose prose-invert prose-p:leading-relaxed prose-pre:bg-black/50 max-w-none">
                    <ReactMarkdown>
                      {m.content}
                    </ReactMarkdown>
                  </div>
                </div>

                {m.role === "user" && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700/50 flex items-center justify-center mt-1 border border-white/10">
                    <User className="w-4 h-4 text-gray-300" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        
        {/* Loading Indicator */}
        {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
              <Bot className="w-4 h-4 text-blue-400" />
            </div>
            <div className="px-5 py-3.5 rounded-2xl bg-[var(--ai-msg-bg)] border border-white/5 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              <span className="text-sm text-gray-400">Searching knowledge base...</span>
            </div>
          </motion.div>
        )}
        
        {/* Sources Display */}
        {sources.length > 0 && !isLoading && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4 ml-12">
             <div className="px-4 py-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs text-purple-300 flex items-center gap-2">
               <BookOpen className="w-3 h-3" />
               <span>Sources: {sources.join(", ")}</span>
             </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-white/10 bg-black/30 backdrop-blur-md">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
            disabled={isLoading}
            className="w-full bg-white/5 border border-white/10 text-white rounded-xl py-4 pl-5 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-gray-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-white/5 disabled:text-gray-500 text-white transition-all disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
