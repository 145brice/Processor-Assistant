import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Hide the dev-only Next.js badge (it covered the sidebar footer). Errors still show as overlays.
  devIndicators: false,
};

export default nextConfig;
