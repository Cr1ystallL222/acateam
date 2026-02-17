/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://acateam-1.onrender.com";
    return [
      {
        source: "/api/:path*",
        destination: `${API_URL}/api/:path*`,
      },
      {
        source: "/uploads/:path*",
        destination: `${API_URL}/uploads/:path*`,
      },
    ];
  },
};

export default nextConfig;
