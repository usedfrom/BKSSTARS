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
    console.log("[TMA DEBUG] Начало инициализации");

    try {
      init();
      console.log("[TMA DEBUG] init() выполнен");
    } catch (e) {
      console.error("[TMA DEBUG] Ошибка init():", e);
    }

    let attempts = 0;
    const maxAttempts = 50;

    const checkTMA = () => {
      attempts++;
      console.log(`[TMA DEBUG] Проверка №${attempts}`);

      if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp;
        console.log("[TMA DEBUG] WebApp найден!");

        try {
          tg.ready();
          console.log("[TMA DEBUG] tg.ready() вызван");
          tg.expand();
          console.log("[TMA DEBUG] tg.expand() вызван");

          console.log("[TMA DEBUG] Пользователь:", tg.initDataUnsafe?.user);
        } catch (e) {
          console.error("[TMA DEBUG] Ошибка при вызове методов:", e);
        }
      } else if (attempts < maxAttempts) {
        setTimeout(checkTMA, 200);
      } else {
        console.error("[TMA DEBUG] WebApp так и не появился после 10 секунд");
      }
    };

    setTimeout(checkTMA, 500);
  }, []);

  return <>{children}</>;
}
