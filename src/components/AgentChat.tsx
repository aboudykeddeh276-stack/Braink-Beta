import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, ChevronDown, Sparkles, StopCircle, ArrowRight, Terminal } from 'lucide-react';

interface Message {
  role: 'user' | 'agent' | 'system' | 'tool';
  content: string;
}

export default function AgentChat({ onAgentAction }: { onAgentAction: (action: any) => void }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'agent', content: '[BRAINK SYSTEM ONLINE] Hello. I am BrainK, your autonomous agent. I have full access to execute bash commands, read, and write files in this environment. What would you like me to do?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sessionId = 'session_alpha_1';

  useEffect(() => {
    // Fetch history
    fetch('/api/chat/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId })
    })
      .then(res => res.json())
      .then(data => {
        if (data.history && data.history.length > 0) {
          const loadedMsgs = data.history.map((h: any) => ({
            role: h.role === 'model' ? 'agent' : 'user',
            content: h.content
          }));
          setMessages(loadedMsgs);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    
    const userText = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    
    onAgentAction({
      type: "EVALUATING",
      details: "Analyzing user intent...",
      activeTool: null
    });
    
    setIsLoading(true);
    setMessages(prev => [...prev, { role: 'agent', content: '' }]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, message: userText })
      });
      
      if (!response.ok || !response.body) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      onAgentAction({
        type: "GENERATING",
        details: "Synthesizing response...",
        activeTool: null
      });

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '');
            if (dataStr === '[DONE]') {
               onAgentAction({ type: "IDLE", details: "Awaiting input", activeTool: null });
               break;
            }
            try {
              const data = JSON.parse(dataStr);
              if (data.error) {
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1].content = data.error;
                  return newMsgs;
                });
                onAgentAction({ type: "ERROR", details: data.error, activeTool: null });
                break;
              }
              if (data.text) {
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1].content += data.text;
                  return newMsgs;
                });
                onAgentAction({ type: "GENERATING", details: "Synthesizing response...", activeTool: null });
              }
              if (data.toolCall) {
                const callStr = `${data.toolCall.name}(${JSON.stringify(data.toolCall.args)})`;
                onAgentAction({
                   type: "EXECUTING_TOOL",
                   details: `Running ${data.toolCall.name}...`,
                   activeTool: callStr
                });
                setMessages(prev => [
                   ...prev, 
                   { role: 'tool', content: `Executing: ${callStr}` },
                   { role: 'agent', content: '' } // new agent message block for the text after tool call
                ]);
              }
              if (data.toolResult) {
                onAgentAction({
                   type: "EVALUATING",
                   details: `Analyzing result from ${data.toolResult.name}...`,
                   activeTool: null
                });
              }
            } catch (e) {
              // Ignore incomplete parse
            }
          }
        }
      }
    } catch (err) {
      onAgentAction({ type: "ERROR", details: "Connection severed.", activeTool: null });
    } finally {
      setIsLoading(false);
      onAgentAction({ type: "IDLE", details: "Awaiting input", activeTool: null });
    }
  };

  return (
    <div className="flex-1 flex flex-col relative h-full bg-white dark:bg-[#09090b]">
      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto custom-scrollbar px-4 pb-36 pt-8 flex flex-col items-center"
      >
        <div className="w-full max-w-3xl flex flex-col gap-6">
          {messages.map((msg, i) => {
            if (msg.role === 'tool') {
              return (
                <div key={i} className="flex justify-start w-full">
                   <div className="flex items-center gap-2 px-3 py-2 bg-neutral-50 dark:bg-neutral-800/60 border border-neutral-200 dark:border-neutral-800 rounded-lg text-xs font-mono text-neutral-500 shadow-sm ml-12">
                     <Terminal size={12} />
                     <span>{msg.content}</span>
                   </div>
                </div>
              );
            }
            if (!msg.content && i === messages.length - 1 && isLoading) {
               // Only show a loading bubble if content is empty and we're loading
               return (
                  <div key={i} className={`flex w-full justify-start`}>
                    <div className="flex gap-4 w-full max-w-[90%]">
                      <div className="w-8 h-8 rounded-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                        <Sparkles size={16} className="text-white dark:text-neutral-900" />
                      </div>
                      <div className="flex-1 text-[15px] leading-relaxed text-neutral-800 dark:text-neutral-200 mt-1 min-h-[32px]">
                        <span className="animate-pulse">●</span>
                      </div>
                    </div>
                  </div>
               );
            }
            if (!msg.content) return null;

            return (
              <div key={i} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'user' ? (
                  <div className="bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 px-5 py-3 rounded-2xl max-w-[80%] text-[15px] leading-relaxed shadow-sm whitespace-pre-wrap">
                    {msg.content}
                  </div>
                ) : (
                  <div className="flex gap-4 w-full max-w-[90%]">
                    <div className="w-8 h-8 rounded-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                      <Sparkles size={16} className="text-white dark:text-neutral-900" />
                    </div>
                    <div className="flex-1 text-[15px] leading-relaxed text-neutral-800 dark:text-neutral-200 mt-1 min-h-[32px] prose prose-neutral dark:prose-invert">
                      {msg.content}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-white via-white to-transparent dark:from-[#09090b] dark:via-[#09090b] pt-12 pb-6 px-4 flex justify-center pointer-events-none">
        <div className="w-full max-w-3xl pointer-events-auto">
          <div className="bg-white dark:bg-neutral-800 border border-border rounded-2xl shadow-lg transition-all focus-within:ring-2 focus-within:ring-neutral-200 dark:focus-within:ring-neutral-700 flex flex-col">
            <div className="px-4 pt-4 pb-2">
              <textarea
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                    e.currentTarget.style.height = 'auto';
                  }
                }}
                placeholder="Message your agent..."
                className="w-full bg-transparent border-none text-[15px] outline-none resize-none max-h-[200px] min-h-[24px] py-0 text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 custom-scrollbar leading-relaxed"
                rows={1}
                disabled={isLoading}
              />
            </div>
            
            <div className="px-3 pb-3 flex justify-between items-center">
              <div className="flex items-center gap-1">
                <button className="p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg transition-colors">
                  <Paperclip size={18} />
                </button>
              </div>
              
              <div className="flex items-center gap-2">
                {isLoading ? (
                  <button 
                    className="w-8 h-8 rounded-full bg-neutral-900 dark:bg-neutral-100 text-white dark:text-neutral-900 flex items-center justify-center hover:opacity-80 transition-opacity"
                  >
                    <StopCircle size={18} />
                  </button>
                ) : (
                  <button 
                    onClick={sendMessage}
                    disabled={!input.trim()}
                    className="w-8 h-8 rounded-full bg-neutral-900 dark:bg-neutral-100 text-white dark:text-neutral-900 flex items-center justify-center hover:opacity-80 transition-opacity disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <ArrowRight size={18} />
                  </button>
                )}
              </div>
            </div>
          </div>
          
          <div className="text-center mt-3 text-xs text-neutral-400">
            Agents can make mistakes. Consider verifying important information.
          </div>
        </div>
      </div>
    </div>
  );
}
