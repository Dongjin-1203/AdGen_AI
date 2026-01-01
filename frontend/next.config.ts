import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // ← 이것이 중요!
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/uploads/**',
      },
      {
        protocol: 'https',
        hostname: 'storage.googleapis.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.run.app',
        pathname: '/uploads/**',
      },
    ],
  },
};

export default nextConfig;