import os
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# အပိုင်း (၁) - Thumbnail ပေါ်တွင် ရက်စွဲတပ်ခြင်း
# ==========================================
def add_date_to_thumbnail(input_path, output_path):
    print("[INFO] ပုံပေါ်တွင် ရက်စွဲ ထည့်သွင်းနေပါသည်...")
    try:
        today_date = datetime.now().strftime("%d.%m.%Y")
        
        img = Image.open(input_path)
        draw = ImageDraw.Draw(img)
        
        # ဖောင့်အရွယ်အစား ၉၀
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        except IOError:
            font = ImageFont.load_default()
            
        bbox = draw.textbbox((0, 0), today_date, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # tayar.py မှ အတိုင်း ညာသို့ ၂၀၀၊ အပေါ်သို့ ၅၀ ပြင်ဆင်ထားသည်
        x = ((img.width - text_width) / 2) + 200
        y = img.height - text_height - 50
        
        # Outline width 3 ဖြင့် အနက်ရောင်အရင်ဆွဲသည်
        outline_color = "black"
        outline_width = 3
        for i in range(-outline_width, outline_width+1):
            for j in range(-outline_width, outline_width+1):
                draw.text((x+i, y+j), today_date, font=font, fill=outline_color)
                
        # အဖြူရောင်စာသားအစစ် ထပ်ရေးသည်
        draw.text((x, y), today_date, font=font, fill="white")
        
        img.convert("RGB").save(output_path)
        print(f"[SUCCESS] ရက်စွဲတပ်ပြီးသောပုံကို {output_path} အမည်ဖြင့် သိမ်းလိုက်ပါပြီ။")
    except Exception as e:
        print(f"[ERROR] ပုံပြင်ရာတွင် အမှားရှိနေပါသည်: {e}")

# ==========================================
# အပိုင်း (၂) - YouTube သို့ Video နှင့် Thumbnail တင်ခြင်း
# ==========================================
def upload_video_to_youtube(video_path, thumb_path, title_name, schedule_time_str):
    print("[INFO] YouTube သို့ ဗီဒီယိုတင်ရန် ပြင်ဆင်နေပါသည်...")
    try:
        # GitHub Secrets မှ လျှို့ဝှက်စာသားများကို ဖတ်၍ ဖိုင်အဖြစ် ပြန်ပြောင်းခြင်း
        with open('client_secrets.json', 'w') as f:
            f.write(os.environ.get('YOUTUBE_CLIENT_SECRETS_DATA', ''))
        with open('token.json', 'w') as f:
            f.write(os.environ.get('YOUTUBE_TOKEN_DATA', ''))
            
        # YouTube API နှင့် ချိတ်ဆက်ခြင်း
        credentials = Credentials.from_authorized_user_file('token.json')
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # ဗီဒီယို ခေါင်းစဉ်၊ ဖော်ပြချက် နှင့် Schedule အချိန် သတ်မှတ်ခြင်း
        body = {
            'snippet': {
                'title': title_name,
                'description': f'နေ့စဉ် နာယူနိုင်ရန် တင်ပေးထားပါသည်။ ရက်စွဲ - {datetime.now().strftime("%d.%m.%Y")}',
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'private', # Schedule အတွက် Private အရင်ထားရသည်
                'publishAt': schedule_time_str
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/*')
        
        # ဗီဒီယို စတင် Upload လုပ်ခြင်း
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
        response = request.execute()
        video_id = response['id']
        print(f"[SUCCESS] ဗီဒီယို တင်ပြီးပါပြီ။ (Video ID: {video_id})")
        
        # Thumbnail ပုံကို Video ပေါ်သို့ ထပ်တင်ခြင်း
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb_path)).execute()
        print("[SUCCESS] Thumbnail ပုံ တင်ပြီးပါပြီ။")
        
    except Exception as e:
        print(f"[ERROR] YouTube သို့ တင်ရာတွင် အမှားဖြစ်နေပါသည်: {e}")

# ==========================================
# အပိုင်း (၃) - အလုပ်ခွဲခြား စေခိုင်းခြင်း (Main Logic)
# ==========================================
if __name__ == "__main__":
    # GitHub Action မှ "morning" သို့မဟုတ် "evening" ဟု လှမ်းပို့မည့် စာသားကို ဖတ်ခြင်း
    job_type = sys.argv[1] if len(sys.argv) > 1 else "morning"
    
    if job_type == "morning":
        print("--- မနက်ပိုင်း လုပ်ငန်းစဉ် ---")
        add_date_to_thumbnail("m_video_thumb_raw.jpg", "m_video_thumb.jpg")
        add_date_to_thumbnail("m_live_thumb_raw.jpg", "m_live_thumb.jpg")
        
        title = f"မနက်ခင်း တရားတော်များ - {datetime.now().strftime('%d.%m.%Y')}"
        # Schedule ပြသမည့်အချိန် (မနက် ၅:၃၀)
        target_time = datetime.now().strftime("%Y-%m-%dT05:30:00+06:30")
        
        upload_video_to_youtube("m_video.mp4", "m_video_thumb.jpg", title, target_time)
        
    elif job_type == "evening":
        print("--- ညနေပိုင်း လုပ်ငန်းစဉ် ---")
        add_date_to_thumbnail("e_video_thumb_raw.jpg", "e_video_thumb.jpg")
        add_date_to_thumbnail("e_live_thumb_raw.jpg", "e_live_thumb.jpg")
        
        title = f"ညနေခင်း တရားတော်များ - {datetime.now().strftime('%d.%m.%Y')}"
        # Schedule ပြသမည့်အချိန် (ညနေ ၆:၃၀)
        target_time = datetime.now().strftime("%Y-%m-%dT18:30:00+06:30")
        
        upload_video_to_youtube("e_video.mp4", "e_video_thumb.jpg", title, target_time)
