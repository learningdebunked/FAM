/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    // Add path aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, '.'),
      '@components': path.resolve(__dirname, 'components'),
      '@lib': path.resolve(__dirname, 'lib'),
    };
    return config;
  },
  // Enable TypeScript support
  typescript: {
    // Temporarily ignore build errors
    ignoreBuildErrors: true,
  },
};

module.exports = nextConfig;
