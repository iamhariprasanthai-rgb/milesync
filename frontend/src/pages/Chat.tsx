import { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { ChatMessage, ChatSession } from '../types/chat';
import * as chatApi from '../api/chat';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

export default function Chat() {
  const [searchParams] = useSearchParams();
  const sessionIdParam = searchParams.get('session');

  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { isListening, startListening, hasSupport } = useSpeechRecognition();

  const handleVoiceInput = () => {
    startListening((text) => setInput((prev) => (prev ? prev + ' ' + text : text)));
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    initializeChat();
  }, [sessionIdParam]);

  async function initializeChat() {
    setIsInitializing(true);
    setError(null);

    try {
      if (sessionIdParam) {
        // Load existing session
        const data = await chatApi.getSession(parseInt(sessionIdParam));
        setSession(data.session);
        setMessages(data.messages);
      } else {
        // Start new session
        const data = await chatApi.startChat();
        setSession(data.session);
        setMessages([data.initial_message]);
        // Update URL with session ID without navigation
        window.history.replaceState(null, '', `/chat?session=${data.session.id}`);
      }
    } catch (err) {
      setError('Failed to initialize chat. Please try again.');
      console.error('Chat init error:', err);
    } finally {
      setIsInitializing(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isLoading || !session) return;

    const userContent = input.trim();
    setInput('');
    setIsLoading(true);
    setError(null);

    // Optimistic update: add user message immediately
    const tempUserMessage: ChatMessage = {
      id: Date.now(),
      session_id: session.id,
      role: 'user',
      content: userContent,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const response = await chatApi.sendMessage(session.id, { content: userContent });
      // Replace temp message with real one and add assistant response
      setMessages((prev) => [
        ...prev.slice(0, -1),
        response.user_message,
        response.assistant_message,
      ]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      // Remove the optimistic message on error
      setMessages((prev) => prev.slice(0, -1));
      console.error('Send message error:', err);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleFinalize() {
    if (!session) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await chatApi.finalizeSession(session.id);
      // Navigate to the created goal
      navigate(`/goals/${response.goal.id}`);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to finalize chat. Please try again.';
      setError(message);
      console.error('Finalize error:', err);
      setIsLoading(false);
    }
  }

  function handleNewChat() {
    navigate('/chat');
    window.location.reload();
  }

  if (isInitializing) {
    return (
      <div className="max-w-4xl mx-auto h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Starting your coaching session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">AI Goal Coach</h1>
          <p className="text-sm text-gray-500">
            {session?.title || 'Define your goal through conversation'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleNewChat}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
          >
            New Chat
          </button>
          {messages.length > 3 && session?.status === 'active' && (
            <button
              onClick={handleFinalize}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50"
            >
              Create Goal & Roadmap
            </button>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <ChatMessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex items-start">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-yellow-500 flex items-center justify-center mr-3 shadow-sm">
              <span className="text-xs text-white font-bold">AI</span>
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t px-6 py-4">
        {session?.status === 'active' ? (
          <form onSubmit={handleSubmit} className="flex space-x-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Tell me about your goal..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={isLoading || isListening}
            />
            {hasSupport && (
              <button
                type="button"
                onClick={handleVoiceInput}
                className={`p-3 rounded-xl transition-all ${isListening
                  ? 'bg-red-100 text-red-600 animate-pulse'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                title="Speak to type"
              >
                {isListening ? (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                )}
              </button>
            )}
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
        ) : (
          <div className="text-center text-gray-500 py-2">
            This session has been finalized.{' '}
            <button onClick={handleNewChat} className="text-primary-600 hover:underline">
              Start a new chat
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm ${isUser
          ? 'bg-gray-800 text-white ml-3'
          : 'bg-gradient-to-br from-primary-500 to-yellow-500 text-white mr-3'
          }`}
      >
        {isUser ? 'ME' : 'AI'}
      </div>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 ${isUser
          ? 'bg-primary-600 text-white rounded-tr-none'
          : 'bg-gray-100 text-gray-900 rounded-tl-none'
          }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
