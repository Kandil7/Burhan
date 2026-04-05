'use client';

import { useState } from 'react';
import { getPrayerTimes, convertHijri } from '@/lib/api';

export function PrayerTimesForm() {
  const [lat, setLat] = useState('25.2854');
  const [lng, setLng] = useState('51.5310');
  const [city, setCity] = useState('الدوحة');
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const data = await getPrayerTimes(parseFloat(lat), parseFloat(lng));
      setResult(data);
    } catch (err) {
      setError('فشل في جلب مواقيت الصلاة.');
    } finally {
      setIsLoading(false);
    }
  };

  const presetCities: Record<string, { lat: number; lng: number }> = {
    'مكة': { lat: 21.4225, lng: 39.8262 },
    'المدينة': { lat: 24.4686, lng: 39.6142 },
    'الدوحة': { lat: 25.2854, lng: 51.5310 },
    'القاهرة': { lat: 30.0444, lng: 31.2357 },
    'عمان': { lat: 31.9454, lng: 35.9284 },
    'بيروت': { lat: 33.8938, lng: 35.5018 },
  };

  const handleCitySelect = (cityName: string) => {
    const coords = presetCities[cityName];
    if (coords) {
      setLat(coords.lat.toString());
      setLng(coords.lng.toString());
      setCity(cityName);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6" dir="rtl">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-primary">مواقيت الصلاة</h2>
        <p className="text-muted-foreground">احسب أوقات الصلاة واتجاه القبلة</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 bg-card p-6 rounded-lg border">
        <div className="space-y-2">
          <label className="text-sm font-medium">المدينة</label>
          <div className="flex flex-wrap gap-2">
            {Object.keys(presetCities).map(cityName => (
              <button
                key={cityName}
                type="button"
                onClick={() => handleCitySelect(cityName)}
                className={`px-3 py-1 rounded-full text-sm ${
                  city === cityName
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                }`}
              >
                {cityName}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <InputField
            label="خط العرض"
            value={lat}
            onChange={setLat}
          />
          <InputField
            label="خط الطول"
            value={lng}
            onChange={setLng}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {isLoading ? 'جاري الحساب...' : 'احسب مواقيت الصلاة'}
        </button>
      </form>

      {error && <ErrorMessage error={error} />}
      {result && <PrayerTimesDisplay result={result} />}
    </div>
  );
}

function PrayerTimesDisplay({ result }: { result: any }) {
  const prayers = [
    { name: 'الفجر', time: result.times?.fajr, icon: '🌅' },
    { name: 'الشروق', time: result.times?.sunrise, icon: '☀️' },
    { name: 'الظهر', time: result.times?.dhuhr, icon: '🌞' },
    { name: 'العصر', time: result.times?.asr, icon: '🌤️' },
    { name: 'المغرب', time: result.times?.maghrib, icon: '🌇' },
    { name: 'العشاء', time: result.times?.isha, icon: '🌙' },
  ];

  return (
    <div className="bg-muted/50 rounded-lg p-6 space-y-4 border">
      <div className="grid grid-cols-2 gap-4">
        {prayers.map(prayer => (
          <div
            key={prayer.name}
            className="flex items-center gap-3 p-3 rounded-lg bg-background"
          >
            <span className="text-2xl">{prayer.icon}</span>
            <div>
              <p className="text-sm text-muted-foreground">{prayer.name}</p>
              <p className="text-xl font-bold">{prayer.time || '—'}</p>
            </div>
          </div>
        ))}
      </div>

      {result.qibla_direction && (
        <div className="mt-4 p-3 rounded bg-background border text-center">
          <p className="text-sm text-muted-foreground mb-1">اتجاه القبلة</p>
          <p className="text-2xl font-bold text-primary">{result.qibla_direction}°</p>
        </div>
      )}
    </div>
  );
}

function InputField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{label}</label>
      <input
        type="number"
        step="0.0001"
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full rounded-lg border bg-background px-3 py-2"
        dir="rtl"
      />
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
