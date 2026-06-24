import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN = "8889052149:AAHQ3LK3KRLVezT96kO907jyHp4hSnQikDs"
PROMO_CODE = "ПАПКА"
PROMO_DISCOUNT = 90
SUBSCRIPTION_PRICE = "10 дол/мес"

# Стикер для Личного кабинета и Старта
STICKER_WELCOME = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"
STICKER_LOBBY   = "CAACAgIAAxkBAzmjtGoymMPPZt9rczW78Lv8ybc-Uz79AAIlHwACGSjRSnHdZJ9l8StePAQ"

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

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="& БЕСПЛАТНОЕ @", callback_data="mode_free")],
        [InlineKeyboardButton(text="# ПЛАТНОЕ °", callback_data="mode_paid")]
    ])

def free_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="√ САМОРАЗВИТИЕ §", callback_data="free_self_dev")],
        [InlineKeyboardButton(text="∆ РАЗВЛЕЧЕНИЯ *", callback_data="free_entertainment")],
        [InlineKeyboardButton(text="« НАЗАД", callback_data="to_main")]
    ])

def pay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="√ ОПЛАТИТЬ §", callback_data="pay_action")]
    ])

def check_pay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="∆ Я оплатил (Эмуляция)", callback_data="pay_success")]
    ])

def cabinet_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ ЛИЧНЫЙ КАБИНЕТ ⭐", callback_data="go_cabinet")]
    ])

def paid_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="√ САМОРАЗВИТИЕ §", callback_data="paid_self_dev")],
        [InlineKeyboardButton(text="∆ РАЗВЛЕЧЕНИЯ *", callback_data="paid_entertainment")],
        [InlineKeyboardButton(text="# ЛИНЕЙНЫЙ ПЛАН &", callback_data="linear_plan")]
    ])

def linear_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📹 Физика: Фанатская Анимация", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [InlineKeyboardButton(text="📐 Математика: Фанатская Анимация", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [InlineKeyboardButton(text="🎙️ £РЕПЕРЫ£: Фанатская Анимация", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [InlineKeyboardButton(text="🏎️ €ТАЧКИ€: Фанатская Анимация", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [InlineKeyboardButton(text="🏡 $ВИЛЫ$: Фанатская Анимация", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [InlineKeyboardButton(text="📱 БЛОГЕРЫ: Повторение роликов", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [InlineKeyboardButton(text="🎬 ФИЛЬМЫ: Создание в Blender", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [InlineKeyboardButton(text="🎮 ИГРЫ: По мотивам игр", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [InlineKeyboardButton(text="« НАЗАД В КАБИНЕТ", callback_data="go_cabinet")]
    ])

def self_dev_kb(is_paid: bool):
    prefix = "paid_" if is_paid else "free_"
    kb = [
        [InlineKeyboardButton(text="√ ОБУЧЕНИЕ §", callback_data=f"{prefix}edu")],
        [InlineKeyboardButton(text="∆ БОГАТСТВО #", callback_data=f"{prefix}wealth")]
    ]
    if is_paid:
        kb.append([InlineKeyboardButton(text="« НАЗАД", callback_data="go_cabinet")])
    else:
        kb.append([InlineKeyboardButton(text="« НАЗАД", callback_data="mode_free")])
        kb.append([InlineKeyboardButton(text="° ОПЛАТИТЬ ПОДПИСКУ √", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def edu_kb(is_paid: bool):
    prefix = "paid_" if is_paid else "free_"
    kb = [
        [InlineKeyboardButton(text="& ФИЗИКА @", callback_data=f"{prefix}physics")],
        [InlineKeyboardButton(text="# МАТЕМАТИКА °", callback_data=f"{prefix}math")]
    ]
    kb.append([InlineKeyboardButton(text="« НАЗАД", callback_data=f"{prefix}self_dev")])
    if not is_paid:
        kb.append([InlineKeyboardButton(text="° ОПЛАТИТЬ ПОДПИСКУ √", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def wealth_kb(is_paid: bool):
    prefix = "paid_" if is_paid else "free_"
    kb = [
        [InlineKeyboardButton(text="£ РЕПЕРЫ £", callback_data=f"{prefix}rappers")],
        [InlineKeyboardButton(text="€ ТАЧКИ €", callback_data=f"{prefix}cars")],
        [InlineKeyboardButton(text="$ ВИЛЫ $", callback_data=f"{prefix}villas")]
    ]
    kb.append([InlineKeyboardButton(text="« НАЗАД", callback_data=f"{prefix}self_dev")])
    if not is_paid:
        kb.append([InlineKeyboardButton(text="° ОПЛАТИТЬ ПОДПИСКУ √", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def entertainment_kb(is_paid: bool):
    prefix = "paid_" if is_paid else "free_"
    kb = [
        [InlineKeyboardButton(text="@ БЛОГЕРЫ &", callback_data=f"{prefix}bloggers")],
        [InlineKeyboardButton(text="° ФИЛЬМЫ #", callback_data=f"{prefix}movies")],
        [InlineKeyboardButton(text="§ ИГРЫ ∆", callback_data=f"{prefix}games")]
    ]
    if is_paid:
        kb.append([InlineKeyboardButton(text="« НАЗАД", callback_data="go_cabinet")])
    else:
        kb.append([InlineKeyboardButton(text="« НАЗАД", callback_data="mode_free")])
        kb.append([InlineKeyboardButton(text="° ОПЛАТИТЬ ПОДПИСКУ √", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def final_content_kb(is_paid: bool, back_target: str):
    kb = [[InlineKeyboardButton(text="📹 Смотреть ролик на YouTube", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")]]
    if is_paid:
        kb.append([InlineKeyboardButton(text="⚡ ЛИЧНЫЙ КАБИНЕТ ⭐", callback_data="go_cabinet")])
    kb.append([InlineKeyboardButton(text="« НАЗАД", callback_data=back_target)])
    if not is_paid:
        kb.append([InlineKeyboardButton(text="° ОПЛАТИТЬ ПОДПИСКУ √", callback_data="mode_paid")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer_sticker(STICKER_WELCOME)
    await message.answer(
        "&@#°√§∆ приветствуем вас\. Я *Alex*\. Вы находитесь на платформе *ONEVERSE*\.\n\n"
        "Чтобы продолжить, *ВВЕДИТЕ СВОЙ НИК В TELEGRAM*\."
    )
    await state.set_state(Registration.waiting_for_nickname)

@router.message(Registration.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    nickname = message.text
    update_nickname(message.from_user.id, nickname)
    await state.clear()
    
    await message.answer(
        "\#°§ *Эта платформа имеет два направления: ПЛАТНОЕ/БЕСПЛАТНОЕ\.*\n"
        "_Выбирайте направление, с которым хотите ознакомиться\._",
        reply_markup=main_menu_kb()
    )

@router.callback_query(F.data == "to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "\#°§ *Эта платформа имеет два направления: ПЛАТНОЕ/БЕСПЛАТНОЕ\.*\n"
        "_Выбирайте направление, с которым хотите ознакомиться\._",
        reply_markup=main_menu_kb()
    )

# ─── ВЕТКА БЕСПЛАТНОГО НАПРАВЛЕНИЯ ──────────────────────────────────────────
@router.callback_query(F.data == "mode_free")
async def free_mode(callback: CallbackQuery):
    await callback.message.edit_text(
        "&@# *Вы выбрали бесплатное направление\.* _Выберите интересующий раздел:_ ",
        reply_markup=free_menu_kb()
    )

@router.callback_query(F.data == "free_self_dev")
async def free_self_dev_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "°√§ *Раздел Саморазвитие\.* _Здесь собрана только фанатская анимация\._ Выберите путь развития:",
        reply_markup=self_dev_kb(is_paid=False)
    )

@router.callback_query(F.data == "free_edu")
async def free_edu_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "∆§λ _Вы перешли в подраздел Обучение_ \n"
        "**Здесь собрана только фанатская анимация\!** Выберите дисциплину:",
        reply_markup=edu_kb(is_paid=False)
    )

@router.callback_query(F.data == "free_physics")
async def free_physics_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "√∆_ Вы открыли бесплатный урок по ФИЗИКЕ\._\n"
        "**Важно:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=False, back_target="free_edu")
    )

@router.callback_query(F.data == "free_math")
async def free_math_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "√∆_ Вы открыли бесплатный урок по МАТЕМАТИКЕ\._\n"
        "**Важно:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=False, back_target="free_edu")
    )

@router.callback_query(F.data == "free_wealth")
async def free_wealth_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "&@#_ Добро пожаловать во вкладку БОГАТСТВО\._\n"
        "**Обратите внимание:** _тут будет только фанатская анимация, сделанная в blender, это не несёт какой\-то поучительный характер\._",
        reply_markup=wealth_kb(is_paid=False)
    )

@router.callback_query(F.data == "free_rappers")
async def free_rappers_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "£ *Категория: РЕПЕРЫ* £\n\n"
        "**Обратите внимание:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=False, back_target="free_wealth")
    )

@router.callback_query(F.data == "free_cars")
async def free_cars_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "€ *Категория: ТАЧКИ* €\n\n"
        "**Обратите внимание:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=False, back_target="free_wealth")
    )

@router.callback_query(F.data == "free_villas")
async def free_villas_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "$ *Категория: ВИЛЫ* $\n\n"
        "**Обратите внимание:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=False, back_target="free_wealth")
    )

@router.callback_query(F.data == "free_entertainment")
async def free_ent_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "∆°√ *Раздел Развлечения\.* _Здесь вас ждут анимационные работы\._ Выберите интересующую подкатегорию:",
        reply_markup=entertainment_kb(is_paid=False)
    )

@router.callback_query(F.data == "free_bloggers")
async def free_bloggers_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "@ *Категория: БЛОГЕРЫ* &\n\n"
        "_Описание: Фанатская анимация — повторение роликов известных блогеров в среде Blender\._",
        reply_markup=final_content_kb(is_paid=False, back_target="free_entertainment")
    )

@router.callback_query(F.data == "free_movies")
async def free_movies_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "° *Категория: ФИЛЬМЫ* #\n\n"
        "_Описание: Создание полноценных короткометражных фильмов и сцен в программе Blender\._",
        reply_markup=final_content_kb(is_paid=False, back_target="free_entertainment")
    )

@router.callback_query(F.data == "free_games")
async def free_games_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "§ *Категория: ИГРЫ* ∆\n\n"
        "_Описание: Фанатская 3D\-анимация, воссозданная по мотивам популярных компьютерных игр\._",
        reply_markup=final_content_kb(is_paid=False, back_target="free_entertainment")
                      )
# ─── ВЕТКА ПЛАТНОГО НАПРАВЛЕНИЯ И ОПЛАТЫ ────────────────────────────────────
@router.callback_query(F.data == "mode_paid")
async def paid_mode(callback: CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if user_data and user_data[1] == 1:
        await go_cabinet_page(callback)
        return

    await callback.message.edit_text(
        "&°§ *Вы выбрали платное направление\.* _Вам будет доступен абсолютно весь премиальный контент платформы без ограничений\._\n\n"
        "Для активации требуется подписка\.",
        reply_markup=pay_kb()
    )

@router.callback_query(F.data == "pay_action")
async def pay_action_handler(callback: CallbackQuery):
    escaped_price = SUBSCRIPTION_PRICE.replace(".", "\.")
    await callback.message.edit_text(
        f"√∆ *Стоимость подписки:* _{escaped_price}_\.\n\n"
        "🔗 \[[ОПЛАТИТЬ ЧЕРЕЗ СИСТЕМУ](https://example.com)\]",
        reply_markup=check_pay_kb()
    )

@router.callback_query(F.data == "pay_success")
async def pay_success_handler(callback: CallbackQuery):
    set_premium(callback.from_user.id, 1)
    await callback.message.edit_text(
        "√§∆ **Ваша подписка успешно активирована\!**\n"
        "_Добро пожаловать во вселенную ONEVERSE\._",
        reply_markup=cabinet_kb()
    )

async def go_cabinet_page(callback: CallbackQuery):
    # При переходе в личный кабинет отправляем стикер
    await callback.message.answer_sticker(STICKER_LOBBY)
    await callback.message.answer(
        "⭐⚡ **ЛИЧНЫЙ КАБИНЕТ ПЛАТФОРМЫ ONEVERSE** ⚡⭐\n\n"
        "_Здесь хранится премиум контент в Blender\._ Выберите интересующий раздел или запустите линейный план:",
        reply_markup=paid_menu_kb()
    )

@router.callback_query(F.data == "go_cabinet")
async def go_cabinet_callback(callback: CallbackQuery):
    await go_cabinet_page(callback)

# ─── КОНТЕНТ ДЛЯ ПЛАТНОЙ ПОДПИСКИ ──────────────────────────────────────────
@router.callback_query(F.data == "linear_plan")
async def linear_plan_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "\#&° *ПОЛНЫЙ ЛИНЕЙНЫЙ ПЛАН КОНТЕНТА*\n\n"
        "**Здесь последовательно собраны все ролики из абсолютно всех папок нашего бота\!**\n"
        "_Просто нажимайте по порядку на кнопки ниже и изучайте фанатскую анимацию Blender_ ↓",
        reply_markup=linear_kb()
    )

@router.callback_query(F.data == "paid_self_dev")
async def paid_self_dev_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "°√§ *Премиум Раздел Саморазвитие\.* _Здесь собрана только фанатская анимация\._ Выберите путь:",
        reply_markup=self_dev_kb(is_paid=True)
    )

@router.callback_query(F.data == "paid_edu")
async def paid_edu_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "∆§λ _Вы перешли в премиум подраздел Обучение_ \n"
        "**Здесь собрана только фанатская анимация\!** Выберите дисциплину:",
        reply_markup=edu_kb(is_paid=True)
    )

@router.callback_query(F.data == "paid_physics")
async def paid_physics_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "√∆_ Вы открыли премиум урок по ФИЗИКЕ\._\n"
        "**Важно:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=True, back_target="paid_edu")
    )

@router.callback_query(F.data == "paid_math")
async def paid_math_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "√∆_ Вы открыли премиум урок по МАТЕМАТИКЕ\._\n"
        "**Важно:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=True, back_target="paid_edu")
    )

@router.callback_query(F.data == "paid_wealth")
async def paid_wealth_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "&@#_ Премиум вкладка БОГАТСТВО\._\n"
        "**Обратите внимание:** _тут будет только фанатская анимация, сделанная в blender, это не несёт какой\-то поучительный характер\._",
        reply_markup=wealth_kb(is_paid=True)
    )

@router.callback_query(F.data == "paid_rappers")
async def paid_rappers_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "£ *Премиум Категория: РЕПЕРЫ* £\n\n"
        "**Обратите внимание:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=True, back_target="paid_wealth")
    )

@router.callback_query(F.data == "paid_cars")
async def paid_cars_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "€ *Премиум Категория: ТАЧКИ* €\n\n"
        "**Обратите внимание:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=True, back_target="paid_wealth")
    )

@router.callback_query(F.data == "paid_villas")
async def paid_villas_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "$ *Премиум Категория: ВИЛЫ* $\n\n"
        "**Обратите внимание:** _Здесь будет только фанатская анимация BLENDER\._",
        reply_markup=final_content_kb(is_paid=True, back_target="paid_wealth")
    )

@router.callback_query(F.data == "paid_entertainment")
async def paid_ent_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "∆°√ *Премиум Раздел Развлечения\.* _Полная медиатека фанатских работ\._ Выберите интересующую подкатегорию:",
        reply_markup=entertainment_kb(is_paid=True)
    )

@router.callback_query(F.data == "paid_bloggers")
async def paid_bloggers_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "@ *Премиум Категория: БЛОГЕРЫ* &\n\n"
        "_Описание: Фанатская анимация — повторение роликов известных блогеров в среде Blender\._",
        reply_markup=final_content_kb(is_paid=True, back_target="paid_entertainment")
    )

@router.callback_query(F.data == "paid_movies")
async def paid_movies_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "° *Премиум Категория: ФИЛЬМЫ* #\n\n"
        "_Описание: Создание полноценных короткометражных фильмов и сцен в программе Blender\._",
        reply_markup=final_content_kb(is_paid=True, back_target="paid_entertainment")
    )

@router.callback_query(F.data == "paid_games")
async def paid_games_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "§ *Премиум Категория: ИГРЫ* ∆\n\n"
        "_Описание: Фанатская 3D\-анимация, воссозданная по мотивам популярных компьютерных игр\._",
        reply_markup=final_content_kb(is_paid=True, back_target="paid_entertainment")
    )

# ─── ЗАПУСК БОТА ──────────────────────────────────────────────────────────────
async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




    
