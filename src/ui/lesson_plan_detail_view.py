import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser,
    QLabel, QListWidget, QListWidgetItem, QScrollArea, QWidget,
    QDialogButtonBox, QApplication, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon # Added QIcon
from typing import Optional, List

from src.core.models import LessonPlan, LessonPlanFile, LessonPlanLink, Entity
from src.core.database_manager import DatabaseManager
import os # For file operations like getting file extension
from datetime import datetime # For date formatting in HTML, if not already available through lesson_plan object
from weasyprint import HTML, CSS # For PDF Generation

DEFAULT_PDF_CSS = """
    @page {
        size: A4;
        margin: 1.5cm;
    }
    body {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.6;
        color: #333;
    }
    h1 {
        font-size: 24pt;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    h2 {
        font-size: 16pt;
        color: #3498db;
        margin-top: 25px;
        margin-bottom: 10px;
        border-bottom: 1px solid #bdc3c7;
        padding-bottom: 5px;
    }
    h3 {
        font-size: 12pt;
        color: #2980b9;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    p {
        margin-bottom: 10px;
    }
    strong {
        font-weight: bold;
    }
    ul {
        padding-left: 20px;
        list-style-type: disc;
    }
    li {
        margin-bottom: 5px;
    }
    .section-block {
        margin-bottom: 20px;
        padding: 10px;
        border: 1px solid #ecf0f1;
        border-radius: 5px;
        background-color: #f9f9f9;
    }
    .section-block h2 { /* Target h2 inside section-block for different styling if needed */
        margin-top: 0;
    }
    .meta-info {
        margin-bottom: 15px;
        font-size: 9pt;
        color: #7f8c8d;
    }
    .meta-info p {
        margin-bottom: 3px;
    }
    a {
        color: #3498db;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
"""

class LessonPlanDetailView(QDialog):
    def __init__(self, lesson_plan: LessonPlan, db_manager: DatabaseManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.lesson_plan = lesson_plan
        self.db_manager = db_manager # Needed to resolve class names, potentially for file actions

        self.setWindowTitle(f"Detalhes do Plano: {self.lesson_plan.title}")
        self.setMinimumSize(700, 600)

        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        layout = QVBoxLayout(content_widget)

        # --- Título ---
        title_label = QLabel(f"<b>Título:</b> {self.lesson_plan.title}")
        title_label.setTextFormat(Qt.TextFormat.RichText)
        title_label.setStyleSheet("font-size: 18pt; margin-bottom: 10px;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # --- Data da Aula ---
        if self.lesson_plan.lesson_date:
            date_str = self.lesson_plan.lesson_date.strftime("%d/%m/%Y") if hasattr(self.lesson_plan.lesson_date, 'strftime') else str(self.lesson_plan.lesson_date)
            date_label = QLabel(f"<b>Data da Aula:</b> {date_str}")
            date_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(date_label)

        # --- Turmas Associadas ---
        if self.lesson_plan.class_ids:
            class_names = []
            for class_id in self.lesson_plan.class_ids:
                entity = self.db_manager.get_entity_by_id(class_id)
                class_names.append(entity.name if entity else f"ID: {class_id}")
            classes_label = QLabel(f"<b>Turma(s):</b> {', '.join(class_names)}")
            classes_label.setTextFormat(Qt.TextFormat.RichText)
            classes_label.setWordWrap(True)
            layout.addWidget(classes_label)

        layout.addSpacing(15)

        # --- Seções de Texto Rico ---
        sections = [
            ("Objetivos", self.lesson_plan.objectives),
            ("Conteúdo Programático", self.lesson_plan.program_content),
            ("Metodologia/Atividades", self.lesson_plan.methodology),
            ("Recursos (descrição textual)", self.lesson_plan.resources_text),
            ("Forma de Avaliação", self.lesson_plan.assessment_method),
        ]

        for title, content in sections:
            if content:
                section_label = QLabel(f"<h3>{title}</h3>")
                section_label.setTextFormat(Qt.TextFormat.RichText)
                layout.addWidget(section_label)
                content_browser = QTextBrowser()
                content_browser.setHtml(content)
                content_browser.setReadOnly(True)
                content_browser.setOpenExternalLinks(True) # For any links within rich text
                # Auto-adjust height based on content - this is tricky for QTextBrowser
                # For now, fixed or reasonable minimum height
                content_browser.setMinimumHeight(100)
                # content_browser.document().contentsChanged.connect(lambda: self.adjust_text_browser_height(content_browser))
                layout.addWidget(content_browser)
                layout.addSpacing(10)

        # --- Arquivos Anexados ---
        if self.lesson_plan.files:
            files_section_label = QLabel("<h3>Arquivos Anexados</h3>")
            files_section_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(files_section_label)
            self.files_list_widget = QListWidget()
            self.files_list_widget.setStyleSheet("QListWidget::item { padding: 5px; }")
            for file_obj in self.lesson_plan.files:
                item = QListWidgetItem(f"{file_obj.file_name} ({os.path.basename(file_obj.file_path)})") # Show original name and stored name/path
                item.setData(Qt.ItemDataRole.UserRole, file_obj) # Store the LessonPlanFile object
                # Add icon based on file type (simple example)
                # generic_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon) # Requires self.style()
                # item.setIcon(generic_icon) # Icon setting needs QListWidget to be a class member
                self.files_list_widget.addItem(item)
            self.files_list_widget.itemDoubleClicked.connect(self._open_selected_file)
            layout.addWidget(self.files_list_widget)
            # Add button to open file as well, for single click action if preferred
            open_file_button = QPushButton("Abrir Arquivo Selecionado")
            open_file_button.clicked.connect(self._open_selected_file_button_action)
            layout.addWidget(open_file_button)
            layout.addSpacing(10)

        # --- Links Externos ---
        if self.lesson_plan.links:
            links_section_label = QLabel("<h3>Links Externos</h3>")
            links_section_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(links_section_label)
            self.links_list_widget = QListWidget()
            self.links_list_widget.setStyleSheet("QListWidget::item { padding: 5px; }")
            for link_obj in self.lesson_plan.links:
                display_text = link_obj.title if link_obj.title else link_obj.url
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, link_obj) # Store the LessonPlanLink object
                self.links_list_widget.addItem(item)
            self.links_list_widget.itemDoubleClicked.connect(self._open_selected_link)
            layout.addWidget(self.links_list_widget)
            layout.addSpacing(10)

        # --- Botões de Ação ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.export_pdf_button = self.button_box.addButton("Exportar para PDF", QDialogButtonBox.ButtonRole.ActionRole)
        self.export_pdf_button.clicked.connect(self._handle_export_to_pdf)
        # TODO: Add Edit button here if desired
        # self.edit_button = self.button_box.addButton("Editar", QDialogButtonBox.ButtonRole.ActionRole)
        # self.edit_button.clicked.connect(self._handle_edit) # Requires _handle_edit method
        self.button_box.rejected.connect(self.reject) # Close button triggers reject
        main_layout.addWidget(self.button_box)

    def _handle_export_to_pdf(self):
        """Handles exporting the lesson plan details to a PDF file."""
        if not self.lesson_plan:
            return

        default_filename = f"{self.lesson_plan.title.replace(' ', '_')}.pdf"
        filePath, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar PDF",
            default_filename,
            "Arquivos PDF (*.pdf);;Todos os Arquivos (*)"
        )

        if filePath:
            try:
                html_content = self._generate_lesson_plan_html(self.lesson_plan)
                html_doc = HTML(string=html_content)
                css_doc = CSS(string=DEFAULT_PDF_CSS)
                html_doc.write_pdf(filePath, stylesheets=[css_doc])
                QMessageBox.information(self, "Sucesso", f"Plano de aula exportado para PDF em:\n{filePath}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Exportar PDF", f"Ocorreu um erro ao gerar o PDF:\n{str(e)}")

    def _generate_lesson_plan_html(self, lesson_plan: LessonPlan) -> str:
        """Constructs an HTML string for the lesson plan details."""
        html_parts = [
            f"<html><head><meta charset='UTF-8'><title>{lesson_plan.title}</title></head><body>",
            f"<h1>{lesson_plan.title}</h1>"
        ]

        # Meta Information Block
        meta_info_parts = ["<div class='meta-info'>"]
        if lesson_plan.lesson_date:
            date_str = lesson_plan.lesson_date.strftime("%d/%m/%Y") if hasattr(lesson_plan.lesson_date, 'strftime') else str(lesson_plan.lesson_date)
            meta_info_parts.append(f"<p><strong>Data da Aula:</strong> {date_str}</p>")

        if lesson_plan.class_ids:
            class_names = []
            for class_id in lesson_plan.class_ids:
                entity = self.db_manager.get_entity_by_id(class_id)
                class_names.append(entity.name if entity else f"ID: {class_id}")
            if class_names:
                 meta_info_parts.append(f"<p><strong>Turma(s):</strong> {', '.join(class_names)}</p>")
        meta_info_parts.append("</div>") # End meta-info
        html_parts.extend(meta_info_parts)

        # Rich Text Sections
        sections_data = [
            ("Objetivos", lesson_plan.objectives),
            ("Conteúdo Programático", lesson_plan.program_content),
            ("Metodologia/Atividades", lesson_plan.methodology),
            ("Recursos (descrição textual)", lesson_plan.resources_text),
            ("Forma de Avaliação", lesson_plan.assessment_method),
        ]

        for title, content_html in sections_data:
            if content_html and content_html.strip():
                # Assuming content_html is already valid HTML (e.g., from QTextEdit.toHtml())
                # Wrap it in a div for styling and to ensure block display
                html_parts.append(f"<div class='section-block'><h2>{title}</h2><div>{content_html}</div></div>")

        # Attached Files
        if lesson_plan.files:
            html_parts.append("<div class='section-block'><h2>Arquivos Anexados</h2><ul>")
            for file_obj in lesson_plan.files:
                # We typically don't make local file paths into clickable links in a PDF
                # unless they are web URLs or resolvable by all PDF viewers.
                # Displaying the name and original path is usually sufficient.
                html_parts.append(f"<li>{file_obj.file_name} (Caminho: {file_obj.file_path})</li>")
            html_parts.append("</ul></div>")

        # External Links
        if lesson_plan.links:
            html_parts.append("<div class='section-block'><h2>Links Externos</h2><ul>")
            for link_obj in lesson_plan.links:
                link_title = link_obj.title if link_obj.title else link_obj.url
                html_parts.append(f"<li><a href='{link_obj.url}'>{link_title}</a></li>")
            html_parts.append("</ul></div>")

        html_parts.append("</body></html>")
        return "".join(html_parts)

    def _open_selected_file(self, item: QListWidgetItem):
        file_obj: Optional[LessonPlanFile] = item.data(Qt.ItemDataRole.UserRole)
        if file_obj and file_obj.file_path:
            # Assuming file_path is an absolute path or resolvable relative path
            # For security, ensure the path is within an allowed directory if needed
            if not os.path.exists(file_obj.file_path):
                QMessageBox.warning(self, "Arquivo não encontrado", f"O arquivo {file_obj.file_path} não foi encontrado no sistema.")
                return
            url = QUrl.fromLocalFile(file_obj.file_path)
            QDesktopServices.openUrl(url)

    def _open_selected_file_button_action(self):
        selected_items = self.files_list_widget.selectedItems()
        if selected_items:
            self._open_selected_file(selected_items[0])
        else:
            QMessageBox.information(self, "Nenhum arquivo selecionado", "Por favor, selecione um arquivo da lista para abrir.")

    def _open_selected_link(self, item: QListWidgetItem):
        link_obj: Optional[LessonPlanLink] = item.data(Qt.ItemDataRole.UserRole)
        if link_obj and link_obj.url:
            QDesktopServices.openUrl(QUrl(link_obj.url))

    # def adjust_text_browser_height(self, browser: QTextBrowser):
    #     # This is a common request but tricky. QTextBrowser doesn't have a simple sizeHint based on content.
    #     # One common workaround is to set height based on document line count or approximate,
    #     # or use a fixed reasonable height as done currently.
    #     # For perfect dynamic height, more complex solutions might be needed (e.g., using document size).
    #     doc_height = browser.document().size().height()
    #     browser.setFixedHeight(int(doc_height) + 10) # Add some padding

if __name__ == '__main__':
    from datetime import datetime
    app = QApplication(sys.argv)

    # --- Mocking for testing ---
    class MockDBManager:
        def get_entity_by_id(self, entity_id: int) -> Optional[Entity]:
            if entity_id == 1: return Entity(id=1, name="Turma 10A", type="turma")
            if entity_id == 2: return Entity(id=2, name="Turma 10B", type="turma")
            return None

    mock_db = MockDBManager()
    sample_files_list = [
        LessonPlanFile(id=1, lesson_plan_id=1, file_name="Apresentacao_Aula1.pptx", file_path=os.path.abspath(__file__)), # Using this file path for testing existence
        LessonPlanFile(id=2, lesson_plan_id=1, file_name="Notas_Aula1.pdf", file_path="/path/to/fake/notas.pdf")
    ]
    sample_links_list = [
        LessonPlanLink(id=1, lesson_plan_id=1, url="https://www.wikipedia.org", title="Wikipedia"),
        LessonPlanLink(id=2, lesson_plan_id=1, url="https://www.google.com")
    ]
    test_lesson_plan = LessonPlan(
        id=1, teacher_id=1, title="Introdução à Programação Web",
        lesson_date=datetime.now(),
        class_ids=[1, 2],
        objectives="<p>Compreender os conceitos básicos de <b>HTML</b>, <i>CSS</i> e <u>JavaScript</u>.</p><ul><li>List item 1</li><li>List item 2</li></ul>",
        program_content="<p>O que é HTTP? Estrutura de uma página HTML. Seletores CSS. Manipulação do DOM com JS.</p>",
        methodology="Aula expositiva seguida de exercícios práticos.",
        resources_text="Livro X, Capítulos 1-3. Computador com acesso à internet e editor de texto.",
        assessment_method="Participação em aula e entrega dos exercícios.",
        files=sample_files_list,
        links=sample_links_list,
        created_at=datetime.now(), updated_at=datetime.now()
    )

    dialog = LessonPlanDetailView(lesson_plan=test_lesson_plan, db_manager=mock_db)
    dialog.show()
    sys.exit(app.exec())
