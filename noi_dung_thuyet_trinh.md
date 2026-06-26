# NỘI DUNG BÀI THUYẾT TRÌNH

## Đề tài: Xây dựng phần mềm quản lý xuất nhập tồn thuốc, vaccine và vật tư y tế tại Trung tâm Kiểm soát bệnh tật TP. Cần Thơ

**Tác giả:** Hồ Sỷ Thoảng
**Đơn vị:** Trung tâm Kiểm soát bệnh tật TP. Cần Thơ

---

## 📋 DÀN BÀI THUYẾT TRÌNH (Gợi ý 12–15 slide)

---

### SLIDE 1 — TRANG BÌA

```
XÂY DỰNG PHẦN MỀM QUẢN LÝ XUẤT NHẬP TỒN
THUỐC, VACCINE VÀ VẬT TƯ Y TẾ
TẠI TRUNG TÂM KIỂM SOÁT BỆNH TẬT TP. CẦN THƠ

Sáng kiến cải tiến

Tác giả: Hồ Sỷ Thoảng
Đơn vị: Trung tâm Kiểm soát bệnh tật TP. Cần Thơ
Năm 2026
```

---

### SLIDE 2 — ĐẶT VẤN ĐỀ

**Tiêu đề:** Tại sao cần phần mềm quản lý kho?

**Nội dung trình bày:**

> CDC Cần Thơ là đầu mối tiếp nhận, bảo quản và cấp phát thuốc, vaccine, vật tư y tế cho toàn bộ hệ thống y tế dự phòng trên địa bàn thành phố. Khối lượng hàng hóa rất lớn: hàng nghìn mặt hàng thuốc, nhiều chủng loại vaccine, và vật tư tiêu hao đa dạng.

**Ý chính (bullet points trên slide):**
- Công tác quản lý kho chủ yếu bằng **sổ sách thủ công** và **Excel rời rạc**
- Theo dõi số lô, hạn dùng bằng tay → **dễ bỏ sót lô cận hạn**
- Tra cứu tồn kho từ nhiều nguồn → **sai sót số lượng, nhầm mã lô**
- Lập báo cáo XNT thủ công → **mất 2–3 ngày, sai sót cao**
- Không có cảnh báo tự động → **không đảm bảo nguyên tắc FEFO**

---

### SLIDE 3 — MỤC TIÊU SÁNG KIẾN

**Tiêu đề:** Mục tiêu

**Nội dung trình bày:**

> Tự nghiên cứu, thiết kế và lập trình một phần mềm quản lý kho chuyên dụng, phù hợp quy trình nghiệp vụ thực tế tại đơn vị, không phụ thuộc bên thứ ba.

**Ý chính:**
1. **Tập trung hóa** toàn bộ dữ liệu thuốc, vaccine, VTYT trên một nền tảng duy nhất
2. **Tự động hóa** quy trình xuất kho theo nguyên tắc FEFO
3. **Tích hợp mã vạch** (Barcode) để đối soát nhanh, chính xác
4. **Tự động tạo báo cáo** XNT, cảnh báo hàng sắp hết hạn
5. **Đảm bảo an toàn dữ liệu** với cơ chế sao lưu tự động

---

### SLIDE 4 — CƠ SỞ LÝ LUẬN

**Tiêu đề:** Cơ sở pháp lý & khoa học

**Nội dung trình bày (điểm qua nhanh):**

| Cơ sở | Nội dung |
|---|---|
| **Nguyên tắc FEFO** | Bắt buộc trong quản lý kho dược phẩm và vaccine (Bộ Y tế) |
| **Thông tư 36/2018/TT-BYT** | Thực hành tốt bảo quản thuốc (GSP) — truy xuất số lô, hạn dùng |
| **Quyết định 749/QĐ-TTg** | Chương trình Chuyển đổi số quốc gia — y tế là lĩnh vực ưu tiên |
| **Công nghệ mã vạch** | Ứng dụng rộng rãi trong quản lý dược phẩm toàn cầu |

---

### SLIDE 5 — THỰC TRẠNG TẠI ĐƠN VỊ

**Tiêu đề:** Thuận lợi & Khó khăn

**Thuận lợi:**
- ✅ Hệ thống máy tính cơ bản sẵn có
- ✅ Cán bộ kho có trình độ chuyên môn, tinh thần tiếp thu CNTT
- ✅ Danh mục thuốc quốc gia đã được số hóa (30.000+ mặt hàng)

**Khó khăn:**
- ❌ Khối lượng hàng lớn, đa dạng (thuốc, vaccine, VTYT)
- ❌ Nhiều mặt hàng tên gần giống nhau → nhầm lẫn thủ công
- ❌ Tra cứu lịch sử cấp phát bất tiện (dữ liệu rải rác nhiều sổ)
- ❌ Lập báo cáo XNT đầy đủ mất 2–3 ngày

---

### SLIDE 6 — GIẢI PHÁP: KIẾN TRÚC PHẦN MỀM

**Tiêu đề:** Thiết kế phần mềm

**Nội dung trình bày:**

> Phần mềm tự xây dựng trên nền tảng Python, CSDL SQLite cục bộ, giao diện ttkbootstrap.

**Sơ đồ kiến trúc (mermaid — có thể vẽ lại dạng hình ảnh cho PowerPoint):**

```
┌─────────────────────────────────────────────────────┐
│              GIAO DIỆN NGƯỜI DÙNG (ttkbootstrap)    │
├──────┬──────┬──────┬──────┬──────┬──────┬───────────┤
│  Sản │ Nhập │ Xuất │ Tồn  │ Cảnh │ Báo  │  Sao lưu  │
│  phẩm│ kho  │ kho  │ kho  │ báo  │ cáo  │  & Phục   │
│      │      │ FEFO │      │ HSD  │Excel │  hồi      │
│      │      │      │      │      │ PDF  │           │
├──────┴──────┴──────┴──────┴──────┴──────┴───────────┤
│           XỬ LÝ NGHIỆP VỤ (Python)                 │
│  • FEFO Engine  • Barcode Scanner  • Report Engine  │
├─────────────────────────────────────────────────────┤
│           CƠ SỞ DỮ LIỆU (SQLite)                   │
│  products │ batches │ stock_movements │ sales       │
└─────────────────────────────────────────────────────┘
```

**Công nghệ sử dụng:**
- **Ngôn ngữ:** Python 3.8+
- **CSDL:** SQLite (cục bộ, không cần server)
- **Giao diện:** ttkbootstrap (modern UI)
- **Barcode:** OpenCV + pyzbar
- **Biểu đồ:** matplotlib
- **Báo cáo:** pandas, openpyxl, ReportLab (PDF)

---

### SLIDE 7 — BIỆN PHÁP 1: CƠ SỞ DỮ LIỆU TẬP TRUNG

**Tiêu đề:** BP1 — Cơ sở dữ liệu tập trung

**Nội dung:**
- Thiết kế 6 bảng chính: [products](file:///d:/build/quan-li-kho-main/quan-li-kho-main/nhathuoc2.py#838-864), `product_units`, `batches`, `stock_movements`, [sales](file:///d:/build/quan-li-kho-main/quan-li-kho-main/nhathuoc2.py#865-912), `sale_items`
- Tích hợp **danh mục thuốc quốc gia** (30.000+ mặt hàng) với **autocomplete thông minh**
- Cán bộ chỉ cần gõ vài ký tự → hệ thống tự gợi ý tên thuốc, số đăng ký, đơn vị tính

**Kết quả:**

| Trước | Sau |
|---|---|
| Nhập thông tin sản phẩm mới: **5 phút** | **10 giây** |

> *(Slide này nên có ảnh chụp giao diện tab Sản phẩm với autocomplete đang hiển thị)*

---

### SLIDE 8 — BIỆN PHÁP 2: XUẤT KHO TỰ ĐỘNG THEO FEFO

**Tiêu đề:** BP2 — Tự động hóa xuất kho FEFO

**Nội dung:**
- Khi thực hiện lệnh xuất kho → hệ thống **tự động chọn lô có hạn dùng gần nhất** để xuất trước
- Cán bộ kho **không cần tra cứu thủ công** lô nào hết hạn trước
- **Kiểm tra tồn kho thời gian thực**, ngăn xuất vượt số lượng hiện có

**Kết quả:**
- ✅ **100% phiếu xuất kho** tuân thủ nguyên tắc FEFO
- ✅ Loại bỏ hoàn toàn rủi ro xuất lô hàng cũ
- ✅ Thời gian lập phiếu xuất: **từ 15–20 phút → 2–3 phút**

> *(Slide này nên có ảnh chụp giao diện tab Xuất kho/Cấp phát)*

---

### SLIDE 9 — BIỆN PHÁP 3: QUÉT MÃ VẠCH

**Tiêu đề:** BP3 — Tích hợp công nghệ quét mã vạch

**Nội dung:**
- Sử dụng **camera máy tính** kết hợp thư viện **OpenCV + pyzbar**
- Hỗ trợ nhiều định dạng: **EAN-13, EAN-8, UPC-A, Code128, QR Code**
- Quét mã vạch trên bao bì → tự động nhận diện sản phẩm, số lô

**Kết quả:**
- Tốc độ đối soát: **gấp 5 lần** so với thủ công
- **0% sai sót** chép tay số lô

> *(Slide này nên có ảnh chụp giao diện quét barcode bằng camera)*

---

### SLIDE 10 — BIỆN PHÁP 4: BÁO CÁO TỰ ĐỘNG

**Tiêu đề:** BP4 — Hệ thống báo cáo tự động

**Nội dung:**
- Báo cáo **Xuất – Nhập – Tồn** theo khoảng thời gian tùy chọn
- **Cảnh báo** danh sách hàng sắp hết hạn trong 90 ngày
- **Biểu đồ trực quan** hóa dữ liệu (matplotlib)
- Xuất file **Excel (.xlsx)** và **PDF** chuyên nghiệp

**Kết quả:**

| Trước | Sau |
|---|---|
| Thời gian lập báo cáo XNT: **2–3 ngày** | **Dưới 5 phút** |

> *(Slide này nên có ảnh chụp báo cáo mẫu hoặc biểu đồ)*

---

### SLIDE 11 — BIỆN PHÁP 5: SAO LƯU & BẢO MẬT

**Tiêu đề:** BP5 — Sao lưu và bảo mật dữ liệu

**Nội dung:**
- Tự động sao lưu CSDL **hàng ngày lúc 02:00**, giữ tối đa **30 bản backup**
- Khôi phục dữ liệu từ bất kỳ bản sao lưu nào
- Xuất/nhập toàn bộ dữ liệu dạng **JSON** để chuyển đổi giữa các máy

**Kết quả:**
- ✅ An toàn dữ liệu tuyệt đối
- ✅ Không phụ thuộc server hay internet

---

### SLIDE 12 — BẢNG SO SÁNH HIỆU QUẢ

**Tiêu đề:** Hiệu quả trước và sau khi áp dụng

| Tiêu chí | Trước (thủ công) | Sau (phần mềm) |
|---|---|---|
| Nhập thông tin sản phẩm mới | 5 phút/SP | **10 giây/SP** |
| Lập phiếu xuất kho | 15–20 phút | **2–3 phút** |
| Tuân thủ FEFO | Không đảm bảo | **100% tự động** |
| Lập báo cáo XNT | 2–3 ngày | **Dưới 5 phút** |
| Sai sót số lô trên phiếu xuất | Thường xuyên | **0%** |
| Cảnh báo hàng sắp hết hạn | Không có | **Tự động (90 ngày)** |
| Sao lưu dữ liệu | Không có | **Tự động hàng ngày** |

> *(Slide quan trọng nhất — nên làm nổi bật bằng màu sắc, các con số gây ấn tượng)*

---

### SLIDE 13 — LỢI ÍCH KINH TẾ – XÃ HỘI

**Tiêu đề:** Lợi ích mang lại

**Lợi ích kinh tế:**
- 💰 Giảm lãng phí thuốc/vaccine quá hạn nhờ FEFO tự động
- 💰 Tiết kiệm **hơn 70% thời gian** lập báo cáo
- 💰 Dự trù hàng hóa chính xác hơn, tránh thừa/thiếu

**Lợi ích xã hội:**
- 🏥 Nâng cao tính **minh bạch, chính xác** trong quản lý tài sản công
- 🏥 Đảm bảo vaccine và thuốc **cấp phát kịp thời, đúng chất lượng**
- 🏥 Góp phần **chuyển đổi số** trong y tế dự phòng tại địa phương

---

### SLIDE 14 — KẾT LUẬN

**Tiêu đề:** Kết luận

**Nội dung:**
1. ✅ **Chuẩn hóa và tự động hóa** quy trình XNK tại CDC Cần Thơ
2. ✅ Đảm bảo **100% tuân thủ FEFO**, giảm thiểu lãng phí
3. ✅ Tiết kiệm **thời gian và nhân lực** đáng kể
4. ✅ Phần mềm **tự xây dựng** → sát quy trình thực tế, dễ điều chỉnh, không phụ thuộc bên ngoài
5. ✅ Có khả năng **mở rộng** cho các đơn vị y tế dự phòng khác

---

### SLIDE 15 — KIẾN NGHỊ

**Tiêu đề:** Kiến nghị

1. Đề nghị Hội đồng **công nhận sáng kiến** và cho phép triển khai rộng rãi
2. Kiến nghị **trang bị máy quét mã vạch chuyên dụng** để nâng cao hiệu quả
3. Kiến nghị **mở rộng triển khai** cho các trạm y tế và đơn vị y tế dự phòng tuyến quận/huyện

---

### SLIDE 16 — DEMO & HỎI ĐÁP (Slide cuối)

```
DEMO PHẦN MỀM TRỰC TIẾP
(Nếu có chuẩn bị máy tính)

XIN CẢM ƠN HỘI ĐỒNG ĐÃ LẮNG NGHE!

Tác giả: Hồ Sỷ Thoảng
Email: hstptcn5@gmail.com
ĐT: 0329381189
```

---

## 💡 GỢI Ý TRÌNH BÀY

### Thời gian phân bổ (nếu 15 phút):
| Nội dung | Thời gian |
|---|---|
| Slide 1: Mở đầu | 0.5 phút |
| Slide 2–3: Đặt vấn đề & Mục tiêu | 2 phút |
| Slide 4–5: Cơ sở lý luận & Thực trạng | 2 phút |
| Slide 6: Kiến trúc phần mềm | 1.5 phút |
| Slide 7–11: 5 Biện pháp | 5 phút |
| Slide 12: Bảng so sánh hiệu quả | 1.5 phút |
| Slide 13–15: Lợi ích, Kết luận, Kiến nghị | 1.5 phút |
| Slide 16: Demo / Hỏi đáp | 1 phút |

### Mẹo trình bày:
1. **Bảng so sánh (Slide 12)** là điểm nhấn quan trọng nhất — nên dừng lại nhấn mạnh các con số
2. **Ảnh chụp giao diện** nên chèn vào các slide biện pháp để minh họa trực quan
3. Nếu có điều kiện, **demo trực tiếp** phần mềm sẽ gây ấn tượng mạnh với Hội đồng
4. Chuẩn bị sẵn một vài **phiếu xuất kho mẫu** đã in từ phần mềm để Hội đồng xem
5. Nhấn mạnh rằng phần mềm **tự xây dựng 100%**, không mua ngoài — đây là điểm cộng lớn
6. Chuẩn bị trả lời câu hỏi thường gặp:
   - "Tại sao không mua phần mềm thương mại?"
   - "Bảo mật dữ liệu như thế nào?"
   - "Khả năng mở rộng ra sao?"
   - "Chi phí triển khai?"

---

## 📚 TÀI LIỆU THAM KHẢO

[1] Bộ Y tế (2018), Thông tư 36/2018/TT-BYT về Thực hành tốt bảo quản thuốc.
[2] Bộ Y tế (2019), Thông tư 11/2019/TT-BYT về quản lý vaccine và sinh phẩm y tế.
[3] Thủ tướng Chính phủ (2020), QĐ 749/QĐ-TTg phê duyệt Chương trình Chuyển đổi số quốc gia.
[4] Bộ Y tế (2024), QĐ 4416/QĐ-BYT về ứng dụng CNTT và chuyển đổi số y tế 2024–2025.
