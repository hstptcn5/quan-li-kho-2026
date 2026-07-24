import html
from datetime import datetime


def render_print_purchase_html(note, items):
    created_str = note['createdAt']
    try:
        dt_val = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')
        date_formatted = dt_val.strftime('%d-%m-%Y %H:%M:%S')
    except Exception:
        date_formatted = created_str

    # Generate table rows
    rows_html = ""
    total_amount = 0.0
    for idx, it in enumerate(items, 1):
        qty = float(it['qty'])
        cost = float(it['cost'])
        amount = qty * cost
        total_amount += amount
        
        cost_str = f"{cost:,.1f}".replace(".0", "") if cost > 0 else "0"
        amount_str = f"{amount:,.1f}".replace(".0", "") if amount > 0 else "0"
        qty_str = f"{qty:,.2f}".rstrip('0').rstrip('.')
        
        expiry_str = it['expiryDate']
        try:
            exp_dt = datetime.strptime(expiry_str, '%Y-%m-%d')
            expiry_formatted = exp_dt.strftime('%d-%m-%Y')
        except Exception:
            expiry_formatted = expiry_str
            
        rows_html += f"""
        <tr>
            <td style="text-align: center;">{idx}</td>
            <td>{html.escape(it['productName'])}</td>
            <td style="text-align: center;">{html.escape(it['unitCode'])}</td>
            <td style="text-align: right;">{qty_str}</td>
            <td style="text-align: right;">{cost_str}</td>
            <td style="text-align: right;">{amount_str}</td>
            <td style="text-align: center;">{html.escape(it['lotNo'] or '')}</td>
            <td style="text-align: center;">{expiry_formatted}</td>
        </tr>
        """
        
    total_amount_str = f"{total_amount:,.1f}".replace(".0", "") if total_amount > 0 else "0"
    
    html_out = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Phieu Nhap Kho {html.escape(note['noteNumber'])}</title>
<style>
    body {{
        font-family: "Times New Roman", Times, serif;
        font-size: 13pt;
        line-height: 1.3;
        margin: 0;
        padding: 20px;
        color: #000;
        background-color: #fff;
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
    }}
    .header-left {{
        font-weight: bold;
        font-size: 11pt;
        text-align: center;
    }}
    .header-right {{
        font-size: 10pt;
        text-align: center;
    }}
    .title-block {{
        text-align: center;
        margin-bottom: 20px;
    }}
    .title {{
        font-size: 16pt;
        font-weight: bold;
        margin: 0;
    }}
    .subtitle {{
        font-size: 12pt;
        font-weight: bold;
        margin: 5px 0 0 0;
    }}
    .info-table {{
        width: 100%;
        margin-bottom: 15px;
        border-collapse: collapse;
    }}
    .info-table td {{
        padding: 4px 0;
        vertical-align: top;
    }}
    .items-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }}
    .items-table th, .items-table td {{
        border: 1px solid #000;
        padding: 6px 8px;
        font-size: 11pt;
    }}
    .items-table th {{
        font-weight: bold;
        text-align: center;
        background-color: #f2f2f2;
    }}
    .signatures {{
        display: flex;
        justify-content: space-around;
        margin-top: 40px;
        page-break-inside: avoid;
    }}
    .signature-block {{
        text-align: center;
        width: 30%;
    }}
    .signature-title {{
        font-weight: bold;
        margin-bottom: 60px;
    }}
    .no-print-btn {{
        background: #4f46e5;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 11pt;
        font-weight: bold;
        cursor: pointer;
        margin-bottom: 20px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }}
    @media print {{
        .no-print {{
            display: none !important;
        }}
        body {{
            padding: 0;
        }}
    }}
</style>
</head>
<body>
<div class="no-print" style="text-align: right;">
    <button class="no-print-btn" onclick="window.print()">
        🖨️ In Phieu / Luu PDF
    </button>
</div>

<div class="header">
    <div class="header-left">
        SO Y TE THANH PHO CAN THO<br>
        TRUNG TAM KIEM SOAT BENH TAT (CDC)
    </div>
    <div class="header-right">
        <strong>Mau so: C30-HD</strong><br>
        <em>(Ban hanh theo Thong tu so 107/2017/TT-BTC)</em>
    </div>
</div>

<div class="title-block">
    <h1 class="title">PHIEU NHAP KHO</h1>
    <div class="subtitle">So: {html.escape(note['noteNumber'])}</div>
</div>

<table class="info-table">
    <tr>
        <td style="width: 180px;"><strong>Nguon cap / Nha CC:</strong></td>
        <td>{html.escape(note['supplier'])}</td>
    </tr>
    <tr>
        <td><strong>Ly do nhap:</strong></td>
        <td>{html.escape(note['reason'])}</td>
    </tr>
    <tr>
        <td><strong>Kho nhap:</strong></td>
        <td>Kho Duoc CDC Can Tho</td>
    </tr>
    <tr>
        <td><strong>Ngay nhap:</strong></td>
        <td>{html.escape(date_formatted)}</td>
    </tr>
    <tr>
        <td><strong>Ghi chu:</strong></td>
        <td>{html.escape(note['note'] or 'Khong')}</td>
    </tr>
</table>

<table class="items-table">
    <thead>
        <tr>
            <th style="width: 5%;">STT</th>
            <th>Ten thuoc, vaccine, VTYT</th>
            <th style="width: 8%;">DVT</th>
            <th style="width: 12%;">So luong</th>
            <th style="width: 12%;">Don gia</th>
            <th style="width: 12%;">Thanh tien</th>
            <th style="width: 12%;">So lo</th>
            <th style="width: 12%;">Han dung</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
        <tr style="font-weight: bold;">
            <td colspan="5" style="text-align: right;">Tong cong:</td>
            <td style="text-align: right;">{total_amount_str}</td>
            <td colspan="2"></td>
        </tr>
    </tbody>
</table>

<div class="signatures">
    <div class="signature-block">
        <div class="signature-title">Nguoi giao hang</div>
        <div>(Ky, ho ten)</div>
    </div>
    <div class="signature-block">
        <div class="signature-title">Thu kho</div>
        <div>(Ky, ho ten)</div>
    </div>
    <div class="signature-block">
        <div class="signature-title">Nguoi lap phieu</div>
        <div>(Ky, ho ten)</div>
    </div>
</div>

<script>
    window.onload = function() {{
        setTimeout(function() {{
            window.print();
        }}, 500);
    }}
</script>
</body>
</html>
"""
    return html_out

def render_print_dispatch_html(note, items):
    created_str = note['createdAt']
    try:
        dt_val = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')
        date_formatted = dt_val.strftime('%d-%m-%Y %H:%M:%S')
    except Exception:
        date_formatted = created_str

    # Generate table rows
    rows_html = ""
    for idx, it in enumerate(items, 1):
        qty = float(it['qty'])
        qty_str = f"{qty:,.2f}".rstrip('0').rstrip('.')
        
        expiry_str = it['expiryDate']
        try:
            exp_dt = datetime.strptime(expiry_str, '%Y-%m-%d')
            expiry_formatted = exp_dt.strftime('%d-%m-%Y')
        except Exception:
            expiry_formatted = expiry_str
            
        rows_html += f"""
        <tr>
            <td style="text-align: center;">{idx}</td>
            <td>{html.escape(it['productName'])}</td>
            <td style="text-align: center;">{html.escape(it['unitCode'])}</td>
            <td style="text-align: right;">{qty_str}</td>
            <td style="text-align: center;">{html.escape(it['lotNo'] or '')}</td>
            <td style="text-align: center;">{expiry_formatted}</td>
            <td></td>
        </tr>
        """
        
    html_out = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Phieu Xuat Kho {html.escape(note['noteNumber'])}</title>
<style>
    body {{
        font-family: "Times New Roman", Times, serif;
        font-size: 13pt;
        line-height: 1.3;
        margin: 0;
        padding: 20px;
        color: #000;
        background-color: #fff;
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
    }}
    .header-left {{
        font-weight: bold;
        font-size: 11pt;
        text-align: center;
    }}
    .header-right {{
        font-size: 10pt;
        text-align: center;
    }}
    .title-block {{
        text-align: center;
        margin-bottom: 20px;
    }}
    .title {{
        font-size: 16pt;
        font-weight: bold;
        margin: 0;
    }}
    .subtitle {{
        font-size: 12pt;
        font-weight: bold;
        margin: 5px 0 0 0;
    }}
    .info-table {{
        width: 100%;
        margin-bottom: 15px;
        border-collapse: collapse;
    }}
    .info-table td {{
        padding: 4px 0;
        vertical-align: top;
    }}
    .items-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }}
    .items-table th, .items-table td {{
        border: 1px solid #000;
        padding: 6px 8px;
        font-size: 11pt;
    }}
    .items-table th {{
        font-weight: bold;
        text-align: center;
        background-color: #f2f2f2;
    }}
    .signatures {{
        display: flex;
        justify-content: space-around;
        margin-top: 40px;
        page-break-inside: avoid;
    }}
    .signature-block {{
        text-align: center;
        width: 30%;
    }}
    .signature-title {{
        font-weight: bold;
        margin-bottom: 60px;
    }}
    .no-print-btn {{
        background: #4f46e5;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 11pt;
        font-weight: bold;
        cursor: pointer;
        margin-bottom: 20px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }}
    @media print {{
        .no-print {{
            display: none !important;
        }}
        body {{
            padding: 0;
        }}
    }}
</style>
</head>
<body>
<div class="no-print" style="text-align: right;">
    <button class="no-print-btn" onclick="window.print()">
        🖨️ In Phieu / Luu PDF
    </button>
</div>

<div class="header">
    <div class="header-left">
        SO Y TE THANH PHO CAN THO<br>
        TRUNG TAM KIEM SOAT BENH TAT (CDC)
    </div>
    <div class="header-right">
        <strong>Mau so: C31-HD</strong><br>
        <em>(Ban hanh theo Thong tu so 107/2017/TT-BTC)</em>
    </div>
</div>

<div class="title-block">
    <h1 class="title">PHIEU XUAT KHO</h1>
    <div class="subtitle">So: {html.escape(note['noteNumber'])}</div>
</div>

<table class="info-table">
    <tr>
        <td style="width: 180px;"><strong>Don vi nhan:</strong></td>
        <td>{html.escape(note['receivingUnit'])}</td>
    </tr>
    <tr>
        <td><strong>Ly do xuat:</strong></td>
        <td>{html.escape(note['reason'])}</td>
    </tr>
    <tr>
        <td><strong>Kho xuat:</strong></td>
        <td>Kho Duoc CDC Can Tho</td>
    </tr>
    <tr>
        <td><strong>Ngay xuat:</strong></td>
        <td>{html.escape(date_formatted)}</td>
    </tr>
    <tr>
        <td><strong>Ghi chu:</strong></td>
        <td>{html.escape(note['note'] or 'Khong')}</td>
    </tr>
</table>

<table class="items-table">
    <thead>
        <tr>
            <th style="width: 5%;">STT</th>
            <th>Ten thuoc, vaccine, VTYT</th>
            <th style="width: 10%;">DVT</th>
            <th style="width: 15%;">So luong</th>
            <th style="width: 15%;">So lo</th>
            <th style="width: 15%;">Han dung</th>
            <th style="width: 15%;">Ghi chu</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>

<div class="signatures">
    <div class="signature-block">
        <div class="signature-title">Nguoi nhan hang</div>
        <div>(Ky, ho ten)</div>
    </div>
    <div class="signature-block">
        <div class="signature-title">Thu kho</div>
        <div>(Ky, ho ten)</div>
    </div>
    <div class="signature-block">
        <div class="signature-title">Nguoi lap phieu</div>
        <div>(Ky, ho ten)</div>
    </div>
</div>

<script>
    window.onload = function() {{
        setTimeout(function() {{
            window.print();
        }}, 500);
    }}
</script>
</body>
</html>
"""
    return html_out
