# -*- coding: utf-8 -*-
import datetime as dt
import os
from tkinter import filedialog, messagebox

import ttkbootstrap as tb

from config import BACKUP_DIR, DB_PATH
from database import DB
from managers import BackupManager, MedicineCatalogManager, ReportManager


class BackupMixin:
    # -------- Backup --------
    def build_backup_tab(self):
        frm = self.tab_backup
        
        # Khung tạo backup
        backup_frame = tb.Labelframe(frm, text='Tạo Backup', bootstyle='secondary')
        backup_frame.pack(fill='x', padx=8, pady=8)
        
        btn_frame = tb.Frame(backup_frame)
        btn_frame.pack(fill='x', padx=8, pady=8)
        
        tb.Button(btn_frame, text='💾 Tạo Backup Ngay', bootstyle='success',
                  command=self.create_manual_backup).pack(side='left', padx=4)
        tb.Button(btn_frame, text='📤 Export Dữ Liệu', bootstyle='info',
                  command=self.export_data).pack(side='left', padx=4)
        tb.Button(btn_frame, text='📥 Import Dữ Liệu', bootstyle='warning',
                  command=self.import_data).pack(side='left', padx=4)
        
        # Khung khôi phục backup
        restore_frame = tb.Labelframe(frm, text='Khôi Phục Backup', bootstyle='secondary')
        restore_frame.pack(fill='x', padx=8, pady=8)
        
        tb.Label(restore_frame, text='Chọn backup để khôi phục:').pack(anchor='w', padx=8, pady=(8,4))
        
        # Bảng danh sách backup
        cols = ('file', 'created', 'size', 'version')
        self.tree_backups = tb.Treeview(restore_frame, columns=cols, show='headings', height=8)
        for c, w, t, anchor in [
            ('file', 300, 'Tên File', 'w'),
            ('created', 150, 'Ngày Tạo', 'center'),
            ('size', 100, 'Kích Thước', 'e'),
            ('version', 80, 'Phiên Bản', 'center')
        ]:
            self.tree_backups.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_backups, col)))
            self.tree_backups.column(c, width=w, anchor=anchor)
        self.tree_backups.tag_configure('odd', background='#f6f8fa')
        self.tree_backups.pack(fill='x', padx=8, pady=8)
        
        # Nút khôi phục
        restore_btn_frame = tb.Frame(restore_frame)
        restore_btn_frame.pack(fill='x', padx=8, pady=(0,8))
        
        tb.Button(restore_btn_frame, text='🔄 Khôi Phục Backup', bootstyle='danger',
                  command=self.restore_selected_backup).pack(side='left', padx=4)
        tb.Button(restore_btn_frame, text='🗑️ Xóa Backup', bootstyle='outline-danger',
                  command=self.delete_selected_backup).pack(side='left', padx=4)
        tb.Button(restore_btn_frame, text='🔄 Làm Mới', bootstyle='secondary',
                  command=self.refresh_backup_list).pack(side='left', padx=4)
        
        # Thông tin auto backup
        info_frame = tb.Labelframe(frm, text='Tự Động Backup', bootstyle='info')
        info_frame.pack(fill='x', padx=8, pady=8)
        
        info_text = tb.Text(info_frame, height=4, wrap='word')
        info_text.pack(fill='x', padx=8, pady=8)
        info_text.insert('1.0', 
            "• Tự động backup mỗi ngày lúc 2:00 AM\n"
            "• Giữ tối đa 30 file backup\n"
            "• Backup được lưu trong thư mục: " + BACKUP_DIR + "\n"
            "• Trước khi khôi phục, hệ thống sẽ tự động tạo backup hiện tại")
        info_text.config(state='disabled')
        
        # Load danh sách backup
        self.refresh_backup_list()

    def create_manual_backup(self):
        """Tạo backup thủ công"""
        try:
            backup_path = self.backup_manager.create_backup("manual")
            self.toast(f'Đã tạo backup: {os.path.basename(backup_path)}')
            self.refresh_backup_list()
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def export_data(self):
        """Export dữ liệu ra file JSON"""
        try:
            path = filedialog.asksaveasfilename(
                defaultextension='.json',
                filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
                initialfile=f'export_data_{dt.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            if path:
                self.backup_manager.export_data(path)
                self.toast('Đã export dữ liệu thành công')
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def import_data(self):
        """Import dữ liệu từ file JSON"""
        if hasattr(self, 'require_admin_action') and not self.require_admin_action('import dữ liệu'):
            return
        try:
            path = filedialog.askopenfilename(
                filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
            )
            if path:
                if messagebox.askyesno('Xác nhận', 
                    'Import sẽ thay thế toàn bộ dữ liệu hiện tại!\n'
                    'Hệ thống sẽ tự động tạo backup trước khi import.\n'
                    'Bạn có chắc chắn muốn tiếp tục?'):
                    
                    self.backup_manager.import_data(path)
                    self.toast('Đã import dữ liệu thành công')
                    # Refresh tất cả dữ liệu
                    self.refresh_products()
                    self.refresh_stock()
                    self.refresh_alerts()
                    self.refresh_report()
                    self.refresh_backup_list()
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def restore_selected_backup(self):
        """Khôi phục backup được chọn"""
        if hasattr(self, 'require_admin_action') and not self.require_admin_action('khôi phục backup'):
            return
        selection = self.tree_backups.selection()
        if not selection:
            messagebox.showwarning('Cảnh báo', 'Chọn backup để khôi phục')
            return
        
        item = self.tree_backups.item(selection[0])
        backup_file = item['values'][0]
        backup_path = os.path.join(BACKUP_DIR, backup_file)
        
        if messagebox.askyesno('Xác nhận', 
            f'Khôi phục backup: {backup_file}\n'
            'Hệ thống sẽ tự động tạo backup hiện tại trước khi khôi phục.\n'
            'Bạn có chắc chắn muốn tiếp tục?'):
            
            try:
                # 1. Kiểm tra trạng thái máy chủ di động và dừng nếu đang chạy
                server_was_running = False
                if self.mobile_server and self.mobile_server.is_running:
                    server_was_running = True
                    try:
                        self.mobile_server.stop()
                    except Exception as server_err:
                        print(f"Lỗi khi dừng server trước khi restore: {server_err}")
                
                # 2. Đóng kết nối cơ sở dữ liệu chính đang mở
                try:
                    self.db.conn.close()
                except Exception as conn_err:
                    print(f"Lỗi khi đóng kết nối DB: {conn_err}")
                
                # 3. Tiến hành khôi phục tệp tin cơ sở dữ liệu
                self.backup_manager.restore_backup(backup_path)
                
                # 4. Khởi tạo lại kết nối DB và gán lại cho các quản lý
                self.db = DB(DB_PATH)
                self.backup_manager = BackupManager(DB_PATH, BACKUP_DIR)
                self.report_manager = ReportManager(DB_PATH)
                self.medicine_catalog = MedicineCatalogManager(DB_PATH)
                
                # 5. Khởi động lại máy chủ di động nếu trước đó nó đang chạy
                if server_was_running:
                    from server import MobileInventoryServer
                    self.mobile_server = MobileInventoryServer(self, host="0.0.0.0", port=5000)
                    self.mobile_server.start()
                
                self.toast('Đã khôi phục backup thành công')
                
                # 6. Làm mới lại toàn bộ giao diện
                self.refresh_all_data()
                self.refresh_backup_list()
                self.update_mobile_server_ui()
                
            except Exception as e:
                # Trong trường hợp có lỗi xảy ra, đảm bảo DB được khởi tạo lại để ứng dụng không bị treo
                try:
                    self.db = DB(DB_PATH)
                    self.backup_manager = BackupManager(DB_PATH, BACKUP_DIR)
                    self.report_manager = ReportManager(DB_PATH)
                    self.medicine_catalog = MedicineCatalogManager(DB_PATH)
                except:
                    pass
                messagebox.showerror('Lỗi', str(e))

    def delete_selected_backup(self):
        """Xóa backup được chọn"""
        if hasattr(self, 'require_admin_action') and not self.require_admin_action('xóa backup'):
            return
        selection = self.tree_backups.selection()
        if not selection:
            messagebox.showwarning('Cảnh báo', 'Chọn backup để xóa')
            return
        
        item = self.tree_backups.item(selection[0])
        backup_file = item['values'][0]
        
        if messagebox.askyesno('Xác nhận', f'Xóa backup: {backup_file}?'):
            try:
                backup_path = os.path.join(BACKUP_DIR, backup_file)
                os.remove(backup_path)
                metadata_path = backup_path.replace('.db', '.json')
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                self.toast('Đã xóa backup')
                self.refresh_backup_list()
            except Exception as e:
                messagebox.showerror('Lỗi', str(e))

    def refresh_backup_list(self):
        """Làm mới danh sách backup"""
        try:
            # Clear tree
            for item in self.tree_backups.get_children():
                self.tree_backups.delete(item)
            
            backups = self.backup_manager.list_backups()
            for idx, backup in enumerate(backups):
                size_mb = backup['size'] / (1024 * 1024)
                created_str = backup['created'].strftime('%Y-%m-%d %H:%M')
                version = backup.get('version', 'N/A')
                
                self.tree_backups.insert('', 'end',
                    values=(backup['file'], created_str, f'{size_mb:.1f} MB', version),
                    tags=('odd',) if idx % 2 else ())
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể load danh sách backup: {str(e)}')


