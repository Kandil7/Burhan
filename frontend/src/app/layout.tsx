import type { Metadata } from 'next';
import { Inter, Noto_Sans_Arabic } from 'next/font/google';
import './globals.css';

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
});

const notoArabic = Noto_Sans_Arabic({ 
  subsets: ['arabic'],
  variable: '--noto-arabic',
  weight: ['400', '500', '600', '700'],
});

export const metadata: Metadata = {
  title: 'أثر - Athar | Islamic QA Assistant',
  description: 'Multi-agent Islamic QA system with verified sources from Quran, Hadith, and Fiqh. Based on Fanar-Sadiq architecture.',
  keywords: ['Islamic', 'QA', 'Quran', 'Hadith', 'Fiqh', 'Zakat', 'Inheritance', 'Prayer Times'],
  authors: [{ name: 'Athar Team' }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl" suppressHydrationWarning>
      <body className={`${inter.variable} ${notoArabic.variable} font-sans`} dir="rtl">
        {children}
      </body>
    </html>
  );
}
