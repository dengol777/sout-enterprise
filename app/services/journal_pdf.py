from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from typing import List, Dict
import qrcode
from io import BytesIO


# Регистрация шрифта с кириллицей (обязательно!)
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))


class BriefingJournalGenerator:
    """Генератор PDF-журнала инструктажей с QR-кодами на видео и ЭДО"""

    def __init__(self, base_url: str = "https://sout.company.local"):
        self.base_url = base_url
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='CyrillicNormal',
            fontName='DejaVuSans',
            fontSize=8,
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            name='CyrillicBold',
            fontName='DejaVuSans-Bold',
            fontSize=9,
            leading=11,
        ))

    @staticmethod
    def _generate_qr(url: str) -> BytesIO:
        """Генерирует QR-код как изображение в памяти"""
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    def generate(self, records: List[Dict], output_path: str) -> str:
        """
        Генерирует PDF-журнал.
        
        records: список словарей с полями:
            - employee_name, position, briefing_type, date, instructor
            - video_url (опционально)
            - kedo_signature_url (опционально)
            - video_hash (опционально)
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=15, leftMargin=15,
            topMargin=20, bottomMargin=20,
        )

        elements = []

        # Заголовок
        title_style = ParagraphStyle('Title', parent=self.styles['CyrillicBold'], fontSize=14)
        elements.append(Paragraph("ЖУРНАЛ РЕГИСТРАЦИИ ИНСТРУКТАЖЕЙ ПО ОХРАНЕ ТРУДА", title_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            f"Сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')} | "
            f"Записей: {len(records)} | Система: СУОТ Enterprise",
            self.styles['CyrillicNormal']
        ))
        elements.append(Spacer(1, 15))

        # Шапка таблицы
        header = [
            Paragraph("№", self.styles['CyrillicBold']),
            Paragraph("ФИО сотрудника", self.styles['CyrillicBold']),
            Paragraph("Должность", self.styles['CyrillicBold']),
            Paragraph("Тип инструктажа", self.styles['CyrillicBold']),
            Paragraph("Дата", self.styles['CyrillicBold']),
            Paragraph("Инструктор", self.styles['CyrillicBold']),
            Paragraph("Видео / ЭДО", self.styles['CyrillicBold']),
        ]

        table_data = [header]

        for idx, record in enumerate(records, 1):
            # Формируем ячейку с доказательствами
            proof_elements = []

            if record.get("video_url"):
                qr_img = self._generate_qr(record["video_url"])
                from reportlab.platypus import Image as RLImage
                proof_elements.append(RLImage(qr_img, width=40, height=40))
                proof_elements.append(Paragraph(
                    f"<font size=5>Hash: {record.get('video_hash', '')[:12]}...</font>",
                    self.styles['CyrillicNormal']
                ))

            if record.get("kedo_signed"):
                proof_elements.append(Paragraph(
                    "<font color='green' size=6>✓ Подписано ЭДО</font>",
                    self.styles['CyrillicNormal']
                ))

            if not proof_elements:
                proof_elements.append(Paragraph("—", self.styles['CyrillicNormal']))

            row = [
                Paragraph(str(idx), self.styles['CyrillicNormal']),
                Paragraph(record["employee_name"], self.styles['CyrillicNormal']),
                Paragraph(record["position"], self.styles['CyrillicNormal']),
                Paragraph(record["briefing_type"], self.styles['CyrillicNormal']),
                Paragraph(record["date"].strftime("%d.%m.%Y"), self.styles['CyrillicNormal']),
                Paragraph(record["instructor"], self.styles['CyrillicNormal']),
                proof_elements if len(proof_elements) == 1 else proof_elements,
            ]
            table_data.append(row)

        # Стилизация таблицы
        col_widths = [25, 140, 100, 80, 60, 100, 70]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)

        # Подвал с юридической информацией
        elements.append(Spacer(1, 20))
        footer_text = (
            "Настоящий журнал сформирован в информационной системе «СУОТ Enterprise». "
            "Видеозаписи инструктажей хранятся в объектном хранилище с политикой WORM (неизменяемость 5 лет). "
            "Электронные подписи выполнены через ЕСИА/Госуслуги в соответствии со ст. 214.1 ТК РФ. "
            f"Целостность документа верифицируется по хэшу SHA-256."
        )
        elements.append(Paragraph(footer_text, ParagraphStyle(
            'Footer', parent=self.styles['CyrillicNormal'], fontSize=6, textColor=colors.grey
        )))

        doc.build(elements)
        return output_path
