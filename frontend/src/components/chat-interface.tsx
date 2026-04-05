'use client';

import { useState, useRef, useEffect } from 'react';
import { Message } from '@/lib/types';
import { submitQuery } from '@/lib/api';
import { Header } from './header';
import { MessageBubble } from './message-bubble';
import { CitationPanel } from './citation-panel';
import { InputArea } from './input-area';
import { LoadingDots } from './loading-dots';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCitations, setShowCitations] = useState(false);
  const [currentCitations, setCurrentCitations] = useState([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSubmit = async (query: string) => {
    setIsLoading(true);
    setError(null);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await submitQuery(query);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        intent: response.intent,
        citations: response.citations,
        confidence: response.intent_confidence,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (response.citations && response.citations.length > 0) {
        setCurrentCitations(response.citations);
        setShowCitations(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex h-screen bg-background" dir="rtl">
      <div className="flex-1 flex flex-col">
        <Header />

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <WelcomeMessage onSuggestionClick={handleSubmit} />
          )}

          {messages.map(message => (
            <MessageBubble
              key={message.id}
              message={message}
              onCitationClick={citations => {
                setCurrentCitations(citations);
                setShowCitations(true);
              }}
            />
          ))}

          {isLoading && <LoadingDots />}
          {error && <ErrorMessage error={error} />}

          <div ref={messagesEndRef} />
        </div>

        <InputArea onSubmit={handleSubmit} isLoading={isLoading} />
      </div>

      {showCitations && (
        <CitationPanel
          citations={currentCitations}
          onClose={() => setShowCitations(false)}
        />
      )}
    </div>
  );
}

function WelcomeMessage({ onSuggestionClick }: { onSuggestionClick: (query: string) => void }) {
  const suggestions = [
    'ما حكم زكاة الأسهم؟',
    'كم عدد آيات سورة البقرة؟',
    'ما حكم صلاة الجمعة؟',
    'أعطني دعاء السفر',
  ];

  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-primary">أثر</h1>
          <p className="text-muted-foreground">مساعد إسلامي ذكي مع مصادر موثقة</p>
        </div>

        <div className="flex flex-wrap gap-2 justify-center max-w-lg mx-auto">
          {suggestions.map(suggestion => (
            <button
              key={suggestion}
              onClick={() => onSuggestionClick(suggestion)}
              className="px-4 py-2 rounded-lg bg-muted hover:bg-muted/80 transition-colors text-sm"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function ErrorMessage({ error }: { error: string }) {
  return (
    <div className="flex justify-center">
      <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-lg text-sm">
        خطأ: {error}
      </div>
    </div>
  );
}
