'use client';

import { ChatInterface } from '@/components/chat-interface';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <ChatInterface />
    </main>
  );
}
