"""Certificate PDF generation using ReportLab."""
import io
import uuid
from datetime import date, timedelta
from typing import Optional

from django.core.files.base import ContentFile
from django.utils import timezone

from courses.models import Certificate, Enrollment


def _build_pdf(certificate):
    """Render the certificate PDF bytes using ReportLab."""
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors

    enrollment = certificate.enrollment
    student = enrollment.student
    course = enrollment.course
    student_name = student.get_full_name().strip() or student.username

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    width, height = landscape(A4)

    c.setStrokeColor(colors.HexColor('#1f3a93'))
    c.setLineWidth(8)
    c.rect(15 * mm, 15 * mm, width - 30 * mm, height - 30 * mm)
    c.setLineWidth(1)
    c.rect(22 * mm, 22 * mm, width - 44 * mm, height - 44 * mm)

    c.setFillColor(colors.HexColor('#1f3a93'))
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(width / 2, height - 55 * mm, 'Certificate of Completion')

    c.setFillColor(colors.black)
    c.setFont('Helvetica', 16)
    c.drawCentredString(width / 2, height - 75 * mm, 'This is to certify that')

    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(width / 2, height - 95 * mm, student_name)

    c.setFont('Helvetica', 16)
    c.drawCentredString(width / 2, height - 115 * mm, 'has successfully completed the course')

    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(width / 2, height - 135 * mm, course.title)

    c.setFont('Helvetica', 12)
    issued_str = certificate.issued_at.strftime('%d %b %Y') if certificate.issued_at else timezone.now().strftime('%d %b %Y')
    c.drawString(40 * mm, 40 * mm, f"Issued on: {issued_str}")
    c.drawRightString(width - 40 * mm, 40 * mm, f"Certificate ID: {certificate.certificate_id}")

    if certificate.expiry_date:
        c.drawCentredString(width / 2, 32 * mm, f"Valid until: {certificate.expiry_date.strftime('%d %b %Y')}")

    issuer = certificate.issued_by.name if certificate.issued_by else 'Certify-U'
    c.setFont('Helvetica-Oblique', 11)
    c.drawCentredString(width / 2, 25 * mm, f"Issued by {issuer}")

    c.showPage()
    c.save()
    return buf.getvalue()


def issue_certificate(enrollment: Enrollment, *, expiry_years: Optional[int] = None, issued_by=None) -> Certificate:
    """Create or refresh a Certificate for a completed enrollment, generating its PDF."""
    certificate, _ = Certificate.objects.get_or_create(
        enrollment=enrollment,
        defaults={
            'certificate_id': f"CU-{uuid.uuid4().hex[:10].upper()}",
        },
    )

    if expiry_years:
        certificate.expiry_date = date.today() + timedelta(days=365 * expiry_years)
    if issued_by is not None:
        certificate.issued_by = issued_by

    pdf_bytes = _build_pdf(certificate)
    filename = f"{certificate.certificate_id}.pdf"
    certificate.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)

    if hasattr(certificate.pdf_file, 'url'):
        try:
            certificate.download_url = certificate.pdf_file.url
        except Exception:
            pass

    certificate.save()
    return certificate
