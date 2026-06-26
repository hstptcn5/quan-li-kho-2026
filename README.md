# 🏥 Quản lý kho hàng hóa - Pharmacy Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Commercial-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-green.svg)](CHANGELOG.md)

> **Phần mềm quản lý kho hàng hóa chuyên nghiệp dành cho nhà thuốc, cửa hàng dược phẩm và các cơ sở kinh doanh cần quản lý kho hàng hiệu quả.**

## 🎯 Tổng quan

**Quản lý kho hàng hóa** là một ứng dụng desktop được phát triển bằng Python với giao diện hiện đại, tích hợp nhiều tính năng chuyên nghiệp để quản lý kho hàng một cách hiệu quả và chính xác.

### ✨ Tính năng nổi bật

- 🏥 **Quản lý danh mục thuốc** với autocomplete thông minh
- 📷 **Quét barcode** bằng camera real-time
- 📊 **Báo cáo nâng cao** với xuất Excel/PDF
- 💾 **Sao lưu tự động** và khôi phục dữ liệu
- 🔐 **Hệ thống license** bảo mật với Ed25519
- 🎨 **Giao diện hiện đại** với ttkbootstrap
- 📈 **Biểu đồ trực quan** với matplotlib

## 🚀 Cài đặt nhanh

### Yêu cầu hệ thống
- **Python 3.8+**
- **Windows 10/11, macOS, hoặc Linux**
- **RAM:** Tối thiểu 4GB
- **Camera:** (Tùy chọn) cho tính năng quét barcode

### Cài đặt
```bash
# 1. Clone repository
git clone https://github.com/your-repo/quan-ly-kho.git
cd quan-ly-kho

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Chạy phần mềm
python nhathuoc2.py
```

### Cài đặt dependencies
```bash
pip install ttkbootstrap>=1.10.1
pip install cryptography>=3.4.8
pip install schedule>=1.2.0
pip install matplotlib>=3.5.0
pip install pandas>=1.5.0
pip install openpyxl>=3.0.0
pip install opencv-python>=4.5.0
pip install pyzbar>=0.1.9
pip install Pillow>=8.0.0
pip install reportlab>=3.6.0
```

## 📱 Hướng dẫn sử dụng

### Workflow cơ bản
1. **Thêm sản phẩm** → Tab "📦 Sản phẩm"
2. **Nhập hàng** → Tab "📥 Nhập hàng"  
3. **Bán hàng** → Tab "🧾 Bán hàng POS"
4. **Xem báo cáo** → Tab "📊 Báo cáo nâng cao"

### Tính năng chính

#### 🏥 Quản lý danh mục thuốc
- Tự động load file `thuoc.csv`
- Autocomplete tên thuốc với gợi ý
- Tự động điền thông tin: tên, số đăng ký, đơn vị

#### 📷 Quét barcode
- Quét barcode bằng camera
- Hỗ trợ nhiều định dạng: EAN, UPC, Code128, QR Code
- Tự động điền thông tin sản phẩm

#### 📊 Báo cáo nâng cao
- Báo cáo doanh thu theo ngày/tháng/năm
- Báo cáo lợi nhuận chi tiết
- Top sản phẩm bán chạy
- Xuất Excel/PDF/CSV

## 🛠️ Đóng gói ứng dụng

### Windows
```bash
# Chạy script đóng gói
build.bat
```

### Linux/macOS
```bash
# Chạy script đóng gói
./build.sh
```

### Thủ công
```bash
# Cài đặt PyInstaller
pip install pyinstaller

# Đóng gói ứng dụng
pyinstaller --onefile --windowed --name="QuanLyKho" nhathuoc2.py
```

## 📚 Tài liệu

- 📖 **[Hướng dẫn sử dụng](HUONG_DAN_SU_DUNG.md)** - Hướng dẫn toàn diện
- 📷 **[Cài đặt barcode scanner](BARCODE_SETUP.md)** - Hướng dẫn quét barcode
- 📊 **[Xuất báo cáo](EXPORT_REPORTS.md)** - Hướng dẫn xuất Excel/PDF
- 🔐 **[Hệ thống license](README_LICENSE.md)** - Hướng dẫn license
- 📝 **[Changelog](CHANGELOG.md)** - Lịch sử phiên bản

## 🔐 Hệ thống License

Phần mềm sử dụng hệ thống license bảo mật với Ed25519:

### Kích hoạt license
1. Chạy phần mềm lần đầu
2. Copy **Hardware Fingerprint** (tự động copy vào clipboard)
3. Gửi fingerprint cho tác giả
4. Nhận license và paste vào dialog kích hoạt

### Tạo license (Cho tác giả)
```bash
# Chạy License Generator
python license_generator.py

# Tạo cặp khóa mới
python create_keys.py
```

## 🏗️ Kiến trúc

### Cấu trúc dự án
```
quan-ly-kho/
├── nhathuoc2.py              # Ứng dụng chính
├── license_generator.py      # Tool tạo license
├── create_keys.py           # Tool tạo khóa
├── requirements.txt         # Dependencies
├── build.bat/build.sh       # Script đóng gói
├── thuoc.csv               # Danh mục thuốc mẫu
├── docs/                   # Tài liệu
│   ├── HUONG_DAN_SU_DUNG.md
│   ├── BARCODE_SETUP.md
│   ├── EXPORT_REPORTS.md
│   └── README_LICENSE.md
└── README.md               # File này
```

### Database Schema
```sql
-- Sản phẩm
products (id, name, defaultUnit, barcode, productType, registrationNumber, createdAt)

-- Đơn vị sản phẩm  
product_units (id, productId, unitCode, toBaseQty, price)

-- Lô hàng
batches (id, productId, lotNo, expiryDate)

-- Xuất nhập kho
stock_movements (id, productId, batchId, unitCode, qty, type, cost, createdAt)

-- Bán hàng
sales (id, createdAt, total, paid, change, note)

-- Chi tiết bán hàng
sale_items (id, saleId, productId, unitCode, qty, price)
```

## 🚀 Roadmap

### [1.1.0] - Planned
- 👥 Quản lý người dùng và phân quyền
- ⚠️ Cảnh báo tồn kho nâng cao
- ✅ Validation dữ liệu mạnh mẽ hơn
- 🌙 Dark mode theme

### [1.2.0] - Planned  
- 🚀 Tối ưu hóa hiệu suất
- 📱 Mobile companion app
- 🌐 API REST cho tích hợp
- ☁️ Cloud sync dữ liệu

### [2.0.0] - Future
- 🌍 Multi-language support
- 🔌 Plugin system
- 📊 Advanced analytics
- 🤖 AI recommendations

## 🐛 Báo lỗi & Yêu cầu tính năng

### Báo lỗi
- **Email:** hstptcn5@gmail.com
- **Mô tả:** Chi tiết lỗi, steps to reproduce, system info

### Yêu cầu tính năng
- **Email:** hstptcn5@gmail.com  
- **Mô tả:** Use case, expected behavior, priority

## 📞 Liên hệ

- **Tác giả:** Hồ Sỷ Thoảng
- **Email:** hstptcn5@gmail.com
- **Điện thoại:** 0329381189
- **Website:** x/yoshinokuna

## 📄 License

**Commercial License** - Tất cả quyền được bảo lưu.

Phần mềm này được bảo vệ bởi hệ thống license Ed25519. Việc sử dụng trái phép sẽ bị truy cứu trách nhiệm pháp lý.

## 🙏 Acknowledgments

- **ttkbootstrap** - Modern UI framework
- **OpenCV** - Computer vision library
- **matplotlib** - Data visualization
- **pandas** - Data manipulation
- **ReportLab** - PDF generation
- **cryptography** - Security library

---

**© 2024 Hồ Sỷ Thoảng. Tất cả quyền được bảo lưu.**

*Phiên bản: 1.0.0 | Cập nhật: 2024*
