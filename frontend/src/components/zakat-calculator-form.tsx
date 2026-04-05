'use client';

import { useState } from 'react';
import { calculateZakat } from '@/lib/api';

interface ZakatFormData {
  cash: string;
  gold_grams: string;
  silver_grams: string;
  trade_goods_value: string;
  stocks_value: string;
  debts: string;
  madhhab: string;
}

export function ZakatCalculatorForm() {
  const [formData, setFormData] = useState<ZakatFormData>({
    cash: '',
    gold_grams: '',
    silver_grams: '',
    trade_goods_value: '',
    stocks_value: '',
    debts: '',
    madhhab: 'general',
  });
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = {
        assets: {
          cash: parseFloat(formData.cash) || 0,
          gold_grams: parseFloat(formData.gold_grams) || 0,
          silver_grams: parseFloat(formData.silver_grams) || 0,
          trade_goods_value: parseFloat(formData.trade_goods_value) || 0,
          stocks_value: parseFloat(formData.stocks_value) || 0,
        },
        debts: parseFloat(formData.debts) || 0,
        madhhab: formData.madhhab,
      };

      const result = await calculateZakat(data);
      setResult(result);
    } catch (err) {
      setError('فشل في حساب الزكاة. يرجى المحاولة مرة أخرى.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: keyof ZakatFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6" dir="rtl">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-primary">حاسبة الزكاة</h2>
        <p className="text-muted-foreground">احسب زكاة مالك بدقة حسب المذهب</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 bg-card p-6 rounded-lg border">
        <div className="grid grid-cols-2 gap-4">
          <InputField
            label="النقد (Cash)"
            value={formData.cash}
            onChange={v => handleChange('cash', v)}
            placeholder="0.00"
          />
          <InputField
            label="الذهب (جرام)"
            value={formData.gold_grams}
            onChange={v => handleChange('gold_grams', v)}
            placeholder="0"
          />
          <InputField
            label="الفضة (جرام)"
            value={formData.silver_grams}
            onChange={v => handleChange('silver_grams', v)}
            placeholder="0"
          />
          <InputField
            label="عروض التجارة"
            value={formData.trade_goods_value}
            onChange={v => handleChange('trade_goods_value', v)}
            placeholder="0.00"
          />
          <InputField
            label="الأسهم"
            value={formData.stocks_value}
            onChange={v => handleChange('stocks_value', v)}
            placeholder="0.00"
          />
          <InputField
            label="الديون"
            value={formData.debts}
            onChange={v => handleChange('debts', v)}
            placeholder="0.00"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">المذهب</label>
          <select
            value={formData.madhhab}
            onChange={e => handleChange('madhhab', e.target.value)}
            className="w-full rounded-lg border bg-background px-3 py-2"
          >
            <option value="general">عام</option>
            <option value="hanafi">حنفي</option>
            <option value="shafii">شافعي</option>
            <option value="maliki">مالكي</option>
            <option value="hanbali">حنبل</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {isLoading ? 'جاري الحساب...' : 'احسب الزكاة'}
        </button>
      </form>

      {error && <ErrorMessage error={error} />}
      {result && <ZakatResultDisplay result={result} />}
    </div>
  );
}

function InputField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{label}</label>
      <input
        type="number"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border bg-background px-3 py-2"
        dir="rtl"
      />
    </div>
  );
}

function ZakatResultDisplay({ result }: { result: any }) {
  return (
    <div className="bg-muted/50 rounded-lg p-6 space-y-4 border">
      <h3 className="text-xl font-bold">نتيجة الزكاة</h3>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">النصاب</p>
          <p className="text-lg font-bold">{result.nisab?.effective?.toFixed(2) || '—'}</p>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">إجمالي الأصول</p>
          <p className="text-lg font-bold">{result.total_assets?.toFixed(2) || '—'}</p>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">الزكاة المستحقة</p>
          <p className="text-2xl font-bold text-primary">{result.zakat_amount?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">حالة الزكاة</p>
          <p className={`text-lg font-bold ${result.is_zakatable ? 'text-green-600' : 'text-red-600'}`}>
            {result.is_zakatable ? 'تجب الزكاة' : 'لا تجب الزكاة'}
          </p>
        </div>
      </div>

      {result.notes && result.notes.length > 0 && (
        <div className="mt-4 p-3 rounded bg-background border">
          <h4 className="font-medium mb-2">ملاحظات:</h4>
          <ul className="space-y-1 text-sm">
            {result.notes.map((note: string, i: number) => (
              <li key={i} className="text-muted-foreground">• {note}</li>
            ))}
          </ul>
        </div>
      )}
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
