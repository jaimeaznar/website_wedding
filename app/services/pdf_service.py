# app/services/pdf_service.py
"""
PDF Generation Service for Wedding Website
Generates professional PDF reports for venue and transport coordination
"""

import io
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfgen import canvas

from app.services.admin_service import AdminService
from app.services.rsvp_service import RSVPService

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF reports."""
    
    # PDF Configuration
    PAGE_SIZE = A4
    MARGIN = 0.75 * inch
    
    # Colors
    COLOR_PRIMARY = colors.HexColor('#2C3E50')      # Dark blue-gray
    COLOR_SECONDARY = colors.HexColor('#3498DB')    # Light blue
    COLOR_ACCENT = colors.HexColor('#E74C3C')       # Red for allergies
    COLOR_SUCCESS = colors.HexColor('#27AE60')      # Green
    COLOR_WARNING = colors.HexColor('#F39C12')      # Orange
    COLOR_LIGHT_GRAY = colors.HexColor('#ECF0F1')   # Light gray for alternating rows
    HEADER_HEIGHT = 1.4 * inch
    

    @staticmethod
    def _create_header(canvas_obj, doc, title: str, subtitle: str = None):
        """
        Create a standard header for all PDFs.
        
        Args:
            canvas_obj: ReportLab canvas object
            doc: Document object
            title: Main title
            subtitle: Optional subtitle
        """
        canvas_obj.saveState()
        
        page_width, page_height = PDFService.PAGE_SIZE
        
        # Wedding couple names - get from config
        wedding_title = current_app.config.get('WEDDING_TITLE', "Irene & Jaime's Wedding")
        canvas_obj.setFont('Helvetica-BoldOblique', 22)
        canvas_obj.setFillColor(PDFService.COLOR_PRIMARY)
        canvas_obj.drawCentredString(
            page_width / 2,
            page_height - 0.6 * inch,
            wedding_title
        )
        
        # Document title
        canvas_obj.setFont('Helvetica-Bold', 14)
        canvas_obj.setFillColor(PDFService.COLOR_SECONDARY)
        canvas_obj.drawCentredString(
            page_width / 2,
            page_height - 0.95 * inch,
            title
        )
        
        # Subtitle if provided
        if subtitle:
            canvas_obj.setFont('Helvetica', 10)
            canvas_obj.setFillColor(colors.gray)
            canvas_obj.drawCentredString(
                page_width / 2,
                page_height - 1.15 * inch,
                subtitle
            )
        
        # Date generated
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.gray)
        canvas_obj.drawRightString(
            page_width - PDFService.MARGIN,
            page_height - 0.4 * inch,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Line under header
        line_y = page_height - 1.35 * inch
        canvas_obj.setStrokeColor(PDFService.COLOR_SECONDARY)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(
            PDFService.MARGIN,
            line_y,
            page_width - PDFService.MARGIN,
            line_y
        )
        
        canvas_obj.restoreState()


    @staticmethod
    def _create_footer(canvas_obj, doc):
        """Create a standard footer for all PDFs."""
        canvas_obj.saveState()
        
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.gray)
        
        # Page number
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.drawCentredString(
            doc.width / 2 + doc.leftMargin,
            0.5 * inch,
            text
        )
        
        # Contact info
        canvas_obj.drawString(
            doc.leftMargin,
            0.5 * inch,
            "Questions? Contact the couple"
        )
        
        canvas_obj.restoreState()
    
    @staticmethod
    def generate_dietary_pdf() -> bytes:
        """
        Generate comprehensive dietary restrictions PDF for venue/caterer.
        
        Returns:
            PDF file as bytes
        """
        logger.info("Generating dietary restrictions PDF")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=PDFService.PAGE_SIZE,
            rightMargin=PDFService.MARGIN,
            leftMargin=PDFService.MARGIN,
            topMargin=1.5 * inch,  # Changed from MARGIN + 0.5 * inch
            bottomMargin=PDFService.MARGIN
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=PDFService.COLOR_PRIMARY,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=PDFService.COLOR_SECONDARY,
            spaceAfter=10,
            spaceBefore=15
        )
        normal_style = styles['Normal']
        
        # Get dietary data
        dietary_data = AdminService.get_dietary_report()

        children_menu_data = PDFService._get_children_menu_data()

        # Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        
        summary_data = [
            ['Metric', 'Count'],
            ['Total Guests with Restrictions', str(dietary_data['total_guests_with_restrictions'])],
            ['Standard Allergens', str(len(dietary_data['standard_allergens']))],
            ['Custom Restrictions', str(len(dietary_data['custom_allergens']))],
            ['Children with Menu', str(children_menu_data['total_with_menu'])],
            ['Children without Menu', str(children_menu_data['total_no_menu'])]
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY])
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Allergen Summary
        if dietary_data['summary']:
            elements.append(Paragraph("Allergen Breakdown", heading_style))
            
            allergen_summary = [['Allergen', 'Guest Count']]
            for allergen, count in sorted(dietary_data['summary'].items(), key=lambda x: x[1], reverse=True):
                allergen_summary.append([allergen, str(count)])
            
            allergen_table = Table(allergen_summary, colWidths=[3.5 * inch, 2 * inch])
            allergen_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_ACCENT),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY])
            ]))
            elements.append(allergen_table)
            elements.append(Spacer(1, 0.3 * inch))
        
        # Page break before detailed lists
        elements.append(PageBreak())
        
        # Detailed Standard Allergens
        if dietary_data['standard_allergens']:
            elements.append(Paragraph("Detailed Guest List - Standard Allergens", heading_style))
            
            for allergen, guests in sorted(dietary_data['standard_allergens'].items()):
                # Allergen name
                allergen_title = Paragraph(
                    f"<b>{allergen}</b> ({len(guests)} guests)",
                    ParagraphStyle('AllergenTitle', 
                                   parent=normal_style,
                                   fontSize=12,
                                   textColor=PDFService.COLOR_ACCENT,
                                   spaceAfter=5)
                )
                elements.append(allergen_title)
                
                # Guest list for this allergen
                guest_data = [['Guest Name']]
                for guest in sorted(guests):
                    guest_data.append([guest])
                
                guest_table = Table(guest_data, colWidths=[5.5 * inch])
                guest_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_WARNING),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))
                elements.append(guest_table)
                elements.append(Spacer(1, 0.2 * inch))
        
        # Custom Allergens/Restrictions
        if dietary_data['custom_allergens']:
            elements.append(PageBreak())
            elements.append(Paragraph("Custom Dietary Restrictions", heading_style))
            
            for restriction, guests in sorted(dietary_data['custom_allergens'].items()):
                # Restriction name
                restriction_title = Paragraph(
                    f"<b>{restriction}</b> ({len(guests)} guests)",
                    ParagraphStyle('RestrictionTitle',
                                   parent=normal_style,
                                   fontSize=12,
                                   textColor=PDFService.COLOR_SECONDARY,
                                   spaceAfter=5)
                )
                elements.append(restriction_title)
                
                # Guest list
                guest_data = [['Guest Name']]
                for guest in sorted(guests):
                    guest_data.append([guest])
                
                guest_table = Table(guest_data, colWidths=[5.5 * inch])
                guest_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_SECONDARY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))
                elements.append(guest_table)
                elements.append(Spacer(1, 0.2 * inch))
        
        # Children Menu Requirements
        if children_menu_data['total_children'] > 0:
            elements.append(PageBreak())
            elements.append(Paragraph("Children Menu Requirements", heading_style))
            
            # Summary
            elements.append(Paragraph(
                f"Total Children: <b>{children_menu_data['total_children']}</b> "
                f"({children_menu_data['total_with_menu']} with menu, "
                f"{children_menu_data['total_no_menu']} without menu)",
                ParagraphStyle('ChildrenSummary', parent=normal_style, fontSize=11, spaceAfter=15)
            ))
            
            # Children WITH menu
            if children_menu_data['with_menu']:
                elements.append(Paragraph(
                    f"<b>Children Requiring Menu</b> ({children_menu_data['total_with_menu']})",
                    ParagraphStyle('MenuTitle', 
                                parent=normal_style,
                                fontSize=12,
                                textColor=PDFService.COLOR_SUCCESS,
                                spaceAfter=5)
                ))
                
                menu_data = [['Child Name', 'Parent/Guardian', 'Contact']]
                for child in sorted(children_menu_data['with_menu'], key=lambda x: x['name']):
                    menu_data.append([
                        child['name'],
                        child['parent'],
                        child['phone'] or '-'
                    ])
                
                menu_table = Table(menu_data, colWidths=[2.2 * inch, 2.2 * inch, 1.6 * inch])
                menu_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_SUCCESS),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(menu_table)
                elements.append(Spacer(1, 0.2 * inch))
            
            # Children WITHOUT menu
            if children_menu_data['no_menu']:
                elements.append(Paragraph(
                    f"<b>Children Not Requiring Menu</b> ({children_menu_data['total_no_menu']})",
                    ParagraphStyle('NoMenuTitle',
                                parent=normal_style,
                                fontSize=12,
                                textColor=PDFService.COLOR_WARNING,
                                spaceAfter=5)
                ))
                
                no_menu_data = [['Child Name', 'Parent/Guardian', 'Contact']]
                for child in sorted(children_menu_data['no_menu'], key=lambda x: x['name']):
                    no_menu_data.append([
                        child['name'],
                        child['parent'],
                        child['phone'] or '-'
                    ])
                
                no_menu_table = Table(no_menu_data, colWidths=[2.2 * inch, 2.2 * inch, 1.6 * inch])
                no_menu_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_WARNING),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(no_menu_table)
                elements.append(Spacer(1, 0.2 * inch))
        
        # Important notes for venue
        elements.append(PageBreak())
        elements.append(Paragraph("Important Notes for Venue Staff", heading_style))
        
        notes = [
            "Please ensure all waitstaff are aware of these dietary restrictions.",
            "Cross-contamination prevention is critical for allergen safety.",
            "Verify ingredients in all dishes, including garnishes and sauces.",
            "Have emergency contact information available in case of allergic reactions.",
            "Update this list if any guests notify of additional restrictions."
        ]
        
        for i, note in enumerate(notes, 1):
            note_para = Paragraph(
                f"<b>{i}.</b> {note}",
                ParagraphStyle('Note',
                               parent=normal_style,
                               fontSize=10,
                               leftIndent=20,
                               spaceAfter=8)
            )
            elements.append(note_para)
        
        # Build PDF with custom header/footer
        def add_page_decorations(canvas_obj, doc):
            PDFService._create_header(canvas_obj, doc, "Dietary Restrictions Report", 
                                     "For Venue & Catering Staff")
            PDFService._create_footer(canvas_obj, doc)
        
        doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated dietary PDF: {len(pdf_data)} bytes")
        return pdf_data
    
    @staticmethod
    def _get_children_menu_data() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get children menu requirements for PDF report.
        
        Returns:
            Dictionary with 'with_menu' and 'no_menu' lists
        """
        from app.models.rsvp import RSVP, AdditionalGuest
        
        children_with_menu = []
        children_no_menu = []
        
        # Get all attending RSVPs
        attending_rsvps = RSVP.query.filter_by(is_attending=True, is_cancelled=False).all()
        
        for rsvp in attending_rsvps:
            # Get children for this RSVP
            children = AdditionalGuest.query.filter_by(
                rsvp_id=rsvp.id,
                is_child=True
            ).all()
            
            for child in children:
                # Build parent name with surname
                parent_name = rsvp.guest.name
                if rsvp.guest.surname:
                    parent_name = f"{rsvp.guest.name} {rsvp.guest.surname}"
                
                # Build child name with family surname
                child_name = child.name
                if rsvp.guest.surname:
                    child_name = f"{child.name} ({rsvp.guest.surname})"
                
                child_info = {
                    'name': child_name,
                    'parent': parent_name,
                    'phone': rsvp.guest.phone
                }
                
                if child.needs_menu:
                    children_with_menu.append(child_info)
                else:
                    children_no_menu.append(child_info)
        
        return {
            'with_menu': children_with_menu,
            'no_menu': children_no_menu,
            'total_with_menu': len(children_with_menu),
            'total_no_menu': len(children_no_menu),
            'total_children': len(children_with_menu) + len(children_no_menu)
        }
    
    @staticmethod
    def generate_transport_pdf() -> bytes:
        """
        Generate comprehensive transport requirements PDF for bus coordination.
        
        Returns:
            PDF file as bytes
        """
        logger.info("Generating transport requirements PDF")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=PDFService.PAGE_SIZE,
            rightMargin=PDFService.MARGIN,
            leftMargin=PDFService.MARGIN,
            topMargin=PDFService.MARGIN + 1.5 * inch,
            bottomMargin=PDFService.MARGIN
        )
        
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=PDFService.COLOR_PRIMARY,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=PDFService.COLOR_SECONDARY,
            spaceAfter=10,
            spaceBefore=15
        )
        route_heading_style = ParagraphStyle(
            'RouteHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=PDFService.COLOR_SUCCESS,
            spaceAfter=8,
            spaceBefore=12,
            leftIndent=10
        )
        normal_style = styles['Normal']
        
        # Get transport data
        transport_data = AdminService.get_transport_report()
        
        # Executive Summary
        elements.append(Paragraph("Transport Summary", heading_style))
        
        summary_data = [
            ['Route', 'Guests Requiring Transport'],
            ['Church → Reception', str(len(transport_data['to_reception']))],
            ['Reception → Hotel', str(len(transport_data['to_hotel']))],
            ['Total Hotels', str(len(transport_data['hotels']))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY])
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # ROUTE 2: Church to Reception
        elements.append(PageBreak())
        elements.append(Paragraph("Route 2: Church → Reception Venue", heading_style))
        elements.append(Paragraph(
            "⏰ <b>Timing:</b> Immediately after ceremony",
            ParagraphStyle('Timing', parent=normal_style, fontSize=10, textColor=colors.red)
        ))
        elements.append(Spacer(1, 0.1 * inch))
        
        if transport_data['to_reception']:
            total_people = sum(g['guest_count'] for g in transport_data['to_reception'])
            elements.append(Paragraph(
                f"Total Passengers: <b>{total_people}</b> ({len(transport_data['to_reception'])} booking{'s' if len(transport_data['to_reception']) != 1 else ''})",
                ParagraphStyle('Info', parent=normal_style, fontSize=10, leftIndent=20)
            ))
            elements.append(Spacer(1, 0.1 * inch))
            
            guest_data = [['Guest Name', 'Phone', 'Passengers', 'Hotel']]
            for guest in sorted(transport_data['to_reception'], key=lambda x: x['name']):
                guest_data.append([
                    guest['name'],
                    guest['phone'],
                    str(guest['guest_count']),
                    guest['hotel'] or 'Not specified'
                ])
            
            guest_table = Table(guest_data, colWidths=[2 * inch, 1.5 * inch, 1 * inch, 2 * inch])
            guest_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_SUCCESS),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY]),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(guest_table)
        else:
            elements.append(Paragraph("No transport required for this route.", normal_style))
        
        # ROUTE 3: Reception to Hotels
        elements.append(PageBreak())
        elements.append(Paragraph("Route 3: Reception → Hotels", heading_style))
        elements.append(Paragraph(
            "⏰ <b>Timing:</b> Multiple departures at guest request",
            ParagraphStyle('Timing', parent=normal_style, fontSize=10, textColor=colors.red)
        ))
        elements.append(Spacer(1, 0.1 * inch))
        
        if transport_data['to_hotel']:
            # Group by hotel for drop-off
            hotel_groups = {}
            for guest in transport_data['to_hotel']:
                hotel = guest['hotel'] or 'Unknown Hotel'
                if hotel not in hotel_groups:
                    hotel_groups[hotel] = []
                hotel_groups[hotel].append(guest)
            
            for hotel, guests in sorted(hotel_groups.items()):
                # Hotel name
                elements.append(Paragraph(f"📍 Drop-off Location: {hotel}", route_heading_style))
                
                # Calculate total people
                total_people = sum(g['guest_count'] for g in guests)
                elements.append(Paragraph(
                    f"Total Passengers: <b>{total_people}</b> ({len(guests)} booking{'s' if len(guests) != 1 else ''})",
                    ParagraphStyle('Info', parent=normal_style, fontSize=9, leftIndent=20)
                ))
                elements.append(Spacer(1, 0.05 * inch))
                
                # Guest list
                guest_data = [['Guest Name', 'Phone', 'Passengers']]
                for guest in sorted(guests, key=lambda x: x['name']):
                    guest_data.append([
                        guest['name'],
                        guest['phone'],
                        str(guest['guest_count'])
                    ])
                
                guest_table = Table(guest_data, colWidths=[2.5 * inch, 1.8 * inch, 1.2 * inch])
                guest_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_SUCCESS),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(guest_table)
                elements.append(Spacer(1, 0.15 * inch))
        else:
            elements.append(Paragraph("No transport required for this route.", normal_style))
        
        # Important notes for drivers
        elements.append(PageBreak())
        elements.append(Paragraph("Important Notes for Drivers", heading_style))
        
        notes = [
            "Verify passenger count at each pickup location.",
            "Have contact information for main guest at each stop.",
            "Coordinate timing with wedding coordinator for church departure.",
            "Allow flexibility for reception-to-hotel departures (staggered times).",
            "Keep this document accessible during all routes.",
            "Report any issues immediately to wedding coordinator."
        ]
        
        for i, note in enumerate(notes, 1):
            note_para = Paragraph(
                f"<b>{i}.</b> {note}",
                ParagraphStyle('Note',
                               parent=normal_style,
                               fontSize=10,
                               leftIndent=20,
                               spaceAfter=8)
            )
            elements.append(note_para)
        
        # Build PDF with custom header/footer
        def add_page_decorations(canvas_obj, doc):
            PDFService._create_header(canvas_obj, doc, "Transport Coordination Plan",
                                     "For Bus Drivers & Coordinators")
            PDFService._create_footer(canvas_obj, doc)
        
        doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated transport PDF: {len(pdf_data)} bytes")
        return pdf_data
    
    @staticmethod
    def generate_preboda_pdf() -> bytes:
        """
        Generate pre-boda attendance report PDF for venue coordination.
        
        Returns:
            PDF file as bytes
        """
        logger.info("Generating pre-boda attendance PDF")
        
        from app.constants import PrebodaConfig
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=PDFService.PAGE_SIZE,
            rightMargin=PDFService.MARGIN,
            leftMargin=PDFService.MARGIN,
            topMargin=PDFService.MARGIN + 1.5 * inch,
            bottomMargin=PDFService.MARGIN
        )
        
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=PDFService.COLOR_SECONDARY,
            spaceAfter=10,
            spaceBefore=15
        )
        normal_style = styles['Normal']
        
        # Get pre-boda data
        preboda_data = AdminService.get_preboda_report()
        
        # Event Details Section
        elements.append(Paragraph("Event Details", heading_style))
        
        event_data = [
            ['Detail', 'Information'],
            ['Date', PrebodaConfig.DATE],
            ['Time', PrebodaConfig.TIME],
            ['Venue', PrebodaConfig.VENUE_NAME],
            ['Address', PrebodaConfig.ADDRESS],
        ]
        
        event_table = Table(event_data, colWidths=[2 * inch, 4.5 * inch])
        event_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY])
        ]))
        elements.append(event_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Attendance Summary
        elements.append(Paragraph("Attendance Summary", heading_style))
        
        summary_data = [
            ['Status', 'Groups', 'Total Adults'],
            ['Attending', str(preboda_data['attending_count']), str(preboda_data['total_adults_attending'])],
            ['Not Attending', str(preboda_data['not_attending_count']), '-'],
            ['Pending Response', str(preboda_data['pending_count']), '-'],
            ['Total Invited', str(preboda_data['total_invited']), '-'],
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5 * inch, 1.5 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (-1, 1), PDFService.COLOR_SUCCESS),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY])
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Attending Guests List
        if preboda_data['attending']:
            elements.append(PageBreak())
            elements.append(Paragraph("Confirmed Attending", heading_style))
            elements.append(Paragraph(
                f"Total Adults: <b>{preboda_data['total_adults_attending']}</b>",
                ParagraphStyle('Info', parent=normal_style, fontSize=11, textColor=PDFService.COLOR_SUCCESS)
            ))
            elements.append(Spacer(1, 0.1 * inch))
            
            guest_data = [['Guest Name', 'Phone', 'Adults', 'Language']]
            for guest in sorted(preboda_data['attending'], key=lambda x: x['name']):
                guest_data.append([
                    guest['name'],
                    guest['phone'] or '-',
                    str(guest['adults_count']),
                    guest['language'].upper()
                ])
            
            guest_table = Table(guest_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 1 * inch])
            guest_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_SUCCESS),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (3, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY])
            ]))
            elements.append(guest_table)
        
        # Dietary Restrictions for Pre-boda
        if preboda_data['allergen_summary']:
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph("Dietary Restrictions (Attending Guests)", heading_style))
            
            allergen_data = [['Restriction', 'Guests']]
            for allergen, guests in sorted(preboda_data['allergen_summary'].items()):
                allergen_data.append([allergen, ', '.join(guests)])
            
            allergen_table = Table(allergen_data, colWidths=[2 * inch, 4.5 * inch])
            allergen_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_ACCENT),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            elements.append(allergen_table)
        
        # Pending Responses
        if preboda_data['pending']:
            elements.append(PageBreak())
            elements.append(Paragraph("Pending Responses", heading_style))
            
            pending_data = [['Guest Name', 'Phone', 'Language']]
            for guest in sorted(preboda_data['pending'], key=lambda x: x['name']):
                pending_data.append([
                    guest['name'],
                    guest['phone'] or '-',
                    guest['language'].upper()
                ])
            
            pending_table = Table(pending_data, colWidths=[2.5 * inch, 2 * inch, 1.5 * inch])
            pending_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLOR_WARNING),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLOR_LIGHT_GRAY])
            ]))
            elements.append(pending_table)
        
        # Build PDF with custom header/footer
        def add_page_decorations(canvas_obj, doc):
            PDFService._create_header(canvas_obj, doc, "Pre-Boda Attendance Report",
                                     f"{PrebodaConfig.VENUE_NAME} - {PrebodaConfig.DATE}")
            PDFService._create_footer(canvas_obj, doc)
        
        doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated pre-boda PDF: {len(pdf_data)} bytes")
        return pdf_data

    @staticmethod
    def generate_combined_pdf() -> bytes:
        """
        Generate a combined PDF with all dietary, transport information and preboda.
        Useful for venue coordinators who need both.
        
        Returns:
            Combined PDF file as bytes
        """
        logger.info("Generating combined dietary & transport PDF")
        
        # For now, we'll generate both separately
        # In a future enhancement, we could merge them into one document
        dietary_pdf = PDFService.generate_dietary_pdf()
        transport_pdf = PDFService.generate_transport_pdf()
        preboda_pdf = PDFService.generate_preboda_pdf()
        
        # Note: Merging PDFs requires PyPDF2 or similar
        # For now, return dietary (primary concern for venue)
        return dietary_pdf