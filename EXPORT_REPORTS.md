# 📊 Hướng dẫn xuất báo cáo Excel/PDF

## 📋 Tổng quan

Phần mềm đã được tích hợp tính năng xuất báo cáo ra nhiều định dạng:
- **📊 Excel (.xlsx)** - Định dạng bảng tính chuyên nghiệp
- **📄 PDF (.pdf)** - Định dạng tài liệu in ấn
- **📋 CSV (.csv)** - Định dạng dữ liệu thuần

## 🔧 Cài đặt thư viện

### Bước 1: Cài đặt thư viện cần thiết
```bash
# Cho Excel
pip install pandas openpyxl

# Cho PDF
pip install reportlab

# Tất cả cùng lúc
pip install pandas openpyxl reportlab
```

### Bước 2: Khởi động lại phần mềm
Sau khi cài đặt xong, khởi động lại phần mềm để sử dụng tính năng xuất báo cáo.

## 📱 Cách sử dụng

### 1. Truy cập báo cáo nâng cao
1. Vào tab **"📊 Báo cáo nâng cao"**
2. Chọn khoảng thời gian (Từ ngày - Đến ngày)
3. Click vào một trong các báo cáo:
   - 💰 Báo cáo doanh thu
   - 📊 Báo cáo lợi nhuận
   - 🏆 Top sản phẩm
   - 📈 Biểu đồ doanh thu

### 2. Xuất báo cáo
Sau khi xem báo cáo, click vào nút xuất tương ứng:

#### **📊 Xuất Excel**
- Click nút **"📊 Excel"**
- Chọn vị trí lưu file
- File sẽ được lưu với định dạng `.xlsx`
- Tự động format header, điều chỉnh độ rộng cột

#### **📄 Xuất PDF**
- Click nút **"📄 PDF"**
- Chọn vị trí lưu file
- File sẽ được lưu với định dạng `.pdf`
- Có tiêu đề, bảng đẹp, phù hợp in ấn

#### **📋 Xuất CSV**
- Click nút **"📋 CSV"**
- Chọn vị trí lưu file
- File sẽ được lưu với định dạng `.csv`
- Định dạng UTF-8, tương thích Excel

## 🎯 Tính năng

### **Excel Export:**
- ✅ **Auto-format** header với font đậm và màu nền
- ✅ **Auto-adjust** độ rộng cột
- ✅ **Multiple sheets** (nếu cần)
- ✅ **Professional styling** với openpyxl

### **PDF Export:**
- ✅ **Professional layout** với ReportLab
- ✅ **Table formatting** với border và màu sắc
- ✅ **Title và metadata** rõ ràng
- ✅ **Print-ready** format

### **CSV Export:**
- ✅ **UTF-8 encoding** hỗ trợ tiếng Việt
- ✅ **Compatible** với Excel, Google Sheets
- ✅ **Lightweight** và nhanh

## 📁 Cấu trúc file xuất

### **Tên file tự động:**
```
bao_cao_2024-01-01_to_2024-01-31.xlsx
bao_cao_2024-01-01_to_2024-01-31.pdf
bao_cao_2024-01-01_to_2024-01-31.csv
```

### **Nội dung báo cáo:**
- **Tiêu đề**: Tên báo cáo và khoảng thời gian
- **Dữ liệu**: Bảng dữ liệu chi tiết
- **Headers**: Tên cột rõ ràng
- **Format**: Số tiền, ngày tháng được format đúng

## 🔍 Các loại báo cáo có thể xuất

### **1. Báo cáo doanh thu:**
- Ngày/Tháng/Năm
- Số đơn hàng
- Tổng doanh thu
- Tổng thanh toán
- Giá trị trung bình/đơn

### **2. Báo cáo lợi nhuận:**
- Sản phẩm
- Số lượng bán
- Doanh thu
- Chi phí
- Lợi nhuận

### **3. Top sản phẩm:**
- Tên sản phẩm
- Số lượng bán
- Số đơn hàng
- Doanh thu
- Giá trung bình

### **4. Báo cáo tóm tắt:**
- Tổng doanh thu
- Tổng đơn hàng
- Giá trị trung bình
- Sản phẩm bán chạy nhất

## ⚠️ Lưu ý

### **Thư viện:**
1. **Pandas + OpenPyXL**: Cho Excel export
2. **ReportLab**: Cho PDF export
3. **CSV**: Không cần thư viện thêm

### **Dữ liệu:**
1. **Khoảng thời gian**: Phải chọn đầy đủ từ ngày đến ngày
2. **Báo cáo**: Phải xem báo cáo trước khi xuất
3. **Quyền ghi**: Đảm bảo có quyền ghi file tại vị trí chọn

### **Performance:**
1. **Dữ liệu lớn**: Excel/PDF có thể chậm với dữ liệu lớn
2. **Memory**: PDF cần nhiều RAM hơn
3. **File size**: PDF thường lớn hơn Excel

## 🛠️ Troubleshooting

### **Lỗi "Thư viện chưa được cài đặt"**
```bash
pip install pandas openpyxl reportlab
```

### **Lỗi "Không có dữ liệu báo cáo"**
- Chọn khoảng thời gian có dữ liệu
- Xem báo cáo trước khi xuất
- Kiểm tra có dữ liệu bán hàng trong khoảng thời gian

### **Lỗi "Không thể ghi file"**
- Chọn vị trí khác
- Kiểm tra quyền ghi
- Đảm bảo file không đang mở

### **Lỗi encoding (tiếng Việt)**
- Sử dụng UTF-8 encoding
- Kiểm tra font hỗ trợ tiếng Việt
- Thử mở bằng ứng dụng khác

## 🚀 Nâng cao

### **Tùy chỉnh format:**
- Thay đổi màu sắc trong code
- Thêm logo công ty
- Custom header/footer

### **Batch export:**
- Xuất nhiều báo cáo cùng lúc
- Tự động hóa với script
- Lên lịch xuất báo cáo định kỳ

### **Integration:**
- Gửi email tự động
- Upload lên cloud
- Tích hợp với hệ thống khác
