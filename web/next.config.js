/** @type {import('next').NextConfig} */
const path = require('path');

// Dev-only: the API is on a different port so Next rewrites forward /api/*
// to FastAPI. In production the built site is served by FastAPI itself, so
// /api/* naturally hits the same origin — rewrites aren't needed.
const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
  outputFileTracingRoot: path.join(__dirname),
};

if (process.env.NODE_ENV !== 'production') {
  // `rewrites` is incompatible with `output: 'export'`, so only wire it up
  // when running `next dev`. The build ignores this block.
  delete nextConfig.output;
  delete nextConfig.trailingSlash;
  nextConfig.rewrites = async () => [
    { source: '/api/:path*', destination: `${backendUrl}/api/:path*` },
  ];
}

module.exports = nextConfig;
