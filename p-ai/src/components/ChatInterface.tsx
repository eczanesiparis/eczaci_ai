import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Pill } from 'lucide-react';
import axios from 'axios';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: string[];
}

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: 'Merhaba! Ben Eczacı AI, size yardımcı olabilirim. Hangi ilaç hakkında bilgi almak istersiniz?'
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await axios.post('https://eczaci-ai.onrender.com/api/chat', { message: userMessage.content });
            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.data.answer || 'Üzgünüm, bir cevap oluşturamadım.',
                sources: response.data.sources ? response.data.sources.slice(0, 1) : []
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error("Error communicating with backend:", error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'Sunucuyla iletişim kurulurken bir hata oluştu. Lütfen arka plan servisinin çalıştığından emin olun.'
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-slate-50 text-slate-800">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10 w-full shadow-sm">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 rounded-xl text-green-600">
                        <Pill size={24} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-green-600 to-emerald-500 bg-clip-text text-transparent">
                            Eczacı AI
                        </h1>
                        <p className="text-xs text-slate-500">Eczane Asistanı</p>
                    </div>
                </div>
            </header>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-4xl mx-auto w-full">
                {messages.map((m) => (
                    <div
                        key={m.id}
                        className={cn(
                            "flex gap-4 w-full animate-in fade-in slide-in-from-bottom-2",
                            m.role === 'user' ? "flex-row-reverse" : "flex-row"
                        )}
                    >
                        <div className={cn(
                            "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border",
                            m.role === 'user'
                                ? "bg-white border-2 border-[#1E9E3D] text-[#1E9E3D]"
                                : "bg-[#1E9E3D] border-transparent text-white"
                        )}>
                            {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                        </div>
                        <div className={cn(
                            "px-4 py-3 rounded-2xl max-w-[85%] text-sm sm:text-base leading-relaxed whitespace-pre-wrap shadow-sm",
                            m.role === 'user'
                                ? "bg-white border-2 border-[#1E9E3D] text-[#1E9E3D] rounded-tr-sm font-medium"
                                : "bg-[#1E9E3D] border border-[#1E9E3D] text-white rounded-tl-sm"
                        )}>
                            {m.content}

                            {m.role === 'assistant' && m.sources && m.sources.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-white/20">
                                    <p className="text-[10px] uppercase tracking-wider text-white/90 font-bold mb-2 flex items-center gap-1">
                                        <div className="w-1 h-1 bg-white rounded-full"></div>
                                        Kaynaklar
                                    </p>
                                    <div className="flex flex-wrap gap-1.5">
                                        {m.sources.map((source, idx) => (
                                            <span
                                                key={idx}
                                                className="text-[10px] px-2 py-0.5 bg-white/10 text-white rounded-md border border-white/20 truncate max-w-full"
                                                title={source}
                                            >
                                                {source}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex gap-4 w-full">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#1E9E3D] border-transparent text-white flex items-center justify-center">
                            <Bot size={16} />
                        </div>
                        <div className="px-5 py-4 rounded-2xl bg-[#1E9E3D] border border-[#1E9E3D] text-white rounded-tl-sm flex items-center gap-2 shadow-sm">
                            <Loader2 className="w-4 h-4 animate-spin text-white" />
                            <span className="text-sm">Yanıt düşünülüyor...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <div className="p-4 bg-white border-t border-slate-200 mt-auto">
                <form
                    onSubmit={handleSubmit}
                    className="max-w-4xl mx-auto relative flex items-center bg-white rounded-2xl border-2 border-slate-200 focus-within:ring-4 focus-within:ring-green-500/10 focus-within:border-green-500 transition-all shadow-sm"
                >
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="İlaç hakkında ne öğrenmek istersiniz? (örn: Parol ne işe yarar?)"
                        className="w-full bg-transparent border-none px-6 py-4 text-slate-800 placeholder:text-slate-400 focus:outline-none rounded-2xl"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="absolute right-2 p-2.5 bg-[#1E9E3D] hover:bg-[#198533] text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
                    >
                        <Send size={18} className="translate-x-[-1px] group-hover:translate-x-0 group-hover:-translate-y-[1px] transition-transform" />
                    </button>
                </form>
                <div className="text-center mt-3">
                    <p className="text-[11px] text-slate-400">
                        Eczacı AI, bilgilendirme amaçlıdır.
                    </p>
                </div>
            </div>
        </div>
    );
}
