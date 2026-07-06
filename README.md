# 🏥 Hệ Thống Quản Lý Xuất - Nhập - Tồn Kho Y Tế CDC
### *Giải pháp chuyên nghiệp quản lý Vaccine, Thuốc và Vật tư y tế chuẩn GSP & Thông tư 107/2017/TT-BTC*

[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/UI-ttkbootstrap%20(Flatly)-orange.svg)](https://ttkbootstrap.readthedocs.io/)
[![Standard](https://img.shields.io/badge/Standard-GSP%20%7C%20TT107-red.svg)](https://thuvienphapluat.vn/)

---

## 🎯 Giới thiệu chung

**Hệ thống Quản lý XNT CDC** là ứng dụng phần mềm Desktop được thiết kế chuyên biệt cho Trung tâm Kiểm soát bệnh tật (CDC) và các đơn vị y tế dự phòng nhằm tối ưu hóa công tác quản lý thuốc, vaccine và vật tư y tế. 

Hệ thống được phát triển trên nền tảng **Python & SQLite**, sử dụng giao diện đồ họa hiện đại **ttkbootstrap** (Flatly Theme) và tích hợp các tiêu chuẩn nghiêm ngặt của Bộ Y tế về Thực hành tốt bảo quản thuốc (**GSP**) cũng như chế độ kế toán hành chính sự nghiệp (**Thông tư 107/2017/TT-BTC**).

---

## ✨ Các tính năng cốt lõi & Nghiệp vụ chuyên sâu

### 1. 🌡️ Nhật ký Nhiệt độ & Độ ẩm chuẩn GSP (Mới nâng cấp)
*   **Theo dõi 2 lần/ngày (Sáng & Chiều)**: Đáp ứng đúng quy định kiểm tra nhiệt độ vắc xin tại các cơ sở lưu trữ vắc xin quốc gia.
*   **Tự động nhận diện & Cảnh báo an toàn**:
    *   *Tủ vaccine / Kho lạnh (2°C – 8°C)*: Cảnh báo đỏ ngay lập tức khi nhiệt độ lệch khỏi biên độ an toàn.
    *   *Kho mát y tế (15°C – 25°C)*: Cảnh báo cam khi vượt ngưỡng.
    *   *Kho thường*: Cảnh báo khi nhiệt độ > 30°C hoặc độ ẩm > 75%.
*   **Trực quan hóa xu hướng**: Tích hợp công cụ vẽ biểu đồ đường biến thiên nhiệt độ tháng (sử dụng Matplotlib) có sẵn các đường giới hạn đỏ/cam để dễ dàng giám sát sự cố dây chuyền lạnh.
*   **Biểu mẫu Nhật ký PDF**: Xuất Sổ nhật ký nhiệt độ hàng tháng định dạng A4 nằm ngang chuyên nghiệp, đầy đủ thông tin chữ ký ban lãnh đạo và các biện pháp khắc phục khi có sự cố.

### 2. 📋 Lập Phiếu Nhập Kho (Receipts - Mẫu C30-HD)
*   **Lập phiếu nhập đa sản phẩm**: Giỏ hàng tạm thời cho phép thêm, sửa, xóa các mặt hàng trước khi ghi sổ chính thức.
*   **Quản lý Số lô & Hạn sử dụng**: Gắn chặt từng mặt hàng nhập kho với thông tin số lô, hạn dùng phục vụ truy xuất nguồn gốc.
*   **Đồng bộ giá tự động**: Hệ thống tự động gán giá xuất cấp phát bằng giá nhập để đáp ứng nguyên tắc phân phối phi lợi nhuận của hệ thống y tế công.
*   **Xuất PDF độc lập**: In trực tiếp Phiếu nhập kho mẫu chuẩn C30-HD bằng ReportLab, tự động mở sau khi xuất.

### 3. 📤 Xuất Kho / Cấp Phát FEFO (Dispatches - Mẫu C31-HD)
*   **Cơ chế phân bổ FEFO (First Expired, First Out)**: Hệ thống tự động quét và trừ tồn kho từ lô có hạn dùng gần nhất trước, giảm thiểu tối đa hao hụt do thuốc hết hạn.
*   **Lý do xuất đa dạng**: Cấp phát định kỳ, chuyển kho nội bộ, thanh lý thuốc hỏng,...
*   **Bảng chữ ký 5 bên chuẩn**: Người lập phiếu, Người nhận hàng, Thủ kho, Kế toán trưởng, Lãnh đạo đơn vị.
*   **Xóa phiếu an toàn**: Hệ thống hỗ trợ hoàn trả số lượng hàng vào đúng các số lô/hạn dùng cũ nếu xóa phiếu xuất lỗi qua cơ chế Transaction an toàn.

### 4. 📊 Báo cáo & Chứng từ kế toán công chuẩn Thông tư 107
*   **Báo cáo Xuất - Nhập - Tồn (Mẫu S12-H - Sổ thẻ kho)**: Tổng hợp số lượng tồn đầu, nhập trong kỳ, xuất trong kỳ và tồn cuối chi tiết theo từng sản phẩm, từng số lô và hạn dùng.
*   **Biên bản kiểm kê kho (Mẫu C33-HD)**: Kết xuất mẫu PDF kiểm kê kho tại thời điểm hiện tại, có cột trống để hội đồng đối chiếu thực tế khi kiểm kho trực tiếp.
*   **Thống kê nâng cao**: Phân tích biểu đồ xu hướng cấp phát y tế theo thời gian, theo dõi chi tiết sản lượng chuyển giao cho từng đơn vị nhận (các Trạm y tế, Trung tâm y tế huyện...).
*   **Định dạng xuất đa dạng**: Hỗ trợ xuất dữ liệu ra Excel (.xlsx), PDF và CSV.

### 5. 📱 Quét mã vạch thông minh bằng Điện thoại di động
*   **Companion Web Server**: Tích hợp một HTTP server mini chạy ngầm trên cổng 5000 để biến camera điện thoại trong mạng LAN thành máy quét vạch không dây.
*   **Quét thời gian thực**: Hỗ trợ EAN-13, UPC-A, Code 128 và QR Code, tự động tra cứu danh mục và đưa vào giỏ hàng lập phiếu.

### 6. 💾 Cơ chế An toàn dữ liệu & Không cần License
*   **Sao lưu tự động**: Backup cơ sở dữ liệu SQLite định kỳ hàng ngày vào lúc 23:00.
*   **Khôi phục 1-Click**: Cho phép phục hồi dữ liệu nhanh từ các tệp sao lưu ngay trên giao diện.
*   **Bản quyền nguồn mở**: Hoàn toàn miễn phí, không khóa mã, không cần key kích hoạt.

---

## 🛠️ Hướng dẫn cài đặt cho Kỹ thuật viên

### 1. Yêu cầu hệ thống
*   Hệ điều hành: Windows 10 hoặc 11 (64-bit).
*   Python: Phiên bản 3.8 đến 3.11.

### 2. Cài đặt thư viện dependencies
Mở Terminal hoặc Command Prompt tại thư mục dự án và chạy:
```bash
pip install -r requirements.txt
```
*Hoặc cài đặt thủ công các thư viện chính:*
```bash
pip install ttkbootstrap matplotlib pandas openpyxl opencv-python pyzbar Pillow reportlab
```

### 3. Khởi chạy ứng dụng
Chạy tệp tin điều phối khởi động:
```bash
python quanly_xnt.py
```

---

## 📦 Hướng dẫn đóng gói File chạy (.exe) độc lập

Để đóng gói phần mềm thành tệp `.exe` duy nhất cho thủ kho chạy trực tiếp không cần cài Python:
1.  **Trên Windows**: Click đúp vào file `build.bat` trong thư mục dự án.
2.  Chờ PyInstaller thu thập mã nguồn, tệp tin cơ sở dữ liệu danh mục mẫu `thuoc.csv` và các file DLL của thư viện quét mã vạch `pyzbar`.
3.  Tệp tin chạy độc lập **`QuanLyKho.exe`** sẽ được lưu trong thư mục `dist/`.

---

## 📚 Hệ thống tài liệu đi kèm

*   📖 [Hướng dẫn sử dụng chi tiết](HUONG_DAN_SU_DUNG.md) - Hướng dẫn chi tiết từng nút bấm và quy trình nghiệp vụ cho thủ kho.
*   📷 [Hướng dẫn thiết lập quét mã vạch](BARCODE_SETUP.md) - Cấu hình camera điện thoại làm máy quét.
*   📊 [Hướng dẫn xuất báo cáo](EXPORT_REPORTS.md) - Hướng dẫn thiết lập bảng biểu và kết xuất Excel.
*   📝 [Tiến độ dự án & Changelog](tiendo_duan.md) - Nhật ký nâng cấp chi tiết của hệ thống.

---

**Hệ thống được thiết kế để vận hành ngoại tuyến (Offline) 100%, bảo mật dữ liệu nội bộ tuyệt đối cho cơ quan y tế.**
