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

DEVICES = {
    "strip1": "🌈 Лента на стеллаже",
}

DEVICE_TOPICS = {
    "strip1": {
        "cmd": "esp32/led1",
        "status": "esp32/led1/status",
    }
}


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
def devices_keyboard():
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"device:{key}")]
        for key, name in DEVICES.items()
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("⛔ Доступ запрещён")
        return

    context.user_data.clear()

    await update.message.reply_text(
        "📟 Выбери устройство:",
        reply_markup=devices_keyboard()
    )


def colors_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔴-", callback_data="cmd:2"),
            InlineKeyboardButton("🔵+", callback_data="cmd:3"),
            InlineKeyboardButton("➖", callback_data="cmd:4"),
            InlineKeyboardButton("➕", callback_data="cmd:5"),
            
        ],
        [
            InlineKeyboardButton("🔅", callback_data="cmd:6"),
            InlineKeyboardButton("🔆", callback_data="cmd:7"),
            InlineKeyboardButton("🎨", callback_data="cmd:8"),
            InlineKeyboardButton("🌊", callback_data="cmd:9"),
        ],
        [
            InlineKeyboardButton("🌈", callback_data="cmd:10"),
            InlineKeyboardButton("🔥", callback_data="cmd:11"),
            InlineKeyboardButton("❤️‍🔥", callback_data="cmd:12"),
            InlineKeyboardButton("🕺", callback_data="cmd:13"),
        ],
        [
            InlineKeyboardButton("☄️", callback_data="cmd:14"),
            InlineKeyboardButton("✨", callback_data="cmd:15"),
            InlineKeyboardButton("🌠", callback_data="cmd:16"),
            InlineKeyboardButton("🌑/💡", callback_data="cmd:1"),
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="back:devices")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_allowed(update):
        await query.answer("⛔ Доступ запрещён", show_alert=True)
        return

    data = query.data

    # ⬅️ Назад
    if data == "back:devices":
        context.user_data.clear()
        await query.edit_message_text(
            "📟 Выбери устройство:",
            reply_markup=devices_keyboard()
        )
        return

    # 📟 Выбор устройства
    if data.startswith("device:"):
        device_key = data.split(":", 1)[1]
        context.user_data["device"] = device_key

        await query.edit_message_text(
            f"✅ Устройство: {DEVICES[device_key]}\n\n🎨 Выбери команду:",
            reply_markup=colors_keyboard()
        )
        return

    # 🎨 Команда
    if data.startswith("cmd:"):
        device_key = context.user_data.get("device")

        if not device_key:
            await query.answer("⚠️ Сначала выбери устройство", show_alert=True)
            return

        payload = data.split(":", 1)[1]
        topic = DEVICE_TOPICS[device_key]["cmd"]

        mqtt_client.publish(topic, payload, qos=1)

        await query.answer("📡 Команда отправлена")

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(
        getenv("BOT_TOKEN")
    ).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("🤖 Telegram bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
