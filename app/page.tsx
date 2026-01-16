"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [tgUser, setTgUser] = useState<any>(null);
  const [balance] = useState<number>(0);

  useEffect(() => {
    // Проверяем наличие Telegram.WebApp (уже инициализировано в layout)
    const tg = window.Telegram?.WebApp;

    if (tg) {
      // Дополнительные проверки на всякий случай
      tg.ready();
      tg.expand();

      // Получаем пользователя
      const user = tg.initDataUnsafe?.user;
      if (user) {
        setTgUser(user);
      }

      // Настраиваем MainButton (нижняя кнопка в Telegram)
      tg.MainButton.setParams({
        text: "Купить подписку 750 ⭐",
        color: "#00f9ff",
        text_color: "#000000",
      });
      tg.MainButton.show();

      tg.MainButton.onClick(() => {
        alert("Здесь будет вызов оплаты через бота или прямая интеграция");
      });

      // BackButton (кнопка "Назад" вверху слева)
      tg.BackButton.show();
      tg.BackButton.onClick(() => tg.close());
    }
  }, []);

  return (
    <div className="min-h-screen flex flex-col p-5 pb-24">
      <header className="text-center mb-10">
        <h1 className="text-4xl font-bold neon-glow">BKS VPN</h1>
        <p className="text-[var(--text-muted)] mt-2">Управление подпиской и рефералами</p>
      </header>

      <div className="card mb-8">
        <h2 className="text-2xl font-semibold mb-4">
          Привет, {tgUser?.first_name || "пользователь"}!
        </h2>
        <p className="text-[var(--text-muted)]">
          Твой текущий баланс: <span className="text-[var(--neon-cyan)] font-bold">{balance} ₽</span>
        </p>
      </div>

      <div className="flex flex-col gap-5">
        <button className="neon-btn">Получить конфиг VLESS</button>
        <button className="neon-btn opacity-90">Моя реферальная ссылка</button>
        <button className="neon-btn opacity-80">Приглашённые друзья</button>
        <button className="neon-btn opacity-70">Вывести средства</button>
      </div>

      <footer className="mt-auto text-center text-[var(--text-muted)] text-sm pt-10">
        Подписка активна до 16.01.2027 • @BKS_Channel
      </footer>
    </div>
  );
}