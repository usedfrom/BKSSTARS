interface TelegramWebApp {
  ready: () => void;
  expand: () => void;
  close: () => void;
  MainButton: {
    setParams: (params: { text: string; color: string; text_color: string }) => void;
    show: () => void;
    onClick: (callback: () => void) => void;
  };
  BackButton: {
    show: () => void;
    onClick: (callback: () => void) => void;
  };
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
      language_code?: string;
      [key: string]: any;
    };
    [key: string]: any;
  };
  version?: string; // опционально, если когда-то понадобится
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

export {};