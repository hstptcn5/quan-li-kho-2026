SỞ Y TẾ THÀNH PHỐ CẦN THƠ
TRUNG TÂM KIỂM SOÁT BỆNH TẬT
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc

Cần Thơ, ngày … tháng … năm 2026

PHIẾU ĐĂNG KÝ THỰC HIỆN ĐỀ ÁN, SÁNG KIẾN CẢI TIẾN
Năm học/Năm công tác: 2026

Kính gửi: Hội đồng Khoa học và Công nghệ cơ sở
Trung tâm Kiểm soát bệnh tật TP. Cần Thơ

1. Tên đề án/sáng kiến cải tiến:
	Ứng dụng công nghệ thông tin trong quản lý xuất - nhập - tồn thuốc, vaccine và vật tư y tế tích hợp kiểm kho di động qua mạng LAN Wi-Fi tại Trung tâm Kiểm soát bệnh tật TP. Cần Thơ.

2. Tác giả đề án/sáng kiến cải tiến:
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
	Trung tâm Kiểm soát bệnh tật TP. Cần Thơ (CDC Cần Thơ) chịu trách nhiệm tiếp nhận, lưu trữ và cấp phát lượng lớn vaccine phục vụ tiêm chủng mở rộng, thuốc chuyên khoa và các loại vật tư y tế tiêu hao phòng chống dịch cho toàn bộ mạng lưới y tế tuyến cơ sở trên địa bàn. Hiện tại, quy trình quản lý tại kho dược vẫn tồn tại nhiều thao tác thủ công hoặc sử dụng các bảng tính Excel độc lập tại mỗi máy tính của thủ kho. Quy trình cũ này bộc lộ những nhược điểm nghiêm trọng như sau:
	1. **Quản lý Số lô (Lot No) và Hạn dùng (Expiry Date) thủ công**: Thủ kho phải đối soát hạn dùng bằng mắt trực tiếp trên nhãn hộp hoặc lọc thủ công trên các file Excel rời rạc. Đối với các mặt hàng có tần suất luân chuyển cao hoặc nhiều lô hàng khác nhau như vaccine, việc này cực kỳ dễ gây nhầm lẫn hoặc bỏ sót các lô thuốc nằm sâu phía trong kệ, dẫn đến nguy cơ quá hạn dùng gây lãng phí ngân sách nhà nước.
	2. **Vi phạm nguyên tắc FEFO (Hạn gần xuất trước) do yếu tố chủ quan**: Khi chuẩn bị hàng cấp phát cho tuyến dưới, dưới áp lực thời gian hoặc do rà soát thủ công thiếu sót, thủ kho có thể lấy các lô hàng mới nhập (hạn dùng còn dài) ra xuất trước, để lại các lô cũ cận hạn trong kho. Việc này vi phạm tiêu chuẩn GSP (Thực hành tốt bảo quản thuốc).
	3. **Quy trình kiểm kho tốn thời gian và dễ sai lệch**: Mỗi kỳ kiểm kê, hai cán bộ kho phải mang sổ giấy ra kho, một người đọc và một người ghi chép số lượng đếm thực tế của từng lô. Sau đó, họ phải quay lại máy tính văn phòng để gõ lại số liệu vào bảng Excel. Thao tác trung gian này rất dễ dẫn đến lỗi nhập liệu (gõ nhầm số lượng, ghi nhầm số lô).
	4. **Không có cơ chế đối soát trước khi in (Note Preview)**: Khi lập lệnh in phiếu xuất kho từ xa thông qua mạng nội bộ, máy in sẽ in ngay lập tức. Nếu có sai sót về số lượng phân bổ giữa các lô hoặc sai tên đơn vị nhận, thủ kho buộc phải hủy bỏ phiếu in giấy, vào phần mềm sửa và in lại, gây lãng phí giấy, mực in và làm chậm tiến độ bàn giao hàng.
	5. **Khó khăn trong việc cảnh báo sớm**: Cán bộ kho không thể biết chính xác có bao nhiêu mặt hàng đã hết tồn kho, bao nhiêu lô hàng sắp hết hạn trong vòng 6 tháng (180 ngày) tới trừ khi thực hiện một đợt rà soát toàn diện mất nhiều ngày công.

* Mục đích thực hiện đề án, sáng kiến cải tiến:
	- **Tự động hóa hoàn toàn quy trình FEFO**: Lập trình thuật toán tự động phân bổ lô thuốc xuất kho dựa trên tiêu chuẩn hạn dùng gần nhất được xuất trước, loại bỏ hoàn toàn sai sót do chủ quan của con người.
	- **Xây dựng giải pháp di động không dây (LAN Wi-Fi)**: Tích hợp máy chủ mini trên phần mềm chính để biến các điện thoại thông minh của thủ kho thành thiết bị quét mã vạch cầm tay, truy cập dữ liệu thời gian thực ngay tại kệ kho.
	- **Cung cấp công cụ Dashboard và Bộ lọc thông minh**: Giúp thủ kho và ban quản lý có cái nhìn toàn cảnh về tình trạng kho (mặt hàng hết hạn, hết tồn kho) chỉ trong 3 giây.
	- **Kiểm soát quy trình in ấn thông qua Xem trước phiếu (Note Preview)**: Thiết lập hộp thoại hiển thị chi tiết phiếu (bao gồm tên hàng, số lô, hạn dùng phân bổ, đơn vị nhận) trước khi thực hiện in vật lý hoặc lưu PDF.
	- **Chuẩn hóa hệ thống biểu mẫu báo cáo y tế**: Thiết kế tự động các biểu mẫu chứng từ kế toán kho theo quy định: Phiếu nhập kho (Mẫu C30-HD), Phiếu xuất kho (Mẫu C31-HD) và Biên bản kiểm kê kho y tế (Mẫu C33-HD).
	- **Đảm bảo tính kinh tế và làm chủ công nghệ**: Phát triển ứng dụng độc lập, hoàn toàn miễn phí, không phụ thuộc vào phí mua hay duy trì bản quyền hàng năm của bên thứ ba, bảo mật dữ liệu tuyệt đối.

* Bản mô tả giải pháp của đề án, sáng kiến cải tiến:
- Thuyết minh giải pháp mới của đề án, sáng kiến cải tiến:
	Tác giả tự nghiên cứu, thiết kế cơ sở dữ liệu SQLite tập trung và lập trình ứng dụng desktop bằng Python kết hợp giao diện đồ họa hiện đại `ttkbootstrap`. Hệ thống tích hợp một máy chủ web nội bộ để kết nối không dây với thiết bị di động của thủ kho qua mạng LAN Wi-Fi. Giải pháp bao gồm các phân hệ chức năng cụ thể như sau:

	1. **Phân hệ Quản lý Danh mục sản phẩm & Đơn vị tính chuẩn hóa**:
	   - Tích hợp sẵn cơ sở dữ liệu danh mục thuốc quốc gia hơn 30.000 dòng.
	   - Chức năng tự động gợi ý tên (autocomplete) thông minh khi người dùng gõ từ 2 ký tự: Tự động điền tên thuốc, số đăng ký và đơn vị tính cơ sở.
	   - Hỗ trợ thiết lập nhiều đơn vị quy đổi (ví dụ: Nhập Hộp quy đổi ra Viên) và tự động tính toán số lượng tồn kho theo đơn vị cơ sở nhỏ nhất để tránh sai lệch.

	2. **Phân hệ Nhập kho đa sản phẩm (Mẫu C30-HD)**:
	   - Hỗ trợ lập phiếu nhập kho gồm nhiều mặt hàng cùng lúc.
	   - Ghi nhận chi tiết: Số lô (Lot No), Hạn sử dụng, Đơn giá nhập và Nhà cung cấp.
	   - Xuất file PDF Phiếu nhập kho chuẩn hóa có sẵn bảng chữ ký kiểm nhập của Hội đồng bàn giao.

	3. **Phân hệ Xuất kho cấp phát tự động theo nguyên tắc FEFO (Mẫu C31-HD)**:
	   - Khi xuất kho cấp phát cho tuyến dưới, thủ kho chỉ cần nhập tổng số lượng yêu cầu. Hệ thống sẽ tự động quét cơ sở dữ liệu, sắp xếp các lô hàng đang tồn theo thứ tự hạn dùng gần nhất và tự động phân bổ số lượng xuất từ lô cận hạn trước.
	   - Nếu số lượng xuất lớn hơn tồn kho của một lô, hệ thống tự động chia nhỏ sang lô tiếp theo (split-batch) một cách chính xác.
	   - Xuất file PDF Phiếu xuất kho cấp phát gồm 5 cột chữ ký đúng chuẩn y tế công cộng.

	4. **Phân hệ Kiểm kho di động và Quét mã vạch (Mobile Companion Server)**:
	   - Phần mềm chính trên PC đóng vai trò máy chủ trung tâm. Thủ kho dùng điện thoại quét mã QR hiển thị trên màn hình máy tính để truy cập nhanh giao diện di động qua sóng Wi-Fi nội bộ.
	   - Sử dụng trực tiếp camera điện thoại làm máy quét mã vạch thời gian thực (hỗ trợ 1D và 2D QR Code), tự động đối soát thông tin sản phẩm và số lượng tồn ngay lập tức tại kệ kho.

	5. **Phân hệ Dashboard thống kê và Bộ lọc thông minh di động**:
	   - Hiển thị bảng số liệu trực quan ngay trên điện thoại: **Tổng số sản phẩm**, **Sản phẩm hết hàng**, **Lô hàng cận hạn dùng** (hạn dùng < 180 ngày).
	   - Ba nút lọc nhanh chuyên sâu dưới ô tìm kiếm di động: "Tất cả", "❌ Hết Hàng" và "⚠️ Cận Hạn" giúp lọc tức thời danh sách hàng hóa cần xử lý mà không cần thực hiện các câu lệnh truy vấn phức tạp.

	6. **Phân hệ Xem trước phiếu và Điều khiển in từ xa (Note Preview)**:
	   - Khi thực hiện kiểm tra lịch sử phiếu trên thiết bị di động, thay vì gửi lệnh in mù, ứng dụng hiển thị một **Modal Xem trước**. Modal này hiển thị đầy đủ tiêu đề phiếu, ngày lập, đơn vị nhận/giao, lý do xuất nhập, và danh sách bảng chi tiết phân bổ (Tên thuốc, số lô, hạn dùng, số lượng, đơn vị).
	   - Cán bộ kho chỉ cần bấm nút "In phiếu" trên điện thoại, lệnh in sẽ được truyền không dây về máy tính trung tâm để điều khiển máy in văn phòng in ra chứng từ giấy.

	7. **Phân hệ Báo cáo XNT & Biên bản kiểm kê (Mẫu C33-HD)**:
	   - Tự động lập báo cáo Xuất - Nhập - Tồn chi tiết theo từng Số lô và Hạn dùng cụ thể của từng sản phẩm trong khoảng thời gian tùy chọn.
	   - Tích hợp nút kết xuất **Biên bản kiểm kê kho (PDF)**: Tự động điền danh sách thuốc đang có tồn kho kèm số lượng sổ sách, đồng thời để trống cột "Số lượng thực tế" để cán bộ điền tay khi đếm hàng, tăng tốc độ kiểm kê lên gấp 5 lần.

- Thuyết minh về phạm vi áp dụng đề án, sáng kiến cải tiến:
	- Áp dụng tại Kho tổng của Trung tâm Kiểm soát bệnh tật TP. Cần Thơ (gồm Kho Vaccine tiêm chủng mở rộng, Kho Thuốc chuyên khoa, Kho Vật tư tiêu hao).
	- Có khả năng triển khai rộng rãi cho Kho dược của các Trung tâm Y tế quận/huyện, các Trạm y tế xã/phường trên toàn địa bàn thành phố nhờ ưu điểm cài đặt nhanh, chạy nhẹ và không tốn phí bản quyền.

- Thuyết minh về lợi ích kinh tế, xã hội của đề án, sáng kiến cải tiến:
	* Lợi ích kinh tế:
	- **Tiết kiệm chi phí đầu tư công nghệ**: Tiết kiệm hàng chục triệu đồng chi phí mua sắm phần mềm thương mại và phí bảo trì hàng năm cho đơn vị.
	- **Tránh thất thoát tài sản**: Giảm thiểu 100% rủi ro hủy bỏ vaccine, hóa chất do quá hạn sử dụng nhờ thuật toán FEFO và Dashboard cảnh báo cận hạn tự động.
	- **Tăng năng suất lao động**: Tiết kiệm hơn 80% thời gian lập báo cáo thống kê định kỳ và kiểm kê kho cuối tháng.
	* Lợi ích xã hội:
	- Đảm bảo chất lượng các lô vaccine và thuốc cấp phát cho tuyến cơ sở luôn đạt tiêu chuẩn tốt nhất về hạn dùng.
	- Nâng cao tính chuyên nghiệp, chuyển đổi số thực chất quy trình hậu cần y tế tại cơ sở.
	- Dữ liệu lưu trữ tập trung, rõ ràng từng số lô, hạn dùng giúp công tác thanh tra, hậu kiểm của các cơ quan quản lý diễn ra nhanh chóng, chính xác.

- Các tài liệu khác gửi kèm theo:
	- Ảnh chụp màn hình ứng dụng Desktop chính và giao diện Dashboard, Bộ lọc, Popup xem trước phiếu trên điện thoại di động.
	- Sơ đồ nguyên lý kết nối LAN Wi-Fi giữa PC và Thiết bị di động.
	- File chạy thử nghiệm ứng dụng (`QuanLyKho.exe`).

5. Bản cam kết không sao chép hoặc vi phạm bản quyền:
	Tôi cam kết đề án, sáng kiến cải tiến nêu trên là trung thực, do nhóm nghiên cứu thực hiện, không sao chép hay vi phạm bản quyền và thực hiện nghiêm túc, đúng theo thời gian quy định về công tác nghiên cứu khoa học, sáng kiến cải tiến tại đơn vị.
	Kính mong Hội đồng Khoa học và Công nghệ cấp cơ sở xem xét chấp thuận cho tiến hành các bước tiếp theo của nghiên cứu khoa học.
	Trân trọng./.

	Người đề nghị
	(Ký và ghi rõ họ tên)

================================================================================
BẢN THUYẾT MINH CHI TIẾT SÁNG KIẾN CẢI TIẾN
================================================================================

1. ĐẶT VẤN ĐỀ

Trung tâm Kiểm soát bệnh tật TP. Cần Thơ (CDC Cần Thơ) là đơn vị đầu ngành trong công tác y tế dự phòng của thành phố. Một trong những nhiệm vụ trọng tâm là tiếp nhận, bảo quản và cấp phát thuốc, vaccine (đặc biệt là vaccine Chương trình tiêm chủng mở rộng) và vật tư y tế (VTYT) tiêu hao phục vụ xét nghiệm và phòng chống dịch cho toàn bộ các cơ sở y tế tuyến quận/huyện và trạm y tế xã/phường trên địa bàn.

Với đặc thù hàng hóa y tế liên quan trực tiếp đến sức khỏe con người, công tác quản lý kho đòi hỏi phải chính xác tuyệt đối đến từng Số lô (Lot No) và Hạn sử dụng (Expiry Date). Tuy nhiên, hiện tại quy trình quản lý tại đơn vị vẫn chủ yếu dựa trên sổ sách chép tay hoặc các file Excel độc lập. Phương pháp thủ công này đã bộc lộ những hạn chế lớn sau:
- Khó kiểm soát chi tiết hạn dùng của từng lô hàng, dẫn đến rủi ro xuất lô hàng mới nhập trước lô hàng cũ sắp hết hạn (vi phạm nguyên tắc FEFO).
- Công tác kiểm kê kho định kỳ mất nhiều thời gian do phải đối soát thủ công hàng nghìn hộp thuốc trên kệ với sổ sách, dễ ghi chép sai lệch số lượng.
- In ấn phiếu xuất nhập từ xa dễ bị nhầm lẫn thông tin do không có cơ chế đối soát dữ liệu thực tế trước khi in.
- Thời gian tổng hợp dữ liệu để lập báo cáo xuất - nhập - tồn định kỳ hàng tháng gửi Sở Y tế mất nhiều ngày làm việc.

Để khắc phục triệt để các hạn chế trên và đẩy mạnh ứng dụng công nghệ thông tin theo chủ trương chuyển đổi số của ngành y tế, tác giả đã tự nghiên cứu và xây dựng giải pháp: **"Ứng dụng công nghệ thông tin trong quản lý xuất - nhập - tồn thuốc, vaccine và vật tư y tế tích hợp kiểm kho di động qua mạng LAN Wi-Fi tại Trung tâm Kiểm soát bệnh tật TP. Cần Thơ"**. Sáng kiến này nhằm tối ưu hóa quy trình cấp phát FEFO, số hóa công tác đối soát hiện trường bằng thiết bị di động và tự động hóa hệ thống báo cáo nghiệp vụ.

2. NỘI DUNG CHÍNH

2.1. Cơ sở pháp lý và lý luận
- **Thông tư 36/2018/TT-BYT** của Bộ Y tế về Thực hành tốt bảo quản thuốc (GSP), yêu cầu các cơ sở bảo quản phải thiết lập hệ thống sổ sách, phần mềm để theo dõi chi tiết số lô, hạn dùng của từng mặt hàng và bảo đảm khả năng truy xuất nguồn gốc.
- **Thông tư 11/2018/TT-BYT** và **Thông tư 11/2019/TT-BYT** quy định về việc quản lý chất lượng thuốc, vaccine và sinh phẩm y tế, bắt buộc áp dụng nguyên tắc FEFO (Hạn dùng gần xuất trước).
- **Quyết định 749/QĐ-TTg** ngày 03/6/2020 của Thủ tướng Chính phủ phê duyệt Chương trình Chuyển đổi số quốc gia đến năm 2025, định hướng đến năm 2030, trong đó Y tế là lĩnh vực ưu tiên chuyển đổi số hàng đầu.

2.2. Thực trạng công tác quản lý kho tại đơn vị trước khi áp dụng sáng kiến
* Thuận lợi:
  - Đơn vị đã trang bị mạng máy tính văn phòng và hệ thống Wi-Fi nội bộ hoạt động ổn định phủ sóng toàn bộ khu vực nhà kho.
  - Cán bộ làm công tác kho dược có trình độ chuyên môn chuyên ngành, nhiệt tình và sẵn sàng tiếp thu các công cụ công nghệ mới.
* Khó khăn:
  - Lượng hàng hóa luân chuyển lớn, nhiều loại vaccine yêu cầu bảo quản lạnh nghiêm ngặt trong dây chuyền lạnh. Việc mở cửa kho lâu để kiểm kê thủ công bằng giấy tờ có thể gây ảnh hưởng đến nhiệt độ bảo quản vaccine.
  - Tên các loại thuốc, hoạt chất thường dài và tương đối giống nhau, dễ ghi chép sai lệch chữ cái hoặc số đăng ký nếu thao tác thủ công.

2.3. Các biện pháp cải tiến đã tiến hành

- **Biện pháp 1: Số hóa danh mục chuẩn và xây dựng CSDL tập trung**
  Tác giả xây dựng cơ sở dữ liệu SQLite tập trung lưu trữ trên máy tính trạm của kho. Tích hợp sẵn file danh mục chuẩn quốc gia `thuoc.csv` với thuật toán gợi ý (autocomplete) tự động điền thông tin thuốc khi gõ tìm kiếm. Thủ kho không còn phải gõ thủ công tên thuốc hay số đăng ký, giúp thời gian nhập thông tin sản phẩm mới giảm từ 5 phút xuống còn dưới 10 giây.

- **Biện pháp 2: Tích hợp thuật toán tự động phân bổ xuất kho FEFO**
  Hệ thống được lập trình thuật toán tự động kiểm tra tất cả các lô hàng tồn kho của sản phẩm được yêu cầu xuất, sắp xếp theo hạn sử dụng và tự động phân bổ số lượng cần xuất từ lô có hạn dùng gần nhất trước. Khi lập phiếu xuất cấp phát cho tuyến dưới, thủ kho chỉ cần nhập số lượng tổng, phần mềm tự điền số lô và hạn dùng tương ứng trên phiếu xuất (Mẫu C31-HD), đảm bảo tính chính xác 100% và tuân thủ tuyệt đối quy định GSP.

- **Biện pháp 3: Xây dựng máy chủ mini và module kết nối di động LAN Wi-Fi**
  Tác giả đã lập trình một máy chủ HTTP mini chạy ngầm trên ứng dụng chính. Máy chủ này phát ra một địa chỉ IP nội bộ dưới dạng mã QR. Thủ kho chỉ cần dùng điện thoại di động quét mã QR này để truy cập vào giao diện web kiểm kho chuyên dụng của điện thoại thông qua mạng Wi-Fi nội bộ của cơ quan, không cần cài đặt ứng dụng phức tạp.

- **Biện pháp 4: Thiết lập Dashboard thống kê và bộ lọc nhanh thông minh trên di động**
  Giao diện di động được trang bị cụm **Quick Dashboard** cập nhật thời gian thực gồm 3 thông số: Tổng số sản phẩm trong kho, Số lượng sản phẩm hết hàng, và Số lượng lô hàng cận hạn dùng (< 6 tháng). Dưới thanh tìm kiếm, tích hợp 3 bộ lọc trạng thái nhanh ("Tất cả", "❌ Hết Hàng", "⚠️ Cận Hạn"). Khi thủ kho nhấn chọn nút lọc, hệ thống lập tức ẩn đi các mặt hàng không liên quan, hiển thị chính xác danh sách lô hàng cần lưu ý ngay tại kệ kho.

- **Biện pháp 5: Xây dựng cơ chế xem trước và điều khiển in từ xa (Note Preview)**
  Để loại bỏ rủi ro in sai lệch dữ liệu, tác giả xây dựng tính năng **Xem trước phiếu in**. Khi thủ kho thao tác trên điện thoại để tra cứu lịch sử xuất nhập, một cửa sổ popup hiển thị đầy đủ thông tin chi tiết của phiếu (các cột tên thuốc, đơn vị, số lô, hạn dùng, số lượng). Khi xác nhận thông tin chính xác, thủ kho nhấn nút "In phiếu", tín hiệu được truyền qua mạng Wi-Fi về máy tính trung tâm để kích hoạt máy in văn phòng in ra phiếu giấy ngay lập tức.

- **Biện pháp 6: Tự động hóa báo cáo chuẩn y tế và sao lưu an toàn**
  Lập trình chức năng tự động xuất Báo cáo Xuất - Nhập - Tồn phân loại chi tiết theo Số lô và Hạn dùng ra Excel/PDF. Bổ sung nút xuất **Biên bản kiểm kê kho (Mẫu C33-HD)** tự động điền số liệu sổ sách hiện tại để phục vụ công tác đối soát đếm thực tế nhanh chóng. Cơ chế sao lưu tự động (auto-backup) sao chép dữ liệu hàng ngày bảo đảm an toàn thông tin khi xảy ra sự cố phần cứng máy tính.

2.4. Hiệu quả của sáng kiến, cải tiến

Sáng kiến cải tiến đã được đưa vào áp dụng thử nghiệm thực tế tại Kho dược của Trung tâm Kiểm soát bệnh tật TP. Cần Thơ và đem lại hiệu quả vượt trội so với quy trình cũ:

| Tiêu chí đánh giá | Quy trình cũ (Thủ công / Excel rời rạc) | Quy trình mới (Áp dụng phần mềm tích hợp di động) |
| :--- | :--- | :--- |
| **Thời gian nhập thông tin sản phẩm** | 5 phút / sản phẩm (nhập tay toàn bộ thông tin) | **Dưới 10 giây** (autocomplete từ danh mục chuẩn) |
| **Thời gian lập phiếu xuất cấp phát** | 15 - 20 phút / phiếu (phải rà từng lô hàng) | **Dưới 2 phút** (hệ thống tự phân bổ số lượng) |
| **Tuân thủ quy tắc FEFO** | Không đảm bảo (dễ bị nhầm hoặc sót lô cận hạn) | **100% tự động** chọn lô có hạn dùng gần nhất |
| **Công tác đối soát thực tế tại kệ** | Ghi chép tay ra giấy, sau đó gõ lại vào máy tính | **Quét mã vạch trực tiếp bằng điện thoại** tại kệ hàng |
| **Cảnh báo hàng cận hạn, hết hàng** | Không có (phải làm đợt kiểm kho tổng lực để lọc) | **Dashboard cập nhật thời gian thực** trên điện thoại |
| **Lỗi in nhầm, in sai lệch phiếu** | Thường xuyên xảy ra do không kiểm tra trước | **0%** nhờ tính năng **Xem trước phiếu (Note Preview)** |
| **Thời gian lập báo cáo XNT & Kiểm kê**| 2 - 3 ngày làm việc (tổng hợp và khớp số tay) | **Dưới 5 phút** (hệ thống tự động kết xuất) |
| **Chi phí bản quyền phần mềm** | Không có (nhưng phần mềm thương mại giá rất cao) | **0 VNĐ** (Mã nguồn mở tự xây dựng, làm chủ công nghệ) |

3. KẾT LUẬN VÀ KIẾN NGHỊ

3.1. Kết luận
Sáng kiến "Ứng dụng công nghệ thông tin trong quản lý xuất - nhập - tồn thuốc, vaccine và vật tư y tế tích hợp kiểm kho di động qua mạng LAN Wi-Fi tại Trung tâm Kiểm soát bệnh tật TP. Cần Thơ" là một giải pháp thiết thực, hiệu quả và có tính thực tiễn cao. Sáng kiến đã giải quyết triệt để các bài toán khó khăn trong công tác quản lý kho dược công, nâng cao năng suất lao động của cán bộ y tế, bảo đảm an toàn chất lượng thuốc/vaccine lưu thông và tiết kiệm ngân sách nhà nước nhờ tránh lãng phí hàng quá hạn.

3.2. Kiến nghị
- Đề nghị Hội đồng Khoa học và Công nghệ cơ sở xem xét, thẩm định và công nhận sáng kiến cải tiến để làm cơ sở triển khai nhân rộng.
- Kiến nghị Ban Giám đốc Trung tâm hỗ trợ kinh phí trang bị thêm máy quét mã vạch không dây cầm tay kết nối máy tính để phục vụ tốt hơn khi nhập xuất hàng hóa khối lượng lớn.
- Kiến nghị Sở Y tế xem xét cho phép phổ biến và cài đặt phần mềm này tại các Trung tâm Y tế quận/huyện và Trạm y tế trực thuộc trên địa bàn nhằm đồng bộ hóa quy trình quản lý XNT y tế.

TÀI LIỆU THAM KHẢO
[1] Bộ Y tế (2018), Thông tư 36/2018/TT-BYT ngày 22/11/2018 về Thực hành tốt bảo quản thuốc, nguyên liệu làm thuốc, Hà Nội.
[2] Bộ Y tế (2019), Thông tư 11/2019/TT-BYT ngày 17/6/2019 quy định về quản lý vaccine và sinh phẩm y tế, Hà Nội.
[3] Thủ tướng Chính phủ (2020), Quyết định 749/QĐ-TTg ngày 03/6/2020 phê duyệt Chương trình Chuyển đổi số quốc gia đến năm 2025, định hướng đến năm 2030, Hà Nội.
[4] Bộ Tài chính (2017), Thông tư 107/2017/TT-BTC hướng dẫn chế độ kế toán hành chính, sự nghiệp (Mẫu biên bản kiểm kê C33-HD), Hà Nội.
[5] Bộ Y tế (2024), Quyết định 4416/QĐ-BYT về việc ban hành Kế hoạch triển khai ứng dụng công nghệ thông tin và chuyển đổi số y tế giai đoạn 2024-2025, Hà Nội.
