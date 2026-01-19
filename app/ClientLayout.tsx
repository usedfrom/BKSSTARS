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
    console.log("[TMA] Начало инициализации");

    try {
      init();
      console.log("[TMA] init() вызван");
    } catch (err) {
      console.error("[TMA] Ошибка init():", err);
    }

    let attempts = 0;
    const maxAttempts = 50; // 10 секунд максимум

    const checkTMA = () => {
      attempts++;
      console.log(`[TMA] Проверка №${attempts}`);

      if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp;
        console.log("[TMA] WebApp найден!");

        try {
          tg.ready();
          console.log("[TMA] tg.ready() вызван");

          tg.expand();
          console.log("[TMA] tg.expand() вызван");

          console.log("[TMA] Пользователь:", tg.initDataUnsafe?.user);
          console.log("[TMA] InitData:", tg.initData);
        } catch (err) {
          console.error("[TMA] Ошибка при вызове методов:", err);
        }
      } else if (attempts < maxAttempts) {
        setTimeout(checkTMA, 200);
      } else {
        console.error("[TMA] WebApp так и не появился после 10 секунд");
      }
    };

    // Даём Telegram чуть больше времени на передачу объекта
    setTimeout(checkTMA, 500);
  }, []);

  return <>{children}</>;
}
