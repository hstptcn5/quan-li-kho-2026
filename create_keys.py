#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo cặp khóa Ed25519 cho License System
"""

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import base64

def create_key_pair():
    """Tạo cặp khóa Ed25519"""
    print("🔐 Đang tạo cặp khóa Ed25519...")
    
    # Tạo private key
    private_key = Ed25519PrivateKey.generate()
    
    # Lưu private key (PEM format)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    with open('private_key.pem', 'wb') as f:
        f.write(private_pem)
    
    # Lưu public key (PEM format)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open('public_key.pem', 'wb') as f:
        f.write(public_pem)
    
    # Tạo public key base64 (raw format) để dùng trong phần mềm
    public_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    public_b64 = base64.b64encode(public_raw).decode('utf-8')
    
    with open('public_key_b64.txt', 'w') as f:
        f.write(public_b64)
    
    print("✅ Đã tạo thành công!")
    print("\n📁 Files đã tạo:")
    print("  • private_key.pem - Private key (giữ bí mật)")
    print("  • public_key.pem - Public key (PEM format)")
    print("  • public_key_b64.txt - Public key (base64 raw)")
    
    print(f"\n🔑 Public Key (Base64):")
    print(f"PUBLIC_B64 = \"{public_b64}\"")
    
    print(f"\n📋 Hướng dẫn:")
    print("1. Copy PUBLIC_B64 vào phần mềm chính (nhathuoc2.py)")
    print("2. Giữ private_key.pem an toàn (dùng để tạo license)")
    print("3. Chạy license_generator.py để tạo license cho khách hàng")
    
    return public_b64

if __name__ == '__main__':
    create_key_pair()
