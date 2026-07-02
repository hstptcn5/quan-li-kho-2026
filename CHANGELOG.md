# 📝 CHANGELOG - Quản lý kho hàng hóa

Tất cả các thay đổi quan trọng của dự án sẽ được ghi lại trong file này.

Format dựa trên [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
và dự án tuân theo [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-07-02

### 🎉 Added - Tính năng mới di động (Mobile Companion)
- **Trang Thống kê nhanh (Quick Dashboard)**: Hiển thị tóm tắt tình trạng kho gồm Tổng số thuốc, Số lượng sản phẩm hết hàng, và số lượng lô cận hạn dùng ngay trên đầu màn hình di động.
- **Bộ lọc thông minh (Intelligent Filters)**: Hỗ trợ lọc nhanh danh sách sản phẩm theo trạng thái "❌ Hết Hàng" hoặc "⚠️ Cận Hạn" (hạn sử dụng < 6 tháng) dưới thanh tìm kiếm danh mục.
- **Xem trước phiếu trước khi in (Note Preview Modal)**: Hiển thị hộp thoại xem trước thông tin phiếu cùng bảng chi tiết danh sách mặt hàng trước khi người dùng thực hiện lệnh in PC hoặc xem PDF di động.

### 🐛 Fixed - Sửa lỗi
- **Lệch phiếu in lịch sử**: Sửa lỗi khớp loại phiếu nhập (`nhap` -> `purchase`) và phiếu xuất (`xuat` -> `dispatch`) khi gửi lệnh in từ di động ra máy in PC.

## [1.1.0] - 2026-07-02

### 🎉 Added - Tính năng mới di động (Mobile Companion)
- **Giao diện sáng xanh nhạt (Light Blue Theme)**: Chuyển đổi toàn bộ UI di động sang tông màu sáng xanh mát mắt, tối ưu tương phản chữ Slate đậm dễ đọc ngoài trời.
- **Tab Lịch Sử Giao Dịch (Transaction History)**: Xem các phiếu nhập xuất gần đây trực tiếp trên điện thoại và gửi lệnh in ra máy tính hoặc in qua điện thoại.
- **Giỏ Hàng Tạm Tính (Mobile Draft Cart)**: Hỗ trợ gom nhiều mặt hàng vào một phiếu nhập/xuất duy nhất thay vì tạo nhiều phiếu lẻ tẻ.
- **Lưu trữ cục bộ**: Tự động lưu trữ giỏ hàng hiện tại vào `localStorage` của điện thoại để chống mất mát dữ liệu khi mất kết nối mạng.

## [1.0.0] - 2024-01-XX

### 🎉 Added - Tính năng mới
- **Giao diện hiện đại** với ttkbootstrap theme
- **Quản lý sản phẩm** với autocomplete thông minh
- **Danh mục thuốc** tự động từ file CSV/Excel
- **Quét barcode** bằng camera với OpenCV
- **Báo cáo nâng cao** với biểu đồ matplotlib
- **Xuất báo cáo** ra Excel, PDF, CSV
- **Sao lưu tự động** và khôi phục dữ liệu
- **Hệ thống license** bảo mật với Ed25519
- **License Generator Tool** cho việc bán phần mềm
- **Toolbar** với các nút nhanh
- **Status bar** hiển thị thông tin chi tiết
- **Tooltips** hướng dẫn sử dụng

### 🔧 Technical - Kỹ thuật
- **Database SQLite** với schema tối ưu
- **Threading** cho sao lưu tự động
- **Error handling** toàn diện
- **Data validation** cơ bản
- **Hardware fingerprinting** cho license
- **Offline license verification**
- **Multi-format export** (Excel, PDF, CSV)

### 📊 Modules - Các module
- **📦 Sản phẩm:** Quản lý danh mục, autocomplete, barcode
- **📥 Nhập hàng:** Nhập hàng vào kho với lô và hạn sử dụng
- **🧾 Bán hàng POS:** Bán hàng tại quầy với quét barcode
- **📊 Tồn kho:** Xem tồn kho hiện tại
- **⚠️ Cảnh báo:** Cảnh báo hết hàng (cơ bản)
- **📈 Báo cáo:** Báo cáo cơ bản
- **📊 Báo cáo nâng cao:** Doanh thu, lợi nhuận, top sản phẩm
- **💾 Sao lưu:** Sao lưu và khôi phục dữ liệu

### 🛠️ Tools - Công cụ
- **LicenseGenerator.exe:** Tạo license cho khách hàng
- **KeyCreator.exe:** Tạo cặp khóa Ed25519
- **build.bat/build.sh:** Script đóng gói tự động

### 📚 Documentation - Tài liệu
- **HUONG_DAN_SU_DUNG.md:** Hướng dẫn sử dụng toàn diện
- **BARCODE_SETUP.md:** Hướng dẫn cài đặt barcode scanner
- **EXPORT_REPORTS.md:** Hướng dẫn xuất báo cáo
- **README_LICENSE.md:** Hướng dẫn hệ thống license

---

## [0.9.0] - 2024-01-XX (Beta)

### 🎉 Added
- Giao diện cơ bản với tkinter
- Quản lý sản phẩm đơn giản
- Nhập hàng và bán hàng cơ bản
- Báo cáo tồn kho

### 🔧 Technical
- Database SQLite cơ bản
- UI với tkinter standard

---

## 🚀 Roadmap - Kế hoạch phát triển

### [1.1.0] - Planned
- **👥 Quản lý người dùng** và phân quyền
- **⚠️ Cảnh báo tồn kho** nâng cao
- **✅ Validation dữ liệu** mạnh mẽ hơn
- **🌙 Dark mode** theme
- **⌨️ Keyboard shortcuts**

### [1.2.0] - Planned
- **🚀 Tối ưu hóa hiệu suất** cho dữ liệu lớn
- **📱 Mobile companion app**
- **🌐 API REST** cho tích hợp
- **☁️ Cloud sync** dữ liệu

### [2.0.0] - Future
- **🌍 Multi-language** support
- **🔌 Plugin system**
- **📊 Advanced analytics**
- **🤖 AI recommendations**

---

## 🔄 Migration Guide

### Từ 0.9.0 lên 1.0.0
1. **Backup dữ liệu** hiện tại
2. **Cài đặt dependencies** mới:
   ```bash
   pip install -r requirements.txt
   ```
3. **Chạy phần mềm** - database sẽ tự động migrate
4. **Kích hoạt license** mới

### Breaking Changes
- **Database schema** đã thay đổi (tự động migrate)
- **File paths** đã thay đổi (tự động migrate)
- **License system** mới (cần kích hoạt lại)

---

## 🐛 Bug Fixes

### [1.0.0]
- Fixed UI initialization order issue
- Fixed autocomplete click not working
- Fixed DataFrame boolean evaluation error
- Fixed NoneType formatting in reports
- Fixed toolbar creation before tabs

---

## ⚠️ Known Issues

### [1.0.0]
- **Camera access** có thể bị từ chối trên một số hệ thống
- **PDF export** có thể chậm với dữ liệu lớn
- **License verification** cần internet lần đầu (để tải public key)

---

## 📞 Support

### Báo lỗi
- **Email:** hstptcn5@gmail.com
- **Mô tả:** Chi tiết lỗi, steps to reproduce, system info

### Yêu cầu tính năng
- **Email:** hstptcn5@gmail.com
- **Mô tả:** Use case, expected behavior, priority

### Hỗ trợ kỹ thuật
- **Email:** hstptcn5@gmail.com
- **Phone:** 0329381189

---

**© 2024 Hồ Sỷ Thoảng. Tất cả quyền được bảo lưu.**
