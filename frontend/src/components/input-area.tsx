'use client';

import { useState } from 'react';
import { Send } from 'lucide-react';

interface InputAreaProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

export function InputArea({ onSubmit, isLoading }: InputAreaProps) {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    onSubmit(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t bg-card p-4">
      <div className="max-w-3xl mx-auto flex gap-2">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="اكتب سؤالك هنا..."
          className="flex-1 resize-none rounded-lg border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          rows={1}
          dir="rtl"
          disabled={isLoading}
        />
        <button
          onClick={handleSubmit}
          disabled={isLoading || !input.trim()}
          className="px-4 py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      <p className="text-xs text-muted-foreground text-center mt-2">
        أثر مبني على معمارية Fanar-Sadiq • جميع الإجابات مع مصادر موثقة
      </p>
    </div>
  );
}
