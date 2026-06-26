# 📚 HƯỚNG DẪN SỬ DỤNG PHẦN MỀM QUẢN LÝ KHO HÀNG HÓA

## 📋 MỤC LỤC
1. [Giới thiệu tổng quan](#giới-thiệu-tổng-quan)
2. [Cài đặt và khởi động](#cài-đặt-và-khởi-động)
3. [Hướng dẫn sử dụng cơ bản](#hướng-dẫn-sử-dụng-cơ-bản)
4. [Các tính năng nổi bật](#các-tính-năng-nổi-bật)
5. [Hướng dẫn chi tiết từng module](#hướng-dẫn-chi-tiết-từng-module)
6. [Tính năng cần hoàn thiện](#tính-năng-cần-hoàn-thiện)
7. [Đóng gói ứng dụng](#đóng-gói-ứng-dụng)
8. [Troubleshooting](#troubleshooting)
9. [Liên hệ hỗ trợ](#liên-hệ-hỗ-trợ)

---

## 🎯 GIỚI THIỆU TỔNG QUAN

**Phần mềm Quản lý kho hàng hóa** là một ứng dụng desktop được phát triển bằng Python, sử dụng giao diện ttkbootstrap hiện đại. Phần mềm được thiết kế đặc biệt cho các nhà thuốc, cửa hàng dược phẩm và các cơ sở kinh doanh cần quản lý kho hàng chuyên nghiệp.

### **Thông tin phần mềm:**
- **Tên:** Quản lý kho hàng hóa
- **Phiên bản:** 1.0.0
- **Tác giả:** Hồ Sỷ Thoảng
- **Email:** hstptcn5@gmail.com
- **Điện thoại:** 0329381189
- **Website:** x/yoshinokuna

### **Đặc điểm nổi bật:**
- ✅ **Giao diện hiện đại** với ttkbootstrap
- ✅ **Quản lý đa dạng sản phẩm** (thuốc, hàng hóa)
- ✅ **Hệ thống barcode** với camera
- ✅ **Báo cáo nâng cao** với xuất Excel/PDF
- ✅ **Sao lưu tự động** và khôi phục dữ liệu
- ✅ **Hệ thống license** bảo mật
- ✅ **Danh mục thuốc** tự động

---

## 🔧 CÀI ĐẶT VÀ KHỞI ĐỘNG

### **Yêu cầu hệ thống:**
- **Hệ điều hành:** Windows 10/11, macOS, Linux
- **Python:** 3.8 trở lên
- **RAM:** Tối thiểu 4GB
- **Ổ cứng:** 500MB trống
- **Camera:** (Tùy chọn) cho tính năng quét barcode

### **Bước 1: Cài đặt Python**
```bash
# Tải Python từ: https://www.python.org/downloads/
# Đảm bảo tick "Add Python to PATH" khi cài đặt
```

### **Bước 2: Cài đặt thư viện**
```bash
# Cài đặt tất cả thư viện cần thiết
pip install -r requirements.txt

# Hoặc cài đặt từng thư viện:
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

### **Bước 3: Khởi động phần mềm**
```bash
# Chạy phần mềm
python nhathuoc2.py
```

### **Bước 4: Kích hoạt license (Lần đầu)**
1. Phần mềm sẽ hiển thị dialog kích hoạt
2. Copy **Hardware Fingerprint** (tự động copy vào clipboard)
3. Gửi fingerprint cho tác giả để nhận license
4. Paste license vào dialog kích hoạt
5. Click "Kích hoạt" để hoàn tất

---

## 🚀 HƯỚNG DẪN SỬ DỤNG CƠ BẢN

### **Giao diện chính:**
Phần mềm có giao diện tab với các module chính:

1. **📦 Sản phẩm** - Quản lý danh mục sản phẩm
2. **📥 Nhập hàng** - Nhập hàng vào kho
3. **🧾 Bán hàng POS** - Bán hàng tại quầy
4. **📊 Tồn kho** - Xem tồn kho hiện tại
5. **⚠️ Cảnh báo** - Cảnh báo hết hàng
6. **📈 Báo cáo** - Báo cáo cơ bản
7. **📊 Báo cáo nâng cao** - Báo cáo chi tiết
8. **💾 Sao lưu** - Sao lưu và khôi phục

### **Workflow cơ bản:**
1. **Thêm sản phẩm** → Tab "Sản phẩm"
2. **Nhập hàng** → Tab "Nhập hàng"
3. **Bán hàng** → Tab "Bán hàng POS"
4. **Xem báo cáo** → Tab "Báo cáo nâng cao"

---

## ⭐ CÁC TÍNH NĂNG NỔI BẬT

### **1. 🏥 Quản lý danh mục thuốc**
- **Tự động load** file `thuoc.csv` khi khởi động
- **Autocomplete** tên thuốc với gợi ý thông minh
- **Tự động điền** thông tin: tên, số đăng ký, đơn vị
- **Hỗ trợ** cả thuốc và hàng hóa thông thường

### **2. 📷 Quét barcode bằng camera**
- **Real-time scanning** với OpenCV
- **Hỗ trợ nhiều định dạng:** EAN, UPC, Code128, QR Code
- **Tự động điền** thông tin sản phẩm
- **Giao diện chuyên nghiệp** với video feed

### **3. 📊 Báo cáo nâng cao**
- **Báo cáo doanh thu** theo ngày/tháng/năm
- **Báo cáo lợi nhuận** chi tiết
- **Top sản phẩm** bán chạy
- **Biểu đồ trực quan** với matplotlib
- **Xuất Excel/PDF/CSV** chuyên nghiệp

### **4. 💾 Sao lưu và khôi phục**
- **Sao lưu tự động** hàng ngày
- **Sao lưu thủ công** bất kỳ lúc nào
- **Khôi phục** từ file backup
- **Export/Import** toàn bộ dữ liệu

### **5. 🔐 Hệ thống license**
- **Bảo mật Ed25519** với chữ ký số
- **Hardware fingerprinting** gắn với máy tính
- **License Generator Tool** cho việc bán phần mềm
- **Offline verification** không cần internet

### **6. 🎨 Giao diện hiện đại**
- **Theme ttkbootstrap** tươi sáng
- **Toolbar** với các nút nhanh
- **Status bar** hiển thị thông tin chi tiết
- **Tooltips** hướng dẫn sử dụng

---

## 📖 HƯỚNG DẪN CHI TIẾT TỪNG MODULE

### **📦 MODULE SẢN PHẨM**

#### **Thêm sản phẩm mới:**
1. Vào tab **"📦 Sản phẩm"**
2. Điền thông tin:
   - **Tên sản phẩm:** Gõ 2+ ký tự để xem gợi ý
   - **Loại sản phẩm:** Chọn "Thuốc" hoặc "Hàng hóa"
   - **Đơn vị cơ sở:** Ví dụ: vien, chai, hộp
   - **Barcode:** Nhập thủ công hoặc quét camera (nút 📷)
   - **Số đăng ký:** (Chỉ hiện khi chọn "Thuốc")
3. Click **"Lưu sản phẩm"**

#### **Quản lý danh mục thuốc:**
- **Load Excel/CSV:** Click "📄 Load Excel/CSV"
- **Load nhanh:** Click "📄 Load thuoc.csv"
- **Tìm kiếm:** Click "🔍 Tìm thuốc"
- **Thông tin:** Click "ℹ️ Thông tin"

#### **Tính năng autocomplete:**
- Gõ 2+ ký tự trong ô "Tên sản phẩm"
- Chọn từ danh sách gợi ý
- Tự động điền: tên, loại, số đăng ký, đơn vị

### **📥 MODULE NHẬP HÀNG**

#### **Nhập hàng vào kho:**
1. Vào tab **"📥 Nhập hàng"**
2. Chọn sản phẩm từ dropdown
3. Nhập thông tin:
   - **Số lô:** Mã lô sản xuất
   - **Hạn sử dụng:** Ngày hết hạn
   - **Số lượng:** Số lượng nhập
   - **Đơn vị:** Đơn vị tính
   - **Giá nhập:** Giá mua vào
4. Click **"Nhập hàng"**

### **🧾 MODULE BÁN HÀNG POS**

#### **Bán hàng tại quầy:**
1. Vào tab **"🧾 Bán hàng POS"**
2. **Quét barcode:**
   - Nhập barcode thủ công
   - Hoặc click "📷 Quét" để dùng camera
3. **Tìm sản phẩm:**
   - Gõ tên sản phẩm
   - Chọn từ dropdown
4. **Thêm vào giỏ:**
   - Nhập số lượng
   - Click "Thêm vào giỏ"
5. **Thanh toán:**
   - Xem tổng tiền
   - Nhập số tiền khách đưa
   - Click "Thanh toán"

#### **Tính năng quét barcode:**
- **Mở camera:** Click "📷 Quét"
- **Đưa barcode** vào khung hình
- **Tự động thêm** vào giỏ hàng
- **Điều khiển:** Bắt đầu/Dừng/Đóng

### **📊 MODULE BÁO CÁO NÂNG CAO**

#### **Xem báo cáo:**
1. Vào tab **"📊 Báo cáo nâng cao"**
2. Chọn khoảng thời gian
3. Click loại báo cáo:
   - **💰 Báo cáo doanh thu**
   - **📊 Báo cáo lợi nhuận**
   - **🏆 Top sản phẩm**
   - **📈 Biểu đồ doanh thu**

#### **Xuất báo cáo:**
- **📊 Excel:** Xuất file .xlsx
- **📄 PDF:** Xuất file .pdf
- **📋 CSV:** Xuất file .csv

### **💾 MODULE SAO LƯU**

#### **Sao lưu thủ công:**
1. Vào tab **"💾 Sao lưu"**
2. Click **"💾 Sao lưu ngay"**
3. Chọn vị trí lưu file

#### **Sao lưu tự động:**
- Tự động sao lưu hàng ngày lúc 23:00
- Lưu trong thư mục `%LOCALAPPDATA%\Nhathuoc\backups`

#### **Khôi phục:**
1. Click **"🔄 Khôi phục"**
2. Chọn file backup
3. Xác nhận khôi phục

---

## 🔨 TÍNH NĂNG CẦN HOÀN THIỆN

### **1. 👥 Quản lý người dùng và phân quyền**
- **Đăng nhập/đăng xuất** hệ thống
- **Phân quyền:** Admin, Nhân viên bán hàng, Kế toán
- **Log hoạt động** của từng user
- **Session management** và timeout

### **2. ⚠️ Cảnh báo tồn kho thấp**
- **Thiết lập mức tồn kho tối thiểu** cho từng sản phẩm
- **Cảnh báo khi sắp hết hàng**
- **Gợi ý nhập hàng** tự động
- **Email/SMS notification**

### **3. ✅ Validation dữ liệu mạnh mẽ hơn**
- **Kiểm tra định dạng barcode** (EAN, UPC...)
- **Validate ngày hết hạn** (không được quá khứ)
- **Kiểm tra số lượng âm**
- **Xác thực giá trị tiền tệ**

### **4. 🚀 Tối ưu hóa hiệu suất**
- **Lazy loading** cho dữ liệu lớn
- **Caching** cho các truy vấn thường dùng
- **Pagination** cho danh sách dài
- **Background processing** cho báo cáo

### **5. 🌐 Tích hợp mở rộng**
- **API REST** cho tích hợp hệ thống khác
- **Webhook** cho thông báo real-time
- **Cloud sync** cho đồng bộ dữ liệu
- **Mobile app** companion

### **6. 📱 Cải thiện UX/UI**
- **Dark mode** theme
- **Keyboard shortcuts** cho thao tác nhanh
- **Drag & drop** cho file import
- **Multi-language** support

---

## 📦 ĐÓNG GÓI ỨNG DỤNG

### **Sử dụng PyInstaller:**

#### **Bước 1: Cài đặt PyInstaller**
```bash
pip install pyinstaller
```

#### **Bước 2: Tạo file spec (Tùy chọn)**
```bash
pyi-makespec --onefile --windowed --name="QuanLyKho" nhathuoc2.py
```

#### **Bước 3: Đóng gói ứng dụng**
```bash
# Đóng gói cơ bản
pyinstaller --onefile --windowed nhathuoc2.py

# Đóng gói với icon và metadata
pyinstaller --onefile --windowed --icon=icon.ico --name="QuanLyKho" nhathuoc2.py

# Đóng gói với tất cả dependencies
pyinstaller --onefile --windowed --hidden-import=pandas --hidden-import=matplotlib --hidden-import=opencv-python --hidden-import=pyzbar --hidden-import=reportlab nhathuoc2.py
```

#### **Bước 4: Tạo installer (Tùy chọn)**
```bash
# Sử dụng Inno Setup (Windows)
# Tạo file .iss script để tạo installer

# Sử dụng NSIS (Cross-platform)
# Tạo file .nsi script
```

### **Script đóng gói tự động:**

#### **build.bat (Windows):**
```batch
@echo off
echo Building QuanLyKho application...

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build with PyInstaller
pyinstaller --onefile --windowed --name="QuanLyKho" --icon=icon.ico --add-data="thuoc.csv;." --hidden-import=pandas --hidden-import=matplotlib --hidden-import=cv2 --hidden-import=pyzbar --hidden-import=reportlab nhathuoc2.py

echo Build completed! Check dist folder.
pause
```

#### **build.sh (Linux/macOS):**
```bash
#!/bin/bash
echo "Building QuanLyKho application..."

# Clean previous builds
rm -rf dist build

# Build with PyInstaller
pyinstaller --onefile --windowed --name="QuanLyKho" --icon=icon.ico --add-data="thuoc.csv:." --hidden-import=pandas --hidden-import=matplotlib --hidden-import=cv2 --hidden-import=pyzbar --hidden-import=reportlab nhathuoc2.py

echo "Build completed! Check dist folder."
```

### **Tạo License Generator Tool:**
```bash
# Đóng gói License Generator
pyinstaller --onefile --windowed --name="LicenseGenerator" license_generator.py

# Đóng gói Key Creator
pyinstaller --onefile --windowed --name="KeyCreator" create_keys.py
```

### **Cấu trúc thư mục sau khi đóng gói:**
```
QuanLyKho/
├── QuanLyKho.exe          # Ứng dụng chính
├── LicenseGenerator.exe   # Tool tạo license
├── KeyCreator.exe         # Tool tạo key
├── thuoc.csv             # Danh mục thuốc mẫu
├── README.txt            # Hướng dẫn cài đặt
└── docs/                 # Tài liệu
    ├── HUONG_DAN_SU_DUNG.md
    ├── BARCODE_SETUP.md
    ├── EXPORT_REPORTS.md
    └── README_LICENSE.md
```

---

## 🛠️ TROUBLESHOOTING

### **Lỗi thường gặp:**

#### **1. Lỗi "Module not found"**
```bash
# Giải pháp: Cài đặt thư viện thiếu
pip install [tên_thư_viện]
```

#### **2. Lỗi camera không hoạt động**
- Kiểm tra camera có được kết nối
- Đảm bảo không có ứng dụng khác đang sử dụng camera
- Cài đặt: `pip install opencv-python pyzbar Pillow`

#### **3. Lỗi license không hợp lệ**
- Kiểm tra hardware fingerprint có đúng
- Đảm bảo license chưa hết hạn
- Liên hệ tác giả để gia hạn

#### **4. Lỗi database bị khóa**
- Đóng tất cả instance của phần mềm
- Xóa file `pharm.db-wal` và `pharm.db-shm`
- Khởi động lại phần mềm

#### **5. Lỗi xuất Excel/PDF**
- Cài đặt: `pip install pandas openpyxl reportlab`
- Kiểm tra quyền ghi file
- Đảm bảo có dữ liệu để xuất

### **Log files:**
- **App log:** `%LOCALAPPDATA%\Nhathuoc\app.log`
- **Database:** `%LOCALAPPDATA%\Nhathuoc\pharm.db`
- **Backups:** `%LOCALAPPDATA%\Nhathuoc\backups\`

### **Reset toàn bộ:**
```bash
# Xóa tất cả dữ liệu (CẨN THẬN!)
rmdir /s /q "%LOCALAPPDATA%\Nhathuoc"
```

---

## 📞 LIÊN HỆ HỖ TRỢ

### **Thông tin liên hệ:**
- **Tác giả:** Hồ Sỷ Thoảng
- **Email:** hstptcn5@gmail.com
- **Điện thoại:** 0329381189
- **Website:** x/yoshinokuna

### **Hỗ trợ kỹ thuật:**
- **Báo lỗi:** Gửi email với mô tả chi tiết
- **Yêu cầu tính năng:** Mô tả rõ ràng nhu cầu
- **Hướng dẫn sử dụng:** Tham khảo tài liệu này

### **Cập nhật phần mềm:**
- **Phiên bản mới:** Kiểm tra website thường xuyên
- **Changelog:** Xem file CHANGELOG.md
- **Migration:** Hướng dẫn cập nhật database

---

## 📄 PHỤ LỤC

### **A. Cấu trúc database:**
```sql
-- Bảng sản phẩm
products (id, name, defaultUnit, barcode, productType, registrationNumber, createdAt)

-- Bảng đơn vị sản phẩm
product_units (id, productId, unitCode, toBaseQty, price)

-- Bảng lô hàng
batches (id, productId, lotNo, expiryDate)

-- Bảng xuất nhập kho
stock_movements (id, productId, batchId, unitCode, qty, type, cost, createdAt)

-- Bảng bán hàng
sales (id, createdAt, total, paid, change, note)

-- Bảng chi tiết bán hàng
sale_items (id, saleId, productId, unitCode, qty, price)
```

### **B. Cấu trúc license:**
```json
{
  "payload": {
    "product": "nhathuoc",
    "customer": "Tên khách hàng",
    "hw": "hardware_fingerprint",
    "expires": "2025-12-31",
    "features": ["full"],
    "created": "2024-01-01 10:00:00"
  },
  "sig": "ed25519_signature"
}
```

### **C. Keyboard shortcuts:**
- **Ctrl+N:** Sản phẩm mới
- **Ctrl+S:** Lưu
- **Ctrl+O:** Mở
- **F1:** Trợ giúp
- **Esc:** Đóng dialog

---

**© 2024 Hồ Sỷ Thoảng. Tất cả quyền được bảo lưu.**

*Phiên bản tài liệu: 1.0.0 - Cập nhật: 2024*
