/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  allowedDevOrigins: ['http://192.168.40.159:3000'],
}

module.exports = nextConfig