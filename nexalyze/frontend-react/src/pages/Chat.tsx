import { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Bot, User, Sparkles, Loader2, Wrench } from 'lucide-react';
import { streamChatMessage, type ChatStreamEvent } from '../services/api';
import { useAppStore } from '../store';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

export default function Chat() {
    const {
        chatMessages,
        addChatMessage,
        chatSessionId,
        setChatSessionId,
        isChatLoading,
        setIsChatLoading,
        clearChatHistory
    } = useAppStore();

    const [input, setInput] = useState('');
    const [streamingContent, setStreamingContent] = useState('');
    const [streamingStatus, setStreamingStatus] = useState('');
    const [currentTools, setCurrentTools] = useState<string[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const cancelRef = useRef<(() => void) | null>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatMessages, streamingContent]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (cancelRef.current) {
                cancelRef.current();
            }
        };
    }, []);

    const handleSubmit = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isChatLoading) return;

        const userMessage = {
            id: Date.now().toString(),
            role: 'user' as const,
            content: input.trim(),
            timestamp: new Date()
        };

        addChatMessage(userMessage);
        const query = input.trim();
        setInput('');
        setIsChatLoading(true);
        setStreamingContent('');
        setStreamingStatus('');
        setCurrentTools([]);

        // Use streaming API
        const { cancel } = streamChatMessage(
            query,
            chatSessionId || undefined,
            (event: ChatStreamEvent) => {
                switch (event.type) {
                    case 'start':
                        setStreamingStatus(event.message || 'Processing...');
                        break;
                    case 'status':
                        setStreamingStatus(event.message || 'Initializing...');
                        if (event.session_id) {
                            setChatSessionId(event.session_id);
                        }
                        break;
                    case 'thinking':
                        setStreamingStatus(event.message || 'Thinking...');
                        break;
                    case 'tool_call':
                        setStreamingStatus(`Calling ${event.tool_name}...`);
                        if (event.tool_name) {
                            setCurrentTools(prev => [...prev, event.tool_name!]);
                        }
                        break;
                    case 'tool':
                        setStreamingStatus(`Executing ${event.tool_name}...`);
                        if (event.tool_name && !currentTools.includes(event.tool_name)) {
                            setCurrentTools(prev => [...prev, event.tool_name!]);
                        }
                        break;
                    case 'content':
                        if (event.message) {
                            setStreamingContent(prev => prev + event.message + ' ');
                        }
                        setStreamingStatus('');
                        break;
                    case 'complete':
                        if (event.session_id) {
                            setChatSessionId(event.session_id);
                        }
                        // Add the final message
                        const aiMessage = {
                            id: (Date.now() + 1).toString(),
                            role: 'assistant' as const,
                            content: event.message || streamingContent.trim(),
                            timestamp: new Date(),
                            tools_used: event.tools_used || currentTools
                        };
                        addChatMessage(aiMessage);
                        setStreamingContent('');
                        setStreamingStatus('');
                        setCurrentTools([]);
                        break;
                    case 'end':
                        setIsChatLoading(false);
                        cancelRef.current = null;
                        break;
                    case 'error':
                        console.error('Chat stream error:', event.message);
                        addChatMessage({
                            id: (Date.now() + 1).toString(),
                            role: 'assistant',
                            content: `I apologize, but I encountered an error: ${event.message}`,
                            timestamp: new Date()
                        });
                        setStreamingContent('');
                        setStreamingStatus('');
                        setCurrentTools([]);
                        setIsChatLoading(false);
                        cancelRef.current = null;
                        break;
                }
            }
        );

        cancelRef.current = cancel;
    };

    const handleCancel = () => {
        if (cancelRef.current) {
            cancelRef.current();
            cancelRef.current = null;
            setIsChatLoading(false);
            setStreamingContent('');
            setStreamingStatus('');
            setCurrentTools([]);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const suggestedQueries = [
        'What are the top AI startups from Y Combinator?',
        'Compare Stripe and Square as fintech companies',
        'What makes a successful B2B SaaS startup?',
        'Analyze the competitive landscape for video streaming',
    ];

    return (
        <div className="flex flex-col h-[calc(100vh-6rem)] max-w-4xl mx-auto px-4 py-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                        <Sparkles className="w-6 h-6 text-primary-500" />
                        AI Chat Assistant
                    </h1>
                    <p className="text-slate-500 text-sm">Powered by Google Gemini with real-time streaming</p>
                </div>
                {chatMessages.length > 0 && (
                    <button
                        onClick={clearChatHistory}
                        className="flex items-center gap-2 px-4 py-2 text-slate-500 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                    >
                        <Trash2 className="w-4 h-4" />
                        Clear
                    </button>
                )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                {chatMessages.length === 0 && !isChatLoading ? (
                    <div className="text-center py-12 animate-fadeIn">
                        <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-secondary-100 rounded-3xl flex items-center justify-center mx-auto mb-6">
                            <Bot className="w-10 h-10 text-primary-500" />
                        </div>
                        <h2 className="text-xl font-semibold text-slate-800 mb-2">
                            How can I help you today?
                        </h2>
                        <p className="text-slate-500 mb-8">
                            Ask me about startups, markets, or competitive analysis
                        </p>

                        <div className="grid sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                            {suggestedQueries.map((query, index) => (
                                <button
                                    key={index}
                                    onClick={() => {
                                        setInput(query);
                                        inputRef.current?.focus();
                                    }}
                                    className="text-left p-4 glass-card hover:bg-primary-50 transition-colors text-sm text-slate-600 hover:text-primary-600"
                                >
                                    "{query}"
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <>
                        {chatMessages.map((message) => (
                            <div
                                key={message.id}
                                className={clsx(
                                    'flex gap-3 animate-slideUp',
                                    message.role === 'user' ? 'justify-end' : 'justify-start'
                                )}
                            >
                                {message.role === 'assistant' && (
                                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-secondary-500 flex items-center justify-center shrink-0">
                                        <Bot className="w-4 h-4 text-white" />
                                    </div>
                                )}

                                <div
                                    className={clsx(
                                        'max-w-[80%] px-4 py-3 rounded-2xl',
                                        message.role === 'user'
                                            ? 'chat-message-user'
                                            : 'chat-message-ai'
                                    )}
                                >
                                    {message.role === 'assistant' ? (
                                        <div className="prose prose-sm max-w-none prose-p:my-2 prose-headings:my-2">
                                            <ReactMarkdown>{message.content}</ReactMarkdown>
                                        </div>
                                    ) : (
                                        <p>{message.content}</p>
                                    )}

                                    {message.tools_used && message.tools_used.length > 0 && (
                                        <div className="mt-2 pt-2 border-t border-slate-200 text-xs text-slate-500 flex items-center gap-1">
                                            <Wrench className="w-3 h-3" />
                                            Used: {message.tools_used.join(', ')}
                                        </div>
                                    )}
                                </div>

                                {message.role === 'user' && (
                                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center shrink-0">
                                        <User className="w-4 h-4 text-white" />
                                    </div>
                                )}
                            </div>
                        ))}
                    </>
                )}

                {/* Streaming response */}
                {isChatLoading && (
                    <div className="flex gap-3 animate-fadeIn">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-secondary-500 flex items-center justify-center">
                            <Bot className="w-4 h-4 text-white" />
                        </div>
                        <div className="chat-message-ai px-4 py-3 max-w-[80%]">
                            {streamingStatus && (
                                <div className="flex items-center gap-2 text-primary-500 mb-2">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span className="text-sm">{streamingStatus}</span>
                                </div>
                            )}
                            {currentTools.length > 0 && !streamingContent && (
                                <div className="flex items-center gap-2 text-slate-500 text-xs mb-2">
                                    <Wrench className="w-3 h-3" />
                                    Tools: {currentTools.join(', ')}
                                </div>
                            )}
                            {streamingContent ? (
                                <div className="prose prose-sm max-w-none prose-p:my-2 prose-headings:my-2">
                                    <ReactMarkdown>{streamingContent}</ReactMarkdown>
                                    <span className="inline-block w-2 h-4 bg-primary-400 animate-pulse ml-1" />
                                </div>
                            ) : !streamingStatus && (
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                            )}
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="glass-card p-4">
                <div className="flex gap-3">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask about startups, markets, or companies..."
                        className="flex-1 input-field resize-none"
                        rows={1}
                        disabled={isChatLoading}
                    />
                    {isChatLoading ? (
                        <button
                            type="button"
                            onClick={handleCancel}
                            className="p-3 rounded-xl bg-red-500 text-white hover:bg-red-600 transition-all"
                        >
                            <span className="sr-only">Cancel</span>
                            ✕
                        </button>
                    ) : (
                        <button
                            type="submit"
                            disabled={!input.trim()}
                            className={clsx(
                                'p-3 rounded-xl transition-all',
                                input.trim()
                                    ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-lg hover:shadow-xl'
                                    : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                            )}
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    )}
                </div>
            </form>
        </div>
    );
}
