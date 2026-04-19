/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
    return {
      beforeFiles: [
        { source: '/api/:path*', destination: `${backendUrl}/api/:path*` },
        { source: '/consumer/:path*', destination: `${backendUrl}/consumer/:path*` },
        { source: '/bundles/:path*', destination: `${backendUrl}/bundles/:path*` },
        { source: '/health', destination: `${backendUrl}/health` },
      ],
    };
  },
};

export default nextConfig;
