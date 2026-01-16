"use client";

import { useEffect } from "react";
import { init } from "@tma.js/sdk";
import "./globals.css";

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    try {
      // Инициализация TMA SDK
      init();

      // Проверяем наличие WebApp с небольшой задержкой
      const checkTMA = () => {
        if (window.Telegram?.WebApp) {
          const tg = window.Telegram.WebApp;

          tg.ready();     // сообщает Telegram, что приложение готово
          tg.expand();    // разворачивает на весь экран

          console.log("Telegram WebApp инициализирован успешно");
          console.log("Пользователь:", tg.initDataUnsafe?.user);
        } else {
          // Повторяем попытку через 100 мс
          setTimeout(checkTMA, 100);
        }
      };

      checkTMA();

    } catch (err) {
      console.error("Ошибка инициализации TMA:", err);
    }
  }, []);

  return <>{children}</>;
}