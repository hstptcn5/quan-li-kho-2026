# TIẾN ĐỘ DỰ ÁN SÁNG KIẾN: HỆ THỐNG QUẢN LÝ XUẤT-NHẬP-TỒN CDC
*(Tài liệu phục vụ ghi nhận git status, git commit và báo cáo công việc)*

---

## 🚀 1. Các Tính năng Hiện có (Current Features)

### 📊 Quản lý Danh mục & Sản phẩm linh hoạt
- **Nguồn sản phẩm**:
  - **Từ danh mục chuẩn**: Tự động khóa trường đơn vị cơ sở & số đăng ký để đảm bảo tính chuẩn hóa của danh mục thuốc/vaccine CDC, bật gợi ý tự động (autocomplete) khi gõ tên sản phẩm.
  - **Ngoài danh mục (Nhập tự do)**: Mở khóa tất cả các trường để người dùng tự do nhập tay sản phẩm mới phát sinh ngoài kế hoạch.
- Phân loại sản phẩm rõ ràng: `Thuốc`, `Vaccine`, `Vật tư y tế`, `Khác`.

### 📦 Quy trình Nhập kho / Lập Phiếu nhập (Mới nâng cấp)
- **Lập phiếu nhập đa sản phẩm**: Cho phép chọn sản phẩm, số lượng, đơn giá, số lô, hạn dùng đưa vào giỏ hàng tạm trước khi xác nhận.
- **Thông tin phiếu**: Số phiếu nhập sinh tự động (`PNK-YYYYMMDDHHMMSS`), Nguồn cấp/Nhà cung cấp, Ngày nhập (hỗ trợ DateEntry), Lý do nhập (Nhận cấp phát tuyến trên, Mua sắm đấu thầu, Viện trợ,...), Ghi chú.
- **Đồng bộ giá**: Loại bỏ trường giá bán khi nhập kho. Hệ thống tự động gán giá xuất bằng giá nhập (`sell_price = cost`) để đảm bảo nguyên tắc cấp phát phi lợi nhuận.

### 📤 Quy trình Xuất kho / Cấp phát (Thay thế POS cũ)
- **Cơ chế FEFO**: Tự động tìm lô hàng có hạn dùng gần nhất để xuất trước.
- **Thông tin phiếu**: Số phiếu xuất (`PXK-YYYYMMDDHHMMSS`), Đơn vị nhận (nhập tay/autocomplete gợi ý), Ngày xuất (hỗ trợ DateEntry hồi tố), Lý do xuất (Cấp phát, Hủy kho, Chuyển kho,...), Ghi chú.
- Loại bỏ hoàn toàn các trường tiền khách đưa, tiền thối của mô hình bán lẻ cũ.

### 📄 In Phiếu Nhập / Xuất kho PDF độc lập & Tự động
- Sử dụng trực tiếp thư viện `reportlab` vẽ PDF tiếng Việt Unicode (dùng font hệ thống `Times New Roman` có sẵn trên Windows), hoạt động độc lập không phụ thuộc vào Edge headless.
- Cho phép người dùng tùy chọn vị trí lưu file PDF trên máy tính thông qua hộp thoại `Save As`.
- Tự động mở file PDF bằng trình xem mặc định ngay sau khi xuất.
- **Bảng chữ ký 5 bên chuẩn mực**: Người lập phiếu, Người nhận/giao hàng, Thủ kho, Kế toán trưởng, Lãnh đạo đơn vị. Gỡ bỏ tên tĩnh "Hồ Sỷ Thoảng" tạo khoảng trống ký tên rộng rãi.
- **Tự động cài đặt thư viện**: Phát hiện thiếu `reportlab`, hỏi ý kiến người dùng và tự động chạy ngầm `pip install` chỉ trong vài giây.

### 📈 Báo cáo Xuất - Nhập - Tồn (XNT) & Báo cáo nâng cao
- **Đồng bộ hóa XNT**: Đã sửa lỗi lọc dữ liệu, tính toán lượng xuất cấp phát (`DISPATCH`) vào cột "Xuất trong kỳ" trong báo cáo XNT chung.
- **Lịch sử phiếu**: Thêm màn hình hiển thị danh sách phiếu xuất/nhập đã lập theo khoảng ngày. Hỗ trợ xem chi tiết và in lại phiếu PDF cũ bất cứ lúc nào.
- **Thống kê nâng cao**: Doanh thu/Cấp phát theo ngày, Thống kê theo đơn vị nhận, Top sản phẩm cấp phát nhiều nhất, Biểu đồ đường xu hướng cấp phát trực quan.
- **Xuất file đồng bộ**: Hỗ trợ xuất dữ liệu hiển thị trên màn hình ra các định dạng Excel, PDF, CSV.

### 💾 Backup Cơ sở dữ liệu & Không cần License
- **Tự động sao lưu**: Backup database định kỳ sang thư mục `backups`.
- **Gỡ bỏ License**: Không còn kiểm tra key kích hoạt hay fingerprint phần cứng. Mở ứng dụng là chạy trực tiếp.

---

## 📝 2. Nhật ký Thay đổi chi tiết (Git Status / Change Log)

### 🛠️ Các File đã chỉnh sửa:
- `nhathuoc2.py`:
  - Thêm bảng `purchase_notes` và `purchase_items` vào Database Schema.
  - Viết các phương thức SQLite mới trong lớp `DB`: `record_purchase`, `get_purchase_notes`, `get_purchase_detail`, `get_suppliers`.
  - Thiết kế lại hoàn toàn tab Nhập kho (`build_purchase_tab`) hỗ trợ giỏ hàng nhập kho tạm thời, autocomplete nguồn cấp, DateEntry chọn ngày nhập, lý do nhập.
  - Viết hàm `print_purchase_note` vẽ phiếu nhập PDF mẫu C30-HD bằng `reportlab`.
  - Tích hợp tính năng **Lịch sử phiếu nhập** và in lại phiếu nhập cũ trong tab Báo cáo nâng cao (`show_purchase_history`, `reprint_selected_purchase`).
  - Cập nhật nút bấm giao diện và an toàn hóa hàm `refresh_stock` bằng `hasattr`.
  - Cấu trúc lại bảng chữ ký PDF phiếu xuất kho (`print_dispatch_note`) thành 5 cột cân đối, thêm Kế toán trưởng, loại bỏ tên in sẵn.

---

## 💡 3. Các Đề xuất Cải thiện thêm (Future Improvements)

1. **Quản lý danh sách nhà cung cấp (Suppliers)**:
   - Hiện tại nhà cung cấp được gợi ý từ danh sách đã nhập trong phiếu nhập cũ (`SELECT DISTINCT`).
   - Có thể thêm một bảng quản lý danh sách nhà cung cấp riêng biệt (tương tự như `receiving_units`) để lưu thêm địa chỉ, số điện thoại, người liên hệ.
2. **Cảnh báo tồn kho tối thiểu (Min-Stock Alerts)**:
   - Thêm trường `min_stock` vào bảng `products` để hệ thống tự động đưa ra cảnh báo khi số lượng tồn của một loại thuốc/vaccine xuống quá thấp.
3. **Phân quyền người dùng (User Authorization)**:
   - Thêm tính năng đăng nhập cho các tài khoản: `Thủ kho`, `Kế toán`, `Admin` để ghi nhận chính xác ai là người lập phiếu nhập/xuất kho (tự động điền vào mục Người lập phiếu trên PDF).
4. **Nhập dữ liệu từ Excel (Import Excel)**:
   - Hỗ trợ import danh mục sản phẩm hoặc danh sách hàng nhập từ file Excel mẫu của Sở Y tế để tiết kiệm thời gian nhập liệu ban đầu cho cán bộ kho.
