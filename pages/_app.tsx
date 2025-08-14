import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { Inter } from 'next/font/google';

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className={`${inter.variable} font-sans min-h-screen flex flex-col bg-gray-50`}>
      <div className="flex-1 flex flex-col">
        <Component {...pageProps} />
      </div>
    </div>
  );
}
