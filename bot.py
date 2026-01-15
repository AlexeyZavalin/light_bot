from os import getenv

from paho.mqtt import client as mqtt
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from dotenv import load_dotenv

load_dotenv()

# ================= MQTT =================
MQTT_BROKER = getenv("MQTT_BROKER")
MQTT_PORT = int(getenv("MQTT_PORT"))
MQTT_TOPIC = getenv("MQTT_TOPIC")
MQTT_USERNAME = getenv("MQTT_USERNAME")
MQTT_PASSWORD = getenv("MQTT_PASSWORD")
MQTT_CA_FILE = getenv("MQTT_CA_FILE")

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)


def load_whitelist():
    raw = getenv("WHITELIST_USERS", "")
    return {int(uid.strip()) for uid in raw.split(",") if uid.strip().isdigit()}


WHITELIST_USERS = load_whitelist()


def is_allowed(update: Update) -> bool:
    user = update.effective_user
    return user and user.id in WHITELIST_USERS


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT connected")
        client.subscribe(MQTT_TOPIC, qos=1)
    else:
        print(f"❌ MQTT connect failed rc={rc}")

mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

# ================= TELEGRAM =================

async def colors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("⛔ Доступ запрещён")
        return

    context.user_data.clear()
    keyboard = [
        [
            InlineKeyboardButton("🔴-", callback_data="2"),
            InlineKeyboardButton("🔵+", callback_data="3"),
            InlineKeyboardButton("➖", callback_data="4"),
            InlineKeyboardButton("➕", callback_data="5"),
            
        ],
        [
            InlineKeyboardButton("🔅", callback_data="6"),
            InlineKeyboardButton("🔆", callback_data="7"),
            InlineKeyboardButton("🎨", callback_data="8"),
            InlineKeyboardButton("🌊", callback_data="9"),
        ],
        [
            InlineKeyboardButton("🌈", callback_data="10"),
            InlineKeyboardButton("🔥", callback_data="11"),
            InlineKeyboardButton("❤️‍🔥", callback_data="12"),
            InlineKeyboardButton("🕺", callback_data="13"),
        ],
        [
            InlineKeyboardButton("☄️", callback_data="14"),
            InlineKeyboardButton("✨", callback_data="15"),
            InlineKeyboardButton("🌠", callback_data="16"),
            InlineKeyboardButton("🌑/💡", callback_data="1"),
        ]
    ]

    await update.message.reply_text(
        "🎨 Выбери цвет ленты:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def color_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer("🎨 Отправляю цвет…", show_alert=False)

    payload = query.data

    mqtt_client.publish(MQTT_TOPIC, payload, qos=1)

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(
        getenv("BOT_TOKEN")
    ).build()

    app.add_handler(CommandHandler("start", colors))
    app.add_handler(CallbackQueryHandler(color_callback))

    print("🤖 Telegram bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
