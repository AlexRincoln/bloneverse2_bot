import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN = "8939981008:AAGODrnmp9qNNs3gPRxpkKl8IUlzX0Sk21o"
PROMO_CODE = "ПАПКА"
PROMO_DISCOUNT = 90
SUBSCRIPTION_PRICE = "10 дол/мес"

STICKER_WELCOME = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"
STICKER_LOBBY   = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"

FREE_LIMIT_TEXT = "\n\n*Учтите, здесь собрана малая часть всего контента. Чтобы получить доступ ко всему контенту — оплатите подписку.*"

# ─── DATABASE ─────────────────────────────────────────────────────────────────
DB_PATH = "database.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                nickname TEXT,
                is_paid INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def add_user(user_id: int, username: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()

def update_nickname(user_id: int, nickname: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (user_id, nickname))
        conn.commit()

def set_premium(user_id: int, status: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_paid = ? WHERE user_id = ?", (status, user_id))
        conn.commit()

def get_user(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nickname, is_paid FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

# ─── STATES ───────────────────────────────────────────────────────────────────
class Registration(StatesGroup):
    waiting_for_nickname = State()
# ─── KEYBOARDS ────────────────────────────────────────────────────────────────
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="БЕСПЛАТНОЕ", callback_data="mode_free")],
        [InlineKeyboardButton(text="ПЛАТНОЕ", callback_data="mode_paid")]
    ])

def free_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="САМОРАЗВИТИЕ", callback_data="free_self_dev")],
        [InlineKeyboardButton(text="РАЗВЛЕЧЕНИЯ", callback_data="free_entertainment")],
        [InlineKeyboardButton(text="НАЗАД", callback_data="to_main")]
    ])

def pay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ОПЛАТИТЬ", callback_data="pay_action")]
    ])

def check_pay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я оплатил (Эмуляция)", callback_data="pay_success")]
    ])

def cabinet_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛИЧНЫЙ КАБИНЕТ", callback_data="go_cabinet")]
    ])

def paid_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="САМОРАЗВИТИЕ", callback_data="paid_self_dev")],
        [InlineKeyboardButton(text="РАЗВЛЕЧЕНИЯ", callback_data="paid_entertainment")],
        [InlineKeyboardButton(text="ЛИНЕЙНЫЙ ПЛАН", callback_data="linear_plan")]
    ])

def linear_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="СТРУКТУРА", callback_data="structure")],
        [InlineKeyboardButton(text="НАЗАД", callback_data="go_cabinet")]
    ])

def structure_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="САМОРАЗВИТИЕ", callback_data="paid_self_dev")],
        [InlineKeyboardButton(text="РАЗВЛЕЧЕНИЯ", callback_data="paid_entertainment")],
        [InlineKeyboardButton(text="ЛИЧНЫЙ КАБИНЕТ", callback_data="go_cabinet")]
    ])

def self_dev_kb(is_paid: bool):
    prefix = "paid_" if is_paid else "free_"
    kb = [
        [InlineKeyboardButton(text="ПРОДУКТИВНОСТЬ", callback_data=f"{prefix}prod")],
        [InlineKeyboardButton(text="ОБУЧЕНИЕ", callback_data=f"{prefix}edu")]
    ]
    if is_paid:
        kb.append([InlineKeyboardButton(text="НАЗАД", callback_data="structure")])
    else:
        kb.append([InlineKeyboardButton(text="НАЗАД", callback_data="mode_free")])
        kb.append([InlineKeyboardButton(text="ОПЛАТИТЬ ПОДПИСКУ", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def productivity_kb(is_paid: bool):
    prefix = "paid_" if is_paid else "free_"
    kb = [
        [InlineKeyboardButton(text="БИЗНЕС", callback_data=f"{prefix}biz")],
        [InlineKeyboardButton(text="УЧЕБА", callback_data=f"{prefix}study")]
    ]
    back_target = f"{prefix}self_dev"
    kb.append([InlineKeyboardButton(text="НАЗАД", callback_data=back_target)])
    if not is_paid:
        kb.append([InlineKeyboardButton(text="ОПЛАТИТЬ ПОДПИСКУ", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def biz_kb(is_paid: bool):
    kb = []
    if is_paid:
        kb.append([InlineKeyboardButton(text="ЛИЧНЫЙ КАБИНЕТ", callback_data="go_cabinet")])
        kb.append([InlineKeyboardButton(text="НАЗАД", callback_data="paid_prod")])
    else:
        kb.append([InlineKeyboardButton(text="НАЗАД", callback_data="free_prod")])
        kb.append([InlineKeyboardButton(text="ОПЛАТИТЬ ПОДПИСКУ", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def study_kb(is_paid: bool):
    prefix = "paid_" if is_paid else "free_"
    kb = [
        [InlineKeyboardButton(text="ФИЗИКА", callback_data=f"{prefix}physics")],
        [InlineKeyboardButton(text="МАТЕМАТИКА", callback_data=f"{prefix}math")]
    ]
    back_target = f"{prefix}prod"
    kb.append([InlineKeyboardButton(text="НАЗАД", callback_data=back_target)])
    if not is_paid:
        kb.append([InlineKeyboardButton(text="ОПЛАТИТЬ ПОДПИСКУ", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def content_back_kb(is_paid: bool, current_section_back: str):
    kb = []
    if is_paid:
        kb.append([InlineKeyboardButton(text="ЛИЧНЫЙ КАБИНЕТ", callback_data="go_cabinet")])
    kb.append([InlineKeyboardButton(text="НАЗАД", callback_data=current_section_back)])
    if not is_paid:
        kb.append([InlineKeyboardButton(text="ОПЛАТИТЬ ПОДПИСКУ", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer_sticker(STICKER_WELCOME)
    await message.answer(
        "Приветствуем вас. Я *Alex*. Вы находитесь на Telegram платформе *ONEVERSE*.\n\n"
        "Чтобы продолжить, *ВВЕДИТЕ СВОЙ НИК В TELEGRAM*."
    )
    await state.set_state(Registration.waiting_for_nickname)

@router.message(Registration.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    nickname = message.text
    update_nickname(message.from_user.id, nickname)
    await state.clear()
    
    await message.answer(
        "Эта платформа имеет два направления: *ПЛАТНОЕ/БЕСПЛАТНОЕ*.\n"
        "Выбирайте направление, с которым хотите ознакомиться.",
        reply_markup=main_menu_kb()
    )

@router.callback_query(F.data == "to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "Эта платформа имеет два направления: *ПЛАТНОЕ/БЕСПЛАТНОЕ*.\n"
        "Выбирайте направление, с которым хотите ознакомиться.",
        reply_markup=main_menu_kb()
    )

# ─── ВЕТКА БЕСПЛАТНОГО НАПРАВЛЕНИЯ ──────────────────────────────────────────
@router.callback_query(F.data == "mode_free")
async def free_mode(callback: CallbackQuery):
    await callback.message.edit_text(
        "Хорошо. На этом направлении имеется немного стилизованного контента. "
        "Выбирайте, что вам по душе:",
        reply_markup=free_menu_kb()
    )

@router.callback_query(F.data == "free_self_dev")
async def free_self_dev_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Здесь можно прокачать себя. Сейчас доступны такие направления:" + FREE_LIMIT_TEXT,
        reply_markup=self_dev_kb(is_paid=False)
    )

@router.callback_query(F.data == "free_entertainment")
async def free_ent_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "_Раздел Развлечения (Бесплатно)_\nЗдесь будут развлекательные материалы." + FREE_LIMIT_TEXT,
        reply_markup=content_back_kb(is_paid=False, current_section_back="mode_free")
    )

@router.callback_query(F.data == "free_prod")
async def free_prod_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Здесь можно прокачать свою внутреннюю систему. Прокачать ментальное состояние. "
        "Научиться мечтать. Нажимай. Что тебя интересует больше всего?" + FREE_LIMIT_TEXT,
        reply_markup=productivity_kb(is_paid=False)
    )

@router.callback_query(F.data == "free_biz")
async def free_biz_handler(callback: CallbackQuery):
    # МЕСТО ДЛЯ БЕСПЛАТНОГО ВИДЕО (БИЗНЕС) БЕЗ СОРТИРОВКИ
    await callback.message.edit_text(
        "В этом разделе научим добывать тебя первые деньги. Смотри ролики по порядку. Прокачивай себя." + FREE_LIMIT_TEXT,
        reply_markup=biz_kb(is_paid=False)
    )

@router.callback_query(F.data == "free_edu")
async def free_edu_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "В этом разделе у нас есть несколько направлений. Здесь мы подготовим тебя к экзаменам. "
        "Смотри все по порядку. Скачивай полезные материалы." + FREE_LIMIT_TEXT,
        reply_markup=study_kb(is_paid=False)
    )

@router.callback_query(F.data == "free_physics")
async def free_physics_handler(callback: CallbackQuery):
    # МЕСТО ДЛЯ БЕСПЛАТНЫХ ССЫЛОК НА ЮТУБ (ФИЗИКА)
    await callback.message.edit_text(
        "Здесь собран контент по физике. Все в едином стиле. Смотри все по порядку. Главное — понимание." + FREE_LIMIT_TEXT,
        reply_markup=content_back_kb(is_paid=False, current_section_back="free_edu")
    )

@router.callback_query(F.data == "free_math")
async def free_math_handler(callback: CallbackQuery):
    # МЕСТО ДЛЯ БЕСПЛАТНЫХ ССЫЛОК НА ЮТУБ (МАТЕМАТИКА)
    await callback.message.edit_text(
        "Здесь собран контент по математике. Все в едином стиле. Смотри все по порядку. Главное — понимание." + FREE_LIMIT_TEXT,
        reply_markup=content_back_kb(is_paid=False, current_section_back="free_edu")
    )

# ─── ВЕТКА ПЛАТНОГО НАПРАВЛЕНИЯ И ОПЛАТЫ ────────────────────────────────────
@router.callback_query(F.data == "mode_paid")
async def paid_mode(callback: CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if user_data and user_data[1] == 1:
        await go_cabinet_page(callback)
        return

    await callback.message.edit_text(
        "Хорошо. Вам будет доступен весь стилизованный контент. "
        "Чтобы продолжить, вам необходимо произвести оплату. Единая помесячная подписка.",
        reply_markup=pay_kb()
    )

@router.callback_query(F.data == "pay_action")
async def pay_action_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Стоимость подписки: *{SUBSCRIPTION_PRICE}*.\n\n"
        "🔗 [ССЫЛКА НА ОПЛАТУ (ПУСТЫШКА)](https://example.com)\n\n"
        "Осталось место для интеграции реальной платежной системы.",
        reply_markup=check_pay_kb()
    )

@router.callback_query(F.data == "pay_success")
async def pay_success_handler(callback: CallbackQuery):
    set_premium(callback.from_user.id, 1)
    await callback.message.edit_text(
        "Ваша подписка оплачена. Нажимайте *ПЕРЕЙТИ В ЛИЧНЫЙ КАБИНЕТ*.",
        reply_markup=cabinet_kb()
    )

async def go_cabinet_page(callback: CallbackQuery):
    await callback.message.edit_text(
        "Ваш *личный кабинет*. Отсюда будет доступ ко всему контенту. "
        "Путешествие по папкам. Находите нужные для себя видео и статьи. "
        "Либо можете просто нажать — линейный план.",
        reply_markup=paid_menu_kb()
    )

@router.callback_query(F.data == "go_cabinet")
async def go_cabinet_callback(callback: CallbackQuery):
    await go_cabinet_page(callback)

# ─── КОНТЕНТ ДЛЯ ПЛАТНОЙ ПОДПИСКИ ──────────────────────────────────────────
@router.callback_query(F.data == "linear_plan")
async def linear_plan_handler(callback: CallbackQuery):
    # СЮДА МОЖНО ВСТАВИТЬ ОТПРАВКУ ВИДЕО НАПРЯМУЮ: await callback.message.answer_video(video="file_id")
    await callback.message.edit_text(
        "Здесь будет весь контент без сортировки. Просто по порядку. Смотрите и изучайте.\n\n"
        "_[Место для видео, которые вы будете заливать прямо в Telegram]_",
        reply_markup=linear_kb()
    )

@router.callback_query(F.data == "structure")
async def structure_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Вы находитесь на промежуточной странице. Здесь можно выбрать — какой раздел вам интересен.",
        reply_markup=structure_kb()
    )

@router.callback_query(F.data == "paid_self_dev")
async def paid_self_dev_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Здесь можно прокачать себя. Сейчас доступны такие направления:",
        reply_markup=self_dev_kb(is_paid=True)
    )

@router.callback_query(F.data == "paid_entertainment")
async def paid_ent_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "_Раздел Развлечения (Платный)_\nЗдесь находится полный развлекательный контент.",
        reply_markup=content_back_kb(is_paid=True, current_section_back="structure")
    )

@router.callback_query(F.data == "paid_prod")
async def paid_prod_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Здесь можно прокачать свою внутреннюю систему. Прокачать ментальное состояние. "
        "Научиться мечтать. Нажимай. Что тебя интересует больше всего?",
        reply_markup=productivity_kb(is_paid=True)
    )

@router.callback_query(F.data == "paid_biz")
async def paid_biz_handler(callback: CallbackQuery):
    # МЕСТО ДЛЯ ПЛАТНЫХ ВИДЕО ПО БИЗНЕСУ ПО ПОРЯДКУ
    await callback.message.edit_text(
        "В этом разделе научим добывать тебя первые деньги. Смотри ролики по порядку. Прокачивай себя.\n\n"
        "_[Место для видео по порядку для Бизнеса]_",
        reply_markup=biz_kb(is_paid=True)
    )

@router.callback_query(F.data == "paid_edu")
async def paid_edu_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "В этом разделе у нас есть несколько направлений. Здесь мы подготовим тебя к экзаменам. "
        "Смотри все по порядку. Скачивай полезные материалы.",
        reply_markup=study_kb(is_paid=True)
    )

@router.callback_query(F.data == "paid_physics")
async def paid_physics_handler(callback: CallbackQuery):
    # МЕСТО ДЛЯ ССЫЛОК НА ПЛАТНЫЕ ВИДЕО С ЮТУБА (ФИЗИКА)
    await callback.message.edit_text(
        "Здесь собран контент по физике. Все в едином стиле. Смотри все по порядку. Главное — понимание.\n\n"
        "*Ссылки на YouTube (Физика):*\n"
        "1. [Тема 1 — Введение](https://youtube.com/...)\n"
        "2. [Тема 2 — Практика](https://youtube.com/...)",
        reply_markup=content_back_kb(is_paid=True, current_section_back="paid_edu")
    )

@router.callback_query(F.data == "paid_math")
async def paid_math_handler(callback: CallbackQuery):
    # МЕСТО ДЛЯ ССЫЛОК НА ПЛАТНЫЕ ВИДЕО С ЮТУБА (МАТЕМАТИКА)
    await callback.message.edit_text(
        "Здесь собран контент по математике. Все в едином стиле. Смотри все по порядку. Главное — понимание.\n\n"
        "*Ссылки на YouTube (Математика):*\n"
        "1. [Тема 1 — Алгебра](https://youtube.com/...)\n"
        "2. [Тема 2 — Геометрия](https://youtube.com/...)",
        reply_markup=content_back_kb(is_paid=True, current_section_back="paid_edu")
    )

# ─── ЗАПУСК БОТА ──────────────────────────────────────────────────────────────
async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    
    bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
