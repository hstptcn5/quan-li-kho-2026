import os

def main():
    file_path = "nhathuoc2.py"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, "rb") as f:
        data = f.read()

    # Normalize line endings to simplify index search
    data_norm = data.replace(b"\r\n", b"\n")

    start_marker = b"story.append(sig_table)"
    end_marker = b"cols = ('productId', 'productName'"

    start_idx = data_norm.find(start_marker)
    if start_idx == -1:
        print("Error: Could not find 'story.append(sig_table)' in nhathuoc2.py.")
        return

    # Find the end of the line containing the start_marker
    start_line_end = data_norm.find(b"\n", start_idx)
    if start_line_end == -1:
        start_line_end = start_idx + len(start_marker)

    end_idx = data_norm.find(end_marker, start_line_end)
    if end_idx == -1:
        print("Error: Could not find the columns declaration block.")
        return

    # We want to replace everything from start_line_end to end_idx
    replacement_str = """\n            story.append(Spacer(1, 60))
            
            doc.build(story)
            os.startfile(pdf_path)
            self.toast("Đã in phiếu nhập ra PDF và mở file thành công")
        except Exception as e:
            messagebox.showerror("Lỗi in PDF", f"Không thể xuất file PDF: {str(e)}")

    # -------- Xuất kho / Cấp phát (Dispatch) --------
    def build_dispatch_tab(self):
        frm = self.tab_dispatch

        # Header với title đẹp
        header_frame = tb.Frame(frm)
        header_frame.pack(fill='x', padx=8, pady=(8,4))
        
        title_label = tb.Label(header_frame, text='📤 Xuất kho / Cấp phát', 
                              font=('Segoe UI', 14, 'bold'), bootstyle='warning')
        title_label.pack(anchor='w')
        
        subtitle_label = tb.Label(header_frame, text='Cấp phát thuốc, vaccine và vật tư y tế cho các đơn vị tuyến dưới theo nguyên tắc FEFO', 
                                 font=('Segoe UI', 9), bootstyle='secondary')
        subtitle_label.pack(anchor='w')

        # --- Khung thông tin phiếu xuất
        info_note = tb.Labelframe(frm, text='📝 Thông tin phiếu xuất kho', bootstyle='light')
        info_note.pack(fill='x', padx=8, pady=8)

        # Đơn vị nhận
        tb.Label(info_note, text='Đơn vị nhận:').grid(row=0, column=0, padx=6, pady=6, sticky='w')
        self.cmb_receiving_unit = tb.Combobox(info_note, width=25)
        self.cmb_receiving_unit.grid(row=0, column=1, padx=6, pady=6, sticky='w')
        self.refresh_receiving_units_combo()

        # Ngày xuất
        tb.Label(info_note, text='Ngày xuất:').grid(row=0, column=2, padx=6, pady=6, sticky='w')
        self.ent_dispatch_date = DateEntry(
            info_note,
            dateformat="%Y-%m-%d",
            firstweekday=0,
            bootstyle='info',
            width=12
        )
        self.ent_dispatch_date.grid(row=0, column=3, padx=6, pady=6, sticky='w')

        # Lý do xuất
        tb.Label(info_note, text='Lý do xuất:').grid(row=0, column=4, padx=6, pady=6, sticky='w')
        self.cmb_reason = tb.Combobox(info_note, values=['Cấp phát', 'Hủy kho', 'Chuyển kho', 'Khác'], width=15, state='readonly')
        self.cmb_reason.set('Cấp phát')
        self.cmb_reason.grid(row=0, column=5, padx=6, pady=6, sticky='w')

        # Ghi chú (đặt xuống hàng 1 để rộng rãi hơn)
        tb.Label(info_note, text='Ghi chú:').grid(row=1, column=0, padx=6, pady=6, sticky='w')
        self.ent_dispatch_note = tb.Entry(info_note)
        self.ent_dispatch_note.grid(row=1, column=1, columnspan=5, padx=6, pady=6, sticky='ew')
        info_note.columnconfigure(1, weight=1)

        # --- Hàng điều khiển chọn sản phẩm
        top = tb.Frame(frm)
        top.pack(fill='x', padx=8, pady=4)

        tb.Label(top, text='Barcode:').pack(side='left')
        self.ent_barcode = tb.Entry(top, width=18)
        self.ent_barcode.pack(side='left', padx=6)
        self.ent_barcode.bind('<Return>', lambda e: self.scan_and_add_dispatch())
        self.ent_barcode.bind('<KP_Enter>', lambda e: self.scan_and_add_dispatch())
        
        # Nút quét barcode bằng camera
        if BARCODE_AVAILABLE:
            tb.Button(top, text='📷 Quét', command=self.open_barcode_scanner_dispatch, 
                     bootstyle='info', width=8).pack(side='left', padx=6)
        else:
            tb.Button(top, text='📷 Quét', command=self.show_barcode_install_info, 
                     bootstyle='secondary', width=8).pack(side='left', padx=6)

        tb.Label(top, text='Tìm tên:').pack(side='left')
        self.search_pos = tb.Entry(top, width=20)
        self.search_pos.pack(side='left', padx=6)

        tb.Label(top, text='Chọn:').pack(side='left')
        self.cmb_prod_pos = tb.Combobox(top, state='readonly', width=30)
        self.cmb_prod_pos.pack(side='left', padx=6)

        tb.Label(top, text='Chọn lô:').pack(side='left')
        self.cmb_lot_pos = tb.Combobox(top, state='readonly', width=18)
        self.cmb_lot_pos.pack(side='left', padx=6)

        tb.Label(top, text='SL xuất:').pack(side='left')
        self.ent_qty_pos = tb.Entry(top, width=8)
        self.ent_qty_pos.insert(0, '1')
        self.ent_qty_pos.pack(side='left', padx=6)
        self._numberize(self.ent_qty_pos)

        # --- Bind sự kiện
        self.search_pos.bind('<KeyRelease>', lambda e: self.filter_product_list_dispatch())
        self.search_pos.bind('<Down>', lambda e: (self.cmb_prod_pos.focus_set(),
                                                   self.cmb_prod_pos.event_generate('<Alt-Down>')))

        self.cmb_prod_pos.bind('<<ComboboxSelected>>', lambda e: self.update_dispatch_unit_label())
        self.cmb_prod_pos.bind('<Escape>', lambda e: self.search_pos.focus_set())
        self.cmb_prod_pos.bind('<Return>', lambda e: (self.cmb_lot_pos.focus_set(),
                                                      self.cmb_lot_pos.event_generate('<Alt-Down>')))
        self.cmb_lot_pos.bind('<Return>', lambda e: self.ent_qty_pos.focus_set())

        # --- Nút tác vụ
        btns = tb.Frame(frm)
        btns.pack(fill='x', padx=8, pady=8)
        tb.Button(btns, text='+ Thêm vào danh sách xuất', bootstyle='secondary', command=self.add_to_dispatch_cart).pack(side='left', padx=4)
        tb.Button(btns, text='Xóa dòng', bootstyle='warning', command=self.remove_selected_dispatch_item).pack(side='left', padx=4)
        tb.Button(btns, text='Xóa danh sách', bootstyle='danger', command=self.clear_dispatch_cart).pack(side='left', padx=4)
        tb.Button(btns, text='Xác nhận xuất kho', bootstyle='success', command=self.confirm_dispatch).pack(side='left', padx=8)
        tb.Button(btns, text='In phiếu xuất kho', bootstyle='info', command=self.print_dispatch_note).pack(side='left', padx=8)

        # --- Info tổng quan đơn vị
        info = tb.Frame(frm)
        info.pack(fill='x', padx=8, pady=(0, 4))
        self.lbl_unit_pos = tb.Label(info, text='Đơn vị tính: -', font=('Segoe UI', 10))
        self.lbl_unit_pos.pack(side='left', padx=(8, 12))

        # Báº£ng giÃ³ hÃ ng xuáº¥t
        """

    replacement_bytes = replacement_str.encode("utf-8")
    final_data_norm = data_norm[:start_line_end] + replacement_bytes + data_norm[end_idx:]

    # Add UTF-8 coding declaration header if missing
    if b"coding:" not in final_data_norm[:200]:
        final_data_norm = b"# -*- coding: utf-8 -*-\n" + final_data_norm

    # Convert back to Windows line endings
    final_data = final_data_norm.replace(b"\n", b"\r\n")

    with open(file_path, "wb") as f:
        f.write(final_data)

    print("Successfully rebuilt build_dispatch_tab and print_purchase_note block as clean UTF-8!")

if __name__ == "__main__":
    main()
