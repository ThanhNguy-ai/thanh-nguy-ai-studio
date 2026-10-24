import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import tempfile, subprocess, asyncio, textwrap, json, random, os
import imageio_ffmpeg

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

def frame(path, title, subtitle, idx, total):
    w,h=720,1280
    palettes=[((15,29,52),(38,82,102)),((41,31,64),(93,58,97)),((19,52,55),(30,107,91)),((59,35,41),(130,79,64))]
    c1,c2=palettes[idx%len(palettes)]
    im=Image.new('RGB',(w,h)); px=im.load()
    for y in range(h):
        a=y/h; col=tuple(int(c1[i]*(1-a)+c2[i]*a) for i in range(3))
        ImageDraw.Draw(im).line([(0,y),(w,y)],fill=col)
    d=ImageDraw.Draw(im)
    d.ellipse((90,155,630,695),outline=(255,216,155),width=5)
    d.ellipse((130,195,590,655),outline=(255,216,155),width=2)
    fp=font_path(); ft=ImageFont.truetype(fp,43) if fp else ImageFont.load_default(); fs=ImageFont.truetype(fp,30) if fp else ImageFont.load_default()
    def wrap(s,limit=23):
        words=s.split(); out=[]; line=''
        for word in words:
            if len(line+' '+word)>limit and line:out.append(line);line=word
            else:line=(line+' '+word).strip()
        if line:out.append(line)
        return out[:9]
    lines=wrap(subtitle)
    y=755
    for line in lines:
        box=d.textbbox((0,0),line,font=ft); x=(w-(box[2]-box[0]))/2
        d.text((x,y),line,font=ft,fill=(255,250,235),stroke_width=1,stroke_fill=(20,20,25));y+=67
    d.text((35,65),title[:32],font=fs,fill=(255,220,175))
    d.text((35,1200),f'THANH NGUY AI STUDIO   •   {idx+1}/{total}',font=fs,fill=(230,230,230))
    im.save(path)

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
                if len(lines)==0:raise ValueError('Không có nội dung để dựng.')
                with tempfile.TemporaryDirectory() as td:
                    td=Path(td); ff=imageio_ffmpeg.get_ffmpeg_exe(); segments=[]
                    for i,line in enumerate(lines):
                        img=td/f'frame{i}.png'; audio=td/f'audio{i}.mp3'; out=td/f'seg{i}.mp4'
                        frame(img,topic,line,i,len(lines))
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
                st.info('Lưu ý: Bản này dùng kịch bản mẫu theo thể loại, nền đồ họa tự tạo và giọng đọc trực tuyến. Thời lượng thực tế theo lời đọc, có thể khác thời lượng mục tiêu. Chưa tích hợp AI tạo ảnh/video.')
        except Exception as e:
            st.error('Chưa thể xuất video: '+str(e))
            st.info('Kiểm tra kết nối Internet, giọng đọc Edge TTS và tài nguyên máy chủ. Thử nội dung ngắn hơn.')
