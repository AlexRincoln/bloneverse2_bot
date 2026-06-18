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
BOT_TOKEN = "8939981008:AAGODrnmp9qNNs3gPRxpkKl8IUlzX0Sk21o"
PROMO_CODE = "ПАПКА"
PROMO_DISCOUNT = 90
SUBSCRIPTION_PRICE = "499₽/мес"

# Разные стикеры из одного стикерпака
STICKER_WELCOME = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"  # первое знакомство
STICKER_LOBBY   = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"  # лобби (замени на другой ID из того же пака)

PAYMENT_LINK = "https://t.me/bloneverse_bot?start=pay"

PRIVATE_CHANNELS = {
    "physics":  "https://t.me/+XXXXXXXXXXXXXXXX",
    "self":     "https://t.me/+XXXXXXXXXXXXXXXX",
    "fun":      "https://t.me/+XXXXXXXXXXXXXXXX",
    "chemistry":"https://t.me/+XXXXXXXXXXXXXXXX",
    "math":     "https://t.me/+XXXXXXXXXXXXXXXX",
}

# ─── НАПРАВЛЕНИЯ САМОРАЗВИТИЯ ─────────────────────────────────────────────────

SELF_SUBJECTS = {
    "physics": {
        "name": "🔍 Физика",
        "description": (
            "<b>🔍 Физика — BLONEVERSE</b>\n\n"
            "После оплаты тебе открывается:\n\n"
            "📡 <b>ТГ-канал по физике</b> — объяснения тем, полезные файлы и методички\n"
            "🎓 <b>2 занятия с репетитором</b> — живой разбор твоих вопросов\n"
            "🎬 <b>Видеоролики по физике</b> — анимированные объяснения в едином стиле BLONEVERSE\n\n"
            "📐 Все ролики, статьи, методички и анимации выполнены в <b>едином фирменном стиле</b> — "
            "никакой мешанины, только структура и качество.\n\n"
            "💾 Физика становится понятной — через образы, а не зубрёжку."
        ),
    },
    "chemistry": {
        "name": "🧪 Химия",
        "description": (
            "<b>🧪 Химия — BLONEVERSE</b>\n\n"
            "После оплаты тебе открывается:\n\n"
            "📡 <b>ТГ-канал по химии</b> — объяснения тем, полезные файлы и методички\n"
            "🎓 <b>2 занятия с репетитором</b> — живой разбор реакций и задач\n"
            "🎬 <b>Видеоролики по химии</b> — анимированные объяснения в едином стиле BLONEVERSE\n\n"
            "📐 Все ролики, статьи, методички и анимации выполнены в <b>едином фирменном стиле</b> — "
            "структурно, красиво, понятно.\n\n"
            "💾 Химия без страха — через визуал и логику."
        ),
    },
    "math": {
        "name": "📊 Математика",
        "description": (
            "<b>📊 Математика — BLONEVERSE</b>\n\n"
            "После оплаты тебе открывается:\n\n"
            "📡 <b>ТГ-канал по математике</b> — объяснения тем, полезные файлы и методички\n"
            "🎓 <b>2 занятия с репетитором</b> — разбор задач и пробелов в знаниях\n"
            "🎬 <b>Видеоролики по математике</b> — анимированные объяснения в едином стиле BLONEVERSE\n\n"
            "📐 Все ролики, статьи, методички и анимации выполнены в <b>едином фирменном стиле</b> — "
            "от простого к сложному, без воды.\n\n"
            "💾 Математика — это не страшно, если объяснить правильно."
        ),
    },
    "wip": {
        "name": "🛠️ В разработке",
        "description": (
            "<b>🛠️ Скоро в BLONEVERSE</b>\n\n"
            "Мы активно работаем над новыми направлениями💾\n\n"
            "🔜 <b>Что готовится:</b>\n"
            "• Новые предметы — история, биология, английский и другие\n"
            "• Новые идеи для анимационных роликов в едином стиле\n"
            "• Расширение платформы для всего мира 🌍\n\n"
            "📐 Все материалы, как всегда, будут в <b>едином фирменном стиле BLONEVERSE</b> — "
            "анимация, структура, качество.\n\n"
            "⌨️ Следи за обновлениями — лучшее впереди 🚀"
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
            InlineKeyboardButton(text="⌨️ Саморазвитие", callback_data="dir_self"),
            InlineKeyboardButton(text="📺 Развлечения",  callback_data="dir_fun"),
        ],
        [InlineKeyboardButton(text="Где Я🔊",           callback_data="where_am_i")],
        [InlineKeyboardButton(text=f"🔍 Оплатить подписку — {SUBSCRIPTION_PRICE}", url=PAYMENT_LINK)],
    ])

def self_subjects_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Физика",       callback_data="subj_physics"),
            InlineKeyboardButton(text="🧪 Химия",        callback_data="subj_chemistry"),
        ],
        [
            InlineKeyboardButton(text="📊 Математика",   callback_data="subj_math"),
            InlineKeyboardButton(text="🛠️ В разработке", callback_data="subj_wip"),
        ],
        [InlineKeyboardButton(text="🗝️ Назад",           callback_data="showcase")],
    ])

def subject_detail_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔊 Оплатить подписку — {SUBSCRIPTION_PRICE}", url=PAYMENT_LINK)],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="dir_self")],
    ])

def fun_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔊 Оплатить подписку — {SUBSCRIPTION_PRICE}", url=PAYMENT_LINK)],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="showcase")],
    ])

def where_am_i_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="showcase")],
    ])

def after_payment_kb():
    buttons = [
        [InlineKeyboardButton(text="🔍 Физика",     url=PRIVATE_CHANNELS["physics"])],
        [InlineKeyboardButton(text="🧪 Химия",      url=PRIVATE_CHANNELS["chemistry"])],
        [InlineKeyboardButton(text="📊 Математика", url=PRIVATE_CHANNELS["math"])],
        [InlineKeyboardButton(text="📺 Развлечения",url=PRIVATE_CHANNELS["fun"])],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ─── TEXTS ────────────────────────────────────────────────────────────────────

def showcase_text(name: str = ""):
    greeting = f"С возвращением, <b>{name}</b>! 👋\n\n" if name else ""
    return (
        f"{greeting}"
        f"<b>💾 BLONEVERSE — одна подписка, всё включено</b>\n\n"
        f"Нажми на раздел чтобы ознакомиться 🩶\n\n"
        f"⌨️ Саморазвитие · 📺 Развлечения\n\n"
        f"⌨️ Цена: <b>{SUBSCRIPTION_PRICE}</b>\n"
        f"🦾 Промокод <code>{PROMO_CODE}</code> — скидка {PROMO_DISCOUNT}%"
    )

SELF_INTRO_TEXT = (
    "<b>⌨️ Саморазвитие — BLONEVERSE</b>\n\n"
    "Здесь собраны направления для прокачки знаний по разным предметам 💡\n\n"
    "Каждое направление — это структурированная база:\n"
    "📡 ТГ-канал с материалами · 🎓 Занятия с репетитором · 🎬 Видеоролики\n\n"
    "Все ролики, статьи, методички и анимации выполнены в <b>едином фирменном стиле BLONEVERSE</b> — "
    "никакой мешанины, только структура.\n\n"
    "👇 Выбери предмет:"
)

FUN_TEXT = (
    "<b>📺 Развлечения — BLONEVERSE</b>\n\n"
    "Мемы. Юмор. Контент который попадает в точку.\n\n"
    "🎧 Что тебя ждёт:\n"
    "• Мемы и короткий развлекательный контент\n"
    "• Всё в фирменном стиле BLONEVERSE💾\n\n"
    "🛠️ <b>Сейчас идёт активная разработка</b> — скоро будет ещё больше контента. "
    "Следи за обновлениями!"
)

WHERE_AM_I_TEXT = (
    "<b>Где Я🔊 — BLONEVERSE</b>\n\n"
    "Ты находишься в боте проекта <b>BLONEVERSE</b> — это анимационная вселенная знаний и контента.\n\n"
    "🎬 <b>Идея компании:</b>\n"
    "Всё что мы делаем — выполнено в <b>едином анимационном стиле</b>. "
    "Ролики, статьи, методички, обложки — единая визуальная система, узнаваемая с первого взгляда.\n\n"
    "🏗️ <b>Структура:</b>\n"
    "• ТГ-каналы по направлениям — учёба и развлечения\n"
    "• Единая платформа в разработке — для всего мира 🌍\n"
    "• YouTube-канал уже создан — все ролики выйдут в едином стиле анимации\n\n"
    "🚀 <b>Цель — глобальный проект</b>, где любой человек в мире может получить "
    "качественный контент на одной платформе.\n\n"
    "📡 Сначала YouTube → потом собственная платформа.\n"
    "Все вперёд 💾"
)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)

    if user:
        await message.answer_sticker(STICKER_LOBBY)
        await message.answer(
            showcase_text(user[1]),
            parse_mode="HTML",
            reply_markup=showcase_kb()
        )
        return

    await message.answer_sticker(STICKER_WELCOME)
    await message.answer(
        "<b>Добро пожаловать в BLONEVERSE💾</b>\n\n"
        "Одна вселенная📱. \n"
        "Наука📼. Саморазвитие📹. Развлечения🖥️.\n\n"
        "Для начала — напиши свой никнейм📽️:",
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

    await message.answer_sticker(STICKER_LOBBY)
    await message.answer(
        f"💾Готово, <b>{nickname}</b>!\n\n" + showcase_text(),
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

@dp.callback_query(F.data == "dir_self")
async def cb_dir_self(call: CallbackQuery):
    await call.message.edit_text(
        SELF_INTRO_TEXT,
        parse_mode="HTML",
        reply_markup=self_subjects_kb()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("subj_"))
async def cb_subject(call: CallbackQuery):
    key = call.data.replace("subj_", "")
    subj = SELF_SUBJECTS.get(key)
    if not subj:
        await call.answer("Раздел не найден")
        return
    await call.message.edit_text(
        subj["description"],
        parse_mode="HTML",
        reply_markup=subject_detail_kb()
    )
    await call.answer()

@dp.callback_query(F.data == "dir_fun")
async def cb_dir_fun(call: CallbackQuery):
    await call.message.edit_text(
        FUN_TEXT,
        parse_mode="HTML",
        reply_markup=fun_kb()
    )
    await call.answer()

@dp.callback_query(F.data == "where_am_i")
async def cb_where_am_i(call: CallbackQuery):
    await call.message.edit_text(
        WHERE_AM_I_TEXT,
        parse_mode="HTML",
        reply_markup=where_am_i_kb()
    )
    await call.answer()

@dp.callback_query(F.data == "access")
async def cb_access(call: CallbackQuery):
    set_subscribed(call.from_user.id)
    await call.message.edit_text(
        "🖥️ <b>Добро пожаловать в BLONEVERSE💾!</b>\n\n"
        "Тебе открыты все разделы — выбирай 📼",
        parse_mode="HTML",
        reply_markup=after_payment_kb()
    )
    await call.answer()

# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    print("📹 Бот BLONEVERSE запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
