import io, os, time, tempfile, textwrap, random, shutil, subprocess
from pathlib import Path
import requests
import streamlit as st
from PIL import Image, ImageOps, ImageDraw, ImageFont
import imageio_ffmpeg

st.set_page_config(page_title='Thanh Nguy AI Studio V3', page_icon='🎬')
st.title('🎬 Thanh Nguy AI Studio V3')
st.caption('Tự tạo ảnh AI → lời đọc → MP4 dọc • thử nghiệm miễn phí')

GENRES = {'🙏 Phật giáo':'serene Buddhist temple, lotus flowers, peaceful sacred atmosphere',
'😂 Hài hước':'funny relatable Vietnamese everyday life, expressive characters',
'📚 Giáo dục':'clear educational illustration, interesting visual explanation',
'💛 Gia đình':'warm Vietnamese family life, candid emotional moments',
'🌿 Chữa lành':'calm natural landscape, uplifting cinematic imagery',
'🎭 Kể chuyện':'cinematic story scene, natural expressions'}

def font_path():
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']:
        if os.path.exists(p): return p
    return None

def draw_frame(img, caption):
    im = ImageOps.fit(img.convert('RGB'), (720,1280), method=Image.Resampling.LANCZOS)
    overlay = Image.new('RGBA', im.size, (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    d.rectangle((0,940,720,1280),fill=(0,0,0,135))
    fp=font_path()
    font=ImageFont.truetype(fp,36) if fp else ImageFont.load_default()
    lines=textwrap.wrap(caption, width=28)[:5]
    for i,line in enumerate(lines):
        box=d.textbbox((0,0),line,font=font)
        x=max(18,(720-(box[2]-box[0]))//2)
        d.text((x,1000+i*53),line,font=font,fill='white',stroke_width=1,stroke_fill='black')
    return Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')

def ai_horde(prompt, timeout=200):
    # Anonymous community compute: best effort, no uptime guarantee.
    base='https://aihorde.net/api/v2'
    headers={'apikey':'0000000000','Client-Agent':'ThanhNguyStudio:3.0:personal-demo'}
    payload={'prompt':prompt+', photorealistic, soft natural lighting, balanced color, no text, no watermark',
             'params':{'width':512,'height':768,'steps':20,'n':1,'cfg_scale':6},'nsfw':False,'censor_nsfw':True}
    r=requests.post(base+'/generate/async',headers=headers,json=payload,timeout=25)
    r.raise_for_status()
    data=r.json()
    job=data.get('id')
    if not job: raise RuntimeError(str(data)[:250])
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        time.sleep(6)
        q=requests.get(base+'/generate/check/'+job,headers=headers,timeout=20)
        q.raise_for_status()
        state=q.json()
        if state.get('faulted'): raise RuntimeError('Máy tạo ảnh cộng đồng báo lỗi.')
        if state.get('done'):
            res=requests.get(base+'/generate/status/'+job,headers=headers,timeout=20).json()
            gens=res.get('generations') or []
            if not gens: raise RuntimeError('Không nhận được ảnh từ máy tạo ảnh.')
            url=gens[0].get('img')
            if not url or not url.startswith('https://'): raise RuntimeError('Đường dẫn ảnh không hợp lệ.')
            pic=requests.get(url,timeout=45)
            pic.raise_for_status()
            return Image.open(io.BytesIO(pic.content)).convert('RGB')
    raise TimeoutError('Hết thời gian chờ ảnh miễn phí. Hãy thử lại sau.')

def make_script(topic,genre,n):
    # Template is deliberately disclosed; not an LLM generated script.
    sentences=[f'{topic}: một câu chuyện đáng để chúng ta suy ngẫm.',
               f'Đôi khi, chỉ một thay đổi nhỏ cũng đem đến góc nhìn mới về {topic}.',
               'Hãy quan sát những điều giản dị quanh mình và cảm nhận sự khác biệt.',
               'Điều quan trọng không chỉ là kết quả, mà còn là cách ta trải nghiệm hành trình.',
               'Nếu thấy ý nghĩa, hãy chia sẻ câu chuyện này với người bạn yêu quý.']
    return [sentences[i%len(sentences)] for i in range(n)]

def create_voice(text, target):
    import asyncio, edge_tts
    async def work():
        await edge_tts.Communicate(text, 'vi-VN-HoaiMyNeural', rate='-5%').save(str(target))
    asyncio.run(work())

def render_video(images, lines, out_path, audio_path=None, seconds_per_scene=5):
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for i,(im,line) in enumerate(zip(images,lines)):
            draw_frame(im,line).save(root/f'{i:03d}.jpg',quality=90)
        concat=root/'concat.txt'
        with concat.open('w',encoding='utf-8') as f:
            for i in range(len(images)):
                f.write(f"file '{root/f'{i:03d}.jpg'}'\n")
                f.write(f'duration {seconds_per_scene}\n')
            f.write(f"file '{root/f'{len(images)-1:03d}.jpg'}'\n")
        cmd=[ffmpeg,'-y','-f','concat','-safe','0','-i',str(concat)]
        if audio_path and audio_path.exists(): cmd+=['-i',str(audio_path)]
        cmd+=['-vf','fps=24,format=yuv420p','-c:v','libx264','-preset','ultrafast','-crf','28']
        if audio_path and audio_path.exists(): cmd+=['-c:a','aac','-shortest']
        else: cmd+=['-an']
        cmd+=['-movflags','+faststart',str(out_path)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
        if result.returncode: raise RuntimeError(result.stderr[-1000:])

with st.form('generate'):
    genre=st.selectbox('🎭 Thể loại',list(GENRES))
    topic=st.text_area('✍️ Chủ đề',placeholder='Ví dụ: Mẹ hiền là Phật sống')
    scenes=st.slider('🖼️ Số cảnh / số ảnh AI',2,5,3)
    seconds=st.slider('⏱️ Giây mỗi cảnh',4,10,6)
    manual=st.checkbox('Tự nhập lời đọc thay cho bản nháp')
    narration=st.text_area('Lời đọc của em') if manual else ''
    use_voice=st.checkbox('🎙️ Tạo giọng đọc tiếng Việt (cần Internet)',value=True)
    submitted=st.form_submit_button('✨ TỰ TẠO ẢNH & VIDEO MP4',use_container_width=True)

if submitted:
    if not topic.strip(): st.error('Vui lòng nhập chủ đề.'); st.stop()
    lines=make_script(topic.strip(),genre,scenes)
    if manual and narration.strip():
        chunks=[x.strip() for x in narration.split('\n') if x.strip()]
        if chunks: lines=[chunks[i%len(chunks)] for i in range(scenes)]
    st.subheader('📝 Kịch bản (có thể chỉnh ở lần chạy tiếp theo)')
    for i,line in enumerate(lines,1): st.write(f'**Cảnh {i}:** {line}')
    imgs=[]
    progress=st.progress(0)
    for i,line in enumerate(lines):
        prompt=f'{GENRES[genre]}, {topic}, scene {i+1} of {scenes}, {line}, cinematic vertical composition'
        with st.spinner(f'Đang tạo ảnh AI {i+1}/{scenes} (máy miễn phí có thể phải xếp hàng)...'):
            try:
                im=ai_horde(prompt)
            except Exception as e:
                st.error(f'Ảnh {i+1} chưa tạo được: {e}')
                st.info('Không xuất video giả bằng nền màu. Thử lại khi dịch vụ miễn phí hoạt động.')
                st.stop()
        imgs.append(im)
        st.image(im,caption=f'Ảnh AI cảnh {i+1}',width=240)
        progress.progress((i+1)/scenes)
    with st.spinner('Đang dựng video...'):
        try:
            with tempfile.TemporaryDirectory() as td:
                audio=Path(td)/'voice.mp3'
                audio_ok=False
                if use_voice:
                    try: create_voice(' '.join(lines),audio); audio_ok=True
                    except Exception as e: st.warning(f'Giọng đọc chưa tạo được ({e}); xuất video không tiếng.')
                output=Path(td)/'Thanh_Nguy_AI_Studio_V3.mp4'
                render_video(imgs,lines,output,audio if audio_ok else None,seconds)
                video=output.read_bytes()
            st.success('Đã tạo MP4!')
            st.video(video)
            st.download_button('⬇️ TẢI VIDEO MP4',video,file_name='Thanh_Nguy_AI_Studio_V3.mp4',mime='video/mp4')
        except Exception as e: st.error(f'Lỗi dựng MP4: {e}')
st.caption('Lưu ý: bản thử nghiệm dùng máy AI Horde cộng đồng. Kịch bản dùng mẫu, chưa phải AI viết; ảnh tự tạo tùy khả năng máy chủ miễn phí. Giọng đọc Edge TTS phụ thuộc dịch vụ bên ngoài.')
