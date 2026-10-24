import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth'

export const metadata: Metadata = {
  title: 'TRAVA - AI Travel Assistant',
  description: 'Your intelligent travel planning companion',
  icons: {
    icon: '/trava-logo.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&family=Inter:wght@400;600&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased font-sans bg-retro-cream text-trava-black">
        <div className="halftone-overlay"></div>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
