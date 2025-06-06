from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from datetime import date, datetime
from typing import List, Optional, Dict, Any
import os

from src.core.database_manager import DatabaseManager
from src.core.models import Entity, QuizAttempt, AttendanceRecord, QuizConfig

class ReportGenerator:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(name='SchoolTitle',
                                       fontName='Helvetica-Bold',
                                       fontSize=18,
                                       alignment=TA_CENTER,
                                       spaceBottom=0.5*cm))
        self.styles.add(ParagraphStyle(name='ReportTitle',
                                       fontName='Helvetica-Bold',
                                       fontSize=16,
                                       alignment=TA_CENTER,
                                       spaceBottom=0.5*cm))
        self.styles.add(ParagraphStyle(name='SectionTitle',
                                       fontName='Helvetica-Bold',
                                       fontSize=14,
                                       alignment=TA_LEFT,
                                       spaceBefore=0.5*cm,
                                       spaceBottom=0.3*cm))
        self.styles.add(ParagraphStyle(name='NormalWithSpace',
                                       parent=self.styles['Normal'],
                                       spaceBottom=0.2*cm))

    def _get_school_name(self) -> str:
        return self.db_manager.get_setting('school_name', 'Nome da Escola Padrão')

    def _common_table_style(self) -> TableStyle:
        return TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('ALIGN', (0,1), (-1,-1), 'LEFT'), # Data cells left aligned
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ])

    def _common_header(self, story: List[Any], report_specific_title: str, student_name: Optional[str] = None, class_name: Optional[str] = None, period_start: Optional[date] = None, period_end: Optional[date] = None):
        story.append(Paragraph(self._get_school_name(), self.styles['SchoolTitle']))
        story.append(Paragraph(report_specific_title, self.styles['ReportTitle']))

        if student_name:
            story.append(Paragraph(f"Aluno: {student_name}", self.styles['NormalWithSpace']))
        if class_name:
            story.append(Paragraph(f"Turma: {class_name}", self.styles['NormalWithSpace']))
        if period_start and period_end:
            period_str = f"Período: {period_start.strftime('%d/%m/%Y')} a {period_end.strftime('%d/%m/%Y')}"
            story.append(Paragraph(period_str, self.styles['NormalWithSpace']))
        story.append(Spacer(1, 0.5*cm))


    def generate_student_report_card_pdf(self, student: Entity, class_entity: Entity,
                                         period_start: date, period_end: date, file_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    leftMargin=1.5*cm, rightMargin=1.5*cm,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm)
            story: List[Any] = []

            # Header
            self._common_header(story,
                                "Boletim Individual do Aluno",
                                student_name=student.name,
                                class_name=class_entity.name,
                                period_start=period_start,
                                period_end=period_end)

            # Grades Section
            grades = self.db_manager.get_student_grades(student.id, period_start, period_end)
            story.append(Paragraph("Desempenho Acadêmico", self.styles['SectionTitle']))
            if grades:
                grades_data = [["Avaliação", "Data", "Nota", "Total"]]
                for attempt in grades:
                    quiz_config = self.db_manager.get_quiz_config_by_id(attempt.quiz_config_id)
                    quiz_name = quiz_config.name if quiz_config and quiz_config.name else f"Avaliação ID {attempt.quiz_config_id}"
                    grades_data.append([
                        Paragraph(quiz_name, self.styles['Normal']),
                        attempt.attempted_at.strftime('%d/%m/%Y %H:%M') if attempt.attempted_at else 'N/A',
                        str(attempt.score),
                        str(attempt.total_questions)
                    ])

                grades_table = Table(grades_data, colWidths=[7*cm, 4*cm, 2*cm, 2*cm]) # Adjusted widths
                grades_table.setStyle(self._common_table_style())
                story.append(grades_table)
            else:
                story.append(Paragraph("Nenhuma avaliação registrada neste período.", self.styles['Normal']))
            story.append(Spacer(1, 0.5*cm))

            # Attendance Section
            attendance_records = self.db_manager.get_student_attendance(student.id, period_start, period_end)
            story.append(Paragraph("Frequência", self.styles['SectionTitle']))
            if attendance_records:
                attendance_data = [["Data", "Status", "Observações"]]
                for record in attendance_records:
                    attendance_data.append([
                        record.date.strftime('%d/%m/%Y'),
                        record.status,
                        Paragraph(record.notes or '', self.styles['Normal'])
                    ])

                attendance_table = Table(attendance_data, colWidths=[3*cm, 3*cm, 9*cm]) # Adjusted widths
                attendance_table.setStyle(self._common_table_style())
                story.append(attendance_table)
            else:
                story.append(Paragraph("Nenhum registro de frequência neste período.", self.styles['Normal']))

            doc.build(story)
            return True
        except Exception as e:
            print(f"Erro ao gerar PDF do boletim do aluno: {e}")
            return False

    def generate_class_performance_pdf(self, class_entity: Entity,
                                       period_start: date, period_end: date,
                                       assessment_id: Optional[int], file_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    leftMargin=1.5*cm, rightMargin=1.5*cm,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm)
            story: List[Any] = []

            report_title = "Desempenho Geral da Turma"
            if assessment_id:
                quiz_config = self.db_manager.get_quiz_config_by_id(assessment_id)
                if quiz_config and quiz_config.name:
                    report_title += f" - {quiz_config.name}"
                elif quiz_config:
                     report_title += f" - Avaliação ID {quiz_config.id}"


            self._common_header(story, report_title, class_name=class_entity.name, period_start=period_start, period_end=period_end)

            class_performance_data = self.db_manager.get_class_performance(class_entity.id, period_start, period_end)

            story.append(Paragraph("Desempenho dos Alunos", self.styles['SectionTitle']))

            if not class_performance_data:
                story.append(Paragraph("Nenhum dado de desempenho encontrado para esta turma/período.", self.styles['Normal']))
            else:
                table_data = [["Aluno", "Média de Notas", "Avaliações Realizadas"]]
                for perf_item in class_performance_data:
                    # If a specific assessment is selected, we might want to filter attempts_details
                    # For now, average_score and total_attempts are based on the period.
                    # If assessment_id is present, get_class_performance would need to be adapted
                    # or we filter here. The current get_class_performance does not use assessment_id.
                    # This part might need refinement based on how assessment_id should precisely filter.
                    table_data.append([
                        Paragraph(perf_item['student_name'], self.styles['Normal']),
                        f"{perf_item['average_score']:.2f}",
                        str(perf_item['total_attempts'])
                    ])

                performance_table = Table(table_data, colWidths=[8*cm, 4*cm, 5*cm])
                performance_table.setStyle(self._common_table_style())
                story.append(performance_table)

            # TODO (Advanced): Add charts for class performance visualization

            doc.build(story)
            return True
        except Exception as e:
            print(f"Erro ao gerar PDF de desempenho da turma: {e}")
            return False

    def generate_class_attendance_pdf(self, class_entity: Entity,
                                      period_start: date, period_end: date, file_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    leftMargin=1.5*cm, rightMargin=1.5*cm,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm)
            story: List[Any] = []

            self._common_header(story, "Lista de Frequência da Turma", class_name=class_entity.name, period_start=period_start, period_end=period_end)

            class_attendance_summary = self.db_manager.get_class_attendance_summary(class_entity.id, period_start, period_end)
            story.append(Paragraph("Resumo de Frequência dos Alunos", self.styles['SectionTitle']))

            if not class_attendance_summary:
                story.append(Paragraph("Nenhum dado de frequência encontrado para esta turma/período.", self.styles['Normal']))
            else:
                table_data = [["Aluno", "Presente(s)", "Falta(s)", "Falta(s) Justif.", "Atraso(s)", "Outros"]]
                for summary_item in class_attendance_summary:
                    other_statuses_str = ", ".join([f"{k}: {v}" for k,v in summary_item['other_statuses'].items()])
                    table_data.append([
                        Paragraph(summary_item['student_name'], self.styles['Normal']),
                        str(summary_item['present_count']),
                        str(summary_item['absent_count']),
                        str(summary_item['justified_count']),
                        str(summary_item['late_count']),
                        Paragraph(other_statuses_str if other_statuses_str else "-", self.styles['Normal'])
                    ])

                # Adjust colWidths as needed
                attendance_summary_table = Table(table_data, colWidths=[6*cm, 2.5*cm, 2.5*cm, 3*cm, 2.5*cm, 3.5*cm])
                attendance_summary_table.setStyle(self._common_table_style())
                story.append(attendance_summary_table)

            doc.build(story)
            return True
        except Exception as e:
            print(f"Erro ao gerar PDF de frequência da turma: {e}")
            return False

```
