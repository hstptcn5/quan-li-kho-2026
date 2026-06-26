#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
License Generator Tool - Nhà thuốc Management System
Tạo license cho khách hàng sử dụng phần mềm
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import base64
import datetime
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import os

class LicenseGenerator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔐 License Generator - Nhà thuốc v1.0.0")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        title_label = tk.Label(header_frame, text="🔐 License Generator", 
                              font=('Segoe UI', 16, 'bold'), fg='#2c3e50')
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="Tạo license cho khách hàng sử dụng phần mềm Nhà thuốc", 
                                 font=('Segoe UI', 10), fg='#7f8c8d')
        subtitle_label.pack()
        
        # Main form
        form_frame = ttk.LabelFrame(self.root, text="📝 Thông tin License", padding=20)
        form_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Customer name
        ttk.Label(form_frame, text="Tên khách hàng:").grid(row=0, column=0, sticky='w', pady=5)
        self.customer_entry = ttk.Entry(form_frame, width=50, font=('Segoe UI', 10))
        self.customer_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Hardware fingerprint
        ttk.Label(form_frame, text="Hardware Fingerprint:").grid(row=1, column=0, sticky='w', pady=5)
        fingerprint_frame = ttk.Frame(form_frame)
        fingerprint_frame.grid(row=1, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        self.fingerprint_entry = ttk.Entry(fingerprint_frame, width=40, font=('Consolas', 10))
        self.fingerprint_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(fingerprint_frame, text="📋 Paste", 
                  command=self.paste_fingerprint).pack(side='right', padx=(5, 0))
        
        # Expiry date
        ttk.Label(form_frame, text="Ngày hết hạn:").grid(row=2, column=0, sticky='w', pady=5)
        expiry_frame = ttk.Frame(form_frame)
        expiry_frame.grid(row=2, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        self.expiry_entry = ttk.Entry(expiry_frame, width=20, font=('Segoe UI', 10))
        self.expiry_entry.pack(side='left')
        
        # Set default expiry (1 year from now)
        default_expiry = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d')
        self.expiry_entry.insert(0, default_expiry)
        
        ttk.Button(expiry_frame, text="📅 Vĩnh viễn", 
                  command=self.set_permanent).pack(side='right', padx=(5, 0))
        
        # Features
        ttk.Label(form_frame, text="Tính năng:").grid(row=3, column=0, sticky='w', pady=5)
        features_frame = ttk.Frame(form_frame)
        features_frame.grid(row=3, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        self.features_var = tk.StringVar(value="full")
        ttk.Radiobutton(features_frame, text="Full (Đầy đủ)", variable=self.features_var, 
                       value="full").pack(side='left')
        ttk.Radiobutton(features_frame, text="Basic (Cơ bản)", variable=self.features_var, 
                       value="basic").pack(side='left', padx=(20, 0))
        
        # Private key
        ttk.Label(form_frame, text="Private Key:").grid(row=4, column=0, sticky='w', pady=5)
        key_frame = ttk.Frame(form_frame)
        key_frame.grid(row=4, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        self.key_entry = ttk.Entry(key_frame, width=40, font=('Consolas', 8), show='*')
        self.key_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(key_frame, text="📁 Load", 
                  command=self.load_private_key).pack(side='right', padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="🔑 Tạo License", 
                  command=self.generate_license, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="💾 Lưu License", 
                  command=self.save_license).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🗑️ Xóa Form", 
                  command=self.clear_form).pack(side='left', padx=5)
        
        # Result area
        result_frame = ttk.LabelFrame(self.root, text="📋 Kết quả", padding=10)
        result_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.result_text = tk.Text(result_frame, height=8, font=('Consolas', 9), 
                                  wrap='word', bg='#f8f9fa', fg='#2c3e50')
        self.result_text.pack(fill='both', expand=True)
        
        # Scrollbar for result
        scrollbar = ttk.Scrollbar(result_frame, orient='vertical', command=self.result_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # Status bar
        self.status_var = tk.StringVar(value="Sẵn sàng tạo license")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief='sunken', anchor='w')
        status_bar.pack(fill='x', side='bottom')
        
        # Load default private key if exists
        self.load_default_private_key()
        
    def load_default_private_key(self):
        """Load private key mặc định nếu có"""
        try:
            # Tìm private key trong thư mục hiện tại
            key_files = ['private_key.pem', 'key.pem', 'license_key.pem']
            for key_file in key_files:
                if os.path.exists(key_file):
                    with open(key_file, 'rb') as f:
                        self.key_entry.delete(0, tk.END)
                        self.key_entry.insert(0, f.read().decode('utf-8'))
                    self.status_var.set(f"Đã load private key từ {key_file}")
                    break
        except Exception as e:
            self.status_var.set(f"Không tìm thấy private key mặc định: {e}")
    
    def paste_fingerprint(self):
        """Paste fingerprint từ clipboard"""
        try:
            clipboard_text = self.root.clipboard_get()
            self.fingerprint_entry.delete(0, tk.END)
            self.fingerprint_entry.insert(0, clipboard_text)
            self.status_var.set("Đã paste fingerprint từ clipboard")
        except Exception:
            messagebox.showerror("Lỗi", "Không thể lấy dữ liệu từ clipboard")
    
    def set_permanent(self):
        """Set license vĩnh viễn"""
        self.expiry_entry.delete(0, tk.END)
        self.expiry_entry.insert(0, "permanent")
        self.status_var.set("Đã set license vĩnh viễn")
    
    def load_private_key(self):
        """Load private key từ file"""
        file_path = filedialog.askopenfilename(
            title="Chọn file Private Key",
            filetypes=[('PEM files', '*.pem'), ('All files', '*.*')]
        )
        
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    key_data = f.read().decode('utf-8')
                    self.key_entry.delete(0, tk.END)
                    self.key_entry.insert(0, key_data)
                    self.status_var.set(f"Đã load private key từ {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file: {e}")
    
    def generate_license(self):
        """Tạo license"""
        try:
            # Validate input
            customer = self.customer_entry.get().strip()
            fingerprint = self.fingerprint_entry.get().strip()
            expiry = self.expiry_entry.get().strip()
            features = self.features_var.get()
            private_key_data = self.key_entry.get().strip()
            
            if not all([customer, fingerprint, expiry, private_key_data]):
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin")
                return
            
            # Validate fingerprint format
            if len(fingerprint) != 16 or not all(c in '0123456789abcdef' for c in fingerprint.lower()):
                messagebox.showerror("Lỗi", "Hardware fingerprint phải có 16 ký tự hex")
                return
            
            # Load private key
            try:
                private_key = serialization.load_pem_private_key(
                    private_key_data.encode('utf-8'), password=None
                )
            except Exception as e:
                messagebox.showerror("Lỗi", f"Private key không hợp lệ: {e}")
                return
            
            # Create payload
            payload = {
                "product": "nhathuoc",
                "customer": customer,
                "hw": fingerprint.lower(),
                "expires": expiry if expiry != "permanent" else "2099-12-31",
                "features": [features],
                "created": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Sign payload
            blob = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
            signature = private_key.sign(blob)
            
            # Create license
            license_data = {
                "payload": payload,
                "sig": base64.b64encode(signature).decode('utf-8')
            }
            
            # Encode license
            license_key = base64.b64encode(
                json.dumps(license_data).encode('utf-8')
            ).decode('utf-8')
            
            # Display result
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, license_key)
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(license_key)
            
            self.status_var.set(f"✅ Đã tạo license cho {customer} - Đã copy vào clipboard")
            
            # Show success message
            messagebox.showinfo("Thành công", 
                f"License đã được tạo thành công!\n\n"
                f"Khách hàng: {customer}\n"
                f"Fingerprint: {fingerprint}\n"
                f"Hết hạn: {expiry}\n"
                f"Tính năng: {features}\n\n"
                f"License đã được copy vào clipboard.")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo license: {e}")
            self.status_var.set(f"❌ Lỗi: {e}")
    
    def save_license(self):
        """Lưu license vào file"""
        license_text = self.result_text.get(1.0, tk.END).strip()
        if not license_text:
            messagebox.showerror("Lỗi", "Không có license để lưu")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Lưu License",
            defaultextension=".lic",
            filetypes=[('License files', '*.lic'), ('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(license_text)
                self.status_var.set(f"✅ Đã lưu license vào {os.path.basename(file_path)}")
                messagebox.showinfo("Thành công", f"License đã được lưu vào:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")
    
    def clear_form(self):
        """Xóa form"""
        self.customer_entry.delete(0, tk.END)
        self.fingerprint_entry.delete(0, tk.END)
        self.expiry_entry.delete(0, tk.END)
        self.expiry_entry.insert(0, (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'))
        self.features_var.set("full")
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("Đã xóa form")
    
    def run(self):
        """Chạy ứng dụng"""
        self.root.mainloop()

def create_sample_private_key():
    """Tạo private key mẫu (chỉ để test)"""
    private_key = Ed25519PrivateKey.generate()
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Lưu private key
    with open('private_key.pem', 'wb') as f:
        f.write(pem)
    
    # Lưu public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open('public_key.pem', 'wb') as f:
        f.write(public_pem)
    
    # Lưu public key base64 (để dùng trong phần mềm chính)
    public_b64 = base64.b64encode(
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    ).decode('utf-8')
    
    with open('public_key_b64.txt', 'w') as f:
        f.write(public_b64)
    
    print("✅ Đã tạo key pair:")
    print(f"Private key: private_key.pem")
    print(f"Public key: public_key.pem") 
    print(f"Public key (base64): {public_b64}")
    print("\n📋 Copy public key base64 này vào phần mềm chính:")
    print(f"PUBLIC_B64 = \"{public_b64}\"")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-keys':
        create_sample_private_key()
    else:
        app = LicenseGenerator()
        app.run()
