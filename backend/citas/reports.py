from django.http import HttpResponse
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def generate_excel_report(queryset):
    """Generates an Excel file from a queryset of Cita objects."""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=citas.xlsx'
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Citas'

    columns = ['Nombre', 'Fecha', 'Servicio', 'Confirmado', 'Estado']
    sheet.append(columns)

    for cita in queryset:
        sheet.append([
            cita.nombre,
            cita.fecha.strftime('%Y-%m-%d %H:%M'),
            ", ".join([s.nombre for s in cita.servicios.all()]),
            'Sí' if cita.confirmado else 'No',
            cita.estado
        ])

    workbook.save(response)
    return response


def generate_pdf_report(queryset):
    """Generates a PDF file from a queryset of Cita objects."""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=citas.pdf'

    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Reporte de Citas", styles['h1']), Spacer(1, 0.2 * inch)]

    for cita in queryset:
        story.append(Paragraph(f"<b>Nombre:</b> {cita.nombre}", styles['Normal']))
        story.append(Paragraph(f"<b>Fecha:</b> {cita.fecha.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"<b>Servicio:</b> {cita.servicio.nombre}", styles['Normal']))
        story.append(Paragraph(f"<b>Confirmado:</b> {'Sí' if cita.confirmado else 'No'}", styles['Normal']))
        story.append(Paragraph(f"<b>Estado:</b> {cita.estado}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
    return response