# bot.py — Полная версия с FastAPI, Web App, Админкой

import asyncio
import logging
import os
import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# ================
# Настройка логирования (сразу в начале)
# ================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================
# Загрузка переменных окружения
# ================

try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ .env загружен")
except ImportError:
    logger.warning("⚠️ Модуль dotenv не установлен — используем переменные окружения напрямую")

# ================
# Переменные окружения
# ================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ ОШИБКА: BOT_TOKEN не найден. Убедитесь, что переменная задана в Render")

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://livbubble-webapp.onrender.com")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@livbubble")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # 🔐 Пароль администратора

# Список администраторов (только они могут управлять ботом)
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    try:
        ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",")]
    except ValueError:
        logger.error("❌ Ошибка: ADMIN_IDS должен содержать только числа, разделённые запятыми")

# ================
# Списки спама
# ================

SPAM_KEYWORDS = [
    "FREE ETH", "FREEETHER.NET", "CLAIM ETH", "GET FREE CRYPTO",
    "BITCOIN GIVEAWAY", "ETHEREUM AIRDROP", "FREE CRYPTO",
    "CONNECT YOUR WALLET", "WALLET VERIFY", "FREE MONEY",
    "CLICK HERE", "INSTANT REWARDS", "NO REGISTRATION",
    "ABSOLUTELY FREE", "DROP ETH", "GIVEAWAY", "FREE NFT",
    "AIRDROP", "SEND ETHER", "FREE MONEY", "CRYPTO BONUS",
    "MAKE MONEY FAST", "PUMP MY WALLET", "VERIFICATION REQUIRED",
    "WALLET SYNC", "DEPOSIT TO CLAIM", "ABSOLUTELY FREE"
]

SPAM_DOMAINS = [
    "freeether.net", "free-eth.com", "claim-eth.org", "airdrop-crypto.ru",
    "getfreecrypto.io", "crypto-giveaway.net", "bitcoin-airdrop.org",
    "wallet-verify.com", "eth-drop.com", "free-crypto.today",
    "claimcrypto.pro", "airdrop-funds.com", "verifywallet.net",
    "bit-airdrop.com", "nft-giveaway.net"
]

# ================
# Бот и диспетчер
# ================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================
# FastAPI
# ================

app = FastAPI()

# ================
# Статические файлы
# ================

# Раздаём статику (HTML, CSS, JS)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# ================
# Middleware для аутентификации администратора
# ================

def require_admin_auth(request: Request):
    token = request.cookies.get("authToken")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return True

# ================
# Маршрут для админки
# ================

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    try:
        with open("admin/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки admin/index.html: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки админ-панели")

# ================
# Проверка пароля
# ================

@app.post("/check-password")
async def check_password(request: Request):
    try:
        data = await request.json()
        password = data.get("password")
        if password == ADMIN_PASSWORD:
            response = JSONResponse({"success": True, "message": "Пароль верный"})
            response.set_cookie(
                key="authToken",
                value=ADMIN_PASSWORD,
                httponly=True,
                secure=True,
                max_age=30 * 60,  # 30 минут
                samesite="lax",
                path="/"  # ✅ Критично: кука доступна для всего домена
            )
            return response
        else:
            response = JSONResponse({"success": False, "message": "Неверный пароль"}, status_code=401)
            response.delete_cookie("authToken", path="/")
            return response
    except Exception as e:
        logger.error(f"❌ Ошибка проверки пароля: {e}")
        return JSONResponse({"success": False, "message": "Ошибка проверки пароля"}, status_code=500)

# ================
# Выход
# ================

@app.post("/logout")
async def logout():
    response = JSONResponse({"success": True})
    response.delete_cookie("authToken", path="/")
    return response

# ================
# Чтение заданий
# ================

@app.get("/tasks.json")
async def get_tasks():
    try:
        with open("tasks.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"priority_tasks": []}
    except Exception as e:
        logger.error(f"❌ Ошибка чтения tasks.json: {e}")
        return {"priority_tasks": []}

# ================
# Сохранение заданий
# ================

@app.post("/save-tasks", dependencies=[Depends(require_admin_auth)])
async def save_tasks(request: Request):
    try:
        data = await request.json()
        priority_tasks = data.get("priority_tasks", [])
        
        if not isinstance(priority_tasks, list):
            return JSONResponse({"success": False, "message": "priority_tasks должен быть массивом"}, status_code=400)

        with open("tasks.json", "w", encoding="utf-8") as f:
            json.dump({"priority_tasks": priority_tasks}, f, ensure_ascii=False, indent=2)

        logger.info("✅ Задания успешно сохранены в tasks.json")
        return JSONResponse({"success": True, "message": "Задания успешно сохранены!"})
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения tasks.json: {e}")
        return JSONResponse({"success": False, "message": "Ошибка сохранения"}, status_code=500)

# ================
# Команда /start
# ================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        
        if member.status in ["member", "administrator", "creator"]:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🎮 Начать игру",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )]
            ])
            await message.answer(
                "🎮 Добро пожаловать в <b>Liv Bubble</b>!\n\n"
                "Вы подписаны — начинайте игру и участвуйте в розыгрыше каждый день в 12:00!",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📢 Подписаться на канал",
                    url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
                )]
            ])
            await message.answer(
                "⚠️ Чтобы играть, вы должны быть подписаны на канал @livbubble.\n\n"
                "Подпишитесь и нажмите /start, чтобы начать игру.",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"❌ Ошибка проверки подписки: {e}")
        await message.answer("⚠️ Ошибка проверки подписки. Попробуйте позже.")

# ================
# Обработка данных из Web App
# ================

@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    logger.info(f"Получены данные из Web App от {message.from_user.id}: {message.web_app_data.data}")
    
    try:
        data = json.loads(message.web_app_data.data)

        if data.get("game_completed"):
            bubbles = data.get("bubbles_popped", "неизвестно")
            await message.answer(
                f"🎉 Поздравляем! Ты успешно завершил игру!\n"
                f"Лопнул пузырей: {bubbles}\n\n"
                "Ты выполнил все задания. Жди награду!"
            )
        elif data.get("task_completed"):
            task_id = data.get("task_id", "неизвестно")
            await message.answer(f"✅ Задание #{task_id} выполнено!")
    except Exception as e:
        logger.error(f"❌ Ошибка обработки WebAppData: {e}")
        await message.answer("⚠️ Ошибка при обработке данных.")

# ================
# Запуск бота
# ================

async def main():
    logger.info("✅ Бот запущен и готов к работе...")
    logger.info("🌐 Ожидание сообщений...")
    
    # Проверяем доступность Web App
    try:
        import requests
        response = requests.get(WEBAPP_URL, timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Web App доступен по адресу: {WEBAPP_URL}")
        else:
            logger.warning(f"⚠️ Web App недоступен. Статус: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки Web App: {e}")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        logger.info("🚀 Запуск бота...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную.")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
