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

**Hệ thống Quản lý Xuất-Nhập-Tồn CDC** là một ứng dụng desktop được phát triển bằng Python, sử dụng giao diện ttkbootstrap hiện đại. Phần mềm được thiết kế đặc biệt cho Trung tâm Kiểm soát bệnh tật (CDC) và các cơ sở y tế nhằm quản lý kho thuốc, vaccine và vật tư y tế (VTYT) chuyên nghiệp.

### **Thông tin phần mềm:**
- **Tên:** Quản lý XNT thuốc, vaccine và VTYT
- **Phiên bản:** 2.0.0
- **Tác giả:** Hồ Sỷ Thoảng
- **Email:** hstptcn5@gmail.com
- **Điện thoại:** 0329381189
- **Website:** x/yoshinokuna

### **Đặc điểm nổi bật:**
- ✅ **Giao diện hiện đại** với ttkbootstrap
- ✅ **Quản lý đa dạng sản phẩm** (thuốc, vaccine, vật tư y tế)
- ✅ **Quy trình xuất FEFO** tự động ưu tiên lô cận hạn dùng trước
- ✅ **Hệ thống barcode** quét bằng camera di động hoặc webcam
- ✅ **Báo cáo XNT & Biên bản kiểm kê** chuyên nghiệp theo mẫu y tế
- ✅ **Sao lưu tự động** và khôi phục dữ liệu
- ✅ **Không cần license** sử dụng trực tiếp và vĩnh viễn

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

---

## 🚀 HƯỚNG DẪN SỬ DỤNG CƠ BẢN

### **Giao diện chính:**
Phần mềm có giao diện tab với các module chính:

1. **📦 Sản phẩm** - Quản lý danh mục sản phẩm
2. **📥 Nhập kho** - Lập phiếu nhập kho nhiều sản phẩm
3. **📤 Xuất kho / Cấp phát** - Lập phiếu xuất kho cấp phát theo nguyên tắc FEFO
4. **📊 Tồn kho** - Xem tồn kho hiện tại
5. **⏰ Hết hạn** - Quản lý và cảnh báo hạn dùng thuốc
6. **📄 Báo cáo XNT** - Báo cáo Xuất - Nhập - Tồn chi tiết
7. **📈 Báo cáo nâng cao** - Báo cáo thống kê chi tiết theo đơn vị nhận, trend biểu đồ
8. **💾 Backup** - Sao lưu và khôi phục cơ sở dữ liệu
9. **📱 Kiểm kho di động** - Module máy chủ mini đồng bộ với điện thoại

### **Workflow cơ bản:**
1. **Khai báo sản phẩm** → Tab "Sản phẩm" (Hỗ trợ tự động autocomplete từ danh mục thuốc chuẩn của CDC hoặc tạo thuốc mới tự do)
2. **Lập Phiếu Nhập** → Tab "Nhập kho"
3. **Lập Phiếu Xuất** → Tab "Xuất kho / Cấp phát" (FEFO tự động)
4. **Xem báo cáo & Biên bản kiểm kê** → Tab "Báo cáo XNT" hoặc "Báo cáo nâng cao"

---

## ⭐ CÁC TÍNH NĂNG NỔI BẬT

### **1. 🏥 Quản lý danh mục chuẩn hóa**
- **Tự động load** file `thuoc.csv` khi khởi động
- **Autocomplete** tên thuốc/vaccine với gợi ý thông minh
- **Tự động điền** thông tin chuẩn: tên, đơn vị cơ sở, số đăng ký
- **Hỗ trợ** linh hoạt tạo thuốc ngoài danh mục khi cần thiết

### **2. 📷 Quét barcode bằng camera di động**
- **Real-time scanning** trực tiếp qua camera điện thoại thông qua module companion di động
- **Hỗ trợ nhiều định dạng:** EAN, UPC, Code128, QR Code
- **Tự động điền** thông tin sản phẩm và quản lý lô/hạn dùng ngay trên điện thoại

### **3. 📊 Báo cáo nâng cao & Biên bản kiểm kê y tế**
- **Báo cáo XNT** chi tiết theo từng Số lô và Hạn sử dụng của sản phẩm
- **Kết xuất Biên bản kiểm kê** (Mẫu C33-HD) độc lập ra PDF có sẵn cột Số lượng sổ sách và ô trống đếm thực tế
- **Vẽ biểu đồ** xu hướng cấp phát y tế trực quan
- **Xuất Excel/PDF/CSV** chuyên nghiệp, in ấn độc lập qua thư viện ReportLab

### **4. 💾 Sao lưu và khôi phục dữ liệu**
- **Sao lưu tự động** hàng ngày
- **Sao lưu thủ công** bất kỳ lúc nào
- **Khôi phục** an toàn từ file backup

### **5. 🎨 Giao diện hiện đại & Đồng bộ**
- **Theme ttkbootstrap** Flatly sạch sẽ, chuyên nghiệp
- **Toolbar** với các nút nhanh đồng bộ màu xanh dương nhạt (info)
- **Status bar** hiển thị thông tin chi tiết và Tooltips hướng dẫn sử dụng

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

### **📤 MODULE XUẤT KHO / CẤP PHÁT**

#### **Lập Phiếu xuất kho:**
1. Vào tab **"📤 Xuất kho / Cấp phát"**
2. **Chọn Sản phẩm**:
   - Gõ tên sản phẩm/thuốc để xem gợi ý autocomplete.
   - Nhập Số lượng xuất.
   - Click **"Thêm vào giỏ"**. Hệ thống sẽ tự động phân bổ theo lô có hạn sử dụng gần nhất (FEFO).
3. **Thông tin phiếu xuất**:
   - Nhập tên **Đơn vị nhận** (tự động gợi ý nếu đã từng xuất).
   - Chọn **Ngày xuất** (mặc định là ngày hiện tại).
   - Nhập **Lý do xuất** (Cấp phát định kỳ, Viện trợ tuyến dưới, Chuyển kho...).
4. Click **"Lập phiếu & In PDF"** để kết xuất phiếu xuất kho.

#### **Tính năng quét barcode:**
- Dùng camera điện thoại thông qua App di động để quét trực tiếp và tự động thêm sản phẩm vào giỏ xuất.

### **📊 MODULE BÁO CÁO NÂNG CAO**

#### **Xem báo cáo:**
1. Vào tab **"📊 Báo cáo nâng cao"**
2. Chọn khoảng thời gian cần thống kê.
3. Click chọn loại báo cáo:
   - **💰 Thống kê Cấp phát theo ngày**: Tổng quan lượng cấp phát qua các ngày.
   - **🏢 Thống kê theo Đơn vị nhận**: Phân tích chi tiết thuốc được chuyển tới những đơn vị nào.
   - **🏆 Top sản phẩm cấp phát**: Thống kê các thuốc/vaccine dùng nhiều nhất.
   - **📈 Biểu đồ xu hướng**: Trực quan hóa dữ liệu bằng biểu đồ.

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

### **Cấu trúc thư mục sau khi đóng gói:**
```
QuanLyKho/
├── QuanLyKho.exe          # Ứng dụng chính
├── thuoc.csv             # Danh mục thuốc mẫu
├── README.txt            # Hướng dẫn cài đặt
└── docs/                 # Tài liệu
    ├── HUONG_DAN_SU_DUNG.md
    ├── BARCODE_SETUP.md
    └── EXPORT_REPORTS.md
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

### **B. Keyboard shortcuts:**
- **Ctrl+N:** Sản phẩm mới
- **Ctrl+S:** Lưu
- **Ctrl+O:** Mở
- **F1:** Trợ giúp
- **Esc:** Đóng dialog

---

**© 2026 Hồ Sỷ Thoảng. Tất cả quyền được bảo lưu.**

*Phiên bản tài liệu: 2.0.0 - Cập nhật: 2026*
