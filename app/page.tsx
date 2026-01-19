"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [tgUser, setTgUser] = useState<any>(null);
  const [balance] = useState<number>(0);
  const [tmaReady, setTmaReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log("[TMA] Страница загружена — начало клиентской инициализации");

    const tg = window.Telegram?.WebApp;

    if (tg) {
      console.log("[TMA] Telegram.WebApp обнаружен");

      try {
        tg.ready();
        console.log("[TMA] tg.ready() успешно вызван");

        tg.expand();
        console.log("[TMA] tg.expand() успешно вызван");

        const user = tg.initDataUnsafe?.user;
        if (user) {
          console.log("[TMA] Пользователь получен:", user);
          setTgUser(user);
        } else {
          console.warn("[TMA] Пользователь не найден в initDataUnsafe");
        }

        // Настраиваем нижнюю кнопку Telegram (MainButton)
        tg.MainButton.setParams({
          text: "Купить подписку 750 ⭐",
          color: "#00f9ff",
          text_color: "#000000",
        });
        tg.MainButton.show();
        console.log("[TMA] MainButton показан");

        tg.MainButton.onClick(() => {
          console.log("[TMA] MainButton нажат — отправляем buy_full");
          tg.sendData("buy_full");
          tg.showAlert("Запрос на покупку подписки отправлен боту");
        });

        // Кнопка "Назад" вверху слева
        tg.BackButton.show();
        tg.BackButton.onClick(() => {
          console.log("[TMA] BackButton нажат — закрываем приложение");
          tg.close();
        });

        setTmaReady(true);
      } catch (err: any) {
        console.error("[TMA] Ошибка при работе с Telegram.WebApp:", err);
        setError("Ошибка инициализации Telegram WebApp: " + (err.message || "неизвестная ошибка"));
      }
    } else {
      console.warn("[TMA] Telegram.WebApp не найден. Возможно, приложение открыто не в Telegram.");
      setError("Mini App запущен вне Telegram — функции TMA недоступны. Откройте через кнопку в боте.");
    }
  }, []);

  const sendCommand = (command: string) => {
    const tg = window.Telegram?.WebApp;
    if (tg && tmaReady) {
      console.log(`[TMA] Отправка команды: ${command}`);
      tg.sendData(command);
      tg.showAlert(`Команда "${command}" отправлена боту`);
    } else {
      console.warn("[TMA] Невозможно отправить команду — Telegram.WebApp не готов");
      alert("Mini App ещё не готов или не запущен внутри Telegram");
    }
  };

  return (
    <div className="min-h-screen flex flex-col p-5 pb-24 bg-[var(--bg)] text-[var(--text)]">
      {/* Заголовок */}
      <header className="text-center mb-10">
        <h1 className="text-5xl font-bold neon-glow mb-2">
          BKS VPN
        </h1>
        <p className="text-[var(--text-muted)] text-lg">
          Управление подпиской и рефералами
        </p>
      </header>

      {/* Карточка приветствия и баланса */}
      <div className="card mb-10">
        <h2 className="text-3xl font-semibold mb-4">
          Привет, {tgUser?.first_name || tgUser?.username || "пользователь"}!
        </h2>
        <p className="text-[var(--text-muted)] text-lg">
          Твой текущий баланс:{" "}
          <span className="text-[var(--neon-cyan)] font-bold">
            {balance} ₽
          </span>
        </p>
      </div>

      {/* Ошибка, если TMA не инициализировался */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 p-6 rounded-3xl mb-8 text-center">
          <p className="font-semibold mb-2">Ошибка TMA:</p>
          <p>{error}</p>
          <p className="mt-2 text-sm">
            Убедитесь, что вы открыли приложение через кнопку в боте, а не по прямой ссылке.
          </p>
        </div>
      )}

      {/* Основные кнопки действий */}
      <div className="flex flex-col gap-6 mb-auto">
        <button
          className="neon-btn text-xl py-5"
          onClick={() => sendCommand("get_config")}
          disabled={!tmaReady}
        >
          Получить конфиг VLESS
        </button>

        <button
          className="neon-btn opacity-90 text-xl py-5"
          onClick={() => sendCommand("get_ref_link")}
          disabled={!tmaReady}
        >
          Моя реферальная ссылка
        </button>

        <button
          className="neon-btn opacity-80 text-xl py-5"
          onClick={() => sendCommand("get_referrals")}
          disabled={!tmaReady}
        >
          Приглашённые друзья
        </button>

        <button
          className="neon-btn opacity-70 text-xl py-5"
          onClick={() => sendCommand("withdraw")}
          disabled={!tmaReady}
        >
          Вывести средства
        </button>
      </div>

      {/* Нижний футер */}
      <footer className="mt-auto text-center text-[var(--text-muted)] text-sm pt-12 pb-8">
        Подписка активна до 16.01.2027 • @BKS_Channel
        <br />
        <span className="text-xs opacity-70 mt-2 block">
          Для полной работы откройте через кнопку в боте Telegram
        </span>
      </footer>
    </div>
  );
}
