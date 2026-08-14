from io import BytesIO
from datetime import datetime
from django.conf import settings
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from .models import Order, MpesaTransaction, Booking


class DocumentGenerator:
    """Service class for generating PDF documents like receipts and invoices"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Normal style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=10,
            spaceBefore=20
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='CustomFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#95A5A6'),
            alignment=TA_CENTER
        ))
    
    def _create_header(self, doc_type, doc_number, date):
        """Create document header"""
        elements = []
        
        # Title
        elements.append(Paragraph("NEUTRIKENYA", self.styles['CustomTitle']))
        elements.append(Paragraph(doc_type.upper(), self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Document info
        doc_info = [
            [f"{doc_type} Number:", doc_number],
            ["Date:", date.strftime('%B %d, %Y')],
            ["Time:", date.strftime('%I:%M %p')]
        ]
        
        table = Table(doc_info, colWidths=[1.5 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495E')),
            ('ALIGN', (0, 0), (0, -1), TA_RIGHT),
            ('ALIGN', (1, 0), (1, -1), TA_LEFT),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_customer_info(self, customer_data):
        """Create customer information section"""
        elements = []
        elements.append(Paragraph("Customer Information", self.styles['CustomHeader']))
        
        customer_info = []
        for label, value in customer_data.items():
            customer_info.append([label, value])
        
        table = Table(customer_info, colWidths=[1.5 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495E')),
            ('ALIGN', (0, 0), (0, -1), TA_RIGHT),
            ('ALIGN', (1, 0), (1, -1), TA_LEFT),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_items_table(self, items, headers):
        """Create items table"""
        elements = []
        elements.append(Paragraph("Items", self.styles['CustomHeader']))
        
        # Add headers
        table_data = [headers]
        
        # Add items
        for item in items:
            table_data.append(item)
        
        table = Table(table_data, colWidths=[0.5 * inch, 3 * inch, 1 * inch, 1 * inch, 1 * inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495E')),
            ('ALIGN', (0, 0), (-1, -1), TA_CENTER),
            ('ALIGN', (1, 0), (1, -1), TA_LEFT),
            ('ALIGN', (2, 0), (-1, -1), TA_RIGHT),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ECF0F1')),
            ('FONTWEIGHT', (0, 0), (-1, 0), 'BOLD'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_payment_info(self, payment_data):
        """Create payment information section"""
        elements = []
        elements.append(Paragraph("Payment Information", self.styles['CustomHeader']))
        
        payment_info = []
        for label, value in payment_data.items():
            payment_info.append([label, value])
        
        table = Table(payment_info, colWidths=[1.5 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495E')),
            ('ALIGN', (0, 0), (0, -1), TA_RIGHT),
            ('ALIGN', (1, 0), (1, -1), TA_LEFT),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_totals(self, totals_data):
        """Create totals section"""
        elements = []
        
        totals = []
        for label, value in totals_data.items():
            totals.append([label, value])
        
        table = Table(totals, colWidths=[4 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495E')),
            ('ALIGN', (0, 0), (0, -1), TA_RIGHT),
            ('ALIGN', (1, 0), (1, -1), TA_RIGHT),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('FONTWEIGHT', (0, -1), (-1, -1), 'BOLD'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_footer(self):
        """Create document footer"""
        elements = []
        
        footer_text = """
        Thank you for your business!<br/>
        If you have any questions, please contact us at:<br/>
        Email: info@neutrikenya.com | Phone: +254 XXX XXX XXX<br/>
        <br/>
        This document is automatically generated and does not require a signature.
        """
        
        elements.append(Paragraph(footer_text, self.styles['CustomFooter']))
        
        return elements
    
    def generate_receipt(self, order, transaction=None):
        """Generate receipt for an order"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []
        
        # Header
        doc_number = f"RCP-{order.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        elements.extend(self._create_header("Receipt", doc_number, order.created_at))
        
        # Customer information
        customer_data = {
            "Name": f"{order.first_name} {order.last_name}",
            "Email": order.email,
            "Phone": order.phone,
            "Address": f"{order.address}, {order.city}"
        }
        elements.extend(self._create_customer_info(customer_data))
        
        # Items
        items = []
        for item in order.items.all():
            items.append([
                str(item.quantity),
                item.product.name,
                f"KES {item.price:.2f}",
                f"KES {item.total_price:.2f}"
            ])
        
        headers = ["Qty", "Item", "Unit Price", "Total"]
        elements.extend(self._create_items_table(items, headers))
        
        # Payment information
        payment_data = {
            "Payment Method": order.get_payment_method_display(),
            "Payment Status": order.payment_status.title(),
        }
        
        if transaction:
            payment_data.update({
                "M-Pesa Receipt": transaction.receipt_number or "Pending",
                "Transaction Date": transaction.transaction_date.strftime('%B %d, %Y %H:%M') if transaction.transaction_date else "Pending",
                "Phone Number": transaction.phone_number
            })
        
        elements.extend(self._create_payment_info(payment_data))
        
        # Totals
        totals_data = {
            "Subtotal": f"KES {order.total_price:.2f}",
            "VAT (16%)": f"KES {order.total_price * 0.16:.2f}",
            "Total": f"KES {order.total_price * 1.16:.2f}"
        }
        elements.extend(self._create_totals(totals_data))
        
        # Footer
        elements.extend(self._create_footer())
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_invoice(self, order):
        """Generate invoice for an order"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []
        
        # Header
        doc_number = f"INV-{order.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        elements.extend(self._create_header("Invoice", doc_number, order.created_at))
        
        # Customer information
        customer_data = {
            "Name": f"{order.first_name} {order.last_name}",
            "Email": order.email,
            "Phone": order.phone,
            "Address": f"{order.address}, {order.city}"
        }
        elements.extend(self._create_customer_info(customer_data))
        
        # Items
        items = []
        for item in order.items.all():
            items.append([
                str(item.quantity),
                item.product.name,
                f"KES {item.price:.2f}",
                f"KES {item.total_price:.2f}"
            ])
        
        headers = ["Qty", "Item", "Unit Price", "Total"]
        elements.extend(self._create_items_table(items, headers))
        
        # Payment information
        payment_data = {
            "Payment Method": order.get_payment_method_display(),
            "Payment Status": order.payment_status.title(),
            "Order Status": order.status.title()
        }
        elements.extend(self._create_payment_info(payment_data))
        
        # Totals
        totals_data = {
            "Subtotal": f"KES {order.total_price:.2f}",
            "VAT (16%)": f"KES {order.total_price * 0.16:.2f}",
            "Total Due": f"KES {order.total_price * 1.16:.2f}"
        }
        elements.extend(self._create_totals(totals_data))
        
        # Footer
        elements.extend(self._create_footer())
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_booking_receipt(self, booking, transaction=None):
        """Generate receipt for service booking"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []
        
        # Header
        doc_number = f"BOOK-RCP-{booking.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        elements.extend(self._create_header("Booking Receipt", doc_number, booking.created_at))
        
        # Customer information
        customer_data = {
            "Name": booking.customer.get_full_name(),
            "Email": booking.customer.email,
            "Phone": booking.phone,
            "Address": f"{booking.address}, {booking.city}"
        }
        elements.extend(self._create_customer_info(customer_data))
        
        # Service information
        service_data = {
            "Service": booking.service.name,
            "Service Type": booking.service.get_service_type_display(),
            "Scheduled Date": booking.scheduled_date.strftime('%B %d, %Y at %I:%M %p'),
            "Booking Status": booking.status.title(),
            "Technician": booking.technician.user.get_full_name() if booking.technician else "To be assigned"
        }
        elements.extend(self._create_payment_info(service_data))
        
        # Payment information
        payment_data = {
            "Payment Method": booking.get_payment_method_display(),
            "Payment Status": booking.payment_status.title(),
        }
        
        if transaction:
            payment_data.update({
                "M-Pesa Receipt": transaction.receipt_number or "Pending",
                "Transaction Date": transaction.transaction_date.strftime('%B %d, %Y %H:%M') if transaction.transaction_date else "Pending",
                "Phone Number": transaction.phone_number
            })
        
        elements.extend(self._create_payment_info(payment_data))
        
        # Totals
        total_cost = booking.get_total_cost()
        totals_data = {
            "Service Fee": f"KES {booking.service.base_price:.2f}",
            "Callout Fee": f"KES {booking.service.callout_fee:.2f}",
            "VAT (16%)": f"KES {(booking.service.base_price + booking.service.callout_fee) * 0.16:.2f}",
            "Total": f"KES {total_cost:.2f}"
        }
        elements.extend(self._create_totals(totals_data))
        
        # Footer
        elements.extend(self._create_footer())
        
        doc.build(elements)
        buffer.seek(0)
        return buffer