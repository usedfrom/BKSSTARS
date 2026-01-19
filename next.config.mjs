/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Отключаем SSR для всех страниц (чтобы TMA SDK работал только на клиенте)
  experimental: {
    serverComponentsExternalPackages: ['@tma.js/sdk'],
  },
  // Делаем все страницы динамическими
  output: 'standalone',
  // Отключаем статическую генерацию
  generateStaticParams: false,
};

export default nextConfig;
