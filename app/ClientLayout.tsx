useEffect(() => {
  try {
    console.log("Попытка инициализации TMA...");

    init();

    const checkTMA = () => {
      console.log("Проверка Telegram.WebApp...");
      if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp;
        console.log("WebApp найден! Версия:", tg.version || "неизвестна");
        console.log("Пользователь:", tg.initDataUnsafe?.user);

        tg.ready();
        console.log("Вызван tg.ready()");

        tg.expand();
        console.log("Вызван tg.expand()");

        tg.MainButton.setParams({
          text: "Купить подписку 750 ⭐",
          color: "#00f9ff",
          text_color: "#000000",
        });
        tg.MainButton.show();
        console.log("MainButton показан");

        tg.MainButton.onClick(() => {
          console.log("MainButton нажат!");
          alert("Оплата запущена (тест)");
        });

        tg.BackButton.show();
        console.log("BackButton показан");

        tg.BackButton.onClick(() => {
          console.log("BackButton нажат → закрытие");
          tg.close();
        });
      } else {
        console.log("WebApp ещё не доступен, ждём...");
        setTimeout(checkTMA, 200); // повторяем каждые 200 мс
      }
    };

    checkTMA();
  } catch (err) {
    console.error("Критическая ошибка TMA:", err);
  }
}, []);
