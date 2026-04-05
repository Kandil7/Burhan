'use client';

import { Message, Citation } from '@/lib/types';
import { cn } from '@/lib/utils';
import { IntentBadge } from './intent-badge';
import { CitationLink } from './citation-link';

interface MessageBubbleProps {
  message: Message;
  onCitationClick: (citations: Citation[]) => void;
}

export function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex w-full message-bubble',
        isUser ? 'justify-start' : 'justify-end'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-3',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-foreground'
        )}
      >
        {!isUser && message.intent && (
          <IntentBadge
            intent={message.intent}
            confidence={message.confidence || 0}
          />
        )}

        <div className="mt-2 arabic-text" dir="rtl">
          {renderContent(message.content, message.citations || [], onCitationClick)}
        </div>

        {message.timestamp && (
          <div className="mt-2 text-xs opacity-60">
            {message.timestamp.toLocaleTimeString('ar-SA', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function renderContent(
  content: string,
  citations: Citation[],
  onCitationClick: (citations: Citation[]) => void
) {
  const parts = content.split(/(\[C\d+\])/g);

  return (
    <p className="whitespace-pre-wrap">
      {parts.map((part, i) => {
        const match = part.match(/\[C(\d+)\]/);
        if (match) {
          const citationId = part;
          const citationIndex = parseInt(match[1]);
          const citation = citations[citationIndex - 1];

          return (
            <CitationLink
              key={i}
              id={citationId}
              citation={citation}
              onClick={() => citation && onCitationClick(citations)}
            />
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </p>
  );
}
