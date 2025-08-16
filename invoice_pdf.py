
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
import os
import datetime

def draw_header(c, shop_name, shop_info, logo_path):
    width, height = A4
    y = height - 20*mm
    if logo_path and os.path.exists(logo_path):
        c.drawImage(logo_path, 15*mm, y-15*mm, width=20*mm, height=20*mm, mask='auto')
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40*mm, y, shop_name)
    c.setFont("Helvetica", 9)
    text = shop_info
    for i, line in enumerate(text.splitlines()[:3]):
        c.drawString(40*mm, y - (6*(i+1)), line)

def money(x):
    try:
        return f"{float(x):,.2f}"
    except:
        return str(x)

def generate_invoice_pdf(path, data):
    """
    data = {
      'invoice_no': 'S-2025-0001',
      'invoice_date': '2025-08-16',
      'invoice_type': 'بيع' or 'شراء',
      'customer_supplier_name': 'اسم العميل/المورد',
      'customer_supplier_info': 'هاتف: ...\nعنوان: ...',
      'items': [{'name': 'صنف', 'qty': 2, 'price': 10.0, 'total': 20.0}, ...],
      'subtotal': 20.0, 'discount': 0.0, 'tax': 0.0, 'total': 20.0,
      'shop_name': 'اسم المحل',
      'shop_info': 'هاتف: ...\nعنوان: ...',
      'logo_path': 'assets/logo.png'
    }
    """
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    # Header
    draw_header(c, data.get('shop_name','المحل'), data.get('shop_info',''), data.get('logo_path'))
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width-15*mm, height-15*mm, f"فاتورة {data.get('invoice_type','بيع')}")
    # Info box
    c.setFont("Helvetica", 10)
    info_y = height - 35*mm
    c.drawRightString(width-15*mm, info_y, f"التاريخ: {data.get('invoice_date','')}")
    c.drawRightString(width-15*mm, info_y-12, f"رقم الفاتورة: {data.get('invoice_no','')}")
    # Party box
    c.drawString(15*mm, info_y, f"العميل/المورد: {data.get('customer_supplier_name','')}")
    party_info = data.get('customer_supplier_info','')
    for i, line in enumerate(party_info.splitlines()[:3]):
        c.drawString(15*mm, info_y-12*(i+1), line)
    # Table
    table_data = [["الصنف", "الكمية", "السعر", "الإجمالي"]]
    for it in data.get('items', []):
        table_data.append([it.get('name',''), str(it.get('qty','')), money(it.get('price','')), money(it.get('total',''))])
    tbl = Table(table_data, colWidths=[90*mm, 25*mm, 30*mm, 30*mm])
    tbl.setStyle(TableStyle([
        ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
        ('FONT', (0,1), (-1,-1), 'Helvetica', 10),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
    ]))
    tw, th = tbl.wrapOn(c, width-30*mm, height)
    tbl.drawOn(c, 15*mm, info_y-80*mm)
    # Totals
    totals_y = info_y-85*mm - th + 20*mm
    if totals_y < 60*mm:
        totals_y = 60*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width-15*mm, totals_y, f"الإجمالي قبل الخصم: {money(data.get('subtotal',0))}")
    c.drawRightString(width-15*mm, totals_y-12, f"الخصم: {money(data.get('discount',0))}")
    c.drawRightString(width-15*mm, totals_y-24, f"الضريبة: {money(data.get('tax',0))}")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width-15*mm, totals_y-38, f"الصافي المستحق: {money(data.get('total',0))}")
    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2, 15*mm, "شكراً لتعاملكم معنا")
    c.showPage()
    c.save()
    return path
