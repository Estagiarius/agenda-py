from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QStackedWidget, QLabel, QComboBox, QPushButton,
                             QDateEdit, QFormLayout, QCompleter, QListWidgetItem,
                             QScrollArea, QDialog, QFileDialog, QMessageBox, QApplication) # Added
from PyQt6.QtCore import QDate, Qt, QStringListModel, QSize, QUrl # Added
from PyQt6.QtGui import QFont, QPixmap, QPainter, QImage, QDesktopServices # Added
from typing import Optional # Ensure Optional is imported
import os
import tempfile
import shutil # Added for _export_pdf

from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError # Added

from src.core.database_manager import DatabaseManager
from src.core.models import Entity # For type hinting
from src.core.report_generator import ReportGenerator # Added ReportGenerator


class PDFPreviewDialog(QDialog):
    def __init__(self, pdf_path: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.images = [] # To store PIL Image objects
        self.current_zoom_level = 1.0

        self.setWindowTitle("Pré-visualização do Relatório")
        # Good practice to set a default size for dialogs
        self.setMinimumSize(800, 600)
        # Allow maximizing, make it resizable
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint | Qt.WindowType.WindowMinimizeButtonHint)


        self._setup_ui()
        self._connect_signals()
        self.load_pdf_pages()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Scroll Area for PDF Pages
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.pages_container = QWidget()
        self.pages_layout = QVBoxLayout(self.pages_container)
        self.pages_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center pages
        self.scroll_area.setWidget(self.pages_container)
        main_layout.addWidget(self.scroll_area, 1) # Give scroll area more stretch factor

        # Buttons Layout
        buttons_widget = QWidget() # Create a widget to contain buttons
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(5,5,5,5) # Reduce margins for button area

        self.zoom_in_button = QPushButton("+ Zoom")
        self.zoom_in_button.setToolTip("Aumentar Zoom")
        buttons_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("- Zoom")
        self.zoom_out_button.setToolTip("Diminuir Zoom")
        buttons_layout.addWidget(self.zoom_out_button)

        buttons_layout.addStretch() # Add spacer to push next buttons to the right

        self.print_button = QPushButton("⎙ Imprimir")
        self.print_button.setToolTip("Abrir PDF no visualizador padrão para impressão")
        buttons_layout.addWidget(self.print_button)

        self.export_button = QPushButton("⇩ Exportar como PDF")
        self.export_button.setToolTip("Salvar o PDF em outro local")
        buttons_layout.addWidget(self.export_button)

        main_layout.addWidget(buttons_widget) # Add the buttons widget


    def load_pdf_pages(self):
        try:
            # Check if Poppler is installed by trying to get PDF info first
            # This might not be a perfect check but convert_from_path itself will raise if poppler is missing
            self.images = convert_from_path(self.pdf_path, dpi=150) # Use a reasonable DPI
            if not self.images:
                QMessageBox.critical(self, "Erro ao Carregar PDF", "Nenhuma página foi retornada ao converter o PDF.")
                self.reject() # Close dialog if no pages
                return
            self.display_pages()
        except PDFInfoNotInstalledError:
            QMessageBox.critical(self, "Erro de Dependência",
                                 "Poppler não encontrado. Por favor, instale Poppler e certifique-se de que está no PATH do sistema. "
                                 "Consulte NOTES_FOR_USER.md para instruções.")
            self.reject() # Close dialog
        except (PDFPageCountError, PDFSyntaxError) as e:
            QMessageBox.critical(self, "Erro ao Ler PDF", f"Não foi possível ler o arquivo PDF: {e}\nO arquivo pode estar corrompido.")
            self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Erro Inesperado", f"Ocorreu um erro inesperado ao carregar o PDF: {e}")
            self.reject()


    def _clear_pages_layout(self):
        while self.pages_layout.count():
            child = self.pages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def display_pages(self):
        self._clear_pages_layout() # Clear previous images

        if not self.images:
            return

        for pil_image in self.images:
            try:
                # Convert PIL image to QImage
                # Ensure image is in RGB format for QImage.Format.Format_RGB888
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")

                q_image = QImage(pil_image.tobytes("raw", "RGB"),
                                 pil_image.width,
                                 pil_image.height,
                                 QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)

                # Scale pixmap according to current zoom level
                scaled_width = int(pixmap.width() * self.current_zoom_level)
                # Cap max width to slightly less than scroll area viewport width to avoid horizontal scrollbar if possible
                # max_display_width = self.scroll_area.viewport().width() - 20 # 20 for margin/scrollbar
                # if scaled_width > max_display_width:
                #     scaled_width = max_display_width

                scaled_pixmap = pixmap.scaledToWidth(scaled_width, Qt.TransformationMode.SmoothTransformation)
                # scaled_pixmap = pixmap.scaled(
                #     scaled_width,
                #     int(pixmap.height() * (scaled_width / pixmap.width())), # Maintain aspect ratio
                #     Qt.AspectRatioMode.KeepAspectRatio,
                #     Qt.TransformationMode.SmoothTransformation
                # )

                image_label = QLabel()
                image_label.setPixmap(scaled_pixmap)
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center image in label
                self.pages_layout.addWidget(image_label)
            except Exception as e:
                print(f"Error displaying page: {e}")
                # Optionally add a placeholder or error message for this specific page
                error_label = QLabel(f"Erro ao exibir página: {e}")
                self.pages_layout.addWidget(error_label)


    def _connect_signals(self):
        self.export_button.clicked.connect(self._export_pdf)
        self.print_button.clicked.connect(self._print_pdf)
        self.zoom_in_button.clicked.connect(self._zoom_in)
        self.zoom_out_button.clicked.connect(self._zoom_out)

    def _export_pdf(self):
        # Suggest original filename
        original_filename = os.path.basename(self.pdf_path)
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar PDF como...", original_filename,
            "Arquivos PDF (*.pdf);;Todos os Arquivos (*)"
        )
        if save_path:
            try:
                shutil.copy(self.pdf_path, save_path)
                QMessageBox.information(self, "Sucesso", f"Relatório exportado para:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Exportar", f"Não foi possível exportar o PDF: {e}")

    def _print_pdf(self):
        # Using QDesktopServices to open the PDF with the default system viewer
        # The user can then print from their default PDF viewer.
        success = QDesktopServices.openUrl(QUrl.fromLocalFile(self.pdf_path))
        if not success:
            QMessageBox.warning(self, "Impressão",
                                "Não foi possível abrir o visualizador de PDF padrão. "
                                "Verifique se você tem um visualizador de PDF instalado.")

    def _zoom_in(self):
        self.current_zoom_level *= 1.2
        self.display_pages()

    def _zoom_out(self):
        if self.current_zoom_level / 1.2 < 0.1: # Prevent zooming out too much
            return
        self.current_zoom_level /= 1.2
        self.display_pages()

    def resizeEvent(self, event):
        # Optional: Debounce or delay redisplay on resize for performance, though usually not critical
        # For now, just redisplay pages to adjust to new viewport width if needed (if scaling to viewport)
        # self.display_pages() # Only if scaling is relative to viewport, not fixed zoom
        super().resizeEvent(event)


class ReportsView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setObjectName("ReportsView") # For styling or identification

        self.setWindowTitle("Visualização de Relatórios")

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) # Add some padding

        # Report selection area
        self.report_list_widget = QListWidget()
        self.report_list_widget.setFixedWidth(250) # Give it a reasonable width
        self.report_list_widget.setFont(QFont("Arial", 11)) # Slightly larger font

        # Add report types
        self.report_list_widget.addItem("Boletim Individual do Aluno")
        self.report_list_widget.addItem("Desempenho Geral da Turma")
        self.report_list_widget.addItem("Lista de Frequência da Turma")

        main_layout.addWidget(self.report_list_widget)

        # Parameter forms area
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create and add forms to stacked widget
        self.boletim_form = self._create_boletim_form()
        self.desempenho_form = self._create_desempenho_form()
        self.frequencia_form = self._create_frequencia_form()

        self.stacked_widget.addWidget(self.boletim_form)
        self.stacked_widget.addWidget(self.desempenho_form)
        self.stacked_widget.addWidget(self.frequencia_form)

        # Connect report selection to form display
        self.report_list_widget.currentItemChanged.connect(self._on_report_selected)

        # Initial data loading
        self._load_initial_data()

        # Set initial selection
        if self.report_list_widget.count() > 0:
            self.report_list_widget.setCurrentRow(0)

    def _create_boletim_form(self) -> QWidget:
        form_widget = QWidget()
        layout = QFormLayout(form_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        self.class_combo_boletim = QComboBox()
        self.class_combo_boletim.setObjectName("class_combo_boletim")
        layout.addRow(QLabel("Turma:"), self.class_combo_boletim)

        self.student_combo_boletim = QComboBox()
        self.student_combo_boletim.setObjectName("student_combo_boletim")
        self.student_combo_boletim.setEditable(True) # For completer

        # Add completer for searchability
        self.student_completer = QCompleter()
        self.student_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # self.student_completer.setFilterMode(Qt.MatchFlag.MatchContains) # Requires a proxy model for QComboBox
        self.student_combo_boletim.setCompleter(self.student_completer)
        # Model for completer will be set in _populate_students_for_boletim

        layout.addRow(QLabel("Aluno:"), self.student_combo_boletim)

        self.start_date_boletim = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_boletim.setObjectName("start_date_boletim")
        self.start_date_boletim.setCalendarPopup(True)
        layout.addRow(QLabel("Data Início:"), self.start_date_boletim)

        self.end_date_boletim = QDateEdit(QDate.currentDate())
        self.end_date_boletim.setObjectName("end_date_boletim")
        self.end_date_boletim.setCalendarPopup(True)
        layout.addRow(QLabel("Data Fim:"), self.end_date_boletim)

        self.generate_boletim_button = QPushButton("Gerar Boletim")
        self.generate_boletim_button.setObjectName("generate_boletim_button")
        self.generate_boletim_button.clicked.connect(self._handle_generate_boletim)
        layout.addRow(self.generate_boletim_button)

        # Connect class selection to student population
        self.class_combo_boletim.currentIndexChanged.connect(self._populate_students_for_boletim)

        return form_widget

    def _create_desempenho_form(self) -> QWidget:
        form_widget = QWidget()
        layout = QFormLayout(form_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        self.class_combo_desempenho = QComboBox()
        self.class_combo_desempenho.setObjectName("class_combo_desempenho")
        layout.addRow(QLabel("Turma:"), self.class_combo_desempenho)

        self.start_date_desempenho = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_desempenho.setObjectName("start_date_desempenho")
        self.start_date_desempenho.setCalendarPopup(True)
        layout.addRow(QLabel("Data Início:"), self.start_date_desempenho)

        self.end_date_desempenho = QDateEdit(QDate.currentDate())
        self.end_date_desempenho.setObjectName("end_date_desempenho")
        self.end_date_desempenho.setCalendarPopup(True)
        layout.addRow(QLabel("Data Fim:"), self.end_date_desempenho)

        self.assessment_combo_desempenho = QComboBox()
        self.assessment_combo_desempenho.setObjectName("assessment_combo_desempenho")
        self.assessment_combo_desempenho.addItem("Todos (Geral)", None) # Default option
        # TODO: Populate with QuizConfig names later
        layout.addRow(QLabel("Avaliação (Opcional):"), self.assessment_combo_desempenho)


        self.generate_desempenho_button = QPushButton("Gerar Relatório de Desempenho")
        self.generate_desempenho_button.setObjectName("generate_desempenho_button")
        self.generate_desempenho_button.clicked.connect(self._handle_generate_desempenho)
        layout.addRow(self.generate_desempenho_button)

        return form_widget

    def _create_frequencia_form(self) -> QWidget:
        form_widget = QWidget()
        layout = QFormLayout(form_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        self.class_combo_frequencia = QComboBox()
        self.class_combo_frequencia.setObjectName("class_combo_frequencia")
        layout.addRow(QLabel("Turma:"), self.class_combo_frequencia)

        self.start_date_frequencia = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_frequencia.setObjectName("start_date_frequencia")
        self.start_date_frequencia.setCalendarPopup(True)
        layout.addRow(QLabel("Data Início:"), self.start_date_frequencia)

        self.end_date_frequencia = QDateEdit(QDate.currentDate())
        self.end_date_frequencia.setObjectName("end_date_frequencia")
        self.end_date_frequencia.setCalendarPopup(True)
        layout.addRow(QLabel("Data Fim:"), self.end_date_frequencia)

        self.generate_frequencia_button = QPushButton("Gerar Lista de Frequência")
        self.generate_frequencia_button.setObjectName("generate_frequencia_button")
        self.generate_frequencia_button.clicked.connect(self._handle_generate_frequencia)
        layout.addRow(self.generate_frequencia_button)

        return form_widget

    def _on_report_selected(self, current_item: QListWidgetItem, previous_item: Optional[QListWidgetItem]):
        if current_item:
            row = self.report_list_widget.row(current_item)
            self.stacked_widget.setCurrentIndex(row)

    def _load_initial_data(self):
        classes = self.db_manager.get_classes() # type: List[Entity]

        # Populate class combos
        class_combos = [
            self.class_combo_boletim,
            self.class_combo_desempenho,
            self.class_combo_frequencia
        ]
        for combo in class_combos:
            combo.clear()
            combo.addItem("Selecione uma turma...", None) # Placeholder
            for class_entity in classes:
                if class_entity.id is not None: # Should always have an ID from DB
                    combo.addItem(class_entity.name, class_entity.id)

        # Populate students for boletim form if a class is already selected (e.g., first one)
        self._populate_students_for_boletim()

        # TODO: Populate assessment_combo_desempenho
        # quiz_configs = self.db_manager.get_all_quiz_configs()
        # self.assessment_combo_desempenho.clear()
        # self.assessment_combo_desempenho.addItem("Todos (Geral)", None)
        # for qc in quiz_configs:
        #     if qc.id is not None:
        #         self.assessment_combo_desempenho.addItem(qc.name if qc.name else f"Quiz ID {qc.id}", qc.id)


    def _populate_students_for_boletim(self):
        self.student_combo_boletim.clear()
        current_class_id = self.class_combo_boletim.currentData()

        student_names = [] # For QCompleter

        if current_class_id is not None:
            students = self.db_manager.get_students_by_class(current_class_id) # type: List[Entity]
            if not students:
                self.student_combo_boletim.addItem("Nenhum aluno nesta turma", None)
            else:
                self.student_combo_boletim.addItem("Selecione um aluno...", None)
                for student in students:
                    if student.id is not None:
                        self.student_combo_boletim.addItem(student.name, student.id)
                        student_names.append(student.name)
        else:
            self.student_combo_boletim.addItem("Selecione uma turma primeiro", None)

        # Update completer model
        # Using a QStringListModel for the completer based on the current items in the combo box
        student_names_model = QStringListModel(student_names)
        self.student_completer.setModel(student_names_model)


    def _handle_generate_boletim(self):
        class_id = self.class_combo_boletim.currentData()
        student_id = self.student_combo_boletim.currentData()
        start_date_val = self.start_date_boletim.date().toPyDate()
        end_date_val = self.end_date_boletim.date().toPyDate()

        if not class_id or not student_id:
            print("Por favor, selecione Turma e Aluno.")
            # Consider showing a QMessageBox here in a real app
            return

        student_entity = self.db_manager.get_entity_by_id(student_id)
        class_entity = self.db_manager.get_entity_by_id(class_id)

        if not student_entity or not class_entity:
            QMessageBox.warning(self, "Erro de Dados", "Não foi possível encontrar a entidade do aluno ou da turma no banco de dados.")
            return

        report_generator = ReportGenerator(self.db_manager)
        temp_dir = tempfile.gettempdir()
        # Sanitize filename a bit more
        s_name_part = "".join(c if c.isalnum() else "_" for c in student_entity.name[:30])
        c_name_part = "".join(c if c.isalnum() else "_" for c in class_entity.name[:20])
        file_name = f"boletim_{s_name_part}_{c_name_part}_{start_date_val.strftime('%Y%m%d')}.pdf"
        file_path = os.path.join(temp_dir, file_name)


        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        success = report_generator.generate_student_report_card_pdf(
            student_entity, class_entity, start_date_val, end_date_val, file_path
        )
        QApplication.restoreOverrideCursor()

        if success and os.path.exists(file_path):
            preview_dialog = PDFPreviewDialog(file_path, self)
            preview_dialog.exec()
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar o relatório PDF em:\n{file_path}")


    def _handle_generate_desempenho(self):
        class_id = self.class_combo_desempenho.currentData()
        start_date_val = self.start_date_desempenho.date().toPyDate()
        end_date_val = self.end_date_desempenho.date().toPyDate()
        assessment_id = self.assessment_combo_desempenho.currentData() # May be None

        if not class_id:
            print("Por favor, selecione uma Turma.")
            return

        class_entity = self.db_manager.get_entity_by_id(class_id)
        if not class_entity:
            QMessageBox.warning(self, "Erro de Dados", "Não foi possível encontrar a entidade da turma no banco de dados.")
            return

        report_generator = ReportGenerator(self.db_manager)
        temp_dir = tempfile.gettempdir()
        c_name_part = "".join(c if c.isalnum() else "_" for c in class_entity.name[:30])
        file_name = f"desempenho_turma_{c_name_part}_{start_date_val.strftime('%Y%m%d')}.pdf"
        file_path = os.path.join(temp_dir, file_name)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        success = report_generator.generate_class_performance_pdf(
            class_entity, start_date_val, end_date_val, assessment_id, file_path
        )
        QApplication.restoreOverrideCursor()

        if success and os.path.exists(file_path):
            preview_dialog = PDFPreviewDialog(file_path, self)
            preview_dialog.exec()
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar o relatório PDF em:\n{file_path}")


    def _handle_generate_frequencia(self):
        class_id = self.class_combo_frequencia.currentData()
        start_date_val = self.start_date_frequencia.date().toPyDate()
        end_date_val = self.end_date_frequencia.date().toPyDate()

        if not class_id:
            print("Por favor, selecione uma Turma.")
            return

        class_entity = self.db_manager.get_entity_by_id(class_id)
        if not class_entity:
            QMessageBox.warning(self, "Erro de Dados", "Não foi possível encontrar a entidade da turma no banco de dados.")
            return

        report_generator = ReportGenerator(self.db_manager)
        temp_dir = tempfile.gettempdir()
        c_name_part = "".join(c if c.isalnum() else "_" for c in class_entity.name[:30])
        file_name = f"frequencia_turma_{c_name_part}_{start_date_val.strftime('%Y%m%d')}.pdf"
        file_path = os.path.join(temp_dir, file_name)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        success = report_generator.generate_class_attendance_pdf(
            class_entity, start_date_val, end_date_val, file_path
        )
        QApplication.restoreOverrideCursor()

        if success and os.path.exists(file_path):
            preview_dialog = PDFPreviewDialog(file_path, self)
            preview_dialog.exec()
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar o relatório PDF em:\n{file_path}")


# Optional: For testing this view directly
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    # Dummy DatabaseManager for testing UI structure
    class DummyDBManager:
        def get_classes(self):
            print("DummyDBManager: get_classes called")
            c1 = Entity(id=1, name="Turma A", type="turma")
            c2 = Entity(id=2, name="Turma B", type="turma")
            return [c1, c2]

        def get_students_by_class(self, class_id):
            print(f"DummyDBManager: get_students_by_class called for class_id {class_id}")
            if class_id == 1:
                s1 = Entity(id=101, name="João Silva (Turma A)", type="aluno", details_json={"turma_id": 1})
                s2 = Entity(id=102, name="Maria Souza (Turma A)", type="aluno", details_json={"turma_id": 1})
                return [s1, s2]
            elif class_id == 2:
                s3 = Entity(id=201, name="Pedro Costa (Turma B)", type="aluno", details_json={"turma_id": 2})
                return [s3]
            return []

        def get_all_quiz_configs(self):
            print("DummyDBManager: get_all_quiz_configs called")
            return []


    app = QApplication(sys.argv)
    # Apply a basic style for better visuals if desired
    # app.setStyleSheet("""
    #     QWidget { font-size: 10pt; }
    #     QPushButton { padding: 5px; }
    #     QListWidget { padding: 5px; }
    #     QComboBox, QDateEdit { padding: 3px; }
    # """)

    db_manager_instance = DummyDBManager()
    main_view = ReportsView(db_manager_instance) # type: ignore # db_manager_instance is a Dummy
    main_view.show()
    sys.exit(app.exec())

```
