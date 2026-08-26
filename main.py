import os
import datetime
import requests
from supabase import create_client, Client
from tiktok_uploader.upload import upload_video

# جلب المتغيرات البيئية من GitHub Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TIKTOK_SESSION_ID = os.environ.get("TIKTOK_SESSION_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_video(url, filename="temp_video.mp4"):
    """دالة لتحميل الفيديو مؤقتاً من الرابط المباشر"""
    print("جاري تحميل الفيديو إلى الخادم...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return filename
    else:
        raise Exception("فشل في تحميل الفيديو من الرابط!")

def main():
    # 1. جلب رقم الفيديو الحالي من قاعدة البيانات
    state_res = supabase.table("bot_state").select("value").eq("key", "current_index").execute()
    if not state_res.data:
        print("خطأ: لم يتم العثور على حالة البوت في قاعدة البيانات!")
        return
    
    current_index = state_res.data[0]["value"]
    print(f"رقم الفيديو في الدور: {current_index}")

    # 2. تحديد عدد الفيديوهات (الجمعة = 3، الأيام الأخرى = 1)
    is_friday = datetime.datetime.now().weekday() == 4
    videos_to_publish = 3 if is_friday else 1

    for _ in range(videos_to_publish):
        video_res = supabase.table("videos").select("*").eq("item_index", current_index).execute()
        
        if not video_res.data:
            print(f"تنبيه: لا يوجد فيديو مسجل بالرقم {current_index}")
            break
        
        video_data = video_res.data[0]
        video_url = video_data["video_url"]
        caption = video_data["caption"]

        # 3. تحميل الفيديو مؤقتاً
        video_path = download_video(video_url)
        
        # 4. الرفع على تيك توك
        print(f"جاري رفع الفيديو رقم {current_index} على تيك توك...")
        
        # تجهيز ملفات تعريف الارتباط (Cookies) المطلوبة للمكتبة
        cookies_list = [{
            'name': 'sessionid',
            'value': TIKTOK_SESSION_ID,
            'domain': '.tiktok.com',
            'path': '/'
        }]
        
        try:
            # دالة الرفع على تيك توك
            upload_video(video_path, description=caption, cookies_list=cookies_list)
            print("تم النشر على تيك توك بنجاح!")
        except Exception as e:
            print(f"حدث خطأ أثناء الرفع: {e}")
        
        # 5. تنظيف الخادم بحذف الفيديو المؤقت
        if os.path.exists(video_path):
            os.remove(video_path)

        # 6. تحديث المؤشر
        current_index = (current_index % 100) + 1

    # حفظ المؤشر الجديد
    supabase.table("bot_state").update({"value": current_index}).eq("key", "current_index").execute()
    print("تم تحديث المؤشر في قاعدة البيانات بنجاح!")

if __name__ == "__main__":
    main()
