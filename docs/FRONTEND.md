# 🎨 Athar Frontend Documentation

Complete guide to the Athar Next.js frontend application.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Components](#components)
- [Styling](#styling)
- [Internationalization](#internationalization)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [RTL Support](#rtl-support)
- [Performance](#performance)
- [Testing](#testing)
- [Deployment](#deployment)

---

## 🎯 Overview

The Athar frontend is a **Next.js 15** application providing a beautiful, RTL-enabled chat interface for the Islamic QA system.

### Key Features

- ✅ Full RTL layout (Arabic/Urdu support)
- ✅ Dark/light mode toggle
- ✅ Responsive design
- ✅ Real-time chat interface
- ✅ Citation panel display
- ✅ Interactive calculator forms
- ✅ Beautiful animations

---

## 💻 Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 15.0 | React framework |
| **TypeScript** | 5.6 | Type safety |
| **Tailwind CSS** | 3.4 | Utility-first styling |
| **next-intl** | 3.0 | Arabic/English i18n |
| **Zustand** | 5.0 | State management |
| **React Markdown** | 9.0 | Message rendering |
| **Lucide React** | 0.400 | Icon library |

---

## 🗂️ Project Structure

```
frontend/
├── src/
│   ├── app/                    # App router pages
│   │   ├── layout.tsx          # Root layout with RTL
│   │   ├── page.tsx            # Home page (chat)
│   │   └── globals.css         # Global styles
│   │
│   ├── components/             # React components
│   │   ├── chat-interface.tsx  # Main chat UI
│   │   ├── message-bubble.tsx  # User/assistant messages
│   │   ├── citation-panel.tsx  # Citation display
│   │   ├── intent-badge.tsx    # Intent visualization
│   │   ├── input-area.tsx      # Message input
│   │   ├── header.tsx          # App header
│   │   ├── loading-dots.tsx    # Loading animation
│   │   ├── citation-link.tsx   # Clickable citation
│   │   ├── zakat-calculator-form.tsx
│   │   ├── prayer-times-form.tsx
│   │   └── hijri-calendar-form.tsx
│   │
│   ├── lib/                    # Utilities
│   │   ├── api.ts              # API client functions
│   │   ├── types.ts            # TypeScript types
│   │   └── utils.ts            # Helper functions
│   │
│   └── hooks/                  # Custom React hooks
│
├── i18n/                       # Internationalization
│   ├── request.ts              # next-intl config
│   └── messages/
│       └── ar.json             # Arabic translations
│
├── public/                     # Static assets
│
├── package.json                # Dependencies
├── next.config.js              # Next.js config
└── tailwind.config.ts          # Tailwind config
```

---

## 🧩 Components

### ChatInterface

**File:** `src/components/chat-interface.tsx`

**Purpose:** Main chat container with message list and input.

**Props:** None (stateful component)

**State:**
- `messages: Message[]` - Chat messages
- `isLoading: boolean` - Loading state
- `error: string | null` - Error message
- `showCitations: boolean` - Citation panel visibility
- `currentCitations: Citation[]` - Current citations to display

**Usage:**
```tsx
import { ChatInterface } from '@/components/chat-interface';

export default function Home() {
  return <ChatInterface />;
}
```

---

### MessageBubble

**File:** `src/components/message-bubble.tsx`

**Purpose:** Display individual messages with markdown rendering.

**Props:**
```typescript
interface MessageBubbleProps {
  message: Message;
  onCitationClick: (citations: Citation[]) => void;
}
```

**Features:**
- Markdown rendering
- Citation link parsing ([C1], [C2])
- Intent badge for assistant messages
- Timestamp display
- RTL text support

---

### CitationPanel

**File:** `src/components/citation-panel.tsx`

**Purpose:** Slide-out panel showing citation sources.

**Props:**
```typescript
interface CitationPanelProps {
  citations: Citation[];
  onClose: () => void;
}
```

**Features:**
- Clickable source links
- External URL opening
- Arabic text support
- Responsive design

---

### IntentBadge

**File:** `src/components/intent-badge.tsx`

**Purpose:** Visual indicator for detected intent.

**Props:**
```typescript
interface IntentBadgeProps {
  intent: string;
  confidence: number;
}
```

**Supported Intents:**
- فقه (fiqh) - Blue
- قرآن (quran) - Green
- زكاة (zakat) - Emerald
- ميراث (inheritance) - Orange
- دعاء (dua) - Pink
- تقويم هجري (hijri_calendar) - Indigo
- مواقيت صلاة (prayer_times) - Cyan

---

### Calculator Forms

**ZakatCalculatorForm:**
- Asset input fields
- Madhhab selection
- Result display with breakdown
- Error handling

**PrayerTimesForm:**
- Preset city buttons
- Custom lat/lng input
- Prayer times grid
- Qibla direction display

**HijriCalendarForm:**
- Date picker
- Gregorian ↔ Hijri conversion
- Special date badges (Ramadan, Eid)

---

## 🎨 Styling

### Tailwind Configuration

**File:** `tailwind.config.ts`

```typescript
export default {
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'hsl(142 76% 36%)', // Islamic green
          foreground: 'hsl(355.7 100% 97.3%)',
        },
      },
    },
  },
}
```

### CSS Variables

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 142 76% 36%;
  --primary-foreground: 355.7 100% 97.3%;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 142 70% 45%;
}
```

### Custom Classes

```css
/* RTL Support */
[dir="rtl"] {
  text-align: right;
}

/* Arabic Font */
.arabic-text {
  font-family: 'Noto Sans Arabic', sans-serif;
  line-height: 1.8;
}

/* Animations */
.message-bubble {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

---

## 🌍 Internationalization

### Setup

**File:** `i18n/request.ts`

```typescript
import {getRequestConfig} from 'next-intl/server';

export default getRequestConfig(async () => {
  const locale = 'ar';
  
  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default
  };
});
```

### Translation Files

**File:** `i18n/messages/ar.json`

```json
{
  "Index": {
    "title": "أثر",
    "subtitle": "مساعد إسلامي ذكي مع مصادر موثقة",
    "placeholder": "اكتب سؤالك هنا..."
  },
  "Intents": {
    "fiqh": "فقه",
    "quran": "قرآن",
    "zakat": "زكاة"
  }
}
```

### Usage in Components

```typescript
// Will be available when using next-intl hooks
// const t = useTranslations();
// t('Index.title') → "أثر"
```

---

## 🔄 State Management

### Zustand Store

```typescript
import { create } from 'zustand';

interface ChatStore {
  messages: Message[];
  isLoading: boolean;
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  setLoading: (loading) => set({ isLoading: loading }),
}));
```

---

## 🌐 API Integration

### API Client

**File:** `src/lib/api.ts`

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function submitQuery(
  query: string,
  language?: string,
  madhhab?: string
): Promise<QueryResponse> {
  const response = await fetch(`${API_URL}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, language, madhhab }),
  });
  
  if (!response.ok) {
    throw new Error('Query failed');
  }
  
  return response.json();
}
```

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ↔️ RTL Support

### Layout Configuration

**File:** `src/app/layout.tsx`

```tsx
export default function RootLayout({ children }) {
  return (
    <html lang="ar" dir="rtl">
      <body dir="rtl">
        {children}
      </body>
    </html>
  );
}
```

### RTL Considerations

- All text aligned to right
- Margins/paddings use `rtl:` variants where needed
- Icons and arrows flipped
- Citation panel on right side

---

## ⚡ Performance

### Optimization Strategies

1. **Code Splitting**: Automatic with Next.js App Router
2. **Image Optimization**: Next.js Image component
3. **Font Loading**: Google Fonts with `next/font`
4. **CSS Optimization**: Tailwind purges unused styles

### Lighthouse Scores (Target)

| Metric | Target |
|--------|--------|
| **Performance** | 90+ |
| **Accessibility** | 95+ |
| **Best Practices** | 95+ |
| **SEO** | 100 |

---

## 🧪 Testing

### Running Tests

```bash
cd frontend
npm run test
```

### Component Testing

```typescript
import { render, screen } from '@testing-library/react';
import { MessageBubble } from '@/components/message-bubble';

test('renders user message', () => {
  const message = {
    id: '1',
    role: 'user',
    content: 'Hello',
  };
  
  render(<MessageBubble message={message} onCitationClick={() => {}} />);
  expect(screen.getByText('Hello')).toBeInTheDocument();
});
```

---

## 🚀 Deployment

### Build

```bash
npm run build
```

### Start Production

```bash
npm start
```

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

---

## 📝 Common Patterns

### Adding New Component

```tsx
'use client';

import { useState } from 'react';

export function MyNewComponent() {
  const [state, setState] = useState();
  
  return (
    <div className="p-4">
      {/* Your JSX */}
    </div>
  );
}
```

### Using API Client

```typescript
import { submitQuery } from '@/lib/api';

async function handleSubmit(query: string) {
  try {
    const response = await submitQuery(query);
    console.log(response.answer);
  } catch (error) {
    console.error('Query failed:', error);
  }
}
```

---

<div align="center">

**Frontend Version:** 0.5.0  
**Last Updated:** Phase 5 Complete  
**Status:** Production-Ready

</div>
