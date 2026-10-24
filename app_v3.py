import io, os, time, tempfile, textwrap, random, shutil, subprocess, re
from pathlib import Path
import requests
import streamlit as st
from PIL import Image, ImageOps, ImageDraw, ImageFont
import imageio_ffmpeg

st.set_page_config(page_title='Thanh Nguy AI Studio V3', page_icon='🎬')
st.title('🎬 Thanh Nguy AI Studio V3')
st.caption('Tạo ảnh AI qua AI Horde → giọng đọc → MP4 dọc • dịch vụ cộng đồng có thể yêu cầu API key')

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

def ai_horde(prompt, api_key, timeout=240):
    base = 'https://aihorde.net/api/v2'
    headers = {'apikey': api_key.strip() or '0000000000',
               'Client-Agent': 'ThanhNguyAIStudio:3.1:personal-use'}
    payload = {'prompt': prompt + ', photorealistic, soft natural lighting, no text, no watermark',
               'params': {'width': 512, 'height': 768, 'steps': 20, 'n': 1, 'cfg_scale': 6},
               'nsfw': False, 'censor_nsfw': True}
    try:
        r = requests.post(base + '/generate/async', headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError('Không kết nối được máy tạo ảnh. Kiểm tra mạng hoặc thử lại sau.') from e
    if r.status_code in (401, 403):
        detail = (r.text or '')[:220]
        raise RuntimeError('AI Horde từ chối yêu cầu (HTTP %s). Khóa dùng chung/ẩn danh có thể bị hạn chế. '
                           'Hãy dùng API key AI Horde cá nhân hoặc thử lại sau. %s' % (r.status_code, detail))
    if not r.ok:
        raise RuntimeError('AI Horde trả về HTTP %s: %s' % (r.status_code, r.text[:200]))
    data = r.json()
    job = data.get('id')
    if not job:
        raise RuntimeError('Không nhận được mã yêu cầu tạo ảnh: ' + str(data)[:200])
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(7)
        q = requests.get(base + '/generate/check/' + job, headers=headers, timeout=25)
        q.raise_for_status()
        state = q.json()
        if state.get('faulted'):
            raise RuntimeError('Máy tạo ảnh cộng đồng báo lỗi. Hãy thử lại.')
        if state.get('done'):
            status = requests.get(base + '/generate/status/' + job, headers=headers, timeout=25)
            status.raise_for_status()
            gens = status.json().get('generations') or []
            if not gens:
                raise RuntimeError('Máy chủ chưa trả ảnh.')
            url = gens[0].get('img')
            if not url or not url.startswith('https://'):
                raise RuntimeError('Đường dẫn ảnh trả về không hợp lệ.')
            pic = requests.get(url, timeout=60)
            pic.raise_for_status()
            return Image.open(io.BytesIO(pic.content)).convert('RGB')
    raise TimeoutError('Hết thời gian chờ máy tạo ảnh miễn phí. Thử lại sau.')


def clean_topic(topic):
    # Remove instructions that should not be spoken aloud.
    topic = re.split(r'(?i)phong cách mong muốn\s*:|phong cách\s*:|khung hình\s*:|em chỉ cần', topic)[0]
    topic = re.sub(r'\s+', ' ', topic).strip(' .\n')
    return topic[:150]


def make_script(topic, genre, n):
    # Offline narrative templates: NOT an AI language model.
    if 'Phật giáo' in genre or 'Gia đình' in genre or any(x in topic.lower() for x in ('mẹ', 'cha', 'báo hiếu')):
        sentences = [
            'Có những yêu thương bình dị mà đôi khi ta vô tình quên mất.',
            'Mẹ không cần những món quà lớn lao, chỉ mong con bình an và nhớ về nhà.',
            'Một cuộc gọi, một lời hỏi thăm cũng có thể làm ấm lòng người mẹ.',
            'Đừng đợi đến khi không còn cơ hội mới nói lời biết ơn.',
            'Hôm nay, hãy dành cho mẹ một chút thời gian và thật nhiều yêu thương.'
        ]
    elif 'Hài hước' in genre:
        sentences = [
            'Có những chuyện tưởng rất bình thường mà lại khiến ta bật cười.',
            'Mọi chuyện bắt đầu bằng một ý tưởng nghe có vẻ hoàn hảo.',
            'Nhưng đời đâu phải lúc nào cũng diễn ra đúng kế hoạch!',
            'Một tình huống bất ngờ khiến ai cũng phải ngạc nhiên.',
            'Đôi khi, biết cười với chính mình là điều tuyệt vời nhất.'
        ]
    elif 'Giáo dục' in genre:
        sentences = [
            'Hôm nay, chúng ta cùng tìm hiểu một điều thú vị.',
            'Hãy bắt đầu từ một ví dụ thật gần gũi trong cuộc sống.',
            'Khi quan sát kỹ, ta sẽ thấy nguyên lý đằng sau hiện tượng.',
            'Thử áp dụng điều vừa học vào một tình huống mới nhé.',
            'Mỗi ngày hiểu thêm một chút là một ngày tiến bộ.'
        ]
    else:
        sentences = [
            'Mỗi câu chuyện đều bắt đầu từ một khoảnh khắc rất giản dị.',
            'Có những điều nhỏ bé lại khiến ta suy nghĩ thật lâu.',
            'Khi thay đổi góc nhìn, ta nhận ra nhiều điều ý nghĩa.',
            'Điều đáng quý nằm ở cách chúng ta sống và cảm nhận.',
            'Hãy giữ lại điều tốt đẹp và chia sẻ với người mình thương.'
        ]
    return [sentences[i % len(sentences)] for i in range(n)]


def scene_prompt(topic, genre, i, total):
    style = GENRES[genre]
    positions = ['wide establishing shot', 'intimate medium shot', 'emotional close-up',
                 'candid daily-life scene', 'hopeful ending shot']
    if any(x in topic.lower() for x in ('mẹ', 'báo hiếu', 'gia đình')):
        visual = [
            'Vietnamese mother at home by a sunlit window',
            'Vietnamese adult child visiting their mother, natural tender moment',
            'close-up of mother gently holding her child hand',
            'Vietnamese mother and adult child sharing a simple meal',
            'mother and adult child walking together at sunset'
        ][i % 5]
    else:
        visual = topic
    return f'{style}, {visual}, {positions[i % len(positions)]}, vertical cinematic composition, realistic photograph'

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
    topic=st.text_area('✍️ Chủ đề (viết ngắn gọn)',placeholder='Ví dụ: Mẹ hiền là Phật sống')
    api_key=st.text_input('🔑 AI Horde API key (không bắt buộc, nhưng có thể cần nếu máy chủ từ chối khách ẩn danh)',type='password',help='Không chia sẻ khóa trong ảnh chụp màn hình. Khóa này chỉ dùng cho yêu cầu tạo ảnh của lần chạy hiện tại.')
    scenes=st.slider('🖼️ Số cảnh / số ảnh AI',2,5,3)
    seconds=st.slider('⏱️ Giây mỗi cảnh',4,10,6)
    manual=st.checkbox('Tự nhập lời đọc thay cho bản nháp')
    narration=st.text_area('Lời đọc của em') if manual else ''
    use_voice=st.checkbox('🎙️ Tạo giọng đọc tiếng Việt (cần Internet)',value=True)
    submitted=st.form_submit_button('✨ TỰ TẠO ẢNH & VIDEO MP4',use_container_width=True)

if submitted:
    if not topic.strip(): st.error('Vui lòng nhập chủ đề.'); st.stop()
    topic_short=clean_topic(topic)
    if not topic_short: st.error('Hãy nhập một chủ đề ngắn gọn.'); st.stop()
    lines=make_script(topic_short,genre,scenes)
    if manual and narration.strip():
        chunks=[x.strip() for x in narration.split('\n') if x.strip()]
        if chunks: lines=[chunks[i%len(chunks)] for i in range(scenes)]
    st.subheader('📝 Kịch bản (có thể chỉnh ở lần chạy tiếp theo)')
    for i,line in enumerate(lines,1): st.write(f'**Cảnh {i}:** {line}')
    imgs=[]
    progress=st.progress(0)
    for i,line in enumerate(lines):
        prompt=scene_prompt(topic_short,genre,i,scenes)
        with st.spinner(f'Đang tạo ảnh AI {i+1}/{scenes} (máy miễn phí có thể phải xếp hàng)...'):
            try:
                im=ai_horde(prompt,api_key)
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
st.caption('V3.1: Kịch bản vẫn dùng mẫu (chưa có AI viết). AI Horde là dịch vụ cộng đồng, có thể yêu cầu API key hoặc từ chối tạo ảnh. Không đảm bảo miễn phí liên tục. Edge TTS phụ thuộc dịch vụ bên ngoài.')
