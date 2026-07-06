# HƯỚNG DẪN & THÔNG TIN ĐĂNG KÝ BẢN QUYỀN TÁC GIẢ
*(Tài liệu chuẩn bị hồ sơ đăng ký Quyền tác giả tại Cục Bản quyền tác giả Việt Nam)*

Tài liệu này tổng hợp toàn bộ các thông tin kỹ thuật, tóm tắt nội dung phần mềm và hướng dẫn in mã nguồn để bạn hoàn thiện hồ sơ đăng ký Quyền tác giả đối với **Chương trình máy tính** của mình.

---

## PHẦN 1: THÔNG TIN ĐIỀN TRÊN TỜ KHAI ĐĂNG KÝ

Khi điền tờ khai đăng ký quyền tác giả (Mẫu tờ khai chương trình máy tính của Cục Bản quyền), bạn sử dụng các thông tin chuẩn hóa sau:

1. **Tên tác phẩm**:
   * *Tiếng Việt*: Phần mềm quản lý xuất - nhập - tồn thuốc, vaccine và vật tư y tế tích hợp kiểm kho di động qua mạng LAN Wi-Fi.
   * *Tên viết tắt (nếu có)*: CDC-XNT
2. **Loại hình tác phẩm**: Chương trình máy tính.
3. **Tác giả**: 
   * Họ và tên: *(Họ tên của bạn)*
   * Quốc tịch: Việt Nam
   * Số CCCD: *(Số CCCD của bạn)*
   * Địa chỉ thường trú / Số điện thoại / Email: *(Thông tin liên hệ của bạn)*
4. **Chủ sở hữu quyền tác giả**:
   * *Trường hợp 1 (Đăng ký dưới tên cá nhân bạn)*: Ghi thông tin trùng khớp với phần Tác giả.
   * *Trường hợp 2 (Đăng ký dưới tên cơ quan)*: 
     * Tên tổ chức: Trung tâm Kiểm soát bệnh tật thành phố Cần Thơ.
     * Địa chỉ: *(Địa chỉ CDC Cần Thơ)*.
     * Mã số thuế / Quyết định thành lập: *(Điền mã số của cơ quan)*.
5. **Ngày hoàn thành tác phẩm**: *(Ghi năm hoàn thành, ví dụ: 2026)*
6. **Tác phẩm đã công bố chưa?**: 
   * Chọn: **Đã công bố**.
   * Ngày công bố: *(Ghi ngày chạy thử nghiệm hoặc bàn giao đầu tiên tại đơn vị, ví dụ: 02/07/2026)*.
   * Hình thức công bố: Cài đặt và vận hành trực tiếp tại Kho dược Trung tâm Kiểm soát bệnh tật TP. Cần Thơ.

---

## PHẦN 2: BẢN TÓM TẮT NỘI DUNG CHƯƠNG TRÌNH MÁY TÍNH
*(Phần này dùng để dán vào Mục "Tóm tắt nội dung tác phẩm" trong tờ khai hoặc làm phụ lục thuyết minh đính kèm hồ sơ)*

### 1. Thông tin kỹ thuật chung:
* **Ngôn ngữ lập trình**: Python 3.8+
* **Hệ quản trị cơ sở dữ liệu**: SQLite (Hệ cơ sở dữ liệu cục bộ dạng tệp tin `.db` bảo mật).
* **Giao diện người dùng (UI)**: Thư viện `ttkbootstrap` (nền tảng giao diện đồ họa hiện đại trên Windows) kết hợp HTML5, CSS3 và Vanilla Javascript (phục vụ giao diện kiểm kho trên di động).
* **Môi trường vận hành**: Hệ điều hành Windows 10/11 (đối với ứng dụng chính) và các thiết bị di động Android/iOS (thông qua trình duyệt web nội bộ kết nối LAN Wi-Fi).

### 2. Các phân hệ chức năng chính:
* **Phân hệ Quản lý Danh mục**: Hỗ trợ tra cứu nhanh danh mục thuốc chuẩn hóa của CDC (hơn 30.000 sản phẩm), tự động gợi ý tên, số đăng ký và quy đổi đơn vị tính.
* **Phân hệ Nhập kho (Mẫu C30-HD)**: Tiếp nhận dữ liệu nhập kho chi tiết theo số lô, hạn sử dụng, đơn giá và đối tác cung ứng.
* **Phân hệ Xuất kho FEFO (Mẫu C31-HD)**: Phân bổ tự động số lượng xuất kho ưu tiên từ các lô hàng cận hạn dùng nhất trong hệ thống, tự động tách lô hàng (split-batch) khi số lượng xuất lớn hơn số lượng tồn của một lô đơn lẻ.
* **Phân hệ Máy chủ di động LAN Wi-Fi (Mobile Companion)**: Tích hợp máy chủ web ngầm (HTTP Server) trên mạng nội bộ không dây giúp điện thoại di động truy cập trực tiếp bằng mã QR.
* **Phân hệ Kiểm kho & Quét mã vạch**: Hỗ trợ camera điện thoại quét mã vạch 1D/2D trực tiếp tại kệ để tìm sản phẩm và kiểm kê.
* **Phân hệ Dashboard & Bộ lọc nhanh**: Cung cấp biểu đồ thống kê tồn kho, hiển thị nhanh số lượng lô cận hạn (< 6 tháng), số lượng mặt hàng hết tồn kho và bộ lọc nhanh trạng thái trên di động.
* **Phân hệ Xem trước phiếu (Note Preview)**: Hiển thị giao diện đối soát chi tiết phiếu xuất/nhập trước khi ra lệnh in hoặc xuất PDF.
* **Phân hệ Báo cáo & Kế toán (Mẫu C33-HD)**: Tự động tổng hợp và xuất Báo cáo Xuất - Nhập - Tồn, Biên bản kiểm kê kho định kỳ ra định dạng Excel và PDF.
* **Phân hệ An toàn**: Tự động sao lưu dữ liệu dự phòng hàng ngày sang thư mục riêng.

---

## PHẦN 3: HƯỚNG DẪN IN MÃ NGUỒN (25 TRANG ĐẦU & 25 TRANG CUỐI)
*(Quy định bắt buộc của Cục Bản quyền là in 25 trang đầu và 25 trang cuối của mã nguồn phần mềm trên giấy A4)*

Mã nguồn chương trình của bạn nằm toàn bộ trong tệp `nhathuoc2.py` (tổng cộng **9.766 dòng**).
Tính trung bình mỗi trang giấy A4 (in font chữ Courier New cỡ 10, dãn dòng đơn) chứa khoảng **50 - 55 dòng code**.

* **25 trang đầu**: Bạn copy và in mã nguồn từ **Dòng 1 đến Dòng 1.300** của file `nhathuoc2.py`.
* **25 trang cuối**: Bạn copy và in mã nguồn từ **Dòng 8.466 đến Dòng 9.766** của file `nhathuoc2.py`.

> [!TIP]
> **Mẹo in ấn**: Bạn nên dùng phần mềm soạn thảo văn bản (như Notepad++ hoặc Microsoft Word), dán đoạn mã nguồn tương ứng vào, chọn font chữ `Consolas` hoặc `Courier New` cỡ `10`, căn lề trang bình thường và chọn in 2 mặt để tiết kiệm giấy.

---

## PHẦN 4: QUY TRÌNH NỘP HỒ SƠ TẠI VIỆT NAM

### Bước 1: Chuẩn bị bộ hồ sơ
Bạn in ấn và tập hợp đầy đủ các giấy tờ sau:
1. **Tờ khai đăng ký quyền tác giả** (đã ký tên tác giả, đóng dấu cơ quan nếu chủ sở hữu là CDC).
2. **02 bản in mã nguồn** (gồm 25 trang đầu + 25 trang cuối).
3. **02 bản in ảnh chụp giao diện phần mềm** trên máy tính và điện thoại.
4. **02 đĩa CD hoặc 02 thẻ USB** (ghi sẵn file mã nguồn `nhathuoc2.py`, file danh mục `thuoc.csv`, và file đóng gói cài đặt `QuanLyKho.exe`).
5. **01 bản sao công chứng CCCD** của tác giả.
6. *Nếu chủ sở hữu là CDC*: **01 bản sao công chứng Quyết định thành lập cơ quan** + **Giấy ủy quyền/Giao nhiệm vụ** cho bạn tự nghiên cứu sáng kiến (có ký tên, đóng dấu của Giám đốc CDC).

### Bước 2: Nộp hồ sơ
Bạn có thể nộp trực tiếp hoặc gửi qua bưu điện về các địa chỉ sau của Cục Bản quyền tác giả:
* **Tại Hà Nội (Trụ sở chính)**: Số 33 Ngõ 294/2 Kim Mã, Quận Ba Đình, Hà Nội.
* **Tại TP. Hồ Chí Minh (Văn phòng đại diện)**: Số 170 Nguyễn Đình Chiểu, Quận 3, TP. Hồ Chí Minh.
* **Tại Đà Nẵng (Văn phòng đại diện)**: Số 58 Phan Chu Trinh, Quận Hải Châu, Thành phố Đà Nẵng.

### Bước 3: Đóng lệ phí & Nhận kết quả
* Lệ phí Nhà nước: **600.000 VNĐ** (Chương trình máy tính).
* Thời gian xử lý: Từ **15 đến 30 ngày** kể từ ngày nhận đủ hồ sơ hợp lệ. Cục sẽ cấp **Giấy chứng nhận đăng ký quyền tác giả** gửi về địa chỉ của bạn.
