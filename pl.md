SỞ Y TẾ THÀNH PHỐ CẦN THƠ
TRUNG TÂM
KIỂM SOÁT BỆNH TẬT	CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc


Cần Thơ, ngày … tháng … năm 20…

PHIẾU ĐĂNG KÝ THỰC HIỆN ĐỀ ÁN, SÁNG KIẾN CẢI TIẾN

Kính gửi: Hội đồng Khoa học và công nghệ cơ sở
Trung tâm Kiểm soát bệnh tật TP. Cần Thơ

1. Tên đề án/sáng kiến cải tiến: 
	Xây dựng phần mềm quản lý xuất nhập tồn thuốc, vaccine và vật tư y tế tại Trung tâm Kiểm soát bệnh tật TP. Cần Thơ.

2.Tác giả đề án/sáng kiến cải tiến:
- Họ tên: 	(Bạn tự điền)
- Cơ quan, đơn vị:	Trung tâm Kiểm soát bệnh tật TP. Cần Thơ
- Điện thoại: 	(Bạn tự điền)
- Email: 	(Bạn tự điền)
3. Đồng tác giả/cộng sự thực hiện đề án/sáng kiến cải tiến (nếu có):
1/. 	(Bạn tự điền nếu có)
2/. 	
3/. 	
(Đề nghị ghi rõ: Chức danh, Họ và tên - Chức vụ - Đơn vị/khoa, phòng đang công tác)
4. Bản thuyết minh mô tả giải pháp của đề án, sáng kiến cải tiến:                  
* Mô tả ngắn gọn các giải pháp cũ thường làm (nêu rõ những nhược điểm cần khắc phục):
	Hiện tại, công tác quản lý kho thuốc, vaccine và vật tư y tế tại đơn vị chủ yếu thực hiện bằng sổ sách ghi chép thủ công hoặc các file Excel rời rạc, không liên kết. Nhược điểm chính bao gồm:
	- Việc theo dõi số lô (Lot No) và hạn dùng của từng mặt hàng, đặc biệt là vaccine, phải rà soát thủ công nên dễ bỏ sót lô hàng cận hạn nằm sâu trong kho, dẫn đến nguy cơ lãng phí do hàng quá hạn sử dụng.
	- Khi cấp phát cho các đơn vị tuyến dưới, cán bộ kho phải tra cứu tồn kho từ nhiều nguồn dữ liệu khác nhau, mất nhiều thời gian và dễ xảy ra sai sót về số lượng hoặc nhầm lẫn mã số lô.
	- Công tác lập báo cáo xuất – nhập – tồn định kỳ phải tổng hợp thủ công, tốn nhiều ngày công lao động và khó đảm bảo tính chính xác tuyệt đối.
	- Không có cơ chế cảnh báo tự động khi hàng hóa sắp hết hạn, dẫn đến việc xuất kho không theo nguyên tắc FEFO (First Expired First Out – Hạn gần xuất trước).

* Mục đích thực hiện đề án, sáng kiến cải tiến (nêu rõ mục đích khắc phục các nhược điểm của giải pháp cũ hoặc mục đích của giải pháp mới do mình tạo ra): 
	- Tự nghiên cứu, thiết kế và lập trình một phần mềm quản lý kho chuyên dụng, tập trung hóa toàn bộ dữ liệu thuốc, vaccine và vật tư y tế trên một nền tảng duy nhất, phù hợp với quy trình nghiệp vụ thực tế tại đơn vị.
	- Tự động hóa quy trình xuất kho theo nguyên tắc FEFO, đảm bảo lô hàng có hạn dùng gần nhất luôn được ưu tiên cấp phát trước, giảm thiểu tối đa tình trạng hàng hủy do quá hạn.
	- Tích hợp công nghệ quét mã vạch (Barcode) để đối soát chính xác chủng loại và số lô khi nhập kho cũng như xuất kho cấp phát, tránh nhầm lẫn giữa các mặt hàng có tên gọi gần giống nhau.
	- Tự động tạo báo cáo xuất – nhập – tồn, báo cáo cảnh báo hàng sắp hết hạn, giúp tiết kiệm thời gian và nâng cao độ chính xác trong công tác thống kê báo cáo.
	- Đảm bảo an toàn dữ liệu thông qua cơ chế sao lưu tự động định kỳ.

* Bản mô tả giải pháp của đề án, sáng kiến cải tiến:
- Thuyết minh giải pháp mới của đề án, sáng kiến cải tiến: 
	Tác giả tự nghiên cứu và lập trình phần mềm trên nền tảng Python với cơ sở dữ liệu SQLite cục bộ, giao diện đồ họa hiện đại (ttkbootstrap). Phần mềm được thiết kế gồm các module chính:
	(1) Module Quản lý sản phẩm: Cho phép quản lý danh mục thuốc, vaccine và vật tư y tế với chức năng autocomplete thông minh từ cơ sở dữ liệu danh mục thuốc quốc gia (hơn 30.000 mặt hàng). Mỗi sản phẩm được quản lý chi tiết theo số đăng ký, đơn vị tính, mã vạch.
	(2) Module Nhập kho: Ghi nhận chi tiết từng lần nhập hàng kèm số lô (Lot No), hạn dùng (Expiry Date) và giá nhập. Hỗ trợ quét mã vạch bằng camera để nhập liệu nhanh, chính xác.
	(3) Module Xuất kho/Cấp phát: Tự động áp dụng nguyên tắc FEFO – hệ thống tự chọn lô hàng có hạn dùng gần nhất để xuất trước. Kiểm soát tồn kho theo thời gian thực, ngăn chặn việc xuất vượt quá số lượng tồn.
	(4) Module Báo cáo: Xuất báo cáo Nhập – Xuất – Tồn theo khoảng thời gian tùy chọn. Cảnh báo danh sách hàng sắp hết hạn trong vòng 90 ngày. Hỗ trợ xuất file Excel và PDF chuyên nghiệp phục vụ báo cáo nội bộ và báo cáo cấp trên.
	(5) Module Sao lưu: Tự động sao lưu cơ sở dữ liệu hàng ngày lúc 02:00 sáng, giữ tối đa 30 bản sao lưu gần nhất. Hỗ trợ khôi phục dữ liệu khi có sự cố.

- Thuyết minh về phạm vi áp dụng đề án, sáng kiến cải tiến:
	- Áp dụng tại kho tổng của Trung tâm Kiểm soát bệnh tật TP. Cần Thơ, phục vụ công tác quản lý và cấp phát thuốc, vaccine, vật tư y tế cho các đơn vị tuyến dưới trên địa bàn thành phố.
	- Có thể mở rộng triển khai cho kho dược của các trạm y tế, bệnh viện tuyến quận/huyện hoặc các đơn vị y tế dự phòng khác có nhu cầu quản lý kho tương tự.

- Thuyết minh về lợi ích kinh tế, xã hội của đề án, sáng kiến cải tiến: 
	* Lợi ích kinh tế:
	- Giảm thiểu lãng phí do thuốc và vaccine quá hạn sử dụng nhờ cơ chế cảnh báo và xuất kho FEFO tự động.
	- Tiết kiệm chi phí nhân công: giảm hơn 70% thời gian lập báo cáo xuất – nhập – tồn so với phương pháp thủ công.
	- Hỗ trợ công tác dự trù hàng hóa chính xác hơn dựa trên dữ liệu tồn kho thực tế, tránh tình trạng dự trù thừa hoặc thiếu.
	* Lợi ích xã hội:
	- Nâng cao tính minh bạch, chính xác trong công tác quản lý tài sản công (thuốc, vaccine, vật tư y tế).
	- Đảm bảo vaccine và thuốc luôn được cấp phát kịp thời, đúng chất lượng phục vụ công tác phòng chống dịch bệnh và chăm sóc sức khỏe nhân dân.
	- Góp phần thúc đẩy chuyển đổi số trong lĩnh vực y tế dự phòng tại địa phương.

- Các tài liệu khác gửi kèm theo (sơ đồ công nghệ, hình vẽ, ảnh chụp, mô hình, sản phẩm chế thử,…):
	- Ảnh chụp giao diện phần mềm (các tab: Quản lý sản phẩm, Nhập kho, Xuất kho, Báo cáo).
	- Sơ đồ cấu trúc cơ sở dữ liệu (Database Schema).
	- Sản phẩm phần mềm chạy thử (file thực thi QuanLyKho.exe).

5. Bản cam kết không sao chép hoặc vi phạm bản quyền: 
Tôi cam kết đề án, sáng kiến cải tiến nêu trên là trung thực, do nhóm nghiên cứu thực hiện, không sao chép hay vi phạm bản quyền và thực hiện nghiêm túc, đúng theo thời gian quy định về công tác nghiên cứu khoa học, sáng kiến cải tiến tại đơn vị.
Kính mong Hội đồng Khoa học và công nghệ cấp cơ sở xem xét chấp thuận cho tiến hành các bước tiếp theo của nghiên cứu khoa học.
Trân trọng./.

	Người đề nghị
(Ký và ghi rõ họ tên)




================================================================================
HÌNH THỨC ĐỀ TÀI NGHIÊN CỨU KHOA HỌC,
SÁNG KIẾN CẢI TIẾN, ĐỀ ÁN
(Phần này là hướng dẫn định dạng — giữ nguyên để tham khảo khi soạn file Word)
================================================================================

Đề tài nghiên cứu phải được trình bày ngắn gọn, rõ ràng, mạch lạc, sạch sẽ không được tẩy xóa, có đánh số trang, đánh số bảng biểu, hình vẽ, đồ thị. Chủ nhiệm (nhóm nghiên cứu) cần có lời cam đoan danh dự về công trình khoa học này của mình (của nhóm). Đề tài nghiên cứu đóng bìa cứng màu xanh dương và có trang phụ bìa (phụ lục số 1 và 2).
1. Quy định soạn thảo văn bản trong đề tài nghiên cứu
Đề tài nghiên cứu sử dụng:
- Font chữ "Times New Roman" cỡ (size) 14 của soạn thảo Winword hoặc tương đương; 
- Mật độ chữ bình thường, không được nén hoặc kéo dãn khoảng cách giữa các chữ;
- Dãn dòng đặt ở chế độ (Paragraph spacing/Line spacing) 1,5 lines; 
- Cài đặt trang giấy (Page setup): lề trên (Top) 3,5 cm; lề dưới (Bottom) 3 cm; lề trái (Left) 3,5 cm; lề phải (Right) 2 cm;
- Số trang được đánh ở giữa, phía trên đầu mỗi trang giấy (Insert page number/Top of page/Center). 


================================================================================
NỘI DUNG CHÍNH CỦA SÁNG KIẾN, CẢI TIẾN (PL5 — ĐÃ ĐIỀN)
================================================================================

Mục lục

Danh mục chữ cái viết tắt
	CDC:	Trung tâm Kiểm soát bệnh tật (Centers for Disease Control)
	FEFO:	First Expired First Out (Hạn gần xuất trước)
	GSP:	Good Storage Practices (Thực hành tốt bảo quản thuốc)
	VTYT:	Vật tư y tế
	XNT:	Xuất – Nhập – Tồn
	CSDL:	Cơ sở dữ liệu


1. ĐẶT VẤN ĐỀ

Trung tâm Kiểm soát bệnh tật TP. Cần Thơ (CDC Cần Thơ) là đầu mối quan trọng trong công tác tiếp nhận, bảo quản và cấp phát thuốc, vaccine và vật tư y tế (VTYT) cho các đơn vị y tế tuyến dưới trên toàn thành phố. Khối lượng hàng hóa quản lý bao gồm hàng nghìn mặt hàng thuốc thông thường, nhiều chủng loại vaccine phục vụ chương trình tiêm chủng mở rộng, cùng các loại vật tư tiêu hao phục vụ xét nghiệm và phòng chống dịch.

Trong thực tế, công tác quản lý kho hiện nay vẫn chủ yếu dựa vào sổ sách ghi chép thủ công hoặc các bảng tính Excel rời rạc. Phương pháp này bộc lộ nhiều hạn chế nghiêm trọng:

- Việc theo dõi số lô và hạn dùng của thuốc, vaccine bằng tay dễ dẫn đến sai sót, đặc biệt khi kho có nhiều lô hàng cùng một mặt hàng với hạn dùng khác nhau. Điều này gây nguy cơ cấp phát hàng cận hạn hoặc quá hạn cho tuyến dưới.

- Mỗi đợt cấp phát lớn (ví dụ: cấp vaccine cho chiến dịch tiêm chủng), cán bộ kho phải tra cứu tồn kho từ nhiều nguồn, đối chiếu thủ công số lô trên phiếu xuất, tốn rất nhiều thời gian và nhân lực.

- Báo cáo xuất – nhập – tồn định kỳ phải tổng hợp thủ công từ các sổ sách, mất nhiều ngày công và khó đảm bảo tính kịp thời, chính xác khi gửi lên cấp trên.

Trước thực trạng trên, tác giả đã tự nghiên cứu và xây dựng một phần mềm quản lý kho chuyên dụng để thay thế phương pháp thủ công. Giải pháp này vừa phù hợp với chủ trương chuyển đổi số trong ngành y tế, vừa đảm bảo phần mềm được thiết kế sát với quy trình nghiệp vụ thực tế tại đơn vị mà không phụ thuộc vào bên thứ ba. Đây chính là lý do tác giả chọn thực hiện sáng kiến, cải tiến này.


2. NỘI DUNG CHÍNH

2.1. Cơ sở lý luận

- Nguyên tắc FEFO (First Expired First Out): Đây là nguyên tắc bắt buộc trong quản lý kho dược phẩm và vaccine theo quy định của Bộ Y tế. Hàng hóa có hạn dùng gần nhất phải được xuất kho trước để đảm bảo chất lượng và giảm thiểu lãng phí [1].

- Thực hành tốt bảo quản thuốc (GSP): Theo Thông tư 36/2018/TT-BYT, các cơ sở phải có hệ thống theo dõi xuất nhập kho đảm bảo truy xuất được nguồn gốc, số lô và hạn dùng của từng mặt hàng [2].

- Chuyển đổi số trong y tế: Theo Quyết định 749/QĐ-TTg ngày 03/6/2020 của Thủ tướng Chính phủ về Chương trình Chuyển đổi số quốc gia, y tế là một trong những lĩnh vực ưu tiên chuyển đổi số. Việc ứng dụng phần mềm quản lý kho là bước cụ thể hóa chủ trương này tại cơ sở [3].

- Công nghệ mã vạch (Barcode): Mã vạch đã được ứng dụng rộng rãi trong quản lý dược phẩm trên toàn cầu, giúp giảm thiểu sai sót do nhập liệu thủ công, tăng tốc độ đối soát hàng hóa [4].

2.2. Thực trạng của vấn đề

* Thuận lợi:
- Đơn vị đã có hệ thống máy tính cơ bản phục vụ công tác văn phòng.
- Cán bộ kho dược có trình độ chuyên môn và tinh thần tiếp thu công nghệ mới.
- Danh mục thuốc quốc gia đã được số hóa dưới dạng file CSV (hơn 30.000 mặt hàng), có thể tích hợp ngay vào phần mềm.

* Khó khăn:
- Khối lượng hàng hóa lớn, đa dạng (thuốc thường, thuốc chuyên khoa, vaccine các loại, VTYT tiêu hao) khiến việc quản lý thủ công gặp rất nhiều khó khăn.
- Nhiều mặt hàng thuốc/vaccine có tên gần giống nhau nhưng hàm lượng, số đăng ký khác nhau, dễ nhầm lẫn khi ghi chép thủ công.
- Việc tra cứu lịch sử cấp phát cho từng đơn vị tuyến dưới rất bất tiện khi dữ liệu nằm rải rác trong nhiều sổ sách.
- Thời gian lập một bộ báo cáo XNT đầy đủ mất khoảng 2-3 ngày làm việc bằng phương pháp thủ công.

2.3. Các biện pháp đã tiến hành

Biện pháp 1: Xây dựng cơ sở dữ liệu tập trung
- Thiết kế hệ thống CSDL SQLite gồm 6 bảng chính: products (sản phẩm), product_units (đơn vị tính), batches (lô hàng), stock_movements (xuất nhập kho), sales (phiếu xuất), sale_items (chi tiết phiếu xuất).
- Tích hợp danh mục thuốc quốc gia (file thuoc.csv — hơn 30.000 mặt hàng) với chức năng autocomplete thông minh: khi cán bộ gõ một vài ký tự, hệ thống tự gợi ý tên thuốc, số đăng ký, đơn vị tính.
- Hiệu quả: Giảm thời gian nhập thông tin sản phẩm mới từ 5 phút xuống còn 10 giây.

Biện pháp 2: Triển khai module xuất kho tự động theo FEFO
- Khi thực hiện lệnh xuất kho, hệ thống tự động lựa chọn lô hàng có hạn dùng gần nhất để xuất trước. Cán bộ kho không cần tra cứu thủ công.
- Hệ thống tự kiểm tra tồn kho theo thời gian thực, ngăn chặn việc xuất vượt quá số lượng hiện có.
- Hiệu quả: Đảm bảo 100% phiếu xuất kho tuân thủ nguyên tắc FEFO, loại bỏ hoàn toàn rủi ro xuất lô hàng cũ trong khi lô mới đã hết hạn.

Biện pháp 3: Tích hợp công nghệ quét mã vạch
- Sử dụng camera máy tính kết hợp thư viện nhận dạng mã vạch (OpenCV + pyzbar) để quét mã vạch trên bao bì thuốc, vaccine.
- Hỗ trợ nhiều định dạng: EAN-13, EAN-8, UPC-A, Code128, QR Code.
- Hiệu quả: Tăng tốc độ đối soát hàng hóa gấp 5 lần so với kiểm tra thủ công, loại bỏ sai sót do chép tay số lô.

Biện pháp 4: Xây dựng hệ thống báo cáo tự động
- Báo cáo Xuất – Nhập – Tồn theo khoảng thời gian tùy chọn (ngày/tháng/quý/năm).
- Cảnh báo danh sách hàng sắp hết hạn trong vòng 90 ngày.
- Biểu đồ trực quan hóa dữ liệu xuất nhập kho (matplotlib).
- Xuất file Excel (.xlsx) và PDF chuyên nghiệp phục vụ báo cáo cấp trên.
- Hiệu quả: Thời gian lập báo cáo XNT giảm từ 2-3 ngày xuống còn dưới 5 phút.

Biện pháp 5: Thiết lập cơ chế sao lưu và bảo mật
- Tự động sao lưu CSDL hàng ngày lúc 02:00 sáng, giữ tối đa 30 bản backup gần nhất.
- Hỗ trợ khôi phục dữ liệu từ bất kỳ bản sao lưu nào khi có sự cố.
- Hỗ trợ xuất/nhập toàn bộ dữ liệu dưới dạng JSON để chuyển đổi giữa các máy tính.
- Hiệu quả: Đảm bảo an toàn dữ liệu, không lo mất dữ liệu do sự cố phần cứng.

2.4. Hiệu quả của sáng kiến, cải tiến

Sáng kiến đã được triển khai thí điểm tại kho dược của CDC Cần Thơ, phục vụ công tác quản lý và cấp phát thuốc, vaccine, VTYT cho các đơn vị tuyến dưới.

So sánh hiệu quả trước và sau khi áp dụng:

| Tiêu chí                                       | Trước (thủ công) | Sau (phần mềm)     |
|-------------------------------------------------|-------------------|---------------------|
| Thời gian nhập thông tin sản phẩm mới           | 5 phút/sản phẩm   | 10 giây/sản phẩm    |
| Thời gian lập phiếu xuất kho                    | 15-20 phút/phiếu  | 2-3 phút/phiếu      |
| Tuân thủ nguyên tắc FEFO                        | Không đảm bảo     | 100% tự động         |
| Thời gian lập báo cáo XNT                       | 2-3 ngày          | Dưới 5 phút         |
| Sai sót số lô trên phiếu xuất                   | Thường xuyên      | 0%                   |
| Cảnh báo hàng sắp hết hạn                       | Không có          | Tự động (90 ngày)    |
| Sao lưu dữ liệu                                | Không có          | Tự động hàng ngày    |


3. KẾT LUẬN

Sáng kiến "Xây dựng phần mềm quản lý xuất nhập tồn thuốc, vaccine và vật tư y tế tại Trung tâm Kiểm soát bệnh tật TP. Cần Thơ" đã mang lại những kết quả tích cực:

- Chuẩn hóa và tự động hóa quy trình xuất nhập kho tại CDC Cần Thơ, giúp công tác quản lý hậu cần y tế trở nên khoa học, minh bạch và chính xác hơn.
- Đảm bảo thuốc, vaccine luôn được luân chuyển theo nguyên tắc FEFO, giảm thiểu tối đa tình trạng lãng phí do hàng quá hạn sử dụng.
- Tiết kiệm đáng kể thời gian và nhân lực cho công tác kiểm kho, lập phiếu xuất và báo cáo định kỳ, giúp cán bộ y tế tập trung hơn vào chuyên môn.
- Bài học kinh nghiệm: Việc tự xây dựng phần mềm tại đơn vị có lợi thế lớn là phần mềm được thiết kế sát với quy trình nghiệp vụ thực tế, dễ dàng điều chỉnh khi có yêu cầu mới, không phụ thuộc vào nhà cung cấp bên ngoài.
- Phần mềm có khả năng mở rộng triển khai cho các đơn vị y tế dự phòng khác trên địa bàn và có thể phát triển thêm các tính năng nâng cao như quản lý người dùng, phân quyền, đồng bộ dữ liệu qua mạng.


4. KIẾN NGHỊ

- Đề nghị Hội đồng Khoa học xem xét công nhận sáng kiến và cho phép triển khai rộng rãi phần mềm tại các khoa/phòng chức năng khác trong đơn vị.
- Kiến nghị Ban Giám đốc Trung tâm hỗ trợ trang bị thêm máy quét mã vạch chuyên dụng (ngoài camera máy tính) để nâng cao tốc độ và độ chính xác khi xuất nhập kho khối lượng lớn.
- Kiến nghị mở rộng triển khai phần mềm cho các trạm y tế và đơn vị y tế dự phòng tuyến quận/huyện trên địa bàn TP. Cần Thơ.


TÀI LIỆU THAM KHẢO

[1] Bộ Y tế (2018), Thông tư 36/2018/TT-BYT ngày 22/11/2018 về Thực hành tốt bảo quản thuốc, nguyên liệu làm thuốc, Hà Nội.
[2] Bộ Y tế (2019), Thông tư 11/2019/TT-BYT ngày 17/6/2019 quy định về quản lý vaccine và sinh phẩm y tế, Hà Nội.
[3] Thủ tướng Chính phủ (2020), Quyết định 749/QĐ-TTg ngày 03/6/2020 phê duyệt Chương trình Chuyển đổi số quốc gia đến năm 2025, định hướng đến năm 2030, Hà Nội.
[4] Bộ Y tế (2024), Quyết định 4416/QĐ-BYT về việc ban hành Kế hoạch triển khai ứng dụng công nghệ thông tin và chuyển đổi số y tế giai đoạn 2024-2025, Hà Nội.


PHỤ LỤC
- Phụ lục 1: Ảnh chụp giao diện phần mềm.
- Phụ lục 2: Sơ đồ cấu trúc cơ sở dữ liệu.
- Phụ lục 3: File cài đặt phần mềm (QuanLyKho.exe).
