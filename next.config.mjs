/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Самое главное — экспортируем как статический сайт
  output: 'export',
  // Отключаем изображение-оптимизацию (не нужна для статического сайта)
  images: {
    unoptimized: true,
  },
  // Если используешь trailingSlash — включи (для Vercel иногда полезно)
  trailingSlash: true,
};

export default nextConfig;
