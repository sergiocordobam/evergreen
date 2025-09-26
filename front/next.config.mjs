/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*", // lo que llamas desde Next.js
        destination: "http://localhost:8000/:path*", // tu backend real
      },
    ]
  },
}

export default nextConfig
