/** @type {import('next').NextConfig} */
const nextConfig = {
  // Output standalone for Docker deployment
  output: 'standalone',
  // Hide the Next.js dev indicator
  devIndicators: false,
  // Enable experimental features if needed
  experimental: {
    // serverActions: true,
  },
  // Environment variables that should be available on the client
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
