'use client';

import { useState } from 'react';
import { convertHijri } from '@/lib/api';

export function HijriCalendarForm() {
  const [gregorianDate, setGregorianDate] = useState('');
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const data = await convertHijri(gregorianDate);
      setResult(data);
    } catch (err) {
      setError('فشل في تحويل التاريخ.');
    } finally {
      setIsLoading(false);
    }
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6" dir="rtl">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-primary">التقويم الهجري</h2>
        <p className="text-muted-foreground">حوّل بين التاريخ الميلادي والهجري</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 bg-card p-6 rounded-lg border">
        <div className="space-y-2">
          <label className="text-sm font-medium">التاريخ الميلادي</label>
          <input
            type="date"
            value={gregorianDate || today}
            onChange={e => setGregorianDate(e.target.value)}
            className="w-full rounded-lg border bg-background px-3 py-2"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {isLoading ? 'جاري التحويل...' : 'حوّل إلى هجري'}
        </button>
      </form>

      {error && <ErrorMessage error={error} />}
      {result && <HijriDateDisplay result={result} />}
    </div>
  );
}

function HijriDateDisplay({ result }: { result: any }) {
  const hijri = result.hijri_date;

  return (
    <div className="bg-muted/50 rounded-lg p-6 space-y-4 border">
      <div className="text-center space-y-3">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-background">
            <p className="text-sm text-muted-foreground mb-1">الميلادي</p>
            <p className="text-lg font-bold">{result.gregorian_date}</p>
          </div>
          <div className="p-4 rounded-lg bg-background">
            <p className="text-sm text-muted-foreground mb-1">الهجري</p>
            <p className="text-lg font-bold">{hijri?.formatted_ar}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 justify-center mt-4">
          {result.is_ramadan && (
            <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-700 text-sm">
              رمضان كريم 🌙
            </span>
          )}
          {result.is_eid && (
            <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-700 text-sm">
              عيد مبارك 🎉
            </span>
          )}
          {result.special_day && (
            <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-700 text-sm">
              {result.special_day.name_ar}
            </span>
          )}
        </div>
      </div>

      <div className="mt-4 p-3 rounded bg-background border text-center text-sm text-muted-foreground">
        ⚠️ التواريخ المحسوبة قد تختلف بيوم واحد حسب رؤية الهلال
      </div>
    </div>
  );
}

function ErrorMessage({ error }: { error: string }) {
  return (
    <div className="bg-destructive/10 text-destructive p-4 rounded-lg text-center">
      {error}
    </div>
  );
}
