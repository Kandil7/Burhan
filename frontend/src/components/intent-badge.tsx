'use client';

import { cn } from '@/lib/utils';

interface IntentBadgeProps {
  intent: string;
  confidence: number;
}

const intentLabels: Record<string, { ar: string; color: string }> = {
  fiqh: { ar: 'فقه', color: 'bg-blue-500/20 text-blue-700 dark:text-blue-300' },
  quran: { ar: 'قرآن', color: 'bg-green-500/20 text-green-700 dark:text-green-300' },
  islamic_knowledge: { ar: 'معرفة إسلامية', color: 'bg-purple-500/20 text-purple-700 dark:text-purple-300' },
  greeting: { ar: 'تحية', color: 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-300' },
  zakat: { ar: 'زكاة', color: 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300' },
  inheritance: { ar: 'ميراث', color: 'bg-orange-500/20 text-orange-700 dark:text-orange-300' },
  dua: { ar: 'دعاء', color: 'bg-pink-500/20 text-pink-700 dark:text-pink-300' },
  hijri_calendar: { ar: 'تقويم هجري', color: 'bg-indigo-500/20 text-indigo-700 dark:text-indigo-300' },
  prayer_times: { ar: 'مواقيت صلاة', color: 'bg-cyan-500/20 text-cyan-700 dark:text-cyan-300' },
};

export function IntentBadge({ intent, confidence }: IntentBadgeProps) {
  const label = intentLabels[intent] || { ar: intent, color: 'bg-gray-500/20 text-gray-700' };

  return (
    <div className="flex items-center gap-2 mb-2">
      <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', label.color)}>
        {label.ar}
      </span>
      <span className="text-xs text-muted-foreground">
        {Math.round(confidence * 100)}% ثقة
      </span>
    </div>
  );
}
