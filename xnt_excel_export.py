# -*- coding: utf-8 -*-
"""Printable operational Excel template for the XNT report.

This module intentionally changes only workbook presentation. XNT quantities
continue to come from DB.xnt_report(), which remains the single calculation
source for opening, inbound, outbound and closing stock.
"""

from __future__ import annotations

import os
from datetime import datetime
from tkinter import filedialog, messagebox

from date_utils import format_date_display


class XntExcelExportMixin:
    """Export the XNT dataset as a print-ready operational workbook."""

    XNT_SHEET_TITLE = "Báo cáo XNT"

    @staticmethod
    def _display_date(value) -> str:
        if value in (None, ""):
            return ""
        try:
            return format_date_display(str(value))
        except Exception:
            return str(value)

    @classmethod
    def _build_xnt_workbook(cls, rows, start_date: str, end_date: str, fund_source: str):
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.page import PageMargins

        wb = Workbook()
        ws = wb.active
        ws.title = cls.XNT_SHEET_TITLE
        ws.sheet_view.showGridLines = False

        last_col = 11  # A:K
        end_col = get_column_letter(last_col)

        # ---- Report identity ----
        ws.merge_cells(f"A1:{end_col}1")
        ws["A1"] = "BÁO CÁO XUẤT - NHẬP - TỒN"
        ws["A1"].font = Font(name="Arial", size=16, bold=True, color="17365D")
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 27

        ws.merge_cells(f"A2:{end_col}2")
        ws["A2"] = f"Từ ngày {cls._display_date(start_date)} đến ngày {cls._display_date(end_date)}"
        ws["A2"].font = Font(name="Arial", size=11, italic=True)
        ws["A2"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A3:F3")
        ws["A3"] = "Đơn vị: ..............................................................."
        ws.merge_cells("G3:K3")
        ws["G3"] = "Kho: Thuốc, vaccine và vật tư y tế"

        ws.merge_cells("A4:F4")
        ws["A4"] = f"Nguồn kinh phí: {fund_source or 'Tất cả'}"
        ws.merge_cells("G4:K4")
        ws["G4"] = "Đơn vị tính số lượng: Đơn vị cơ sở"

        for cell in (ws["A3"], ws["G3"], ws["A4"], ws["G4"]):
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(vertical="center")

        # ---- Two-level formal header ----
        header_top = 6
        header_bottom = 7
        single_headers = {
            "A": "STT",
            "B": "Mã SP",
            "C": "Tên hàng hóa",
            "D": "ĐVT",
            "E": "Số lô",
            "F": "Hạn sử dụng",
            "G": "Nguồn kinh phí",
        }
        for col, label in single_headers.items():
            ws.merge_cells(f"{col}{header_top}:{col}{header_bottom}")
            ws[f"{col}{header_top}"] = label

        ws.merge_cells(f"H{header_top}:K{header_top}")
        ws[f"H{header_top}"] = "SỐ LƯỢNG"
        ws[f"H{header_bottom}"] = "Tồn đầu"
        ws[f"I{header_bottom}"] = "Nhập trong kỳ"
        ws[f"J{header_bottom}"] = "Xuất trong kỳ"
        ws[f"K{header_bottom}"] = "Tồn cuối"

        thin = Side(style="thin", color="7F8C8D")
        medium = Side(style="medium", color="34495E")
        table_border = Border(left=thin, right=thin, top=thin, bottom=thin)
        header_fill = PatternFill("solid", fgColor="D9EAF7")
        total_fill = PatternFill("solid", fgColor="E7E6E6")

        for row in ws.iter_rows(min_row=header_top, max_row=header_bottom, min_col=1, max_col=last_col):
            for cell in row:
                cell.font = Font(name="Arial", size=9, bold=True, color="17202A")
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = table_border
        ws.row_dimensions[header_top].height = 24
        ws.row_dimensions[header_bottom].height = 30

        # ---- Data rows ----
        first_data_row = 8
        current_row = first_data_row
        for index, row in enumerate(rows, start=1):
            values = [
                index,
                row["productId"],
                row["productName"],
                row["unit"] or "",
                row["lotNo"] or "",
                cls._display_date(row["expiryDate"]),
                row["fundSource"] or "",
                float(row["opening"] or 0),
                float(row["inbound"] or 0),
                float(row["outbound"] or 0),
                float(row["closing"] or 0),
            ]
            for col_index, value in enumerate(values, start=1):
                cell = ws.cell(row=current_row, column=col_index, value=value)
                cell.font = Font(name="Arial", size=9)
                cell.border = table_border
                cell.alignment = Alignment(
                    horizontal="left" if col_index in (3, 7) else "center",
                    vertical="center",
                    wrap_text=col_index in (3, 7),
                )
                if col_index >= 8:
                    cell.number_format = '#,##0.####'
            ws.row_dimensions[current_row].height = 26
            current_row += 1

        last_data_row = current_row - 1
        total_row = current_row
        ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=7)
        total_label = ws.cell(total_row, 1, "TỔNG CỘNG")
        total_label.font = Font(name="Arial", size=10, bold=True)
        total_label.alignment = Alignment(horizontal="center", vertical="center")
        total_label.fill = total_fill

        for col in range(1, last_col + 1):
            cell = ws.cell(total_row, col)
            cell.border = Border(left=thin, right=thin, top=medium, bottom=medium)
            cell.fill = total_fill

        for col in range(8, 12):
            cell = ws.cell(total_row, col)
            letter = get_column_letter(col)
            if last_data_row >= first_data_row:
                cell.value = f"=SUM({letter}{first_data_row}:{letter}{last_data_row})"
            else:
                cell.value = 0
            cell.font = Font(name="Arial", size=10, bold=True)
            cell.number_format = '#,##0.####'
            cell.alignment = Alignment(horizontal="center")
        ws.row_dimensions[total_row].height = 24

        # ---- Report note and signatures ----
        note_row = total_row + 2
        ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=11)
        ws.cell(note_row, 1).value = (
            "Ghi chú: Số liệu được tổng hợp theo đơn vị tính cơ sở, chi tiết theo lô, "
            "hạn sử dụng và nguồn kinh phí."
        )
        ws.cell(note_row, 1).font = Font(name="Arial", size=9, italic=True, color="595959")
        ws.cell(note_row, 1).alignment = Alignment(wrap_text=True)
        ws.row_dimensions[note_row].height = 28

        date_row = note_row + 2
        ws.merge_cells(start_row=date_row, start_column=8, end_row=date_row, end_column=11)
        ws.cell(date_row, 8).value = "Ngày ..... tháng ..... năm ........"
        ws.cell(date_row, 8).alignment = Alignment(horizontal="center")
        ws.cell(date_row, 8).font = Font(name="Arial", size=10, italic=True)

        signature_row = date_row + 1
        signatures = (
            (1, 3, "NGƯỜI LẬP BIỂU"),
            (4, 7, "THỦ KHO"),
            (8, 11, "PHỤ TRÁCH ĐƠN VỊ"),
        )
        for start_col, end_col_idx, label in signatures:
            ws.merge_cells(start_row=signature_row, start_column=start_col, end_row=signature_row, end_column=end_col_idx)
            cell = ws.cell(signature_row, start_col, label)
            cell.font = Font(name="Arial", size=10, bold=True)
            cell.alignment = Alignment(horizontal="center")
            ws.merge_cells(start_row=signature_row + 1, start_column=start_col, end_row=signature_row + 1, end_column=end_col_idx)
            hint = ws.cell(signature_row + 1, start_col, "(Ký, ghi rõ họ tên)")
            hint.font = Font(name="Arial", size=9, italic=True)
            hint.alignment = Alignment(horizontal="center")
        ws.row_dimensions[signature_row].height = 22
        ws.row_dimensions[signature_row + 1].height = 18
        signature_end_row = signature_row + 5

        # ---- Page layout ----
        widths = {
            "A": 6, "B": 10, "C": 34, "D": 10, "E": 14, "F": 14,
            "G": 22, "H": 13, "I": 13, "J": 13, "K": 13,
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width

        ws.freeze_panes = "A8"
        ws.print_title_rows = f"{header_top}:{header_bottom}"
        ws.print_area = f"A1:K{signature_end_row}"
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_margins = PageMargins(left=0.25, right=0.25, top=0.45, bottom=0.45, header=0.2, footer=0.2)
        ws.oddFooter.center.text = "Trang &P / &N"
        ws.oddFooter.center.size = 9
        ws.oddFooter.center.font = "Arial"
        ws.oddFooter.right.text = "Báo cáo XNT"
        ws.oddFooter.right.size = 8
        ws.oddFooter.right.font = "Arial"

        # Workbook metadata is intentionally operational, not a legal-form claim.
        wb.properties.title = "Báo cáo Xuất - Nhập - Tồn"
        wb.properties.subject = "Báo cáo nghiệp vụ kho"
        wb.properties.creator = "QUẢN LÝ KHO 2026"
        wb.properties.created = datetime.now()

        return wb

    def export_report_excel(self):
        start_s, end_s = self._date_range_from_entries(self.de_from, self.de_to) if hasattr(self, "de_from") and hasattr(self, "de_to") else ("", "")
        if not start_s or not end_s:
            messagebox.showwarning("Thiếu ngày", "Chọn đủ Từ ngày và Đến ngày")
            return

        fund_source = self.cmb_report_fund.get().strip() if hasattr(self, "cmb_report_fund") else "Tất cả"
        rows = self.db.xnt_report(start_s, end_s, fund_source)
        if not rows:
            messagebox.showwarning("Không có dữ liệu", "Không có dữ liệu XNT trong khoảng thời gian đã chọn.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile=f"Bao_cao_XNT_{start_s}_{end_s}.xlsx",
        )
        if not path:
            return

        try:
            wb = self._build_xnt_workbook(rows, start_s, end_s, fund_source)
            wb.save(path)
            self.toast("Đã lưu báo cáo X–N–T Excel theo mẫu")
            try:
                os.startfile(path)
            except Exception:
                pass
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo Excel: {exc}")
