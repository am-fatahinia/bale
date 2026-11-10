import gspread
import os
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from balebale import Bot, Dispatcher
from balebale.Filters import Command

# بارگذاری متغیرهای فایل .env
load_dotenv()

# خواندن توکن و آیدی ادمین
TOKEN = os.getenv("BALE_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))


# --- 1. تنظیمات اتصال به گوگل شیت ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# نام فایل گوگل شیت خود را اینجا وارد کنید
sheet = client.open("bale").sheet1

# --- 2. تنظیمات ربات بله ---
bot = Bot(TOKEN)
dp = Dispatcher(bot)

@dp.message(Command("start"))
def start(message):
    message.answer("سلام! لطفاً اطلاعات دانش‌آموز را در قالب 'نام, نام خانوادگی, کد ملی' ارسال کنید.")

@dp.message()
def handle_message(message):
    text = message.text
    # فرض بر این است که کاربر اطلاعات را با کاما جدا می‌کند
    if text and "," in text:
        try:
            # تقسیم اطلاعات و پاک‌سازی فاصله‌های اضافی
            data = [item.strip() for item in text.split(",")]
            if len(data) == 3:
                # نوشتن در ردیف بعدی گوگل شیت
                sheet.append_row(data)
                message.answer(f"اطلاعات دانش‌آموز با موفقیت ثبت شد:\nنام: {data[0]}\nنام خانوادگی: {data[1]}\nکد ملی: {data[2]}")
            else:
                message.answer("لطفاً دقیقاً سه بخش اطلاعات را با کاما جدا کنید.")
        except Exception as e:
            message.answer("خطا در ثبت اطلاعات. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")
    else:
        message.answer("فرمت پیام صحیح نیست. لطفاً از قالب 'نام, نام خانوادگی, کد ملی' استفاده کنید.")

# --- 3. شروع ربات ---
print("ربات در حال اجراست...")
bot.start_polling(dp)