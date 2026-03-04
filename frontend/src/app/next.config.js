/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  allowedDevOrigins: [
    process.env.NEXT_PUBLIC_APP_ORIGIN || 'http://localhost:3000',
  ],
}

module.exports = nextConfig