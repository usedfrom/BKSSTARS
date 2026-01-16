import asyncio
import logging
import os
from datetime import datetime, timedelta
import aiosqlite
import uuid
import csv
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove, LabeledPrice, PreCheckoutQuery, SuccessfulPayment
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from py3xui import Api, Client

# ────────────────────────────────────────────────
# Настройка подробного логирования
# ────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
# Константы
# ────────────────────────────────────────────────

BOT_TOKEN = "8191782023:AAF_LwyAb7URmTSgLEwtXgXHWIgOKUF5PDI"

ADMIN_ID = 5685680934

FULL_STARS = 750         # полная цена в Telegram Stars
DISCOUNT_STARS = 350     # цена с промокодом
PROMO_CODE = "happy2026"
SUBSCRIPTION_DAYS = 365

CHANNEL_USERNAME = "@BKS_Channel"
CHANNEL_ID = -1003600648881

XUI_HOST = "http://127.0.0.1:2053/lCqf5Cxg1557ZCaz35"
XUI_USERNAME = "sPTpifci4m"
XUI_PASSWORD = "fDtMcSaJt4"
XUI_INBOUND_ID = 1
XUI_SERVER_IP = "162.120.16.181"
XUI_SERVER_PORT = 443
XUI_PUBLIC_KEY = "5Nd6YCui4WtPOU8MVjtl08uhqceFIDcHNuwDVIxJcFc"
XUI_SHORT_ID = "a1b2c3"
XUI_SNI = "ozon.ru"
XUI_FP = "chrome"

DB_FILE = "subscriptions.db"

# ────────────────────────────────────────────────
# Инициализация бота и диспетчера
# ────────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

xui_api = Api(host=XUI_HOST, username=XUI_USERNAME, password=XUI_PASSWORD)

try:
    xui_api.login()
    logger.info("Успешная авторизация в панели 3x-ui")
except Exception as e:
    logger.error(f"Ошибка авторизации в 3x-ui: {e}")

# ────────────────────────────────────────────────
# Состояния FSM
# ────────────────────────────────────────────────

class PromoForm(StatesGroup):
    waiting_for_promo = State()

class WithdrawForm(StatesGroup):
    method = State()
    details = State()

# ────────────────────────────────────────────────
# Инициализация базы данных
# ────────────────────────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                expiry_date TEXT,
                paid_amount REAL,
                client_email TEXT UNIQUE,
                client_uuid TEXT,
                referral_balance REAL DEFAULT 0,
                referrer_id INTEGER DEFAULT NULL,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                payment_date TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS withdraw_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                method TEXT,
                details TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES subscriptions(user_id)
            )
        ''')
        await db.commit()
    logger.info("База данных проверена/создана")

# ────────────────────────────────────────────────
# Вспомогательные функции
# ────────────────────────────────────────────────

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки user_id={user_id}: {e}")
        return False

async def get_subscription(user_id: int) -> dict:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT expiry_date, client_email, client_uuid, referral_balance "
            "FROM subscriptions WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            expiry_str, email, uuid_str, balance = row
            expiry = datetime.fromisoformat(expiry_str) if expiry_str else None
            if expiry and expiry > datetime.now():
                return {
                    "active": True,
                    "expiry": expiry,
                    "email": email,
                    "uuid": uuid_str,
                    "balance": balance or 0
                }
    return {"active": False, "balance": 0}

async def activate_subscription(user_id: int, days: int, amount: float, referrer_id=None):
    expiry = datetime.now() + timedelta(days=days)
    client_uuid = str(uuid.uuid4())
    client_email = f"user_{user_id}_{int(expiry.timestamp())}"

    try:
        new_client = Client(
            id=client_uuid,
            email=client_email,
            enable=True,
            expiryTime=int(expiry.timestamp() * 1000),
            totalGB=0,
            limitIp=3,
        )
        xui_api.client.add(XUI_INBOUND_ID, [new_client])
        logger.info(f"Клиент добавлен в 3x-ui: {client_email}")
    except Exception as e:
        logger.error(f"Ошибка добавления клиента в 3x-ui: {e}")
        raise

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            INSERT OR REPLACE INTO subscriptions 
            (user_id, username, expiry_date, paid_amount, client_email, client_uuid, referrer_id, payment_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            (await bot.get_chat(user_id)).username,
            expiry.isoformat(),
            amount,
            client_email,
            client_uuid,
            referrer_id,
            datetime.now().isoformat()
        ))

        if referrer_id:
            # Начисление рефералу происходит в successful_payment (только за полную оплату)
            pass

        await db.commit()
    logger.info(f"Подписка активирована user_id={user_id} до {expiry}")

def generate_vless_config(uuid: str, email: str, expiry: datetime) -> str:
    expiry_str = expiry.strftime("%d.%m.%Y")
    return (
        f"vless://{uuid}@{XUI_SERVER_IP}:{XUI_SERVER_PORT}"
        f"?security=reality&encryption=none&pbk={XUI_PUBLIC_KEY}&headerType=none&type=tcp"
        f"&flow=xtls-rprx-vision&fp={XUI_FP}&sni={XUI_SNI}&sid={XUI_SHORT_ID}"
        f"#{email}_до_{expiry_str}"
    ).strip()

def main_keyboard(has_active: bool = False):
    kb = [
        [InlineKeyboardButton(text="Купить подписку · 750 ⭐ / год", callback_data="buy_full")],
        [InlineKeyboardButton(text="У меня промокод", callback_data="promo")],
        [InlineKeyboardButton(text="Мой баланс", callback_data="my_balance")],
        [InlineKeyboardButton(text="Реферальная ссылка", callback_data="get_ref_link")],
        [InlineKeyboardButton(text="Перейти в канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
    ]
    if has_active:
        kb.extend([
            [InlineKeyboardButton(text="Проверить подписку", callback_data="check_sub")],
            [InlineKeyboardButton(text="Получить конфиг заново", callback_data="get_config")],
        ])
    kb.append([InlineKeyboardButton(text="Вывести средства", callback_data="withdraw")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ────────────────────────────────────────────────
# Отправка инвойса Stars
# ────────────────────────────────────────────────

async def send_stars_invoice(user_id: int, stars_amount: int, payload: str, is_promo: bool = False):
    title = "VPN-подписка на год (VLESS + Reality)"
    description = "365 дней • 3 устройства • Reality-обфускация"
    if is_promo:
        description += "\nСкидка по промокоду (было 750 ⭐)"

    prices = [LabeledPrice(label="Годовая подписка", amount=stars_amount)]

    try:
        await bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",          # Обязательно пустая строка для XTR!
            currency="XTR",
            prices=prices,
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
        )
        logger.info(f"Инвойс {stars_amount} ⭐ отправлен пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки инвойса Stars: {e}")
        await bot.send_message(user_id, "Не удалось создать счёт. Попробуйте позже.")

# ────────────────────────────────────────────────
# Хендлеры
# ────────────────────────────────────────────────

@router.message(CommandStart(deep_link=True))
@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    logger.info(f"[START] Пользователь {user.id} ({user.username}) запустил бота")
    args = message.text.split()
    referrer_id = None

    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("_")[1])
            logger.info(f"[REF] Реферальная ссылка от {referrer_id}")
        except:
            logger.warning(f"[REF] Некорректная реф-ссылка: {message.text}")

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            INSERT OR IGNORE INTO subscriptions 
            (user_id, username, referral_balance, created_at)
            VALUES (?, ?, 0, datetime('now', 'localtime'))
        ''', (user.id, user.username))
        
        if referrer_id:
            await db.execute(
                "UPDATE subscriptions SET referrer_id = ? WHERE user_id = ? AND referrer_id IS NULL",
                (referrer_id, user.id)
            )
        await db.commit()

    if not await is_subscribed(user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="Я подписался", callback_data="check_subscribe")]
        ])
        await message.answer(
            "Чтобы пользоваться ботом и купить VPN, подпишитесь на наш канал!\n"
            "Там новости, промокоды и обновления.",
            reply_markup=kb
        )
        return

    sub = await get_subscription(user.id)
    text = (
        "Спасибо за подписку! Теперь можно пользоваться ботом.\n"
        "Все инструкции по подключению на канале @BKS_Channel.\n"
        "Пригласи друга и получи 500 ₽ (только за полную оплату 750 ⭐)!"
    )
    await message.answer(text, reply_markup=main_keyboard(sub["active"]))

@router.callback_query(F.data == "check_subscribe")
async def check_subscribe(callback: CallbackQuery):
    user_id = callback.from_user.id
    if await is_subscribed(user_id):
        await callback.message.delete()
        
        sub = await get_subscription(user_id)
        text = (
            "Спасибо за подписку! Теперь можно пользоваться ботом.\n"
            "Все инструкции по подключению на канале @BKS_Channel.\n"
            "Пригласи друга и получи 500 ₽ (только за полную оплату)!"
        )
        
        await callback.message.answer(text, reply_markup=main_keyboard(sub["active"]))
    else:
        await callback.answer("Вы ещё не подписались! Подпишитесь и нажмите снова.", show_alert=True)

@router.callback_query(F.data.in_({"buy_full", "promo"}))
async def require_subscribe(callback: CallbackQuery, state: FSMContext = None):
    user_id = callback.from_user.id
    data = callback.data

    if not await is_subscribed(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="Я подписался", callback_data="check_subscribe")]
        ])
        await callback.message.answer("Сначала подпишитесь на канал!", reply_markup=kb)
        await callback.answer()
        return

    if data == "buy_full":
        sub = await get_subscription(user_id)
        if sub["active"]:
            await callback.message.answer("У вас уже есть активная подписка!")
            await callback.answer()
            return
        payload = f"sub_full_{user_id}_{int(datetime.now().timestamp())}"
        await send_stars_invoice(user_id, FULL_STARS, payload)
    elif data == "promo":
        await callback.message.answer("Введите промокод:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(PromoForm.waiting_for_promo)

    await callback.answer()

@router.message(PromoForm.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext):
    if message.text.strip().lower() == PROMO_CODE.lower():
        payload = f"sub_promo_{message.from_user.id}_{int(datetime.now().timestamp())}"
        await send_stars_invoice(message.from_user.id, DISCOUNT_STARS, payload, is_promo=True)
        await message.answer("Промокод принят → 350 ⭐")
        await state.clear()
    else:
        await message.answer("Неверный промокод. Попробуйте снова или /cancel")

@router.message(F.text.lower() == "/cancel")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_keyboard())

# ────────────────────────────────────────────────
# Обработчики Telegram Stars
# ────────────────────────────────────────────────

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payment: SuccessfulPayment = message.successful_payment
    user_id = message.from_user.id
    stars = payment.total_amount
    payload = payment.invoice_payload

    logger.info(f"[STARS SUCCESS] {stars} ⭐ | user={user_id} | payload={payload}")

    is_full = stars == FULL_STARS

    sub = await get_subscription(user_id)
    if sub["active"]:
        await message.answer("Подписка уже активна. Повторная оплата не требуется.")
        return

    referrer_id = None
    async with aiosqlite.connect(DB_FILE) as db:
        row = await (await db.execute(
            "SELECT referrer_id FROM subscriptions WHERE user_id = ?",
            (user_id,)
        )).fetchone()
        if row and row[0]:
            referrer_id = row[0]

    rub_equiv = 1239 if is_full else 619
    await activate_subscription(user_id, SUBSCRIPTION_DAYS, rub_equiv, referrer_id)

    if referrer_id and is_full:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "UPDATE subscriptions SET referral_balance = referral_balance + 500 WHERE user_id = ?",
                (referrer_id,)
            )
            await db.commit()
        try:
            await bot.send_message(
                referrer_id,
                f"Друг (ID {user_id}) купил подписку за 750 ⭐ → +500 ₽ на баланс!"
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить реферала {referrer_id}: {e}")

    expiry_str = (datetime.now() + timedelta(days=SUBSCRIPTION_DAYS)).strftime("%d.%m.%Y")
    text = f"Оплата {stars} ⭐ прошла успешно!\nПодписка активна до {expiry_str}"
    if not is_full:
        text += "\n(применена скидка по промокоду)"

    await message.answer(text, reply_markup=main_keyboard(has_active=True))

# ────────────────────────────────────────────────
# Остальные обработчики (баланс, реф.ссылка, конфиг, вывод, админ и т.д.)
# ────────────────────────────────────────────────

@router.callback_query(F.data == "my_balance")
async def my_balance(callback: CallbackQuery):
    user_id = callback.from_user.id
    sub = await get_subscription(user_id)
    
    async with aiosqlite.connect(DB_FILE) as db:
        c = await db.execute("SELECT COUNT(*) FROM subscriptions WHERE referrer_id = ?", (user_id,))
        total_invited = (await c.fetchone())[0]
        
        c = await db.execute("SELECT COUNT(*) FROM subscriptions WHERE referrer_id = ? AND expiry_date IS NOT NULL", (user_id,))
        paid_invited = (await c.fetchone())[0]
    
    text = (
        f"Ваш реферальный баланс: {sub['balance']} ₽\n\n"
        f"Приглашено друзей: {total_invited} человек\n"
        f"Из них оплатили подписку: {paid_invited} человек\n\n"
        f"Приглашайте ещё — 500 ₽ за каждого оплатившего за 750 ⭐!"
    )
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "get_ref_link")
async def get_ref_link(callback: CallbackQuery):
    bot_me = await bot.get_me()
    link = f"https://t.me/{bot_me.username}?start=ref_{callback.from_user.id}"
    await callback.message.answer(
        f"Ваша реф-ссылка:\n{link}\nПриглашайте друзей — 500 ₽ за каждого оплатившего полную подписку!"
    )
    await callback.answer()

@router.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):
    sub = await get_subscription(callback.from_user.id)
    if sub["active"]:
        await callback.message.answer(f"Подписка активна до {sub['expiry'].strftime('%d.%m.%Y')}")
    else:
        await callback.message.answer("Подписка не активна.")
    await callback.answer()

@router.callback_query(F.data == "get_config")
async def get_config(callback: CallbackQuery):
    sub = await get_subscription(callback.from_user.id)
    if not sub["active"]:
        await callback.message.answer("Подписка не активна!")
        await callback.answer()
        return
    config = generate_vless_config(sub["uuid"], sub["email"], sub["expiry"])
    await callback.message.answer(
        f"Ваш VLESS:\n```\n{config}\n```",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "withdraw")
async def start_withdraw(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    sub = await get_subscription(user_id)
    
    if sub["balance"] < 1500:
        await callback.message.answer("Минимум для вывода — 1500 ₽")
        await callback.answer()
        return
    
    async with aiosqlite.connect(DB_FILE) as db:
        c = await db.execute("SELECT COUNT(*) FROM subscriptions WHERE referrer_id = ? AND expiry_date IS NOT NULL", (user_id,))
        ref_count = (await c.fetchone())[0]
    
    if ref_count < 3:
        await callback.message.answer(f"Нужно минимум 3 оплативших друга. У тебя: {ref_count}")
        await callback.answer()
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="TON", callback_data="wd_ton")],
        [InlineKeyboardButton(text="СБП (телефон)", callback_data="wd_sbp")],
        [InlineKeyboardButton(text="Карта", callback_data="wd_card")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_withdraw")],
    ])
    
    await callback.message.answer(
        f"Доступно: {sub['balance']} ₽\nВыберите способ:",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("wd_"))
async def choose_method(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    await state.update_data(method=method)
    
    prompts = {
        "ton": "Укажите адрес TON-кошелька (EQ... или UQ...):",
        "sbp": "Номер телефона для СБП (+7XXXXXXXXXX) и банк:",
        "card": "Номер карты (16 цифр), банк и ФИО (через запятую):"
    }
    
    await callback.message.answer(prompts[method])
    await state.set_state(WithdrawForm.details)
    await callback.answer()

@router.message(WithdrawForm.details)
async def process_details(message: Message, state: FSMContext):
    data = await state.get_data()
    method = data["method"]
    details = message.text.strip()
    
    user_id = message.from_user.id
    sub = await get_subscription(user_id)
    amount = sub["balance"]
    
    if amount < 1500:
        await message.answer("Баланс изменился. Вывод невозможен.")
        await state.clear()
        return
    
    created_at = datetime.now().isoformat()
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('''
            INSERT INTO withdraw_requests (user_id, amount, method, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, method, details, created_at))
        request_id = cursor.lastrowid
        await db.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_withdraw_{request_id}_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_withdraw_{request_id}_{user_id}")
        ]
    ])
    
    await bot.send_message(
        ADMIN_ID,
        f"Новый запрос на вывод!\n"
        f"Пользователь: @{message.from_user.username} (ID {user_id})\n"
        f"Сумма: {amount} ₽\n"
        f"Способ: {method.upper()}\n"
        f"Реквизиты: {details}\n"
        f"Приглашено: {await get_referral_count(user_id)}\n"
        f"ID запроса: {request_id}",
        reply_markup=kb
    )
    
    await message.answer("Запрос на вывод отправлен администратору. Ожидайте обработки (1–24 часа).")
    await state.clear()

@router.callback_query(F.data.startswith("approve_withdraw_"))
async def approve_withdraw(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    parts = callback.data.split("_")
    request_id = int(parts[2])
    user_id = int(parts[3])
    
    async with aiosqlite.connect(DB_FILE) as db:
        c = await db.execute("SELECT status, amount FROM withdraw_requests WHERE id = ?", (request_id,))
        row = await c.fetchone()
        if not row or row[0] != "pending":
            await callback.answer("Запрос уже обработан", show_alert=True)
            return
        amount = row[1]
        
        await db.execute("UPDATE withdraw_requests SET status = 'approved' WHERE id = ?", (request_id,))
        await db.execute("UPDATE subscriptions SET referral_balance = 0 WHERE user_id = ?", (user_id,))
        await db.commit()
    
    try:
        await bot.send_message(user_id, f"Ваш вывод {amount} ₽ **подтверждён**! Средства будут переведены в ближайшее время.")
    except:
        pass
    
    await callback.message.edit_text(callback.message.text + "\n\n✅ Вывод подтверждён")
    await callback.answer()

@router.callback_query(F.data.startswith("reject_withdraw_"))
async def reject_withdraw(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    parts = callback.data.split("_")
    request_id = int(parts[2])
    user_id = int(parts[3])
    
    async with aiosqlite.connect(DB_FILE) as db:
        c = await db.execute("SELECT status FROM withdraw_requests WHERE id = ?", (request_id,))
        row = await c.fetchone()
        if not row or row[0] != "pending":
            await callback.answer("Запрос уже обработан", show_alert=True)
            return
        
        await db.execute("UPDATE withdraw_requests SET status = 'rejected' WHERE id = ?", (request_id,))
        await db.commit()
    
    try:
        await bot.send_message(user_id, "Ваш запрос на вывод **отклонён**.\nСвяжитесь с администратором для уточнения причин.")
    except:
        pass
    
    await callback.message.edit_text(callback.message.text + "\n\n❌ Вывод отклонён")
    await callback.answer()

@router.callback_query(F.data == "cancel_withdraw")
async def cancel_withdraw(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Вывод отменён.", reply_markup=main_keyboard())
    await callback.answer()

async def get_referral_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_FILE) as db:
        c = await db.execute("SELECT COUNT(*) FROM subscriptions WHERE referrer_id = ? AND expiry_date IS NOT NULL", (user_id,))
        return (await c.fetchone())[0]

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещён")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика рефералов", callback_data="admin_ref_stats")],
        [InlineKeyboardButton(text="Топ пригласивших", callback_data="admin_top_invites")],
        [InlineKeyboardButton(text="Кому должен (≥1500 ₽)", callback_data="admin_debts")],
        [InlineKeyboardButton(text="Экспорт CSV", callback_data="admin_export_csv")],
        [InlineKeyboardButton(text="Графики", callback_data="admin_graphs")],
    ])
    
    await message.answer("Админ-панель:", reply_markup=kb)

# Остальные админ-обработчики остаются без изменений (admin_ref_stats, admin_top_invites и т.д.)
# ... (вставь их из оригинального кода, если нужно)

# ────────────────────────────────────────────────
# Запуск бота
# ────────────────────────────────────────────────

async def main():
    await init_db()
    logger.info("База данных готова. Запуск поллинга...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())