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

STICKER_WELCOME = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"
STICKER_LOBBY   = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"  # замени на другой file_id из того же пака

PAYMENT_LINK = "https://t.me/bloneverse_bot?start=pay"

# Заглушки ссылок — позже заменишь на реальные приватные каналы / плейлисты
LINKS = {
    "physics_tg":   "https://t.me/+XXXXXXXXXXXXXXXX",
    "physics_yt":   "https://youtube.com/@bloneverse",
    "math_tg":      "https://t.me/+XXXXXXXXXXXXXXXX",
    "math_yt":      "https://youtube.com/@bloneverse",
    "fun_tg":       "https://t.me/+XXXXXXXXXXXXXXXX",
    "fun_yt":       "https://youtube.com/@bloneverse",
}

# ════════════════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════════════════

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

# ════════════════════════════════════════════════════════════════════════════
# STATES
# ════════════════════════════════════════════════════════════════════════════

class Register(StatesGroup):
    waiting_username = State()

# ════════════════════════════════════════════════════════════════════════════
# KEYBOARDS — главная / витрина
# ════════════════════════════════════════════════════════════════════════════

def showcase_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⌨️ Саморазвитие", callback_data="dir_self"),
            InlineKeyboardButton(text="📺 Развлечения",  callback_data="dir_fun"),
        ],
        [InlineKeyboardButton(text="Где Я🔊", callback_data="where_am_i")],
        [InlineKeyboardButton(text=f"💳 Оплатить подписку — {SUBSCRIPTION_PRICE}", url=None, callback_data="pay_intro")],
    ])

def pay_back_kb(back_cb: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить подписку — {SUBSCRIPTION_PRICE}", callback_data="pay_intro")],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data=back_cb)],
    ])

# ── Саморазвитие (витрина, до оплаты) ─────────────────────────────────────────

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
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="showcase")],
    ])

def subject_menu_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 2 занятия",  callback_data=f"detail_{subj}_lessons")],
        [InlineKeyboardButton(text="▶️ YouTube",    callback_data=f"detail_{subj}_yt")],
        [InlineKeyboardButton(text="📡 Telegram",   callback_data=f"detail_{subj}_tg")],
        [InlineKeyboardButton(text=f"💳 Оплатить — {SUBSCRIPTION_PRICE}", callback_data="pay_intro")],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="dir_self")],
    ])

def wip_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="dir_self")],
    ])

def fun_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 Telegram", callback_data="fun_tg")],
        [InlineKeyboardButton(text="▶️ YouTube",  callback_data="fun_yt")],
        [InlineKeyboardButton(text=f"💳 Оплатить — {SUBSCRIPTION_PRICE}", callback_data="pay_intro")],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="showcase")],
    ])

def where_am_i_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Кто Я", callback_data="who_am_i")],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="showcase")],
    ])

def who_am_i_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="where_am_i")],
    ])

# ════════════════════════════════════════════════════════════════════════════
# KEYBOARDS — оплата (демо) и личный кабинет
# ════════════════════════════════════════════════════════════════════════════

def pay_intro_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить — {SUBSCRIPTION_PRICE}", callback_data="do_pay")],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="showcase")],
    ])

def cabinet_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⌨️ Саморазвитие", callback_data="cab_self"),
            InlineKeyboardButton(text="📺 Развлечения",  callback_data="cab_fun"),
        ],
    ])

def cabinet_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="cabinet")],
    ])

# ── Кабинет → Саморазвитие ────────────────────────────────────────────────────

def cab_self_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Предметные курсы", callback_data="cab_self_subjects")],
        [InlineKeyboardButton(text="⚡ Продуктивность",   callback_data="cab_self_productivity")],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="cabinet")],
    ])

def cab_subjects_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Физика",     callback_data="cab_subj_physics"),
            InlineKeyboardButton(text="📊 Математика", callback_data="cab_subj_math"),
        ],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="cab_self")],
    ])

def cab_subject_detail_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 Telegram", url=LINKS.get(f"{subj}_tg", "https://t.me/"))],
        [InlineKeyboardButton(text="▶️ YouTube",  url=LINKS.get(f"{subj}_yt", "https://youtube.com/"))],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="cab_self_subjects")],
    ])

def cab_productivity_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Цели",       callback_data="cab_prod_goals"),
            InlineKeyboardButton(text="🕳️ Хронофаги",  callback_data="cab_prod_chronophages"),
        ],
        [
            InlineKeyboardButton(text="⏳ Время",       callback_data="cab_prod_time"),
            InlineKeyboardButton(text="🔋 Энергия",     callback_data="cab_prod_energy"),
        ],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="cab_self")],
    ])

def cab_productivity_detail_kb(topic: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 Telegram", callback_data="empty_link")],
        [InlineKeyboardButton(text="▶️ YouTube",  callback_data="empty_link")],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="cab_self_productivity")],
    ])

# ── Кабинет → Развлечения ─────────────────────────────────────────────────────

def cab_fun_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎞️ Мультфильмы", callback_data="cab_fun_cartoons")],
        [InlineKeyboardButton(text="🎬 Ролики",       callback_data="cab_fun_clips")],
        [InlineKeyboardButton(text="😂 Мемы",         callback_data="cab_fun_memes")],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="cabinet")],
    ])

def cab_fun_detail_kb(topic: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 Telegram", url=LINKS.get("fun_tg", "https://t.me/"))],
        [InlineKeyboardButton(text="▶️ YouTube",  url=LINKS.get("fun_yt", "https://youtube.com/"))],
        [InlineKeyboardButton(text="🗝️ Назад", callback_data="cab_fun")],
    ])

# ════════════════════════════════════════════════════════════════════════════
# ТЕКСТЫ — общая витрина (до оплаты)
# ════════════════════════════════════════════════════════════════════════════

def showcase_text(name: str = ""):
    greeting = f"С возвращением, <b>{name}</b>! 👋\n\n" if name else ""
    return (
        f"{greeting}"
        f"<b>💾 BLONEVERSE — одна подписка, всё включено</b>\n\n"
        f"Нажми на раздел чтобы ознакомиться 🩶\n\n"
        f"⌨️ Саморазвитие · 📺 Развлечения\n\n"
        f"💳 Цена: <b>{SUBSCRIPTION_PRICE}</b>\n"
        f"🦾 Промокод <code>{PROMO_CODE}</code> — скидка {PROMO_DISCOUNT}%"
    )

SELF_INTRO_TEXT = (
    "<b>⌨️ Саморазвитие — BLONEVERSE</b>\n\n"
    "Здесь собраны направления для прокачки знаний по разным предметам 💡\n\n"
    "Каждое направление — это три уровня доступа:\n"
    "🎓 Занятия с преподавателем · ▶️ YouTube-ролики · 📡 Telegram-канал\n\n"
    "Все ролики, статьи, методички и анимации выполнены в "
    "<b>едином фирменном стиле BLONEVERSE</b> — никакой мешанины, только структура.\n\n"
    "👇 Выбери предмет:"
)

SUBJECT_MENU_TEXTS = {
    "physics": (
        "<b>🔍 Физика — BLONEVERSE</b>\n\n"
        "Выбери что тебя интересует:\n\n"
        "🎓 <b>2 занятия</b> — живые сессии с преподавателем\n"
        "▶️ <b>YouTube</b> — анимационные ролики по темам\n"
        "📡 <b>Telegram</b> — статьи, методички, файлы\n\n"
        "Всё в едином стиле BLONEVERSE 💾"
    ),
    "chemistry": (
        "<b>🧪 Химия — BLONEVERSE</b>\n\n"
        "Выбери что тебя интересует:\n\n"
        "🎓 <b>2 занятия</b> — живые сессии с преподавателем\n"
        "▶️ <b>YouTube</b> — анимационные ролики по темам\n"
        "📡 <b>Telegram</b> — статьи, методички, файлы\n\n"
        "Всё в едином стиле BLONEVERSE 💾"
    ),
    "math": (
        "<b>📊 Математика — BLONEVERSE</b>\n\n"
        "Выбери что тебя интересует:\n\n"
        "🎓 <b>2 занятия</b> — живые сессии с преподавателем\n"
        "▶️ <b>YouTube</b> — анимационные ролики по темам\n"
        "📡 <b>Telegram</b> — статьи, методички, файлы\n\n"
        "Всё в едином стиле BLONEVERSE 💾"
    ),
}

LESSONS_TEXTS = {
    "physics": (
        "<b>🎓 2 занятия с преподавателем — Физика</b>\n\n"
        "После оплаты общей подписки тебе открываются <b>2 бесплатных занятия</b> "
        "с нашим преподавателем физики.\n\n"
        "📌 Живой разбор твоих вопросов и пробелов\n"
        "📌 Объяснения через образы и анимацию\n"
        "📌 Онлайн, в удобное для тебя время\n\n"
        "Все материалы — в едином стиле BLONEVERSE 💾"
    ),
    "chemistry": (
        "<b>🎓 2 занятия с преподавателем — Химия</b>\n\n"
        "После оплаты общей подписки тебе открываются <b>2 бесплатных занятия</b> "
        "с нашим преподавателем химии.\n\n"
        "📌 Живой разбор реакций и задач\n"
        "📌 Объяснения через визуал\n"
        "📌 Онлайн, в удобное для тебя время\n\n"
        "Все материалы — в едином стиле BLONEVERSE 💾"
    ),
    "math": (
        "<b>🎓 2 занятия с преподавателем — Математика</b>\n\n"
        "После оплаты общей подписки тебе открываются <b>2 бесплатных занятия</b> "
        "с нашим преподавателем математики.\n\n"
        "📌 Разбор задач и пробелов\n"
        "📌 От простого к сложному\n"
        "📌 Онлайн, в удобное для тебя время\n\n"
        "Все материалы — в едином стиле BLONEVERSE 💾"
    ),
}

YT_TEXTS = {
    "physics": (
        "<b>▶️ YouTube — Физика</b>\n\n"
        "После оплаты подписки открывается доступ к <b>закрытым роликам на YouTube</b>.\n\n"
        "🎬 Анимационные объяснения тем\n"
        "🎬 Каждый ролик — в отдельной папке по теме\n"
        "🎬 Единый анимационный стиль BLONEVERSE\n\n"
        "📐 Только чёткая система знаний 💾"
    ),
    "chemistry": (
        "<b>▶️ YouTube — Химия</b>\n\n"
        "После оплаты подписки открывается доступ к <b>закрытым роликам на YouTube</b>.\n\n"
        "🎬 Анимационные объяснения тем\n"
        "🎬 Каждый ролик — в отдельной папке по теме\n"
        "🎬 Единый анимационный стиль BLONEVERSE\n\n"
        "📐 Только чёткая система знаний 💾"
    ),
    "math": (
        "<b>▶️ YouTube — Математика</b>\n\n"
        "После оплаты подписки открывается доступ к <b>закрытым роликам на YouTube</b>.\n\n"
        "🎬 Анимационные объяснения тем\n"
        "🎬 Каждый ролик — в отдельной папке по теме\n"
        "🎬 Единый анимационный стиль BLONEVERSE\n\n"
        "📐 Только чёткая система знаний 💾"
    ),
}

TG_TEXTS = {
    "physics": (
        "<b>📡 Telegram — Физика</b>\n\n"
        "По общей подписке открывается <b>закрытый Telegram-канал по физике</b>.\n\n"
        "📄 Статьи и объяснения тем\n"
        "📁 Методики, пособия, конспекты\n"
        "📐 Всё в едином стиле BLONEVERSE\n\n"
        "💾 Структура знаний — у тебя в кармане."
    ),
    "chemistry": (
        "<b>📡 Telegram — Химия</b>\n\n"
        "По общей подписке открывается <b>закрытый Telegram-канал по химии</b>.\n\n"
        "📄 Статьи и объяснения тем\n"
        "📁 Методики, пособия, конспекты\n"
        "📐 Всё в едином стиле BLONEVERSE\n\n"
        "💾 Структура знаний — у тебя в кармане."
    ),
    "math": (
        "<b>📡 Telegram — Математика</b>\n\n"
        "По общей подписке открывается <b>закрытый Telegram-канал по математике</b>.\n\n"
        "📄 Статьи и объяснения тем\n"
        "📁 Методики, пособия, конспекты\n"
        "📐 Всё в едином стиле BLONEVERSE\n\n"
        "💾 Структура знаний — у тебя в кармане."
    ),
    }
WIP_TEXT = (
    "<b>🛠️ Скоро в BLONEVERSE</b>\n\n"
    "Мы активно работаем над новыми направлениями 💾\n\n"
    "🔜 Новые предметы, новые анимационные ролики, расширение платформы для всего мира 🌍\n\n"
    "⌨️ Следи за обновлениями — лучшее впереди 🚀"
)

FUN_TEXT = (
    "<b>📺 Развлечения — BLONEVERSE</b>\n\n"
    "Это не просто мемы. Это отдельное направление с полноценным контентом.\n\n"
    "Развлечениям уделяется столько же внимания, сколько и обучению — "
    "здесь своя система, свой стиль, свои форматы.\n\n"
    "👇 Выбери платформу:"
)

FUN_TG_TEXT = (
    "<b>📡 Telegram — Развлечения</b>\n\n"
    "По подписке открывается <b>закрытый Telegram-канал</b> с развлекательным контентом.\n\n"
    "🎭 Мемы и юмор в фирменном стиле\n"
    "💡 Советы и интересные посты\n"
    "🎨 Единый анимационный стиль компании\n\n"
    "💾 Контент который попадает в точку — каждый день."
)

FUN_YT_TEXT = (
    "<b>▶️ YouTube — Развлечения</b>\n\n"
    "По подписке открывается доступ к <b>закрытым роликам на YouTube</b>.\n\n"
    "🎬 Анимационные мультфильмы и короткометражки\n"
    "🎬 Анимационные фильмы в едином стиле\n"
    "🎬 Каждый ролик — в своей папке, в своей теме\n\n"
    "📐 Единый стиль анимации — узнаваемо с первого кадра 💾"
)

WHERE_AM_I_TEXT = (
    "<b>Где Я🔊 — BLONEVERSE</b>\n\n"
    "Ты находишься в боте проекта <b>BLONEVERSE</b> — анимационной вселенной знаний и контента.\n\n"
    "🎬 <b>Идея компании:</b>\n"
    "Всё что мы делаем — в <b>едином анимационном стиле</b>. "
    "Ролики, статьи, методички, обложки — единая визуальная система.\n\n"
    "🏗️ <b>Структура:</b>\n"
    "• ТГ-каналы по направлениям — учёба и развлечения\n"
    "• YouTube-канал уже создан\n"
    "• Единая платформа в разработке — для всего мира 🌍\n\n"
    "🚀 <b>Цель</b> — глобальный проект, доступный каждому в мире.\n\n"
    "📡 YouTube → собственная платформа. Все вперёд 💾\n\n"
    "👤 Хочешь узнать кто за этим стоит? Нажми <b>Кто Я</b> ниже."
)

WHO_AM_I_TEXT = (
    "<b>👤 Кто Я — BLONEVERSE</b>\n\n"
    "Меня зовут создатель BLONEVERSE. Мне <b>20 лет</b>.\n\n"
    "Я строю проект с нуля — с идеи до глобальной платформы.\n\n"
    "🎯 <b>Моя цель:</b> создать идеальную структуру обучения и развлечения — "
    "где каждый ролик анимационный, каждый материал в своей папке, "
    "каждая тема в своём разделе.\n\n"
    "🎬 Каждый ролик — анимация. Каждая анимация — в едином стиле.\n"
    "📁 Каждая тема — в своей папке. Никакого хаоса.\n\n"
    "🌍 Проект создан для всего мира — начиная с YouTube, заканчивая своей платформой.\n\n"
    "💾 Я верю что структура и визуал меняют то, как люди учатся и отдыхают."
)

# ════════════════════════════════════════════════════════════════════════════
# ТЕКСТЫ — оплата (демо) и личный кабинет
# ════════════════════════════════════════════════════════════════════════════

PAY_INTRO_TEXT = (
    "<b>💳 Подписка BLONEVERSE</b>\n\n"
    "После оплаты тебя ждёт:\n\n"
    "🔐 Доступ к <b>приватным Telegram-каналам</b>\n"
    "▶️ Доступ к <b>закрытым видео на YouTube</b>\n"
    "🎓 <b>2 созвона с наставником</b>\n\n"
    f"💳 Стоимость: <b>{SUBSCRIPTION_PRICE}</b>\n"
    f"🦾 Промокод <code>{PROMO_CODE}</code> — скидка {PROMO_DISCOUNT}%\n\n"
    "👇 Нажми «Оплатить» чтобы продолжить"
)

def cabinet_text(name: str):
    return (
        f"<b>👤 Личный кабинет</b>\n\n"
        f"Твой аккаунт: <b>{name}</b>\n"
        f"Статус подписки: <b>Активна ✅</b>\n"
        f"<i>(после окончания месяца нужно будет снова оплатить подписку)</i>\n\n"
        f"👇 Выбери направление:"
    )

CAB_SELF_TEXT = (
    "<b>⌨️ Саморазвитие</b>\n\n"
    "Здесь будет структура по направлению: обучение.\n\n"
    "👇 Выбери раздел:"
)

CAB_SUBJECTS_TEXT = (
    "<b>📚 Предметные курсы</b>\n\n"
    "Эти курсы содержат несколько направлений.\n\n"
    "👇 Выбери предмет:"
)

CAB_SUBJECT_DETAIL_TEXTS = {
    "physics": "<b>🔍 Физика</b>\n\nКраткий обзор материалов по физике — видео и канал ниже.",
    "math":    "<b>📊 Математика</b>\n\nКраткий обзор материалов по математике — видео и канал ниже.",
}

CAB_PRODUCTIVITY_TEXT = (
    "<b>⚡ Продуктивность</b>\n\n"
    "Курс затрагивает темы:\n\n"
    "👇 Выбери тему:"
)

CAB_PRODUCTIVITY_DETAIL_TEXTS = {
    "goals":          "<b>🎯 Цели</b>\n\nКак ставить цели и доходить до результата — кратко о теме.",
    "chronophages":   "<b>🕳️ Хронофаги</b>\n\nЧто крадёт твоё время и как это остановить — кратко о теме.",
    "time":           "<b>⏳ Время</b>\n\nКак управлять временем эффективно — кратко о теме.",
    "energy":         "<b>🔋 Энергия</b>\n\nКак управлять своей энергией и не выгорать — кратко о теме.",
}

CAB_FUN_TEXT = (
    "<b>📺 Развлечения</b>\n\n"
    "Здесь будет структура с анимационным контентом.\n\n"
    "👇 Выбери раздел:"
)

CAB_FUN_DETAIL_TEXTS = {
    "cartoons": "<b>🎞️ Мультфильмы</b>\n\nАнимационные мультфильмы в едином стиле BLONEVERSE — кратко о разделе.",
    "clips":    "<b>🎬 Ролики</b>\n\nКороткие анимационные ролики — кратко о разделе.",
    "memes":    "<b>😂 Мемы</b>\n\nМемы и юмор в фирменном стиле — кратко о разделе.",
}

# ════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ════════════════════════════════════════════════════════════════════════════

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user:
        await message.answer_sticker(STICKER_LOBBY)
        await message.answer(showcase_text(user[1]), parse_mode="HTML", reply_markup=showcase_kb())
        return
    await message.answer_sticker(STICKER_WELCOME)
    await message.answer(
        "<b>Добро пожаловать в BLONEVERSE💾</b>\n\n"
        "Одна вселенная📱.\n"
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
        f"💾 Готово, <b>{nickname}</b>!\n\n" + showcase_text(),
        parse_mode="HTML",
        reply_markup=showcase_kb()
    )

@dp.callback_query(F.data == "showcase")
async def cb_showcase(call: CallbackQuery):
    user = get_user(call.from_user.id)
    name = user[1] if user else ""
    await call.message.edit_text(showcase_text(name), parse_mode="HTML", reply_markup=showcase_kb())
    await call.answer()

# ── Саморазвитие (витрина, до оплаты) ─────────────────────────────────────────

@dp.callback_query(F.data == "dir_self")
async def cb_dir_self(call: CallbackQuery):
    await call.message.edit_text(SELF_INTRO_TEXT, parse_mode="HTML", reply_markup=self_subjects_kb())
    await call.answer()

@dp.callback_query(F.data.startswith("subj_"))
async def cb_subject(call: CallbackQuery):
    key = call.data.replace("subj_", "")
    if key == "wip":
        await call.message.edit_text(WIP_TEXT, parse_mode="HTML", reply_markup=wip_kb())
        await call.answer()
        return
    text = SUBJECT_MENU_TEXTS.get(key)
    if not text:
        await call.answer("Раздел не найден")
        return
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=subject_menu_kb(key))
    await call.answer()

@dp.callback_query(F.data.startswith("detail_"))
async def cb_detail(call: CallbackQuery):
    parts = call.data.split("_", 2)
    if len(parts) != 3:
        await call.answer("Ошибка")
        return
    _, subj, kind = parts
    if kind == "lessons":
        text = LESSONS_TEXTS.get(subj, "Информация скоро появится.")
    elif kind == "yt":
        text = YT_TEXTS.get(subj, "Информация скоро появится.")
    elif kind == "tg":
        text = TG_TEXTS.get(subj, "Информация скоро появится.")
    else:
        await call.answer("Неизвестный раздел")
        return
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=pay_back_kb(f"subj_{subj}"))
    await call.answer()

# ── Развлечения (витрина, до оплаты) ──────────────────────────────────────────

@dp.callback_query(F.data == "dir_fun")
async def cb_dir_fun(call: CallbackQuery):
    await call.message.edit_text(FUN_TEXT, parse_mode="HTML", reply_markup=fun_menu_kb())
    await call.answer()

@dp.callback_query(F.data == "fun_tg")
async def cb_fun_tg(call: CallbackQuery):
    await call.message.edit_text(FUN_TG_TEXT, parse_mode="HTML", reply_markup=pay_back_kb("dir_fun"))
    await call.answer()

@dp.callback_query(F.data == "fun_yt")
async def cb_fun_yt(call: CallbackQuery):
    await call.message.edit_text(FUN_YT_TEXT, parse_mode="HTML", reply_markup=pay_back_kb("dir_fun"))
    await call.answer()

# ── Где Я / Кто Я ─────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "where_am_i")
async def cb_where_am_i(call: CallbackQuery):
    await call.message.edit_text(WHERE_AM_I_TEXT, parse_mode="HTML", reply_markup=where_am_i_kb())
    await call.answer()

@dp.callback_query(F.data == "who_am_i")
async def cb_who_am_i(call: CallbackQuery):
    await call.message.edit_text(WHO_AM_I_TEXT, parse_mode="HTML", reply_markup=who_am_i_kb())
    await call.answer()

# ── Оплата (демо) ──────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "pay_intro")
async def cb_pay_intro(call: CallbackQuery):
    await call.message.edit_text(PAY_INTRO_TEXT, parse_mode="HTML", reply_markup=pay_intro_kb())
    await call.answer()

@dp.callback_query(F.data == "do_pay")
async def cb_do_pay(call: CallbackQuery):
    # ──────────────────────────────────────────────────────────────────────
    # TODO: здесь будет интеграция реальной платёжной системы
    # (например ЮKassa / Telegram Payments / CryptoBot).
    # Сейчас это ДЕМО-режим: оплата считается успешной сразу,
    # без проверки реального платежа.
    #
    # Когда подключишь платёжку:
    # 1. Создай инвойс / ссылку на оплату здесь
    # 2. Дождись вебхука/колбэка об успешной оплате
    # 3. Только после этого вызывай set_subscribed() и открывай кабинет
    # ──────────────────────────────────────────────────────────────────────
    set_subscribed(call.from_user.id)
    user = get_user(call.from_user.id)
    name = user[1] if user else call.from_user.full_name
    await call.message.edit_text(
        "✅ <b>Оплата прошла успешно! (демо-режим)</b>\n\n"
        "Добро пожаловать в личный кабинет 💾",
        parse_mode="HTML"
    )
    await call.message.answer(cabinet_text(name), parse_mode="HTML", reply_markup=cabinet_kb())
    await call.answer()

@dp.callback_query(F.data == "empty_link")
async def cb_empty_link(call: CallbackQuery):
    await call.answer("Скоро здесь появится ссылка 🚧", show_alert=True)

# ── Личный кабинет ─────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "cabinet")
async def cb_cabinet(call: CallbackQuery):
    user = get_user(call.from_user.id)
    name = user[1] if user else call.from_user.full_name
    await call.message.edit_text(cabinet_text(name), parse_mode="HTML", reply_markup=cabinet_kb())
    await call.answer()

# ── Кабинет → Саморазвитие ────────────────────────────────────────────────────

@dp.callback_query(F.data == "cab_self")
async def cb_cab_self(call: CallbackQuery):
    await call.message.edit_text(CAB_SELF_TEXT, parse_mode="HTML", reply_markup=cab_self_kb())
    await call.answer()

@dp.callback_query(F.data == "cab_self_subjects")
async def cb_cab_self_subjects(call: CallbackQuery):
    await call.message.edit_text(CAB_SUBJECTS_TEXT, parse_mode="HTML", reply_markup=cab_subjects_kb())
    await call.answer()

@dp.callback_query(F.data.startswith("cab_subj_"))
async def cb_cab_subject_detail(call: CallbackQuery):
    key = call.data.replace("cab_subj_", "")
    text = CAB_SUBJECT_DETAIL_TEXTS.get(key, "Информация скоро появится.")
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=cab_subject_detail_kb(key))
    await call.answer()

@dp.callback_query(F.data == "cab_self_productivity")
async def cb_cab_self_productivity(call: CallbackQuery):
    await call.message.edit_text(CAB_PRODUCTIVITY_TEXT, parse_mode="HTML", reply_markup=cab_productivity_kb())
    await call.answer()

@dp.callback_query(F.data.startswith("cab_prod_"))
async def cb_cab_productivity_detail(call: CallbackQuery):
    key = call.data.replace("cab_prod_", "")
    text = CAB_PRODUCTIVITY_DETAIL_TEXTS.get(key, "Информация скоро появится.")
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=cab_productivity_detail_kb(key))
    await call.answer()

# ── Кабинет → Развлечения ─────────────────────────────────────────────────────

@dp.callback_query(F.data == "cab_fun")
async def cb_cab_fun(call: CallbackQuery):
    await call.message.edit_text(CAB_FUN_TEXT, parse_mode="HTML", reply_markup=cab_fun_kb())
    await call.answer()

@dp.callback_query(F.data.startswith("cab_fun_"))
async def cb_cab_fun_detail(call: CallbackQuery):
    key = call.data.replace("cab_fun_", "")
    text = CAB_FUN_DETAIL_TEXTS.get(key, "Информация скоро появится.")
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=cab_fun_detail_kb(key))
    await call.answer()

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    print("📹 Бот BLONEVERSE запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
