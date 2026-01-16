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
      console.log("Начало инициализации TMA SDK");

      init();

      const checkTMA = () => {
        if (window.Telegram?.WebApp) {
          const tg = window.Telegram.WebApp;

          console.log("Telegram.WebApp найден");
          tg.ready();
          console.log("Вызван tg.ready()");
          tg.expand();
          console.log("Вызван tg.expand()");

          console.log("InitDataUnsafe:", tg.initDataUnsafe);
        } else {
          console.log("Telegram.WebApp ещё не доступен, ждём...");
          setTimeout(checkTMA, 200);
        }
      };

      checkTMA();
    } catch (err) {
      console.error("Ошибка инициализации TMA:", err);
    }
  }, []);

  return <>{children}</>;
}
