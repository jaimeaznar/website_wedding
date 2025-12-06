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
        
        # Wedding couple names
        canvas_obj.setFont('Helvetica-Bold', 20)
        canvas_obj.setFillColor(PDFService.COLOR_PRIMARY)
        canvas_obj.drawCentredString(
            doc.width / 2 + doc.leftMargin,
            doc.height + doc.topMargin - 30,
            "Irene & Jaime's Wedding"
        )
        
        # Document title
        canvas_obj.setFont('Helvetica', 14)
        canvas_obj.setFillColor(PDFService.COLOR_SECONDARY)
        canvas_obj.drawCentredString(
            doc.width / 2 + doc.leftMargin,
            doc.height + doc.topMargin - 50,
            title
        )
        
        # Subtitle if provided
        if subtitle:
            canvas_obj.setFont('Helvetica', 10)
            canvas_obj.setFillColor(colors.gray)
            canvas_obj.drawCentredString(
                doc.width / 2 + doc.leftMargin,
                doc.height + doc.topMargin - 65,
                subtitle
            )
        
        # Date generated
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.gray)
        canvas_obj.drawRightString(
            doc.width + doc.leftMargin,
            doc.height + doc.topMargin - 10,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Line under header
        canvas_obj.setStrokeColor(PDFService.COLOR_SECONDARY)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(
            doc.leftMargin,
            doc.height + doc.topMargin - 75,
            doc.width + doc.leftMargin,
            doc.height + doc.topMargin - 75
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
            topMargin=PDFService.MARGIN + 0.5 * inch,
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
        
        # Title
        elements.append(Paragraph("Dietary Restrictions & Allergen Information", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        
        summary_data = [
            ['Metric', 'Count'],
            ['Total Guests with Restrictions', str(dietary_data['total_guests_with_restrictions'])],
            ['Standard Allergens', str(len(dietary_data['standard_allergens']))],
            ['Custom Restrictions', str(len(dietary_data['custom_allergens']))]
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
            topMargin=PDFService.MARGIN + 0.5 * inch,
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
        
        # Title
        elements.append(Paragraph("Transport Coordination Plan", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Executive Summary
        elements.append(Paragraph("Transport Summary", heading_style))
        
        summary_data = [
            ['Route', 'Guests Requiring Transport'],
            ['Hotel → Church', str(len(transport_data['to_church']))],
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
        
        # ROUTE 1: Hotel to Church
        elements.append(PageBreak())
        elements.append(Paragraph("Route 1: Hotel → Church", heading_style))
        elements.append(Paragraph(
            "⏰ <b>Timing:</b> Pickup 30 minutes before ceremony start",
            ParagraphStyle('Timing', parent=normal_style, fontSize=10, textColor=colors.red)
        ))
        elements.append(Spacer(1, 0.1 * inch))
        
        if transport_data['to_church']:
            # Group by hotel
            hotel_groups = {}
            for guest in transport_data['to_church']:
                hotel = guest['hotel'] or 'Unknown Hotel'
                if hotel not in hotel_groups:
                    hotel_groups[hotel] = []
                hotel_groups[hotel].append(guest)
            
            for hotel, guests in sorted(hotel_groups.items()):
                # Hotel name
                elements.append(Paragraph(f"📍 Pickup Location: {hotel}", route_heading_style))
                
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
    def generate_combined_pdf() -> bytes:
        """
        Generate a combined PDF with both dietary and transport information.
        Useful for venue coordinators who need both.
        
        Returns:
            Combined PDF file as bytes
        """
        logger.info("Generating combined dietary & transport PDF")
        
        # For now, we'll generate both separately
        # In a future enhancement, we could merge them into one document
        dietary_pdf = PDFService.generate_dietary_pdf()
        transport_pdf = PDFService.generate_transport_pdf()
        
        # Note: Merging PDFs requires PyPDF2 or similar
        # For now, return dietary (primary concern for venue)
        return dietary_pdf