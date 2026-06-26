# 🔐 License System - Nhà thuốc Management

## 📋 Tổng quan

Hệ thống license sử dụng mã hóa Ed25519 để bảo vệ phần mềm, đảm bảo chỉ khách hàng có license hợp lệ mới có thể sử dụng đầy đủ tính năng.

## 🚀 Cài đặt

### 1. Tạo cặp khóa
```bash
python create_keys.py
```

### 2. Cập nhật Public Key trong phần mềm chính
Copy `PUBLIC_B64` từ output và paste vào `nhathuoc2.py`:
```python
PUBLIC_B64 = "your_public_key_here"
```

### 3. Chạy License Generator
```bash
python license_generator.py
```

## 📝 Quy trình bán phần mềm

### Bước 1: Khách hàng chạy phần mềm
1. Phần mềm hiển thị dialog kích hoạt
2. Hiển thị **Hardware Fingerprint** (tự động copy vào clipboard)
3. Khách hàng gửi fingerprint cho bạn

### Bước 2: Tạo license
1. Mở `license_generator.py`
2. Nhập thông tin:
   - **Tên khách hàng**: Tên khách hàng
   - **Hardware Fingerprint**: Mã từ khách hàng
   - **Ngày hết hạn**: Ngày hết hạn license
   - **Tính năng**: Full hoặc Basic
3. Click "🔑 Tạo License"
4. License sẽ được copy vào clipboard

### Bước 3: Gửi license cho khách hàng
1. Gửi license cho khách hàng
2. Khách hàng paste license vào dialog kích hoạt
3. Phần mềm sẽ verify và kích hoạt

## 🔧 Cấu trúc License

```json
{
  "payload": {
    "product": "nhathuoc",
    "customer": "Tên khách hàng",
    "hw": "a1b2c3d4e5f6g7h8",
    "expires": "2025-12-31",
    "features": ["full"],
    "created": "2024-01-01 10:00:00"
  },
  "sig": "chữ_ký_số_Ed25519"
}
```

## 🛡️ Bảo mật

- **Ed25519**: Thuật toán mã hóa mạnh mẽ
- **Hardware Fingerprint**: Gắn license với máy tính cụ thể
- **Chữ ký số**: Đảm bảo license không bị giả mạo
- **Offline**: Không cần kết nối internet để verify

## 📁 Files quan trọng

- `private_key.pem` - **GIỮ BÍ MẬT** - Dùng để tạo license
- `public_key.pem` - Public key (PEM format)
- `public_key_b64.txt` - Public key (base64 raw)
- `license_generator.py` - Tool tạo license
- `create_keys.py` - Script tạo cặp khóa

## ⚠️ Lưu ý

1. **Bảo mật Private Key**: Không chia sẻ `private_key.pem` với ai
2. **Backup**: Sao lưu private key ở nơi an toàn
3. **Hardware Fingerprint**: Mỗi máy tính có fingerprint duy nhất
4. **License Transfer**: License không thể chuyển sang máy khác

## 🔄 Renewal License

Để gia hạn license:
1. Khách hàng gửi lại hardware fingerprint
2. Tạo license mới với ngày hết hạn mới
3. Gửi license mới cho khách hàng

## 🆘 Troubleshooting

### Lỗi "License không hợp lệ"
- Kiểm tra hardware fingerprint có đúng không
- Kiểm tra private key có đúng không
- Kiểm tra ngày hết hạn

### Lỗi "License không thuộc máy này"
- Hardware fingerprint không khớp
- Khách hàng đã thay đổi phần cứng

### Lỗi "Chưa kích hoạt"
- Khách hàng chưa nhập license
- File license bị xóa hoặc hỏng
