import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // The order export is read from disk at runtime; make sure it ships with the server bundle.
  outputFileTracingIncludes: {
    "/api/analytics/*": ["./data/orders.csv"],
    "/api/chat": ["./data/orders.csv"],
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
