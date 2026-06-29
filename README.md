# 🏥 Phần Mềm Quản Lý Kho Hàng Hóa - Pharmacy Management System

> **Phần mềm quản lý kho hàng hóa chuyên nghiệp dành cho nhà thuốc, cửa hàng dược phẩm và các cơ sở kinh doanh cần quản lý xuất-nhập-tồn kho hàng hiệu quả, chính xác.**

---

## 🎯 Tổng quan dự án

**Quản lý kho hàng hóa** là một ứng dụng Desktop chuyên nghiệp được xây dựng bằng ngôn ngữ lập trình Python, sử dụng giao diện hiện đại từ thư viện `ttkbootstrap`. Dự án tích hợp các công nghệ tiên tiến để tối ưu hóa quy trình quản lý kho, nhập kho bằng Excel, quét mã vạch bằng camera, và báo cáo trực quan.

---

## ✨ Các tính năng nổi bật

- 🏥 **Quản lý danh mục hàng hóa**: Tra cứu, tìm kiếm nhanh sản phẩm với tính năng tự động gợi ý tên (autocomplete).
- 📋 **Nhập liệu hàng loạt (Excel)**: Cho phép tải file Excel mẫu và nhập hàng loạt danh mục sản phẩm kèm số lượng tồn kho ban đầu một cách nhanh chóng.
- 🗑️ **Xóa phiếu an toàn**: Hỗ trợ xóa các phiếu nhập kho hoặc xuất kho bị nhập nhầm. Hệ thống tự động cân đối và trừ/hoàn trả số lượng tồn kho tương ứng của các lô hàng một cách chính xác qua cơ chế Database Transaction.
- 📷 **Quét mã vạch (Barcode)**: Tích hợp camera thời gian thực để quét mã vạch sản phẩm (EAN, UPC, Code128, QR Code) và tự động điền thông tin nhanh.
- 📊 **Báo cáo chuyên sâu**:
  - Báo cáo doanh thu, chi phí, lợi nhuận chi tiết.
  - Thống kê top sản phẩm bán chạy nhất.
  - Xuất báo cáo đẹp mắt sang các định dạng Excel (.xlsx), PDF và CSV.
- 💾 **Sao lưu và phục hồi**: Tự động hoặc chủ động tạo bản sao lưu cơ sở dữ liệu (`pharm.db`) để bảo vệ dữ liệu tuyệt đối.
- 🔐 **Hệ thống bản quyền (License)**: Kích hoạt bản quyền ngoại tuyến (offline) bảo mật cao bằng chữ ký số Ed25519.
- 🎨 **Giao diện người dùng hiện đại**: Thiết kế giao diện phẳng sang trọng, tối ưu trải nghiệm người dùng với các hiệu ứng tương tác mượt mà.

---

## 🚀 Hướng dẫn cài đặt nhanh (Dành cho nhà phát triển)

### Yêu cầu hệ thống
- **Python 3.8 trở lên**
- **Hệ điều hành**: Windows 10/11, macOS, hoặc Linux
- **RAM**: Tối thiểu 4GB
- **Camera**: Dành cho chức năng quét mã vạch (không bắt buộc)

### Cài đặt các thư viện cần thiết
Mở terminal tại thư mục dự án và chạy lệnh sau để tự động cài đặt các dependencies:
```bash
python -m pip install -r requirements.txt
```

Hoặc cài đặt thủ công các thư viện chính:
```bash
python -m pip install ttkbootstrap>=1.10.1 cryptography>=3.4.8 schedule>=1.2.0 matplotlib>=3.5.0 pandas>=1.5.0 openpyxl>=3.0.0 opencv-python>=4.5.0 pyzbar>=0.1.9 Pillow>=8.0.0 reportlab>=3.6.0
```

### Khởi chạy ứng dụng
Chạy lệnh sau để khởi động phần mềm:
```bash
python nhathuoc2.py
```

## 📱 Hướng dẫn kích hoạt Camera cho Kiểm kho di động (LAN Wi-Fi)

Ứng dụng hỗ trợ kiểm kho di động bằng cách khởi chạy máy chủ web nội bộ trên cổng `5000`. Khi quét mã QR truy cập từ điện thoại qua Wi-Fi (HTTP), trình duyệt di động mặc định sẽ chặn truy cập Camera vì lý do bảo mật (không có HTTPS).

Để mở camera trên trình duyệt **Chrome (Android)**, bạn thực hiện thiết lập như sau:

1. Mở trình duyệt **Chrome** trên điện thoại.
2. Truy cập vào địa chỉ cấu hình ẩn:
   ```text
   chrome://flags/#unsafely-treat-insecure-origin-as-secure
   ```
3. Tìm tùy chọn **"Insecure origins treated as secure"**.
4. Chuyển trạng thái từ **Disabled** sang **Enabled**.
5. Nhập địa chỉ kết nối LAN của máy tính vào ô văn bản bên cạnh. Ví dụ:
   ```text
   http://192.168.1.75:5000
   ```
   *(Lưu ý: Phải điền đầy đủ tiền tố `http://` và KHÔNG được thêm ký tự gạch chéo `/` ở cuối).*
6. Nhấn nút **Relaunch** ở góc dưới cùng bên phải màn hình để khởi động lại trình duyệt Chrome.
7. Truy cập lại trang kiểm kho di động, bấm **Request Camera Permissions** và chọn **Cho phép (Allow)** để bắt đầu quét mã vạch.

---

## 🛠️ Hướng dẫn đóng gói ứng dụng thành file `.exe`

Dự án đã cấu hình sẵn kịch bản đóng gói ứng dụng sang file thực thi độc lập (.exe) không cần cài đặt Python trên máy khách:

### Trên Windows
Chạy file script đóng gói tự động:
```cmd
build.bat
```
*(Script sẽ tự động cài đặt PyInstaller nếu thiếu, cài đặt các dependencies và đóng gói ứng dụng chính cùng các công cụ quản lý khóa bản quyền vào thư mục `dist`).*

---

## 📚 Tài liệu đính kèm

Để hiểu rõ hơn về các phần hành cụ thể, bạn có thể tham khảo tài liệu chi tiết:
- 📖 [Hướng dẫn sử dụng chi tiết](HUONG_DAN_SU_DUNG.md) - Hướng dẫn vận hành đầy đủ từng tab chức năng.
- 📷 [Hướng dẫn thiết lập quét mã vạch](BARCODE_SETUP.md) - Hướng dẫn cấu hình camera quét barcode.
- 📊 [Hướng dẫn xuất báo cáo](EXPORT_REPORTS.md) - Chi tiết cấu trúc xuất báo cáo Excel và PDF.
- 🔐 [Hướng dẫn hệ thống License](README_LICENSE.md) - Hướng dẫn sinh khóa bản quyền cho khách hàng.
- 📝 [Nhật ký thay đổi (Changelog)](CHANGELOG.md) - Nhật ký phát triển qua các phiên bản.

---

## 📞 Liên hệ và hỗ trợ

- **Tác giả**: Hồ Sỷ Thoảng
- **Email**: hstptcn5@gmail.com
- **Số điện thoại**: 0329381189
- **Bản quyền**: **Commercial License** - Tất cả các quyền được bảo lưu.

---

**© 2026 Hồ Sỷ Thoảng. Bảo lưu mọi quyền.**
