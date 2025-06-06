import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont

from src.core.database_manager import DatabaseManager
from src.core.models import StudentGroup, Assessment
from src.ui.grades_entry_view import GradesEntryView # Import for later use (navigation)

class AssessmentItemWidget(QFrame):
    """Custom widget to display an assessment item with a 'Lançar Notas' button."""
    enter_grades_requested = pyqtSignal(int) # Emits assessment_id

    def __init__(self, assessment: Assessment, parent=None):
        super().__init__(parent)
        self.assessment = assessment
        self.setFrameShape(QFrame.Shape.Panel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setContentsMargins(8, 8, 8, 8)
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setSpacing(10)

        title_text = f"<b>{self.assessment.title}</b>"
        if self.assessment.date:
            title_text += f" - <i>{self.assessment.date.strftime('%d/%m/%Y')}</i>"
        else:
            title_text += " - <i>Sem data</i>"
        title_text += f" (Max: {self.assessment.max_value:.2f})"

        title_label = QLabel(title_text)
        title_label.setWordWrap(True)
        layout.addWidget(title_label, 1) # Stretch factor for title

        self.enter_grades_button = QPushButton("✍️ Lançar Notas")
        self.enter_grades_button.setIconSize(QSize(16,16)) # Example, if using an icon
        self.enter_grades_button.setToolTip(f"Lançar notas para {self.assessment.title}")
        self.enter_grades_button.clicked.connect(self._emit_enter_grades_signal)
        layout.addWidget(self.enter_grades_button)

        # TODO: Add Edit/Delete buttons for the assessment itself later
        # self.edit_assessment_button = QPushButton("Editar")
        # self.delete_assessment_button = QPushButton("Excluir")
        # layout.addWidget(self.edit_assessment_button)
        # layout.addWidget(self.delete_assessment_button)

    def _emit_enter_grades_signal(self):
        if self.assessment.id is not None:
            self.enter_grades_requested.emit(self.assessment.id)


class AssessmentsView(QWidget):
    # Signal to indicate an assessment might have been added/edited, to trigger refresh if needed elsewhere
    assessment_updated = pyqtSignal()
    # Signal to navigate to the grades entry view
    request_grades_entry_view = pyqtSignal(int) # Emits assessment_id

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_student_group_id: int | None = None

        self.setWindowTitle("Gerenciador de Avaliações")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Título
        title_label = QLabel("Gerenciador de Avaliações")
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Filtro de Turma
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filtrar por Turma:")
        self.group_filter_combo = QComboBox()
        self.group_filter_combo.setPlaceholderText("Selecione uma Turma...")
        self.group_filter_combo.setMinimumWidth(250)
        self.group_filter_combo.currentIndexChanged.connect(self._on_group_selected)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.group_filter_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Botão para Adicionar Nova Avaliação
        self.add_assessment_button = QPushButton("✚ Nova Avaliação")
        self.add_assessment_button.clicked.connect(self._open_new_assessment_dialog)
        self.add_assessment_button.setEnabled(False) # Habilitar apenas quando uma turma for selecionada
        # Styling for the button could be added here
        add_button_layout = QHBoxLayout()
        add_button_layout.addStretch()
        add_button_layout.addWidget(self.add_assessment_button)
        main_layout.addLayout(add_button_layout)

        # Área de Scroll para Avaliações
        self.assessments_scroll_area = QScrollArea()
        self.assessments_scroll_area.setWidgetResizable(True)
        self.assessments_scroll_area.setFrameShape(QFrame.Shape.StyledPanel) # Adiciona uma borda sutil

        self.assessments_container_widget = QWidget() # Widget interno para o layout das avaliações
        self.assessments_layout = QVBoxLayout(self.assessments_container_widget)
        self.assessments_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.assessments_layout.setSpacing(8)

        self.assessments_scroll_area.setWidget(self.assessments_container_widget)
        main_layout.addWidget(self.assessments_scroll_area)

        self._populate_student_groups_combo()
        self._load_assessments() # Carga inicial (deve mostrar placeholder)

    def _populate_student_groups_combo(self):
        self.group_filter_combo.clear()
        self.group_filter_combo.addItem("Selecione uma Turma...", None) # Placeholder

        try:
            student_groups = self.db_manager.get_all_student_groups()
            if student_groups:
                for group in student_groups:
                    self.group_filter_combo.addItem(group.name, group.id)
            else:
                self.group_filter_combo.addItem("Nenhuma turma cadastrada", None)
                self.group_filter_combo.setEnabled(False)
        except Exception as e:
            print(f"Erro ao carregar turmas: {e}")
            # Considerar mostrar mensagem de erro na UI
            self.group_filter_combo.addItem("Erro ao carregar turmas", None)
            self.group_filter_combo.setEnabled(False)


    def _on_group_selected(self, index: int):
        self.selected_student_group_id = self.group_filter_combo.itemData(index)
        self.add_assessment_button.setEnabled(self.selected_student_group_id is not None)
        self._load_assessments()

    def _clear_assessments_layout(self):
        # Remove todos os widgets do layout de avaliações
        while self.assessments_layout.count():
            child = self.assessments_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _load_assessments(self):
        self._clear_assessments_layout()

        if self.selected_student_group_id is None:
            placeholder_label = QLabel("Selecione uma turma para visualizar as avaliações.")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_label.setStyleSheet("font-style: italic; color: grey;")
            self.assessments_layout.addWidget(placeholder_label)
            return

        try:
            assessments = self.db_manager.get_assessments_by_group(self.selected_student_group_id)
            if not assessments:
                no_assessments_label = QLabel("Nenhuma avaliação cadastrada para esta turma.")
                no_assessments_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.assessments_layout.addWidget(no_assessments_label)
            else:
                for assessment in assessments:
                    assessment_text = f"<b>{assessment.title}</b>"
                    if assessment.date:
                        assessment_text += f" - <i>{assessment.date.strftime('%d/%m/%Y')}</i>"
                    else:
                        assessment_text += " - <i>Sem data</i>"

                    # Aqui poderíamos usar um widget customizado para cada avaliação
                    # Por agora, um QLabel com rich text.
                    assessment_label = QLabel(assessment_text)
                    assessment_label.setWordWrap(True)
                    assessment_label.setFrameShape(QFrame.Shape.Panel)
                    # Create custom widget for each assessment
                    assessment_widget = AssessmentItemWidget(assessment)
                    assessment_widget.enter_grades_requested.connect(self.request_grades_entry_view.emit)
                    # TODO: Connect edit/delete signals from assessment_widget if those buttons are added
                    self.assessments_layout.addWidget(assessment_widget)
        except Exception as e:
            print(f"Erro ao carregar avaliações: {e}") # Log para o console
            error_label = QLabel(f"Erro ao carregar avaliações: {e}") # Mostrar erro na UI
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: red;")
            self.assessments_layout.addWidget(error_label)

        self.assessments_layout.addStretch() # Para empurrar os itens para cima


    def _open_new_assessment_dialog(self):
        if self.selected_student_group_id is None:
            QMessageBox.warning(self, "Turma Necessária", "Por favor, selecione uma turma antes de adicionar uma avaliação.")
            return

        # Placeholder para o diálogo de Avaliação
        # from src.ui.assessment_dialog import AssessmentDialog # Será criado depois
        # dialog = AssessmentDialog(db_manager=self.db_manager, student_group_id=self.selected_student_group_id, parent=self)
        # if dialog.exec() == QDialog.DialogCode.Accepted:
        #     self._load_assessments() # Recarregar avaliações
        #     self.assessment_updated.emit() # Emitir sinal

        print(f"Placeholder: Abrir diálogo para adicionar avaliação para turma ID: {self.selected_student_group_id}")
        # Simular que uma avaliação foi adicionada para teste de UI
        QMessageBox.information(self, "Placeholder", f"Simulando: Diálogo de Nova Avaliação para turma ID {self.selected_student_group_id} seria aberto aqui.")
        # self._load_assessments() # Descomentar quando o diálogo real for implementado
        from src.ui.assessment_dialog import AssessmentDialog # Importa aqui para evitar importação circular a nível de módulo se AssessmentDialog importasse algo de AssessmentsView

        dialog = AssessmentDialog(db_manager=self.db_manager, student_group_id=self.selected_student_group_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_assessments() # Recarregar avaliações
            self.assessment_updated.emit() # Emitir sinal
        # else: Dialogo foi cancelado ou houve erro (já tratado no dialogo com QMessageBox)


    def refresh_view(self):
        """Método público para ser chamado externamente para recarregar dados."""
        current_group_id = self.group_filter_combo.currentData()
        self._populate_student_groups_combo() # Recarrega as turmas no combo

        # Tenta reselecionar a turma que estava selecionada
        if current_group_id is not None:
            for i in range(self.group_filter_combo.count()):
                if self.group_filter_combo.itemData(i) == current_group_id:
                    self.group_filter_combo.setCurrentIndex(i)
                    break
            else: # Se a turma selecionada anteriormente não existe mais
                self.group_filter_combo.setCurrentIndex(0) # Seleciona o placeholder
        else:
             self.group_filter_combo.setCurrentIndex(0)

        # _load_assessments será chamado automaticamente pelo _on_group_selected (se o índice mudou)
        # ou precisamos chamar explicitamente se o índice não mudou mas os dados podem ter mudado.
        if self.group_filter_combo.itemData(self.group_filter_combo.currentIndex()) == current_group_id:
            self._load_assessments()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication

    # --- Mock DatabaseManager para teste de UI ---
    class MockDBManager: # Reutilizar a classe mock do assessment_dialog se for similar
        def get_all_student_groups(self):
            print("MockDB: get_all_student_groups called")
            return [
                StudentGroup(id=1, name="Turma A - Manhã"),
                StudentGroup(id=2, name="Turma B - Tarde"),
                StudentGroup(id=3, name="Turma C - Noite")
            ]

        def get_assessments_by_group(self, group_id: int):
            from datetime import datetime # Local import for mock data
            print(f"MockDB: get_assessments_by_group called for group_id {group_id}")
            if group_id == 1:
                return [
                    Assessment(id=101, title="Prova 1 - Unidade 1", student_group_id=1, max_value=10.0, date=datetime(2024, 3, 15)),
                    Assessment(id=102, title="Trabalho em Grupo - Biomas", student_group_id=1, max_value=5.0, date=datetime(2024, 4, 5)),
                ]
            elif group_id == 2:
                return [
                    Assessment(id=201, title="Avaliação Contínua - Semanal", student_group_id=2, max_value=2.0, date=datetime(2024, 3, 20)),
                ]
            return []

    app = QApplication(sys.argv)
    mock_db = MockDBManager()

    # Teste da AssessmentsView
    assessments_widget = AssessmentsView(db_manager=mock_db)

    # Mock para a navegação para GradesEntryView
    def handle_grades_entry_request(assessment_id):
        print(f"MAIN WINDOW MOCK: Navegar para GradesEntryView para assessment_id: {assessment_id}")
        # Aqui, uma MainWindow real instanciaria e mostraria GradesEntryView
        # Para este teste, podemos apenas imprimir ou até instanciar GradesEntryView se quisermos testar a chamada.
        # grades_entry_mock_view = GradesEntryView(db_manager=mock_db) # Supondo que GradesEntryView pode ser mockada ou usada com o mesmo mock_db
        # grades_entry_mock_view.load_assessment_data(assessment_id)
        # grades_entry_mock_view.show() # Isso criaria uma nova janela no teste, talvez não ideal.
        QMessageBox.information(assessments_widget, "Navegação Mock", f"Navegaria para lançar notas da avaliação ID: {assessment_id}")

    assessments_widget.request_grades_entry_view.connect(handle_grades_entry_request)

    assessments_widget.setGeometry(100, 100, 700, 500) # Aumentar tamanho para melhor visualização
    assessments_widget.show()

    sys.exit(app.exec())
