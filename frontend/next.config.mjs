/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  basePath: "/autopunk-pitch",
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
