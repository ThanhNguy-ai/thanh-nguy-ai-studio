import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import tempfile, subprocess, asyncio, textwrap, json, random, os
import imageio_ffmpeg
import requests, io, re

st.set_page_config(page_title='Thanh Nguy AI Studio',page_icon='🎬',layout='centered')
st.markdown('''<style>.block-container{max-width:680px;padding-top:1.4rem} .stButton button{min-height:3.3rem;border-radius:12px} h1{font-size:1.8rem!important}</style>''',unsafe_allow_html=True)
st.title('🎬 Thanh Nguy AI Studio')
st.caption('Tạo video dọc từ chủ đề • Chạy trên điện thoại qua trình duyệt')

GENRES={'🙏 Phật giáo':'Phật giáo','😂 Hài hước':'Hài hước','📚 Giáo dục':'Giáo dục','❤️ Cảm xúc':'Cảm xúc','🐱 Kể chuyện':'Kể chuyện','🍜 Ẩm thực':'Ẩm thực','✨ Khác':'Khác'}
with st.form('video'):
    genre=GENRES[st.selectbox('🎭 Thể loại',list(GENRES))]
    topic=st.text_area('✍️ Chủ đề',placeholder='Ví dụ: Mẹ hiền là Phật sống',height=80)
    duration=st.select_slider('⏱️ Thời lượng mục tiêu (giây)',options=[15,30,45,60,90],value=30)
    voice=st.selectbox('🎙️ Giọng đọc',['vi-VN-HoaiMyNeural','vi-VN-NamMinhNeural'],format_func=lambda v:'Nữ - Hoài My' if 'Hoai' in v else 'Nam - Nam Minh')
    mode=st.radio('📝 Nội dung', ['Tự tạo bản nháp theo chủ đề','Tôi tự nhập lời đọc'],horizontal=False)
    custom=st.text_area('Lời đọc (nếu tự nhập)',height=140) if mode=='Tôi tự nhập lời đọc' else ''
    photos=st.file_uploader('🖼️ Ảnh minh họa (chọn 1–8 ảnh, tùy chọn)',type=['jpg','jpeg','png','webp'],accept_multiple_files=True,help='Ảnh em chọn sẽ được dùng làm cảnh video. Nếu không chọn, ứng dụng thử tìm ảnh trên Wikimedia Commons.')
    submitted=st.form_submit_button('✨ TẠO VIDEO MP4',use_container_width=True)

TEMPLATES={
'Phật giáo':['Có những điều bình dị lại mang ý nghĩa sâu xa.','Khi nghĩ về {topic}, ta nhớ rằng lòng từ bi bắt đầu từ những hành động nhỏ.','Một lời nói dịu dàng có thể giúp người khác nhẹ lòng.','Hôm nay, hãy dành ít phút để sống chậm và biết ơn.'],
'Hài hước':['Chuyện gì sẽ xảy ra khi {topic}?','Ban đầu ai cũng tưởng mọi thứ rất đơn giản.','Nhưng đời không như là mơ, tình huống bất ngờ xuất hiện!','Và cuối cùng, người tự tin nhất lại là người ngạc nhiên nhất.'],
'Giáo dục':['Bạn đã thực sự hiểu về {topic} chưa?','Hãy bắt đầu bằng một câu hỏi nhỏ và một ví dụ dễ hình dung.','Khi chia vấn đề thành từng bước, mọi thứ trở nên rõ ràng hơn.','Thử tự giải thích lại bằng lời của mình để ghi nhớ lâu hơn nhé.'],
'Cảm xúc':['Có những khoảnh khắc khiến ta nhớ mãi về {topic}.','Đôi khi một hành động rất nhỏ lại chứa đựng tình cảm lớn.','Điều quý giá không phải lúc nào cũng cần nói thành lời.','Hãy trân trọng những người đang ở bên mình.'],
'Kể chuyện':['Ngày nọ, có một câu chuyện thú vị về {topic}.','Mọi thứ diễn ra bình thường cho đến khi một điều bất ngờ xuất hiện.','Nhân vật chính phải đưa ra một lựa chọn quan trọng.','Và bài học cuối cùng là hãy luôn suy nghĩ trước khi hành động.'],
'Ẩm thực':['Hôm nay cùng khám phá {topic} nhé!','Đầu tiên, hãy chuẩn bị nguyên liệu phù hợp và làm sạch cẩn thận.','Tiếp theo, chế biến từng bước và điều chỉnh gia vị theo khẩu vị.','Thành phẩm sẽ hấp dẫn hơn khi trình bày gọn gàng và đẹp mắt.'],
'Khác':['Hôm nay chúng ta cùng nói về {topic}.','Điều thú vị đầu tiên là hãy nhìn vấn đề từ một góc độ khác.','Tiếp theo, thử áp dụng một ý tưởng nhỏ trong cuộc sống.','Bạn nghĩ sao về chủ đề này?']}

def font_path():
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf','C:/Windows/Fonts/arialbd.ttf']:
        if Path(p).exists():return p
    return None

def commons_image(query):
    """Best-effort openly licensed photo search; never pretend generated AI imagery."""
    api='https://commons.wikimedia.org/w/api.php'
    headers={'User-Agent':'ThanhNguyAIStudio/2.0 (educational prototype)'}
    try:
        r=requests.get(api,params={'action':'query','generator':'search','gsrsearch':query+' filetype:bitmap','gsrnamespace':6,'gsrlimit':8,'prop':'imageinfo','iiprop':'url|mime|extmetadata','iiurlwidth':900,'format':'json'},headers=headers,timeout=12)
        r.raise_for_status()
        pages=r.json().get('query',{}).get('pages',{})
        for page in pages.values():
            for info in page.get('imageinfo',[]):
                url=info.get('thumburl') or info.get('url','')
                if info.get('mime','').startswith('image/') and url:
                    data=requests.get(url,headers=headers,timeout=15)
                    data.raise_for_status()
                    im=Image.open(io.BytesIO(data.content)).convert('RGB')
                    if min(im.size)>=300:
                        meta=info.get('extmetadata',{})
                        return im,{'source':info.get('descriptionurl',url),'license':re.sub('<[^>]*>','',meta.get('LicenseShortName',{}).get('value','Xem trang nguồn'))}
    except Exception:
        pass
    return None,None

def frame(path,title,subtitle,idx,total,photo=None):
    w,h=720,1280
    if photo is not None:
        im=photo.convert('RGB')
        iw,ih=im.size
        factor=max(w/iw,h/ih)
        nw,nh=round(iw*factor),round(ih*factor)
        im=im.resize((nw,nh),Image.Resampling.LANCZOS)
        left=(nw-w)//2; top=(nh-h)//2
        im=im.crop((left,top,left+w,top+h))
    else:
        im=Image.new('RGB',(w,h),(37,45,62))
        d=ImageDraw.Draw(im)
        for y in range(h):
            d.line((0,y,w,y),fill=(25+int(y/h*32),36+int(y/h*23),55+int(y/h*15)))
    overlay=Image.new('RGBA',(w,h),(0,0,0,0))
    od=ImageDraw.Draw(overlay)
    od.rectangle((0,790,w,h),fill=(0,0,0,155))
    od.rectangle((0,0,w,140),fill=(0,0,0,95))
    im=Image.alpha_composite(im.convert('RGBA'),overlay)
    d=ImageDraw.Draw(im)
    fp=font_path()
    ft=ImageFont.truetype(fp,43) if fp else ImageFont.load_default()
    fs=ImageFont.truetype(fp,23) if fp else ImageFont.load_default()
    def wrap(s,limit=25):
        words=s.split();out=[];line=''
        for word in words:
            if len((line+' '+word).strip())>limit and line:
                out.append(line);line=word
            else:line=(line+' '+word).strip()
        if line:out.append(line)
        return out[:6]
    lines=wrap(subtitle)
    y=860+(6-len(lines))*12
    for line in lines:
        bbox=d.textbbox((0,0),line,font=ft)
        x=(w-(bbox[2]-bbox[0]))/2
        d.text((x,y),line,font=ft,fill='white',stroke_width=2,stroke_fill=(0,0,0))
        y+=65
    d.text((28,40),title[:35],font=fs,fill='white')
    d.text((28,1220),f'THANH NGUY AI STUDIO  •  {idx+1}/{total}',font=fs,fill='white')
    im.convert('RGB').save(path)

def run(args):
    result=subprocess.run(args,capture_output=True,text=True,timeout=240)
    if result.returncode:raise RuntimeError(result.stderr[-1200:])

async def speech(text,path,voice):
    import edge_tts
    await edge_tts.Communicate(text,voice,rate='+0%').save(str(path))

if submitted:
    if not topic.strip():st.error('Vui lòng nhập chủ đề trước khi tạo video.')
    elif mode=='Tôi tự nhập lời đọc' and not custom.strip():st.error('Em chưa nhập lời đọc.')
    else:
        try:
            with st.spinner('Đang tạo lời đọc, dựng cảnh và xuất MP4...'):
                topic=topic.strip()[:140]
                lines=[s.format(topic=topic) for s in TEMPLATES[genre]] if mode!='Tôi tự nhập lời đọc' else [x.strip() for x in custom.replace('\n',' ').split('.') if x.strip()]
                lines=lines[:8]
                uploaded=[]
                for f in (photos or []):
                    try: uploaded.append(Image.open(io.BytesIO(f.getvalue())).convert('RGB'))
                    except Exception: pass
                source_notes=[]
                if len(lines)==0:raise ValueError('Không có nội dung để dựng.')
                with tempfile.TemporaryDirectory() as td:
                    td=Path(td); ff=imageio_ffmpeg.get_ffmpeg_exe(); segments=[]
                    for i,line in enumerate(lines):
                        img=td/f'frame{i}.png'; audio=td/f'audio{i}.mp3'; out=td/f'seg{i}.mp4'
                        photo=uploaded[i%len(uploaded)] if uploaded else None
                        if photo is None:
                            photo,meta=commons_image(topic if i==0 else genre+' '+topic)
                            if meta:source_notes.append(meta)
                        frame(img,topic,line,i,len(lines),photo)
                        asyncio.run(speech(line,audio,voice))
                        run([ff,'-y','-loop','1','-framerate','25','-i',str(img),'-i',str(audio),'-vf','scale=720:1280,format=yuv420p','-c:v','libx264','-preset','ultrafast','-tune','stillimage','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(out)])
                        segments.append(out)
                    concat=td/'files.txt';concat.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in segments),encoding='utf-8')
                    final=td/'video.mp4'
                    run([ff,'-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)])
                    video=final.read_bytes()
                st.success('Đã tạo xong video!')
                st.video(video)
                st.download_button('📥 TẢI VIDEO MP4',video,file_name='Thanh_Nguy_AI_Studio.mp4',mime='video/mp4',use_container_width=True)
                st.download_button('📝 TẢI KỊCH BẢN','\n'.join(lines),file_name='kich_ban.txt',mime='text/plain')
                if source_notes:
                    st.caption('Nguồn ảnh Wikimedia Commons (kiểm tra giấy phép và ghi công trước khi đăng):')
                    for item in {x['source']:x for x in source_notes}.values(): st.write(item['source']+' — '+item['license'])
                st.info('Bản nâng cấp dùng ảnh em tải lên hoặc thử tìm ảnh từ Wikimedia Commons; nếu không tìm được sẽ dùng nền dự phòng. Chưa có AI tạo ảnh hay AI viết kịch bản. Thời lượng thực tế phụ thuộc lời đọc.')
        except Exception as e:
            st.error('Chưa thể xuất video: '+str(e))
            st.info('Kiểm tra kết nối Internet, giọng đọc Edge TTS và tài nguyên máy chủ. Thử nội dung ngắn hơn.')
