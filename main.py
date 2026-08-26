import os
import datetime
from supabase import create_client, Client
import requests

# جلب المتغيرات البيئية من نظام التشغيل (GitHub Secrets)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_telegram_video(video_url, caption):
    """إرسال الفيديو إلى قناة أو مجموعة تليجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "video": video_url,
        "caption": caption
    }
    response = requests.post(url, json=payload)
    return response.json()

def main():
    # 1. جلب رقم الفيديو الحالي (Index) من قاعدة البيانات
    state_res = supabase.table("bot_state").select("value").eq("key", "current_index").execute()
    if not state_res.data:
        print("خطأ: لم يتم العثور على حالة البوت في قاعدة البيانات!")
        return
    
    current_index = state_res.data[0]["value"]
    print(f"رقم الفيديو الحالي في الدور: {current_index}")

    # 2. تحديد عدد الفيديوهات بناءً على اليوم (الجمعة = 3 فيديوهات، الأيام الأخرى = فيديو واحد)
    # weekday() يعيد 4 يوم الجمعة
    is_friday = datetime.datetime.now().weekday() == 4
    videos_to_publish = 3 if is_friday else 1
    print(f"عدد الفيديوهات التي سيتم نشرها اليوم: {videos_to_publish}")

    for _ in range(videos_to_publish):
        # جلب تفاصيل الفيديو بناءً على الترتيب الحالي
        video_res = supabase.table("videos").select("*").eq("item_index", current_index).execute()
        
        if not video_res.data:
            print(f"تنبيه: لا يوجد فيديو مسجل بالرقم {current_index}")
            break
        
        video_data = video_res.data[0]
        video_url = video_data["video_url"]
        caption = video_data["caption"]

        print(f"جاري نشر الفيديو رقم {current_index}...")
        res = send_telegram_video(video_url, caption)
        print("نتيجة النشر:", res)

        # 3. تحديث المؤشر (إذا وصل إلى 100، يعود إلى 1 تلقائياً)
        current_index = (current_index % 100) + 1

    # حفظ المؤشر الجديد في قاعدة البيانات
    supabase.table("bot_state").update({"value": current_index}).eq("key", "current_index").execute()
    print("تم الانتهاء من النشر وتحديث المؤشر بنجاح!")

if name == "main":
    main()