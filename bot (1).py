import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN = "8862540650:AAG374nrX0fY7R4tt1DyfPSWCV2H9tps7oo"
PROMO_CODE = "ПАПКА"
PROMO_DISCOUNT = 90
SUBSCRIPTION_PRICE = "499₽/мес"
GULYA_STICKER = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"
PAYMENT_LINK = "https://t.me/bloneverse_bot?start=pay"  # заменишь на реальную ссылку

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
            "⚛️ *Физика — BLONEVERSE*\n\n"
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
            "🧠 *Саморазвитие — BLONEVERSE*\n\n"
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
            "😄 *Развлечения — BLONEVERSE*\n\n"
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
            "🔭 *Научпоп — BLONEVERSE*\n\n"
            "Наука простым языком. Без воды.\n\n"
            "📌 Что тебя ждёт:\n"
            "• Интересные факты и открытия\n"
            "• Разборы сложных тем доступно\n"
            "• Контент который расширяет кругозор"
        ),
    },
}

REGISTER = 1
users = {}

logging.basicConfig(level=logging.INFO)

# ─── KEYBOARDS ────────────────────────────────────────────────────────────────

def showcase_keyboard():
    """Витрина — кнопки направлений + оплата"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚛️ Физика", callback_data="dir_physics"),
            InlineKeyboardButton("🧠 Саморазвитие", callback_data="dir_self"),
        ],
        [
            InlineKeyboardButton("😄 Развлечения", callback_data="dir_fun"),
            InlineKeyboardButton("🔭 Научпоп", callback_data="dir_science"),
        ],
        [InlineKeyboardButton(f"💳 Оплатить подписку — {SUBSCRIPTION_PRICE}", url=PAYMENT_LINK)],
    ])

def direction_keyboard():
    """Внутри направления — оплата + назад"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 Оплатить подписку — {SUBSCRIPTION_PRICE}", url=PAYMENT_LINK)],
        [InlineKeyboardButton("◀️ Назад", callback_data="showcase")],
    ])

def after_payment_keyboard():
    """После оплаты — ссылки на все приватные каналы"""
    buttons = [
        [InlineKeyboardButton(d["name"], url=PRIVATE_CHANNELS[k])]
        for k, d in DIRECTIONS.items()
    ]
    return InlineKeyboardMarkup(buttons)

# ─── HELPERS ──────────────────────────────────────────────────────────────────

async def send_with_sticker(update, context, text, reply_markup=None):
    chat_id = update.effective_chat.id
    await context.bot.send_sticker(chat_id=chat_id, sticker=GULYA_STICKER)
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

def showcase_text():
    return (
        "📁 *BLONEVERSE — одна подписка, всё включено*\n\n"
        "Нажми на раздел чтобы ознакомиться 👇\n\n"
        "⚛️ Физика · 🧠 Саморазвитие\n"
        "😄 Развлечения · 🔭 Научпоп\n\n"
        f"💳 Цена: *{SUBSCRIPTION_PRICE}*\n"
        f"🎁 Промокод `{PROMO_CODE}` — скидка {PROMO_DISCOUNT}%"
    )

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in users:
        name = users[user_id]["username"]
        await send_with_sticker(
            update, context,
            f"С возвращением, *{name}*! 👋\n\n" + showcase_text(),
            reply_markup=showcase_keyboard()
        )
        return ConversationHandler.END

    await send_with_sticker(
        update, context,
        "📁 *Добро пожаловать в BLONEVERSE*\n\n"
        "Одна вселенная. Разные миры.\n"
        "Наука. Саморазвитие. Развлечения.\n\n"
        "Для начала — напиши свой никнейм:"
    )
    return REGISTER

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nickname = update.message.text.strip()

    if len(nickname) < 2:
        await send_with_sticker(update, context, "Никнейм слишком короткий, попробуй ещё раз:")
        return REGISTER

    users[user_id] = {"username": nickname, "subscribed": False}

    await send_with_sticker(
        update, context,
        f"✅ Готово, *{nickname}*!\n\n" + showcase_text(),
        reply_markup=showcase_keyboard()
    )
    return ConversationHandler.END

async def showcase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат на витрину"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        showcase_text(),
        parse_mode="Markdown",
        reply_markup=showcase_keyboard()
    )

async def direction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открывает описание направления"""
    query = update.callback_query
    await query.answer()
    key = query.data.replace("dir_", "")
    d = DIRECTIONS[key]

    await query.edit_message_text(
        d["description"],
        parse_mode="Markdown",
        reply_markup=direction_keyboard()
    )

async def access_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """После оплаты — даёт ссылки на все каналы"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎉 *Добро пожаловать в BLONEVERSE!*\n\n"
        "Тебе открыты все разделы — выбирай 👇",
        parse_mode="Markdown",
        reply_markup=after_payment_keyboard()
    )

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={REGISTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register)]},
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(showcase_handler, pattern="^showcase$"))
    app.add_handler(CallbackQueryHandler(direction_handler, pattern="^dir_"))
    app.add_handler(CallbackQueryHandler(access_handler, pattern="^access$"))

    print("✅ Бот BLONEVERSE запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
