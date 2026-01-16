"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [tgUser, setTgUser] = useState<any>(null);
  const [balance, setBalance] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;

    if (tg) {
      tg.ready();
      tg.expand();

      // Получаем пользователя и данные
      const user = tg.initDataUnsafe?.user;
      if (user) {
        setTgUser(user);
      }

      // Показываем баланс и статус (заглушка, можно запросить у бота позже)
      // В реальном проекте здесь можно запросить баланс через sendData("get_balance")
      setBalance(0); // заменить на реальный запрос

      // Настраиваем нижнюю кнопку Telegram
      tg.MainButton.setParams({
        text: "Купить подписку 750 ⭐",
        color: "#00f9ff",
        text_color: "#000000",
      });
      tg.MainButton.show();

      tg.MainButton.onClick(() => {
        tg.sendData("buy_full");
        tg.showAlert("Запрос на покупку отправлен. Ожидайте ответа бота.");
      });

      tg.BackButton.show();
      tg.BackButton.onClick(() => tg.close());

      setLoading(false);
    } else {
      setLoading(false);
    }
  }, []);

  const sendCommand = (command: string) => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.sendData(command);
      window.Telegram.WebApp.showAlert(`Команда "${command}" отправлена боту`);
    } else {
      alert("Mini App не запущен внутри Telegram");
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-[var(--neon-cyan)]">Загрузка...</div>;
  }

  return (
    <div className="min-h-screen flex flex-col p-5 pb-24">
      <header className="text-center mb-10">
        <h1 className="text-4xl font-bold neon-glow">BKS VPN</h1>
        <p className="text-[var(--text-muted)] mt-2">Управление подпиской и рефералами</p>
      </header>

      <div className="card mb-8">
        <h2 className="text-2xl font-semibold mb-4">
          Привет, {tgUser?.first_name || tgUser?.username || "пользователь"}!
        </h2>
        <p className="text-[var(--text-muted)]">
          Твой текущий баланс: <span className="text-[var(--neon-cyan)] font-bold">{balance} ₽</span>
        </p>
      </div>

      <div className="flex flex-col gap-5">
        <button className="neon-btn" onClick={() => sendCommand("get_config")}>
          Получить конфиг VLESS
        </button>

        <button className="neon-btn opacity-90" onClick={() => sendCommand("get_ref_link")}>
          Моя реферальная ссылка
        </button>

        <button className="neon-btn opacity-80" onClick={() => sendCommand("get_referrals")}>
          Приглашённые друзья
        </button>

        <button className="neon-btn opacity-70" onClick={() => sendCommand("withdraw")}>
          Вывести средства
        </button>
      </div>

      <footer className="mt-auto text-center text-[var(--text-muted)] text-sm pt-10">
        Подписка активна до 16.01.2027 • @BKS_Channel
      </footer>
    </div>
  );
}
