# bot.py
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# 🔴 Замени на твой токен из @BotFather
BOT_TOKEN = "7792432750:AAEPP3pGgrXev7yQmRa8nsRFx4UU1nG4ats"

# 📌 Юзернейм канала (без @)
CHANNEL_USERNAME = "livbubble"
CHANNEL_URL = f"https://t.me/{CHANNEL_USERNAME}"

# URL твоего Web App (через ngrok или хостинг)
# Пример: https://abcd-123-45-67-89.ngrok.io
WEBAPP_URL = "https://livbubble-bot-webapp.onrender.com"  # ⚠️ Замени на свой!

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Кнопка "Подписаться"
def get_subscribe_button():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_URL)],
            [types.InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
        ]
    )


# Обработчик /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        chat_member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=message.from_user.id)

        if chat_member.status in ("member", "administrator", "creator"):
            # Пользователь подписан — показываем кнопку игры
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="🎮 Начать игру",
                        web_app=types.WebAppInfo(url=WEBAPP_URL)
                    )]
                ]
            )
            await message.answer(
                "🎮 Добро пожаловать в <b>Liv Bubble</b>!\n\n"
                "Вы подписаны — начинайте игру и участвуйте в розыгрыше каждый день в 12:00!",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            # Не подписан — просим подписаться
            await message.answer(
                "🔔 Чтобы участвовать в розыгрыше, подпишитесь на наш канал!",
                reply_markup=get_subscribe_button()
            )
    except Exception as e:
        await message.answer(
            "⚠️ Ошибка при проверке подписки. Попробуйте позже.",
            reply_markup=get_subscribe_button()
        )


# Обработчик кнопки "Проверить подписку"
@dp.callback_query(F.data == "check_subscription")
async def check_subscription(callback: types.CallbackQuery):
    try:
        chat_member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=callback.from_user.id)

        if chat_member.status in ("member", "administrator", "creator"):
            # Подписан — показываем кнопку игры
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="🎮 Начать игру",
                        web_app=types.WebAppInfo(url=WEBAPP_URL)
                    )]
                ]
            )
            await callback.message.edit_text(
                "✅ Вы подписаны! Добро пожаловать в <b>Liv Bubble</b>!\n\n"
                "Нажмите кнопку ниже, чтобы начать игру и участвовать в розыгрыше!",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            await callback.answer(
                "Вы всё ещё не подписаны. Подпишитесь и нажмите 'Проверить' снова.",
                show_alert=True
            )
    except Exception as e:
        await callback.answer("Ошибка проверки. Попробуйте позже.", show_alert=True)


# Обработчик данных из Web App (когда игра завершена)
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    data = message.web_app_data.data
    await message.answer(
        "🎉 Игра завершена! Вы участвуете в розыгрыше!\n\n"
        "Первые 100 участников получат Telegram Stars.\n"
        "Главные призы (iPhone, PS5, наушники) будут разыграны среди всех участников.",
        parse_mode="HTML"
    )
    # Получаем данные из Web App
    data = update.web_app_data.data
    try:
        # Здесь можно распарсить JSON, если нужно
        # Например: import json; payload = json.loads(data)
        await update.message.answer(
            "🎉 Игра завершена! Вы участвуете в розыгрыше!\n\n"
            "Первые 100 участников получат Telegram Stars.\n"
            "Главные призы (iPhone, PS5, наушники) будут разыграны среди всех участников.",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.answer("Произошла ошибка при обработке данных.")
        print(f"Ошибка: {e}")


# Основная функция запуска
async def main():
    print("✅ Бот Liv Bubble запущен и слушает сообщения...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())