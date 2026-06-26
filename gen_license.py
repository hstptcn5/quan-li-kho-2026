#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo license nhanh — debug & fix
"""
import json, base64, datetime, uuid, platform, hashlib, subprocess, os

# ---- Lấy fingerprint máy (copy y từ nhathuoc2.py) ----
def machine_fingerprint() -> str:
    parts = [
        platform.node() or '',
        platform.system() or '',
        platform.machine() or '',
        hex(uuid.getnode()) or ''
    ]
    if os.name == 'nt':
        for cmd in ('wmic bios get serialnumber', 'wmic csproduct get uuid'):
            try:
                out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
                lines = [x.strip() for x in out.decode(errors='ignore').splitlines()
                         if x.strip() and 'serial' not in x.lower() and 'uuid' not in x.lower()]
                if lines:
                    parts.append(lines[-1])
                    break
            except Exception:
                pass
    raw = '|'.join(parts)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]

# ---- Public key đang dùng trong nhathuoc2.py ----
PUBLIC_B64 = "cfCth+TwUKiTYPS0gjUoSmwEBBPM6ElQo82e8RdtWl8="

# ---- Load private key từ dist ----
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), 'dist', 'private_key.pem')

def load_private_key():
    with open(PRIVATE_KEY_PATH, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def generate_license(customer, fingerprint, expiry="2099-12-31", features="full"):
    private_key = load_private_key()

    payload = {
        "product": "nhathuoc",
        "customer": customer,
        "hw": fingerprint.lower(),
        "expires": expiry,
        "features": [features],
        "created": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    blob = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    signature = private_key.sign(blob)

    license_data = {
        "payload": payload,
        "sig": base64.b64encode(signature).decode('utf-8')
    }

    license_key = base64.b64encode(
        json.dumps(license_data).encode('utf-8')
    ).decode('utf-8')
    return license_key

def verify_license(license_key):
    pub_bytes = base64.b64decode(PUBLIC_B64)
    pack = json.loads(base64.b64decode(license_key).decode('utf-8'))
    payload = pack["payload"]
    sig = base64.b64decode(pack["sig"])
    blob = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    try:
        Ed25519PublicKey.from_public_bytes(pub_bytes).verify(sig, blob)
        print("✅ Verify ok!")
    except InvalidSignature:
        print("❌ Verify FAIL — sig không khớp")

    # Check pub key từ private key
    priv = load_private_key()
    pub_from_priv = base64.b64encode(
        priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode()
    print(f"   Public key từ private_key.pem : {pub_from_priv}")
    print(f"   PUBLIC_B64 trong nhathuoc2.py  : {PUBLIC_B64}")
    if pub_from_priv == PUBLIC_B64:
        print("   ✅ 2 key KHỚP NHAU — license sẽ hợp lệ")
    else:
        print("   ❌ 2 key KHÔNG KHỚP — đây là nguyên nhân lỗi!")

if __name__ == '__main__':
    fp = machine_fingerprint()
    print(f"Hardware Fingerprint: {fp}")

    lic = generate_license("KhachHang", fp)
    print(f"\nLicense Key:\n{lic}\n")

    print("Đang verify...")
    verify_license(lic)

    # Ghi license vào file để dùng thử
    out_path = os.path.join(os.path.dirname(__file__), 'test_license.lic')
    with open(out_path, 'w') as f:
        f.write(lic)
    print(f"\nĐã lưu vào: {out_path}")
