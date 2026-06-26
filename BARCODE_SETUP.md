# 📷 Hướng dẫn cài đặt Barcode Scanner

## 📋 Tổng quan

Phần mềm đã được tích hợp tính năng quét barcode bằng camera. Bạn có thể quét barcode để:
- **Thêm sản phẩm mới** (tab Sản phẩm)
- **Bán hàng nhanh** (tab Bán hàng POS)

## 🔧 Cài đặt thư viện

### Bước 1: Cài đặt các thư viện cần thiết
```bash
pip install opencv-python pyzbar Pillow
```

### Bước 2: Khởi động lại phần mềm
Sau khi cài đặt xong, khởi động lại phần mềm để sử dụng tính năng quét barcode.

## 📱 Cách sử dụng

### 1. Quét barcode khi thêm sản phẩm mới
1. Vào tab **"📦 Sản phẩm"**
2. Click nút **📷** bên cạnh ô Barcode
3. Đưa barcode vào khung hình camera
4. Barcode sẽ tự động được điền vào ô

### 2. Quét barcode khi bán hàng
1. Vào tab **"🧾 Bán hàng POS"**
2. Click nút **"📷 Quét"**
3. Đưa barcode vào khung hình camera
4. Sản phẩm sẽ tự động được thêm vào giỏ hàng

## 🎯 Tính năng

- ✅ **Quét barcode real-time** bằng camera
- ✅ **Hỗ trợ nhiều định dạng** barcode (EAN, UPC, Code128, QR Code...)
- ✅ **Tự động điền thông tin** sản phẩm
- ✅ **Giao diện thân thiện** với nút điều khiển
- ✅ **Hiển thị khung** quanh barcode được quét
- ✅ **Tạm dừng/tiếp tục** quét

## 🔍 Các loại barcode được hỗ trợ

- **EAN-13** (European Article Number)
- **EAN-8** (European Article Number 8)
- **UPC-A** (Universal Product Code)
- **UPC-E** (Universal Product Code E)
- **Code 128**
- **Code 39**
- **QR Code**
- **Data Matrix**
- **PDF417**

## ⚠️ Lưu ý

1. **Camera**: Cần có camera hoặc webcam
2. **Ánh sáng**: Đảm bảo đủ ánh sáng khi quét
3. **Khoảng cách**: Giữ barcode cách camera 10-30cm
4. **Độ rõ nét**: Barcode phải rõ nét, không bị mờ

## 🛠️ Troubleshooting

### Lỗi "Không thể mở camera"
- Kiểm tra camera có được kết nối không
- Đảm bảo không có ứng dụng khác đang sử dụng camera
- Thử khởi động lại phần mềm

### Lỗi "Thư viện chưa được cài đặt"
- Chạy lệnh: `pip install opencv-python pyzbar Pillow`
- Khởi động lại phần mềm

### Không quét được barcode
- Kiểm tra ánh sáng
- Thử điều chỉnh khoảng cách
- Đảm bảo barcode không bị hỏng

## 🎨 Giao diện Scanner

```
┌─────────────────────────────────────┐
│           📷 Quét Barcode           │
│    Đưa barcode vào khung hình       │
├─────────────────────────────────────┤
│                                     │
│        [Video Camera Feed]          │
│                                     │
├─────────────────────────────────────┤
│ ▶️ Bắt đầu  ⏹️ Dừng    ❌ Đóng     │
├─────────────────────────────────────┤
│            Trạng thái: Sẵn sàng     │
└─────────────────────────────────────┘
```

## 🚀 Nâng cao

### Tùy chỉnh camera
- Thay đổi độ phân giải trong code
- Điều chỉnh tốc độ quét
- Thêm hiệu ứng âm thanh khi quét thành công

### Tích hợp với thiết bị ngoài
- Kết nối với máy quét barcode USB
- Sử dụng smartphone làm camera
- Tích hợp với hệ thống POS chuyên nghiệp
