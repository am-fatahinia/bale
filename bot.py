import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from balebale import Bot, Dispatcher
from balebale.Filters import Command

# ==========================================
# ۱. خواندن تنظیمات از متغیرهای محیطی (Render)
# ==========================================
BOT_TOKEN = os.getenv("BALE_BOT_TOKEN")
ADMIN_ID_STR = os.getenv("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_STR) if ADMIN_ID_STR else 0

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# ==========================================
# ۲. اتصال به گوگل شیت
# ==========================================
if not GOOGLE_CREDENTIALS:
    raise ValueError("متغیر محیطی GOOGLE_CREDENTIALS تنظیم نشده است!")

# تبدیل رشته JSON به دیکشنری برای احراز هویت
creds_dict = json.loads(GOOGLE_CREDENTIALS)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# اتصال به شیت با استفاده از ID
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# ==========================================
# ۳. تنظیمات ربات بله
# ==========================================
bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message(Command("start"))
def start(message):
    message.answer("سلام! لطفاً اطلاعات دانش‌آموز را در قالب 'نام, نام خانوادگی, کد ملی' ارسال کنید.")

# --- دستور اضافه کردن ستون (فقط برای ادمین) ---
@dp.message(Command("addcol"))
def add_column(message):
    if message.from_user.id != ADMIN_ID:
        return message.answer("⛔ شما دسترسی به این دستور را ندارید.")
    
    col_name = message.text.replace("/addcol", "").strip()
    if not col_name:
        return message.answer("لطفاً نام ستون را وارد کنید. مثال:\n/addcol معدل")
    
    try:
        headers = sheet.row_values(1)
        next_col_index = len(headers) + 1
        sheet.add_cols(1)
        sheet.update_cell(1, next_col_index, col_name)
        message.answer(f"✅ ستون «{col_name}» با موفقیت به شیت اضافه شد.")
    except Exception as e:
        message.answer(f"❌ خطا در اضافه کردن ستون:\n{str(e)}")

# --- دستور حذف ستون (فقط برای ادمین) ---
@dp.message(Command("delcol"))
def delete_column(message):
    if message.from_user.id != ADMIN_ID:
        return message.answer("⛔ شما دسترسی به این دستور را ندارید.")
    
    try:
        col_index = int(message.text.replace("/delcol", "").strip())
        if col_index <= 1:
            return message.answer("⚠️ شما نمی‌توانید ستون اول (نام) را حذف کنید!")
        sheet.delete_cols(col_index)
        message.answer(f"✅ ستون شماره {col_index} با موفقیت حذف شد.")
    except ValueError:
        message.answer("لطفاً شماره ستون را به درستی وارد کنید. مثال:\n/delcol 3")
    except Exception as e:
        message.answer(f"❌ خطا در حذف ستون:\n{str(e)}")

# --- ثبت اطلاعات دانش‌آموز ---
@dp.message()
def handle_message(message):
    # اگر پیام یک دستور بود، نادیده گرفته شود
    if message.text and message.text.startswith("/"):
        return
        
    text = message.text
    if text and "," in text:
        try:
            data = [item.strip() for item in text.split(",")]
            if len(data) == 3:
                sheet.append_row(data)
                message.answer(f"اطلاعات دانش‌آموز با موفقیت ثبت شد:\nنام: {data[0]}\nنام خانوادگی: {data[1]}\nکد ملی: {data[2]}")
            else:
                message.answer("لطفاً دقیقاً سه بخش اطلاعات را با کاما جدا کنید.")
        except Exception as e:
            message.answer("خطا در ثبت اطلاعات. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")
    else:
        message.answer("فرمت پیام صحیح نیست. لطفاً از قالب 'نام, نام خانوادگی, کد ملی' استفاده کنید.")


# ==========================================
# ۴. وب‌سرور بسیار سبک برای زنده نگه داشتن Render
# ==========================================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass  # برای اینکه لاگ‌های اضافی در Render تولید نشود

def run_web_server():
    # Render یک پورت تصادفی به برنامه می‌دهد، آن را می‌خوانیم
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# ==========================================
# ۵. اجرای همزمان وب‌سرور و ربات
# ==========================================
if __name__ == "__main__":
    print("Web server is starting...")
    # اجرای وب‌سرور در یک ترد جداگانه تا مانع کار ربات نشود
    threading.Thread(target=run_web_server, daemon=True).start()
    
    print("Bale Bot is starting...")
    bot.start_polling(dp)