import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN = "ВСТАВЬ_СВОЙ_TOKEN_ЗДЕСЬ"
PROMO_CODE = "ПАПКА"
PROMO_DISCOUNT = 90
SUBSCRIPTION_PRICE = "499₽/мес"
GULYA_STICKER = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"
PAYMENT_LINK = "https://t.me/bloneverse_bot?start=pay"

PRIVATE_CHANNELS = {
    "physics": "https://t.me/+XXXXXXXXXXXXXXXX",
    "self":    "https://t.me/+XXXXXXXXXXXXXXXX",
    "fun":     "https://t.me/+XXXXXXXXXXXXXXXX",
    "science": "https://t.me/+XXXXXXXXXXXXXXXX",
}

DIRECTIONS = {
    "physics": {
        "name": "⚛️ Физика",
        "description": (
            "<b>⚛️ Физика — BLONEVERSE</b>\n\n"
            "Здесь физику не заучивают — её видят.\n\n"
            "📌 Что тебя ждёт:\n"
            "• Качественные анимации явлений\n"
            "• Методички по ключевым темам\n"
            "• Объяснения через образы, а не формулы\n\n"
            "🎓 Идеально если готовишься к ЕГЭ или поступаешь в универ."
        ),
    },
    "self": {
        "name": "🧠 Саморазвитие",
        "description": (
            "<b>🧠 Саморазвитие — BLONEVERSE</b>\n\n"
            "Не мотивационный спам. Реальные инструменты.\n\n"
            "📌 Что тебя ждёт:\n"
            "• Методики продуктивности\n"
            "• Разборы привычек и мышления\n"
            "• Практики которые работают"
        ),
    },
    "fun": {
        "name": "😄 Развлечения",
        "description": (
            "<b>😄 Развлечения — BLONEVERSE</b>\n\n"
            "Мемы. Юмор. Контент который попадает в точку.\n\n"
            "📌 Что тебя ждёт:\n"
            "• Мемы про науку и жизнь\n"
            "• Короткий развлекательный контент\n"
            "• Всё в фирменном стиле BLONEVERSE"
        ),
    },
    "science": {
        "name": "🔭 Научпоп",
        "description": (
            "<b>🔭 Научпоп — BLONEVERSE</b>\n\n"
            "Наука простым языком. Без воды.\n\n"
            "📌 Что тебя ждёт:\n"
            "• Интересные факты и открытия\n"
            "• Разборы сложных тем доступно\n"
            "• Контент который расширяет кругозор"
        ),
    },
}

# ─── DATABASE ─────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("bloneverse.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            subscribed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = sqlite3.connect("bloneverse.db")
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row

def add_user(user_id: int, username: str):
    conn = sqlite3.connect("bloneverse.db")
    conn.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def set_subscribed(user_id: int):
    conn = sqlite3.connect("bloneverse.db")
    conn.execute("UPDATE users SET subscribed = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ─── STATES ───────────────────────────────────────────────────────────────────

class Register(StatesGroup):
    waiting_username = State()

# ─── KEYBOARDS ────────────────────────────────────────────────────────────────

def showcase_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚛️ Физика", callback_data="dir_physics"),
            InlineKeyboardButton(text="🧠 Саморазвитие", callback_data="dir_self"),
        ],
        [
            InlineKeyboardButton(text="😄 Развлечения", callback_data="dir_fun"),
            InlineKeyboardButton(text="🔭 Научпоп", callback_data="dir_science"),
        ],
        [InlineKeyboardButton(text=f"💳 Оплатить подписку — {SUBSCRIPTION_PRICE}", url=PAYMENT_LINK)],
    ])

def direction_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить подписку — {SUBSCRIPTION_PRICE}", url=PAYMENT_LINK)],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="showcase")],
    ])

def after_payment_kb():
    buttons = [
        [InlineKeyboardButton(text=d["name"], url=PRIVATE_CHANNELS[k])]
        for k, d in DIRECTIONS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ─── TEXTS ────────────────────────────────────────────────────────────────────

def showcase_text(name: str = ""):
    greeting = f"С возвращением, <b>{name}</b>! 👋\n\n" if name else ""
    return (
        f"{greeting}"
        f"<b>📁 BLONEVERSE — одна подписка, всё включено</b>\n\n"
        f"Нажми на раздел чтобы ознакомиться 👇\n\n"
        f"⚛️ Физика · 🧠 Саморазвитие\n"
        f"😄 Развлечения · 🔭 Научпоп\n\n"
        f"💳 Цена: <b>{SUBSCRIPTION_PRICE}</b>\n"
        f"🎁 Промокод <code>{PROMO_CODE}</code> — скидка {PROMO_DISCOUNT}%"
    )

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)

    if user:
        await message.answer_sticker(GULYA_STICKER)
        await message.answer(
            showcase_text(user[1]),
            parse_mode="HTML",
            reply_markup=showcase_kb()
        )
        return

    await message.answer_sticker(GULYA_STICKER)
    await message.answer(
        "<b>📁 Добро пожаловать в BLONEVERSE</b>\n\n"
        "Одна вселенная. Разные миры.\n"
        "Наука. Саморазвитие. Развлечения.\n\n"
        "Для начала — напиши свой никнейм:",
        parse_mode="HTML"
    )
    await state.set_state(Register.waiting_username)

@dp.message(Register.waiting_username)
async def process_username(message: Message, state: FSMContext):
    nickname = message.text.strip()

    if len(nickname) < 2:
        await message.answer("Никнейм слишком короткий, попробуй ещё раз:")
        return

    add_user(message.from_user.id, nickname)
    await state.clear()

    await message.answer_sticker(GULYA_STICKER)
    await message.answer(
        f"✅ Готово, <b>{nickname}</b>!\n\n" + showcase_text(),
        parse_mode="HTML",
        reply_markup=showcase_kb()
    )

@dp.callback_query(F.data == "showcase")
async def cb_showcase(call: CallbackQuery):
    user = get_user(call.from_user.id)
    name = user[1] if user else ""
    await call.message.edit_text(
        showcase_text(name),
        parse_mode="HTML",
        reply_markup=showcase_kb()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("dir_"))
async def cb_direction(call: CallbackQuery):
    key = call.data.replace("dir_", "")
    d = DIRECTIONS.get(key)
    if not d:
        await call.answer("Раздел не найден")
        return
    await call.message.edit_text(
        d["description"],
        parse_mode="HTML",
        reply_markup=direction_kb()
    )
    await call.answer()

@dp.callback_query(F.data == "access")
async def cb_access(call: CallbackQuery):
    set_subscribed(call.from_user.id)
    await call.message.edit_text(
        "🎉 <b>Добро пожаловать в BLONEVERSE!</b>\n\n"
        "Тебе открыты все разделы — выбирай 👇",
        parse_mode="HTML",
        reply_markup=after_payment_kb()
    )
    await call.answer()

# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    print("✅ Бот BLONEVERSE запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
