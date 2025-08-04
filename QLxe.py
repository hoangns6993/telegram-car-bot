import logging
import json
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8134332232:AAFpQC86iubMsbq9hLWi5Qj3DRfTvXHOZ6E"  # ⚠️ Nhớ thay bằng token bot thật

logging.basicConfig(level=logging.INFO)

# ------------------- Data Handling -------------------

def load_data():
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return {}

def save_data():
    with open("data.json", "w") as f:
        json.dump(car_data, f, indent=2)

car_data = load_data()

# ------------------- Bot Handlers -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚗 Chào mừng bạn đến với bot quản lý đăng kiểm!\n"
        "Dùng lệnh:\n"
        "/add <biển số> <đăng kiểm dd-mm-yyyy> <bảo hiểm dd-mm-yyyy>\n"
        "/list để xem danh sách xe"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("❗ Dùng: /add <biển số> <đăng kiểm dd-mm-yyyy> <bảo hiểm dd-mm-yyyy>")
        return

    plate, inspection_str, insurance_str = context.args
    try:
        datetime.strptime(inspection_str, "%d-%m-%Y")
        datetime.strptime(insurance_str, "%d-%m-%Y")
    except ValueError:
        await update.message.reply_text("❌ Sai định dạng ngày. Dùng dd-mm-yyyy.")
        return

    chat_id = str(update.effective_chat.id)
    car_data.setdefault(chat_id, []).append({
        "plate": plate,
        "inspection_date": inspection_str,
        "insurance_date": insurance_str
    })
    save_data()
    await update.message.reply_text(
        f"✅ Đã lưu xe {plate}\n📆 Đăng kiểm: {inspection_str}\n🛡 Bảo hiểm: {insurance_str}"
    )

async def list_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    cars = car_data.get(chat_id, [])

    if not cars:
        await update.message.reply_text("📭 Chưa có xe nào. Thêm bằng lệnh /add")
        return

    text = "📋 Danh sách xe của bạn:\n"
    for car in cars:
        text += (
            f"• {car['plate']}\n"
            f"  - Đăng kiểm: {car['inspection_date']}\n"
            f"  - Bảo hiểm:  {car['insurance_date']}\n"
        )
    await update.message.reply_text(text)

async def remind(application):
    today = datetime.today().date()

    for chat_id, cars in car_data.items():
        for car in cars:
            plate = car["plate"]
            try:
                inspection_date = datetime.strptime(car["inspection_date"], "%d-%m-%Y").date()
                insurance_date = datetime.strptime(car["insurance_date"], "%d-%m-%Y").date()
            except:
                continue

            # Nhắc đăng kiểm
            if today == inspection_date - timedelta(days=7):
                await application.bot.send_message(
                    chat_id=int(chat_id),
                    text=f"🔔 Xe {plate} sắp đến hạn **đăng kiểm** vào ngày {car['inspection_date']}!"
                )
            # Nhắc bảo hiểm
            if today == insurance_date - timedelta(days=7):
                await application.bot.send_message(
                    chat_id=int(chat_id),
                    text=f"🛡 Xe {plate} sắp hết **bảo hiểm bắt buộc** vào ngày {car['insurance_date']}!"
                )

# ------------------- Main -------------------

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_cars))

    # Gọi remind mỗi 24h (giả lập test local: mỗi 60s)
    app.job_queue.run_repeating(remind, interval=60, first=10)

    print("🚀 Bot đang chạy...")
    app.run_polling()
