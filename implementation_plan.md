# 📋 Tổng hợp đánh giá & Kế hoạch hoàn thiện sáng kiến

## Đề tài: Xây dựng phần mềm quản lý XNT thuốc, vaccine và VTYT tại CDC Cần Thơ

**Tác giả:** Hồ Sỷ Thoảng | **Đơn vị:** CDC Cần Thơ | **Năm:** 2026

---

## 1. TỔNG HỢP NHỮNG PHẦN ĐÃ LÀM ĐƯỢC ✅

### Biện pháp 1: Cơ sở dữ liệu tập trung ✅ **Hoàn thành tốt**

| Yêu cầu đề cương | Hiện trạng code | Đánh giá |
|---|---|---|
| CSDL SQLite 6 bảng chính | ✅ Đã có đủ: `products`, `product_units`, `batches`, `stock_movements`, `sales`, `sale_items` | Đạt |
| Tích hợp danh mục thuốc quốc gia (30.000+) | ✅ Đã có `thuoc.csv` (32MB) + `MedicineCatalogManager` | Đạt |
| Autocomplete thông minh | ✅ Đã có `get_medicine_suggestions()` + UI Listbox | Đạt |
| Giảm nhập SP từ 5 phút → 10 giây | ✅ Logic đã hoàn chỉnh | Đạt |

---

### Biện pháp 2: Xuất kho tự động FEFO ✅ **Hoàn thành tốt**

| Yêu cầu đề cương | Hiện trạng code | Đánh giá |
|---|---|---|
| Tự động chọn lô hạn gần nhất | ✅ Hàm `sell()` dòng 380–403: `ORDER BY DATE(b.expiryDate)` | Đạt |
| Kiểm tra tồn kho thời gian thực | ✅ `stock_view()`, kiểm tra `need_base > 0` → raise Exception | Đạt |
| 100% tuân thủ FEFO | ✅ Logic tự động, không cho phép xuất thủ công | Đạt |

---

### Biện pháp 3: Tích hợp quét mã vạch ✅ **Hoàn thành tốt**

| Yêu cầu đề cương | Hiện trạng code | Đánh giá |
|---|---|---|
| Quét camera real-time | ✅ `BarcodeScanner` class (dòng 3445–3618), dùng OpenCV + pyzbar | Đạt |
| Hỗ trợ EAN-13, EAN-8, UPC-A, Code128, QR | ✅ pyzbar hỗ trợ tất cả | Đạt |
| Quét cho tab Sản phẩm + POS | ✅ Cả 2 tab đều có nút 📷 | Đạt |

---

### Biện pháp 4: Hệ thống báo cáo tự động ✅ **Hoàn thành tốt**

| Yêu cầu đề cương | Hiện trạng code | Đánh giá |
|---|---|---|
| Báo cáo XNT theo thời gian | ✅ `xnt_report()` — có opening/inbound/outbound/closing | Đạt |
| Cảnh báo hàng sắp hết hạn 90 ngày | ✅ `expiring_view(days=90)` | Đạt |
| Biểu đồ trực quan | ✅ matplotlib integrated (tab Báo cáo nâng cao) | Đạt |
| Xuất Excel (.xlsx) | ✅ `ExportManager.export_to_excel()` dùng pandas/openpyxl | Đạt |
| Xuất PDF | ✅ `ExportManager.export_to_pdf()` dùng ReportLab | Đạt |
| Xuất CSV | ✅ Có hỗ trợ | Đạt |

---

### Biện pháp 5: Sao lưu & bảo mật ✅ **Hoàn thành tốt**

| Yêu cầu đề cương | Hiện trạng code | Đánh giá |
|---|---|---|
| Tự động backup lúc 02:00 | ✅ `BackupManager.start_auto_backup()` + schedule | Đạt |
| Giữ tối đa 30 bản | ✅ `max_backups = 30`, `_cleanup_old_backups()` | Đạt |
| Khôi phục từ backup | ✅ `restore_backup()` | Đạt |
| Export/Import JSON | ✅ `export_data()`, `import_data()` | Đạt |

---

### Các phần bổ sung đã làm (ngoài đề cương)

| Tính năng | Mô tả |
|---|---|
| 🔐 Hệ thống License Ed25519 | Bảo mật phần mềm bằng chữ ký số, gắn hardware fingerprint |
| 🖨️ In hóa đơn | Chức năng print invoice |
| ⌨️ Phím tắt F1–F9 | Điều hướng nhanh giữa các tab |
| 💡 Tooltip | Hướng dẫn sử dụng ngay trên giao diện |
| 📄 Tài liệu đầy đủ | README, HUONG_DAN_SU_DUNG, BARCODE_SETUP, EXPORT_REPORTS |
| 📦 Script đóng gói | build.bat, build.sh cho PyInstaller |
| 📊 Báo cáo nâng cao | Doanh thu, lợi nhuận, top sản phẩm (vượt yêu cầu đề cương) |

---

## 2. NHỮNG PHẦN CHƯA LÀM / CẦN CẢI THIỆN ⚠️

### 2.1. Về mặt PHẦN MỀM — Thiếu sót kỹ thuật

| # | Vấn đề | Mức độ | Chi tiết |
|---|---|---|---|
| 1 | **Tab Bán hàng POS** dùng ngữ cảnh "nhà thuốc bán lẻ" | 🔴 Quan trọng | Đề cương nói "xuất kho/cấp phát cho tuyến dưới" nhưng UI ghi "Bán hàng POS", "Thanh toán", "Tiền khách đưa" → không phù hợp với nghiệp vụ CDC |
| 2 | **Chưa có module "Cấp phát" riêng** | 🔴 Quan trọng | CDC cấp phát thuốc/vaccine cho trạm y tế, cần ghi nhận "đơn vị nhận", không phải "khách hàng trả tiền" |
| 3 | **Chưa có phiếu xuất kho** in được | 🟡 Cần cải thiện | Đề cương nói "phiếu xuất kho" nhưng hiện tại chỉ có "hóa đơn bán hàng" |
| 4 | **Chưa có trường "Đơn vị nhận"** khi xuất kho | 🔴 Quan trọng | CDC cấp phát cho các đơn vị tuyến dưới, cần track ai nhận hàng |
| 5 | **Tên app = "Quản lý kho hàng hóa" + "nhathuoc2.py"** | 🟡 Cần đổi | Nên đổi thành "Quản lý XNT thuốc, vaccine và VTYT" cho đúng đề tài |
| 6 | **Chưa phân loại rõ: Thuốc / Vaccine / VTYT** | 🟡 Cần cải thiện | `productType` chỉ có 'general' và 'medicine', chưa có 'vaccine', 'vtyt' |
| 7 | **PDF export tiếng Việt** có thể bị lỗi font | 🟡 Cần kiểm tra | ReportLab mặc định không hỗ trợ font tiếng Việt |
| 8 | **Debug print** còn lại trong code | 🟢 Nhỏ | Nhiều dòng `print(f"DEBUG: ...")` cần xóa |

### 2.2. Về mặt HỒ SƠ SÁNG KIẾN — Thiếu sót tài liệu

| # | Phần | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | **File Word đề cương (De cuong.docx)** | ✅ Có | Cần rà soát format theo PL5 |
| 2 | **Phiếu đăng ký (PL3)** | ⚠️ Chưa điền đầy đủ | Thiếu tên, SĐT, email tác giả (ghi "Bạn tự điền") |
| 3 | **Ảnh chụp giao diện phần mềm (Phụ lục 1)** | ❌ Chưa có | Đề cương yêu cầu ảnh chụp các tab chính |
| 4 | **Sơ đồ cấu trúc CSDL (Phụ lục 2)** | ❌ Chưa có file riêng | Có mô tả trong README nhưng chưa có sơ đồ ERD đẹp |
| 5 | **File cài đặt QuanLyKho.exe (Phụ lục 3)** | ❌ Chưa build | Cần đóng gói bằng PyInstaller |
| 6 | **Bài thuyết trình PowerPoint** | ⚠️ Có nội dung (noi_dung_thuyet_trinh.md) nhưng chưa có file .pptx | Cần tạo slide |
| 7 | **Format văn bản** | ⚠️ Cần kiểm tra | Times New Roman 14, dãn dòng 1.5, lề theo quy định |

---

## 3. NHẬN XÉT VỀ ĐỊNH HƯỚNG

### ✅ Những điểm tốt

1. **Định hướng đúng**: Sáng kiến giải quyết vấn đề thực tế, có cơ sở pháp lý vững chắc
2. **Công nghệ phù hợp**: Python + SQLite + ttkbootstrap — nhẹ, không cần server, dễ triển khai
3. **5 biện pháp rõ ràng**: Mỗi biện pháp đều có mục tiêu và kết quả đo lường được
4. **Code chất lượng**: 3.648 dòng code, có kiến trúc module rõ ràng, error handling tốt
5. **Tài liệu đầy đủ**: README, hướng dẫn, changelog — rất chuyên nghiệp

### ⚠️ Vấn đề cần khắc phục

> [!IMPORTANT]
> **Vấn đề lớn nhất**: Phần mềm hiện tại thiết kế theo mô hình **"nhà thuốc bán lẻ"** (POS, khách hàng, thanh toán tiền) nhưng đề cương sáng kiến lại nói về **"cấp phát cho tuyến dưới"** tại CDC. Cần chuyển đổi/bổ sung module **"Cấp phát"** để phù hợp với nghiệp vụ thực tế.

> [!WARNING]  
> **Hồ sơ chưa hoàn chỉnh**: Thiếu ảnh chụp giao diện, sơ đồ CSDL, file exe, và slide thuyết trình — đây là các phụ lục bắt buộc theo yêu cầu Hội đồng.

---

## 4. KẾ HOẠCH HOÀN THIỆN

### Giai đoạn 1: Chỉnh sửa phần mềm cho phù hợp CDC (2-3 ngày) 🔴 Ưu tiên cao

#### [MODIFY] [nhathuoc2.py](file:///d:/Bot2025/Quanlikho2026/quan-li-kho-2026/nhathuoc2.py)

**1.1. Đổi tên & ngữ cảnh ứng dụng**
- `APP_NAME = "Quản lý XNT thuốc, vaccine và VTYT"`
- Đổi tên file từ `nhathuoc2.py` → `quanly_xnt.py`
- Cập nhật tất cả string hiển thị từ "nhà thuốc" → "kho dược"

**1.2. Thêm loại sản phẩm `vaccine` và `vtyt`**
- Mở rộng `productType` ComboBox: `['thuoc', 'vaccine', 'vtyt', 'other']`
- Thêm icon/label phân biệt trên giao diện

**1.3. Chuyển tab "Bán hàng POS" → "Xuất kho / Cấp phát"**
- Đổi tên tab, label, nút bấm
- Thêm trường **"Đơn vị nhận"** (ví dụ: TYT Phường X, TTYT Quận Y)
- Thêm trường **"Lý do xuất"** (Cấp phát, Hủy, Chuyển kho)
- Đổi "Thanh toán" → "Xác nhận xuất kho"
- Bỏ "Tiền khách đưa", "Tiền thối" (CDC không bán hàng)

**1.4. Thêm "Phiếu xuất kho" in được**
- Tạo template phiếu xuất kho theo mẫu CDC
- Hỗ trợ in phiếu xuất kho PDF
- Bao gồm: Số phiếu, ngày, đơn vị nhận, danh sách thuốc/vaccine, số lô, HSD, số lượng, người giao, người nhận

**1.5. Cải thiện module báo cáo XNT**
- Thêm cột "Đơn vị nhận" trong báo cáo xuất kho
- Báo cáo theo đơn vị nhận (ai đã nhận bao nhiêu thuốc/vaccine)

---

### Giai đoạn 2: Chuẩn bị phụ lục hồ sơ (1-2 ngày) 🟡 Ưu tiên trung bình

**2.1. Chụp ảnh giao diện phần mềm (Phụ lục 1)**
- Chạy phần mềm → chụp screenshot từng tab
- Cần ít nhất 6 ảnh: Sản phẩm, Nhập kho, Xuất kho/Cấp phát, Tồn kho, Cảnh báo HSD, Báo cáo XNT

**2.2. Tạo sơ đồ ERD cơ sở dữ liệu (Phụ lục 2)**
- Vẽ sơ đồ Entity-Relationship bằng Mermaid hoặc draw.io
- Xuất hình ảnh chất lượng cao

**2.3. Đóng gói file exe (Phụ lục 3)**
- Chạy `build.bat` để tạo QuanLyKho.exe
- Test exe trên máy sạch
- Kèm file thuoc.csv

---

### Giai đoạn 3: Hoàn thiện hồ sơ văn bản (1 ngày) 🟡 Ưu tiên trung bình

**3.1. Hoàn thiện file Word đề cương**
- Điền đầy đủ thông tin tác giả
- Format theo quy định: Times New Roman 14, dãn dòng 1.5
- Lề: trên 3.5cm, dưới 3cm, trái 3.5cm, phải 2cm
- Chèn ảnh chụp giao diện vào phần biện pháp
- Chèn sơ đồ CSDL
- Đánh số trang giữa, đầu trang

**3.2. Cập nhật nội dung đề cương**
- Cập nhật BP3 (mô tả tab "Xuất kho/Cấp phát" thay vì POS)
- Thêm mô tả chức năng "Phiếu xuất kho"
- Bổ sung loại sản phẩm vaccine, VTYT

---

### Giai đoạn 4: Tạo bài thuyết trình (1 ngày) 🟢 Ưu tiên thấp

**4.1. Tạo PowerPoint từ nội dung có sẵn**
- Sử dụng `noi_dung_thuyet_trinh.md` làm nền tảng
- 12-16 slide, thiết kế chuyên nghiệp
- Chèn ảnh chụp giao diện thực tế
- Biểu đồ so sánh trước/sau

---

### Giai đoạn 5: Kiểm thử & hoàn chỉnh (1 ngày) 🟢

**5.1. Test toàn diện**
- Kiểm tra tất cả chức năng sau khi sửa
- Test trên máy sạch (không có Python)
- Kiểm tra xuất báo cáo Excel/PDF tiếng Việt

**5.2. Clean up code**
- Xóa debug print statements
- Cập nhật version → 2.0.0
- Cập nhật CHANGELOG

---

## 5. TỔNG KẾT

### Bảng tóm tắt tiến độ

| Hạng mục | Hoàn thành | Cần làm thêm |
|---|---|---|
| **BP1: CSDL tập trung** | 95% | Thêm loại vaccine/VTYT |
| **BP2: FEFO tự động** | 100% | — |
| **BP3: Quét mã vạch** | 100% | — |
| **BP4: Báo cáo tự động** | 90% | Phiếu xuất kho, báo cáo theo đơn vị nhận |
| **BP5: Sao lưu & bảo mật** | 100% | — |
| **Module Cấp phát (CDC)** | 30% | Chuyển đổi POS → Cấp phát |
| **Hồ sơ văn bản** | 60% | Ảnh, sơ đồ, format, slide |
| **File exe** | 0% | Build & test |

### Timeline ước tính

```
Tuần 1 (Ngày 1-3): Giai đoạn 1 — Sửa phần mềm
Tuần 1 (Ngày 4-5): Giai đoạn 2 — Phụ lục hồ sơ  
Tuần 2 (Ngày 6):   Giai đoạn 3 — Hoàn thiện văn bản
Tuần 2 (Ngày 7):   Giai đoạn 4 — Thuyết trình
Tuần 2 (Ngày 8):   Giai đoạn 5 — Test & clean up
```

> [!IMPORTANT]
> **Tổng thời gian ước tính: 6-8 ngày làm việc**

---

## Open Questions

> [!IMPORTANT]
> 1. **Tab POS**: Anh muốn **giữ nguyên** tab "Bán hàng POS" (vì có thể CDC cũng bán thuốc?) hay **chuyển hoàn toàn** sang "Xuất kho/Cấp phát"? Hay **giữ cả 2** (thêm tab mới)?
> 2. **Đơn vị nhận**: Anh có danh sách các đơn vị tuyến dưới (trạm y tế, TTYT quận/huyện) không? Để tôi tích hợp sẵn vào ComboBox.
> 3. **Mẫu phiếu xuất kho**: CDC có mẫu phiếu xuất kho riêng không? Nếu có, gửi cho tôi để tạo template PDF cho đúng.
> 4. **Deadline**: Hội đồng sẽ xét sáng kiến khi nào? Để ưu tiên đúng thứ tự.
> 5. **Tôi có thể hỗ trợ** trực tiếp việc sửa code (giai đoạn 1) và tạo sơ đồ CSDL (giai đoạn 2). Anh muốn tôi bắt đầu phần nào trước?
