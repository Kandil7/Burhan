'use client';

import { X } from 'lucide-react';
import { Citation } from '@/lib/types';

interface CitationPanelProps {
  citations: Citation[];
  onClose: () => void;
}

export function CitationPanel({ citations, onClose }: CitationPanelProps) {
  return (
    <div className="w-96 border-r bg-card p-4 overflow-y-auto" dir="rtl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">المصادر / Sources</h3>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-muted transition-colors"
          aria-label="إغلاق"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3">
        {citations.map((citation, index) => (
          <div
            key={citation.id || index}
            className="p-3 rounded-lg border bg-muted/50"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold">
                {index + 1}
              </span>
              <span className="text-xs uppercase text-muted-foreground">
                {citation.type}
              </span>
            </div>

            <p className="text-sm font-medium mb-1">{citation.source}</p>
            <p className="text-xs text-muted-foreground mb-2">
              {citation.reference}
            </p>

            {citation.text_excerpt && (
              <blockquote className="text-xs border-r-2 border-primary pr-2 italic">
                "{citation.text_excerpt.substring(0, 150)}..."
              </blockquote>
            )}

            {citation.url && (
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary hover:underline mt-2 inline-block"
              >
                عرض المصدر ←
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
