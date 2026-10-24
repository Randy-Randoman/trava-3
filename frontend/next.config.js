/** @type {import('next').NextConfig} */
const nextConfig = {
  // Output standalone for Docker deployment
  output: 'standalone',
  // Hide the Next.js dev indicator
  devIndicators: false,
}

module.exports = nextConfig
