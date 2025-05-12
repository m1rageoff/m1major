from aiogram import Router, Bot, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import CHANNEL_ID, CHAT_ID, ADMIN_ID
from states import Form
from payment import create_payment, is_payment_successful
from sheets import append_row

router = Router()


async def is_user_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        chat_member_channel = await bot.get_chat_member(CHANNEL_ID, user_id)
        chat_member_chat = await bot.get_chat_member(CHAT_ID, user_id)
        return (
            chat_member_channel.status in ["member", "administrator", "creator"]
            and chat_member_chat.status in ["member", "administrator", "creator"]
        )
    except TelegramBadRequest:
        return False


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
    intro_text = (
        "🎮 Привет! Я Юрий, основатель киберспортивной команды M1.\n"
        "Мы не просто катаем — мы идём за Мажором.\n"
        "Хочешь играть на топовом уровне, заявить о себе на стримах и быть частью сильной движухи?\n\n"
        "Оставляй заявку и заполняй всё внимательно.\n"
        "Сюда попадают не все — только те, кто реально заряжен на победу.🔥"
    )
    await message.answer(intro_text)

    if await is_user_subscribed(bot, message.from_user.id):
        await message.answer("✅ Подписка подтверждена! Введите ваш Faceit ник:")
        await state.set_state(Form.faceit_nick)
    else:
        await message.answer(
            "❗ Чтобы продолжить, подпишитесь на:\n"
            "📢 Канал: https://t.me/m1rageoff\n"
            "💬 Чат: https://t.me/m1rageoff1\n\n"
            "После подписки нажмите /start заново."
        )


async def show_confirmation(message_or_call, state: FSMContext):
    data = await state.get_data()
    msg = (
        f"🔍 Проверьте правильность своих данных:\n\n"
        f"🔹 Faceit ник: {data.get('faceit_nick', '-')}\n"
        f"🔹 Ссылка: {data.get('faceit_link', '-')}\n"
        f"🔹 Email: {data.get('email', '-')}\n\n"
        f"Если всё верно — нажмите «✅ Всё верно».\n"
        f"Если хотите изменить — выберите, что изменить."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить Faceit ник", callback_data="edit_nick")],
        [InlineKeyboardButton(text="✏️ Изменить ссылку", callback_data="edit_link")],
        [InlineKeyboardButton(text="✏️ Изменить email", callback_data="edit_email")],
        [InlineKeyboardButton(text="✅ Всё верно", callback_data="confirm_data")]
    ])

    if isinstance(message_or_call, CallbackQuery):
        await message_or_call.message.edit_text(msg, reply_markup=keyboard)
    else:
        await message_or_call.answer(msg, reply_markup=keyboard)


@router.message(Form.faceit_nick)
async def process_nick(message: Message, state: FSMContext):
    await state.update_data(faceit_nick=message.text)
    await message.answer("Введите ссылку на ваш профиль Faceit:")
    await state.set_state(Form.faceit_link)


@router.message(Form.faceit_link)
async def process_link(message: Message, state: FSMContext):
    await state.update_data(faceit_link=message.text)
    await message.answer("Введите ваш email:")
    await state.set_state(Form.email)


@router.message(Form.email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await show_confirmation(message, state)


@router.callback_query(F.data == "edit_nick")
async def edit_nick(call: CallbackQuery, state: FSMContext):
    await call.message.answer("✏️ Введите новый Faceit ник:")
    await state.set_state(Form.faceit_nick)


@router.callback_query(F.data == "edit_link")
async def edit_link(call: CallbackQuery, state: FSMContext):
    await call.message.answer("✏️ Введите новую ссылку на профиль:")
    await state.set_state(Form.faceit_link)


@router.callback_query(F.data == "edit_email")
async def edit_email(call: CallbackQuery, state: FSMContext):
    await call.message.answer("✏️ Введите новый email:")
    await state.set_state(Form.email)


@router.callback_query(F.data == "confirm_data")
async def handle_confirm_data(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    msg = (
        f"✅ Анкета собрана:\n\n"
        f"🔹 Faceit ник: {data['faceit_nick']}\n"
        f"🔹 Ссылка: {data['faceit_link']}\n"
        f"🔹 Email: {data['email']}\n\n"
        f"Нажмите кнопку ниже, чтобы оплатить участие."
    )

    pay_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 50₽", callback_data="pay_50")]
    ])

    await call.message.answer(msg, reply_markup=pay_button)


@router.callback_query(F.data == "pay_50")
async def handle_payment(call: CallbackQuery):
    url, _ = create_payment(call.from_user.id)

    await call.message.answer(
        "💳 Нажмите кнопку ниже, чтобы перейти к оплате:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к оплате", url=url)]
        ])
    )
    await call.message.answer(
        "❗После оплаты нажмите кнопку ниже:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid_50")]
        ])
    )


@router.callback_query(F.data == "paid_50")
async def handle_paid(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id

    if is_payment_successful(user_id):
        data = await state.get_data()
        data["telegram_id"] = user_id

        try:
            append_row(data)

            text = (
                f"🔔 Новый пользователь оплатил:\n\n"
                f"🆔 Telegram ID: {user_id}\n"
                f"🔹 Faceit ник: {data['faceit_nick']}\n"
                f"🔹 Ссылка: {data['faceit_link']}\n"
                f"🔹 Email: {data['email']}"
            )

            await bot.send_message(chat_id=ADMIN_ID, text=text)

            with open("paid_users.txt", "a", encoding="utf-8") as file:
                file.write(text + "\n\n")

            await call.message.answer(
                "✅ Спасибо за оплату и регистрацию!\n"
                "🔗 Добавь меня в друзья на Faceit:\n"
                "https://www.faceit.com/ru/players/_xMIRAGEx_"
            )
            await call.message.answer("🙏 Удачи и до встречи в игре!")
        except Exception as e:
            await call.message.answer("❌ Ошибка при сохранении данных. Попробуйте позже.")
            print(f"Ошибка записи в Google Sheets: {e}")
    else:
        await call.message.answer(
            "❗ Оплата не найдена. Попробуйте через минуту или оплатите заново.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔁 Проверить ещё раз", callback_data="paid_50")]
            ])
        )
