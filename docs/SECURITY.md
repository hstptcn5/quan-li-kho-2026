# Desktop Admin Security

## Mục đích

Bản hardening H0.3 thay cơ chế chọn vai trò `Admin / Thủ kho / Chỉ xem` trước đây bằng cơ chế mở khóa Admin cục bộ có PIN. Trước H0.3, người dùng có thể chọn trực tiếp `Admin` từ menu nên `require_admin_action()` chỉ là một UI guard, không phải xác thực.

## Cách hoạt động

- Ứng dụng khởi động ở trạng thái **Admin đã khóa**.
- Lần đầu thực hiện một thao tác cần quyền Admin, ứng dụng yêu cầu tạo PIN gồm đúng 6 chữ số.
- PIN không được lưu plaintext. Ứng dụng lưu salt ngẫu nhiên và giá trị PBKDF2-HMAC-SHA256 trong `admin_auth.json` ở thư mục dữ liệu của ứng dụng.
- Sau khi nhập đúng PIN, quyền Admin được mở trong 15 phút rồi tự khóa.
- 5 lần nhập sai liên tiếp sẽ khóa tạm việc thử PIN trong 5 phút.
- Menu **Bảo mật** cho phép mở khóa, khóa ngay và đổi PIN Admin.

## Các thao tác hiện yêu cầu Admin unlock

Các luồng đang dùng `require_admin_action()` gồm ít nhất:

- Import dữ liệu JSON thay thế dữ liệu hiện tại.
- Khôi phục backup.
- Xóa backup.
- Áp dụng điều chỉnh kiểm kê.

Các thao tác này không còn được phép chỉ vì một biến UI đang có giá trị `Admin`.

## Ranh giới bảo mật

PIN Admin là lớp bảo vệ **bên trong ứng dụng desktop**, phù hợp để tránh thao tác quản trị ngoài ý muốn hoặc người dùng thông thường tại cùng máy trạm.

Đây không phải ranh giới chống lại người đã có quyền truy cập filesystem/Windows account tới thư mục dữ liệu. Người có quyền sửa trực tiếp `pharm.db` hoặc `admin_auth.json` đã nằm ngoài threat model của lớp PIN này. Nếu cần phân quyền nhiều người dùng có định danh và audit theo tài khoản, phải triển khai hệ thống user authentication riêng ở một checkpoint sau.

## Khi cấu hình PIN bị hỏng

Ứng dụng **fail closed**: không tự động xóa hoặc reset file PIN, vì tự reset có thể biến lỗi cấu hình thành đường bypass quyền Admin. Hãy sao lưu thư mục dữ liệu trước khi xử lý thủ công.
