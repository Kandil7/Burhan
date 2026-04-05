'use client';

import { Citation } from '@/lib/types';
import { cn } from '@/lib/utils';

interface CitationLinkProps {
  id: string;
  citation?: Citation;
  onClick: () => void;
}

export function CitationLink({ id, citation, onClick }: CitationLinkProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'citation-link',
        !citation && 'opacity-50 cursor-not-allowed'
      )}
      title={citation ? `${citation.source} - ${citation.reference}` : 'مرجع'}
    >
      {id}
    </button>
  );
}
