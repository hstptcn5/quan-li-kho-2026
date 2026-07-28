# PROJECT GOAL — HỆ THỐNG QUẢN LÝ KHO 2026

## 1. Mục tiêu tổng thể

Xây dựng một phần mềm quản lý kho thuốc, vaccine và vật tư y tế chạy ổn định trên Windows, cho phép quản lý chính xác toàn bộ quá trình nhập kho, xuất kho, tồn kho và truy vết chứng từ theo:

* Sản phẩm
* Số lô
* Hạn sử dụng
* Đơn vị tính và đơn vị quy đổi
* Nguồn kinh phí
* Ngày chứng từ
* Đơn vị cấp hoặc nhận hàng

Hệ thống phải đủ đơn giản để nhân viên kho sử dụng hằng ngày, đồng thời đủ chính xác và an toàn để số liệu trên phần mềm có thể được dùng làm căn cứ đối chiếu với tồn kho thực tế.

---

## 2. Kết quả cuối cùng cần đạt

Khi dự án hoàn thành, người dùng phải có thể tin tưởng rằng:

> Với cùng một bộ chứng từ, hệ thống luôn tính ra đúng số tồn kho theo từng sản phẩm, từng lô và từng nguồn kinh phí, tại thời điểm hiện tại cũng như tại một ngày lịch sử bất kỳ.

Hệ thống không được tạo tồn kho âm, không sử dụng hàng chưa được nhập tại thời điểm xuất, không xuất từ lô đã hết hạn tại ngày xuất và không làm sai số liệu khi người dùng nhập chứng từ lùi ngày.

---

## 3. Phạm vi chức năng chính

### Quản lý danh mục

Hệ thống phải quản lý được:

* Tên sản phẩm
* Mã vạch
* Loại sản phẩm
* Số đăng ký
* Đơn vị cơ sở
* Các đơn vị quy đổi
* Giá nhập và giá bán tham khảo
* Nhà cung cấp
* Đơn vị nhận
* Nguồn kinh phí

### Quản lý lô và tồn kho

Mỗi lượng tồn phải được xác định rõ theo:

```text
Sản phẩm + Số lô + Hạn sử dụng + Nguồn kinh phí
```

Hệ thống phải:

* Theo dõi tồn theo đơn vị cơ sở.
* Hiển thị tồn theo lô.
* Cảnh báo lô sắp hết hạn.
* Chặn lô đã hết hạn tại ngày xuất.
* Chặn xuất vượt số lượng đang có.
* Không trộn tồn giữa các nguồn kinh phí.

### Nhập kho

Người dùng có thể:

* Nhập kho thủ công.
* Nhập nhiều sản phẩm trong một phiếu.
* Chọn ngày nhập.
* Ghi nhận nhà cung cấp, lý do và ghi chú.
* Nhập dữ liệu hàng loạt từ Excel.
* Cập nhật sản phẩm đã tồn tại mà không tạo bản ghi trùng.

Nếu nhập Excel gặp lỗi nghiêm trọng, toàn bộ dữ liệu của lần nhập phải được rollback, không được để lại sản phẩm, đơn vị, lô hoặc phiếu dở dang.

### Xuất kho

Người dùng có thể:

* Xuất kho theo sản phẩm.
* Chọn lô thủ công hoặc để hệ thống tự chọn FEFO.
* Chọn nguồn kinh phí hoặc để hệ thống tự phân bổ.
* Chọn ngày xuất.
* Xuất cho một đơn vị nhận.
* In phiếu sau khi xuất.

FEFO phải dựa trên ngày xuất của chứng từ, không phải ngày hiện tại của máy tính.

Tồn kho dùng để kiểm tra xuất phải là tồn tại đúng thời điểm chứng từ:

```text
Chỉ tính các biến động có ngày <= ngày xuất
```

### Chứng từ và truy vết

Mỗi giao dịch kho phải liên kết được với chứng từ tạo ra nó.

Hệ thống phải trả lời được:

* Phiếu nào tạo ra biến động này?
* Sản phẩm nào bị ảnh hưởng?
* Lô nào bị ảnh hưởng?
* Nguồn kinh phí nào bị ảnh hưởng?
* Số lượng thay đổi bao nhiêu?
* Ai hoặc thiết bị nào thực hiện?
* Thực hiện vào thời điểm nào?

### Báo cáo

Hệ thống phải cung cấp tối thiểu:

* Báo cáo nhập kho.
* Báo cáo xuất kho.
* Báo cáo tồn kho hiện tại.
* Báo cáo tồn theo lô.
* Báo cáo tồn theo nguồn kinh phí.
* Báo cáo lô sắp hết hạn.
* Tra cứu chứng từ theo khoảng ngày.
* Chi tiết lịch sử biến động của từng sản phẩm.

### Sử dụng trên điện thoại

Trong cùng mạng nội bộ, người dùng có thể:

* Đăng nhập bằng mã PIN.
* Tìm hoặc quét sản phẩm.
* Nhập kho.
* Xuất kho.
* Xem lịch sử.
* Xem trước và in phiếu.
* Gửi lệnh in sang máy tính.

Hệ thống quét QR phải hoạt động khi không có Internet.

### Sao lưu và phục hồi

Hệ thống phải:

* Tạo bản sao lưu database.
* Phục hồi database từ bản sao lưu.
* Không tiếp tục sử dụng kết nối database cũ sau khi phục hồi.
* Có thể quay lại dữ liệu trước đó khi xảy ra sự cố.

---

## 4. Yêu cầu về tính đúng dữ liệu

Đây là phần quan trọng nhất của dự án.

### Không tồn kho âm

Sau bất kỳ thao tác nhập, xuất, xóa hoặc phục hồi nào:

```text
Tồn kho của mọi sản phẩm, lô và nguồn kinh phí phải >= 0
```

### Tồn kho theo thời điểm

Khi tạo chứng từ có ngày trong quá khứ, hệ thống phải tính tồn tại đúng ngày đó.

Ví dụ:

* Nhập 10 hộp ngày 01/01.
* Xuất 8 hộp ngày 01/02.
* Tạo thêm phiếu xuất ngày 20/01.

Tồn dùng để kiểm tra tại ngày 20/01 phải là 10 hộp, không phải 2 hộp.

Tương tự, hàng nhập ngày 01/02 không được phép dùng để xuất cho ngày 20/01.

### Hạn dùng theo ngày xuất

Một lô được phép xuất khi:

```text
Hạn sử dụng >= Ngày xuất
```

Không được dùng ngày hiện tại để đánh giá một phiếu xuất lùi ngày.

### Transaction nguyên tử

Những thao tác gồm nhiều bước phải được thực hiện trong cùng một transaction.

Khi một bước thất bại:

```text
Toàn bộ thao tác phải rollback
```

Không được để lại dữ liệu một phần.

### Không sửa ngày âm thầm

Nếu người dùng nhập ngày sai định dạng, hệ thống phải báo lỗi và yêu cầu nhập lại.

Không được tự đổi ngày sai thành ngày hôm nay.

---

## 5. Yêu cầu về triển khai

Phần mềm chính thức phải được đóng gói thành bản chạy độc lập trên Windows.

Máy người dùng không cần:

* Cài Python.
* Cài pip.
* Cài môi trường ảo.
* Tải dependency.
* Chạy mã nguồn.

Quy trình phát hành mong muốn:

```text
Build trên máy phát triển
→ Tạo bản EXE
→ Đóng gói thư mục phát hành
→ Copy sang máy sử dụng
→ Mở ứng dụng và dùng
```

`run.bat` chỉ phục vụ phát triển và kiểm thử mã nguồn.

---

## 6. Những việc không thuộc GOAL hiện tại

Dự án chưa cần trở thành:

* Hệ thống ERP hoàn chỉnh.
* Phần mềm kế toán.
* Hệ thống bán hàng đa chi nhánh.
* Dịch vụ cloud nhiều người dùng.
* Ứng dụng di động riêng trên Android hoặc iOS.
* Nền tảng quản lý kho cho nhiều tổ chức.

Mục tiêu hiện tại là hoàn thiện một hệ thống kho nội bộ chạy ổn định, chính xác và dễ sử dụng.

---

## 7. Definition of Done

Dự án chỉ được xem là hoàn thành khi đáp ứng toàn bộ các điều kiện sau.

### Nghiệp vụ

* Nhập kho hoạt động đúng.
* Xuất kho hoạt động đúng.
* Xuất FEFO đúng lô.
* Nguồn kinh phí không bị trộn.
* Không thể xuất vượt tồn.
* Không thể tạo tồn âm.
* Tồn kho lịch sử được tính đúng.
* Giao dịch tương lai không ảnh hưởng số dư quá khứ.
* Hạn dùng được kiểm tra theo ngày xuất.
* Ngày không hợp lệ bị chặn.

### Dữ liệu

* Mọi biến động đều liên kết với chứng từ.
* Import Excel có rollback đầy đủ.
* Xóa chứng từ không làm sai tồn kho.
* Sao lưu và phục hồi hoạt động đúng.
* Database vẫn toàn vẹn sau khi ứng dụng bị đóng bất ngờ.

### Giao diện và sử dụng

* Nhân viên có thể nhập và xuất kho mà không cần biết kỹ thuật.
* Thông báo lỗi nói rõ sản phẩm, lô hoặc nguồn bị thiếu.
* Điện thoại nhập, xuất và in được.
* QR hoạt động offline.
* Không có dữ liệu người dùng được đưa trực tiếp vào HTML mà không escape.

### Kiểm thử

Toàn bộ test tự động phải chạy thành công, bao gồm:

* Nhập và xuất thông thường.
* Xuất vượt tồn.
* Tồn theo lô và nguồn.
* FEFO.
* Chứng từ lùi ngày.
* Giao dịch tương lai không cấp hàng cho quá khứ.
* Giao dịch tương lai không làm giảm tồn quá khứ.
* Rollback import Excel.
* Xóa chứng từ.
* Backup và restore.
* Xác thực mobile và quyền truy cập URL in.

### Phát hành

* Build EXE thành công.
* Chạy được trên máy Windows không cài Python.
* Hoạt động khi mất Internet.
* Chạy thử bằng database bản sao.
* Đối chiếu tồn kho với dữ liệu thực tế.
* Không phát hiện sai lệch sau giai đoạn UAT.

---

## 8. Tiêu chí thành công cuối cùng

Dự án thành công khi người quản lý kho có thể nói:

> Tôi có thể nhập chứng từ, xuất chứng từ, xem tồn theo lô và nguồn kinh phí, đối chiếu lại dữ liệu lịch sử và in báo cáo mà không phải sửa tay trong Excel. Tôi tin rằng số tồn trên phần mềm phản ánh đúng dữ liệu kho.

---

## 9. Trạng thái hiện tại

Dự án hiện đã vượt qua giai đoạn prototype và đã đạt mức beta nội bộ.

Các chức năng chính gần như đã đầy đủ, nhưng dự án chưa hoàn thành GOAL cuối cùng cho đến khi xử lý xong:

1. Tồn kho tại ngày lịch sử.
2. Giao dịch tương lai không ảnh hưởng quá khứ.
3. Chặn ngày nhập sai.
4. Chạy đầy đủ test tự động.
5. Kiểm thử bằng dữ liệu thực tế.
6. Build và thử bản EXE trên máy sạch.

Sau khi sáu phần này hoàn tất, dự án có thể được đánh dấu:

```text
Production Ready — Version 1.0.0
```
