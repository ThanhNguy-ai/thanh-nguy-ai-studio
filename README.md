# Thanh Nguy AI Studio — thử nghiệm

Ứng dụng Streamlit tạo video dọc MP4 từ mẫu kịch bản theo chủ đề, nền đồ họa và giọng đọc Edge TTS.

## Triển khai bằng điện thoại
1. Trên github.com chọn dấu + > New repository. Đặt tên `thanh-nguy-ai-studio`, chọn Private nếu có thể, rồi Create repository.
2. Trong repository chọn Add file > Upload files (nếu không thấy trên điện thoại, bật Chrome > Trang web cho máy tính).
3. Tải riêng `app.py` và `requirements.txt` từ ChatGPT về điện thoại, chọn cả hai để upload, rồi Commit changes.
4. Truy cập https://share.streamlit.io, đăng nhập bằng GitHub, chọn Create app > Deploy a public app from GitHub, chọn repository và file `app.py`, sau đó Deploy. Nếu repository riêng tư không được hỗ trợ theo hạn mức hiện tại, kiểm tra quyền và lựa chọn triển khai trước khi chuyển sang Public.
5. Khi được cấp URL https, mở trong Chrome Android > menu ba chấm > Thêm vào màn hình chính.

## Giới hạn
Chưa tạo ảnh AI chân thực, kịch bản chỉ là mẫu, thời lượng thực tế không đảm bảo bằng thời lượng chọn, Edge TTS phụ thuộc Internet và có thể bị giới hạn. Chưa kiểm thử đầu cuối trên Streamlit Cloud. Không nhập dữ liệu riêng tư nếu ứng dụng công khai.
