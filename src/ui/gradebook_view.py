import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QApplication, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from src.core.database_manager import DatabaseManager
from src.core.models import StudentGroup, Assessment, Entity, Grade, ENTITY_TYPE_STUDENT # Constants

class GradebookView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_student_group_id: int | None = None
        self.loaded_assessments: list[Assessment] = [] # To keep track of assessment columns

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Title
        title_label = QLabel("Boletim da Turma")
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Student Group Filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Selecionar Turma:")
        self.group_filter_combo = QComboBox()
        self.group_filter_combo.setPlaceholderText("Selecione uma Turma...")
        self.group_filter_combo.setMinimumWidth(250)
        self.group_filter_combo.currentIndexChanged.connect(self._on_group_selected)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.group_filter_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Gradebook Table
        self.gradebook_table = QTableWidget()
        self.gradebook_table.setSortingEnabled(True)
        self.gradebook_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
        main_layout.addWidget(self.gradebook_table)

        self._populate_student_groups_combo()
        # _load_gradebook_data will be called by _on_group_selected or refresh_view

    def _populate_student_groups_combo(self):
        self.group_filter_combo.blockSignals(True)
        self.group_filter_combo.clear()
        self.group_filter_combo.addItem("Selecione uma Turma...", None)
        try:
            student_groups = self.db_manager.get_all_student_groups()
            if student_groups:
                for group in student_groups:
                    self.group_filter_combo.addItem(group.name, group.id)
            else:
                self.group_filter_combo.addItem("Nenhuma turma cadastrada", None)
                self.group_filter_combo.setEnabled(False)
        except Exception as e:
            print(f"Erro ao carregar turmas para o boletim: {e}")
            self.group_filter_combo.addItem("Erro ao carregar turmas", None)
            self.group_filter_combo.setEnabled(False)
        self.group_filter_combo.blockSignals(False)
        if self.group_filter_combo.count() > 1: # If actual groups were added
             self.group_filter_combo.setCurrentIndex(0) # Trigger initial load for placeholder or first group
        else: # No groups or only placeholder/error
            self._clear_gradebook_table()


    def _on_group_selected(self, index: int):
        self.current_student_group_id = self.group_filter_combo.itemData(index)
        self._load_gradebook_data()

    def _clear_gradebook_table(self):
        self.gradebook_table.setRowCount(0)
        self.gradebook_table.setColumnCount(0)
        self.loaded_assessments = []

    def _create_table_item(self, text: str = "", is_numeric: bool = False, data_value=None) -> QTableWidgetItem:
        item = QTableWidgetItem()
        if is_numeric:
            try:
                num_val = float(text.replace(",", ".")) # Allow comma
                item.setData(Qt.ItemDataRole.DisplayRole, f"{num_val:.2f}") # Display formatted
                item.setData(Qt.ItemDataRole.UserRole, num_val) # Store float for sorting
            except ValueError:
                item.setText(text) # Fallback to text if not purely numeric (e.g., "-")
        else:
            item.setText(text)

        if data_value is not None and not is_numeric: # For non-numeric, store data in UserRole if needed
             item.setData(Qt.ItemDataRole.UserRole, data_value)

        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _load_gradebook_data(self):
        self._clear_gradebook_table()
        if self.current_student_group_id is None:
            return

        # Fetch students (simplified: all students of type 'aluno')
        students = self.db_manager.get_all_entities(entity_type=ENTITY_TYPE_STUDENT)
        if not students:
            # TODO: Display "Nenhum aluno encontrado" in table area
            return

        # Fetch assessments for the group, sorted by title for consistent column order
        self.loaded_assessments = sorted(
            self.db_manager.get_assessments_by_group(self.current_student_group_id),
            key=lambda x: x.title.lower() # Sort by title
        )

        # Setup Table Columns
        num_assessment_cols = len(self.loaded_assessments)
        self.gradebook_table.setColumnCount(1 + num_assessment_cols + 1) # Aluno + Assessments + Média Final

        headers = ["Aluno"]
        for i, assessment in enumerate(self.loaded_assessments):
            # Store assessment_id and max_value with header data if possible, or use self.loaded_assessments by index
            headers.append(f"{assessment.title}\n(Max: {assessment.max_value:.2f})")
        headers.append("Média Final (%)")
        self.gradebook_table.setHorizontalHeaderLabels(headers)

        # Resize headers
        self.gradebook_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(num_assessment_cols):
            self.gradebook_table.horizontalHeader().setSectionResizeMode(1 + i, QHeaderView.ResizeMode.ResizeToContents)
        self.gradebook_table.horizontalHeader().setSectionResizeMode(1 + num_assessment_cols, QHeaderView.ResizeMode.ResizeToContents)


        # Populate Table Rows
        self.gradebook_table.setRowCount(len(students))
        for row_idx, student in enumerate(students):
            student_name_item = self._create_table_item(student.name, data_value=student.id)
            self.gradebook_table.setItem(row_idx, 0, student_name_item)

            total_normalized_score = 0.0
            num_grades_for_avg = 0

            for col_idx, assessment in enumerate(self.loaded_assessments):
                grade = self.db_manager.get_grades_by_assessment_and_student(assessment.id, student.id)
                score_display = "-"
                if grade and grade.score is not None:
                    score_display = f"{grade.score:.2f}"
                    if assessment.max_value > 0: # Avoid division by zero
                        normalized_score = (grade.score / assessment.max_value)
                        total_normalized_score += normalized_score
                        num_grades_for_avg += 1

                score_item = self._create_table_item(score_display, is_numeric=(grade and grade.score is not None))
                self.gradebook_table.setItem(row_idx, 1 + col_idx, score_item)

            # Calculate and Display Average
            avg_score_display = "-"
            if num_grades_for_avg > 0:
                final_average_percentage = (total_normalized_score / num_grades_for_avg) * 100
                avg_score_display = f"{final_average_percentage:.2f}%"

            avg_item = self._create_table_item(avg_score_display, is_numeric=(num_grades_for_avg > 0))
            avg_item.setBackground(QColor(230, 230, 250)) # Light lavender for average column
            self.gradebook_table.setItem(row_idx, 1 + num_assessment_cols, avg_item)

    def refresh_view(self):
        """Public method to refresh the view, re-populating groups and reloading data."""
        current_group_id = self.current_student_group_id
        self._populate_student_groups_combo()

        if current_group_id is not None:
            for i in range(self.group_filter_combo.count()):
                if self.group_filter_combo.itemData(i) == current_group_id:
                    self.group_filter_combo.setCurrentIndex(i)
                    # _on_group_selected will call _load_gradebook_data
                    return
        # If previous group not found or none was selected, trigger for current selection
        self._on_group_selected(self.group_filter_combo.currentIndex())


if __name__ == '__main__':
    from datetime import datetime
    # Mocking (similar to previous views)
    class MockStudentGroup:
        def __init__(self, id, name): self.id = id; self.name = name
    class MockAssessment:
        def __init__(self, id, title, student_group_id, max_value, date=None):
            self.id = id; self.title = title; self.student_group_id = student_group_id
            self.max_value = max_value; self.date = date or datetime.now()
    class MockEntity:
        def __init__(self, id, name, type): self.id = id; self.name = name; self.type = type
    class MockGrade:
        def __init__(self, id, assessment_id, student_id, score, observations=""):
            self.id = id; self.assessment_id = assessment_id; self.student_id = student_id
            self.score = score; self.observations = observations

    class MockDBManager:
        def get_all_student_groups(self):
            return [MockStudentGroup(id=1, name="Turma Alpha"), MockStudentGroup(id=2, name="Turma Beta")]

        def get_assessments_by_group(self, group_id: int):
            if group_id == 1: # Turma Alpha
                return [
                    MockAssessment(id=101, title="Prova 1", student_group_id=1, max_value=10.0, date=datetime(2024,3,10)),
                    MockAssessment(id=102, title="Trabalho A", student_group_id=1, max_value=5.0, date=datetime(2024,3,20))
                ]
            if group_id == 2: # Turma Beta
                 return [MockAssessment(id=201, title="Quiz Semanal", student_group_id=2, max_value=2.0, date=datetime(2024,3,15))]
            return []

        def get_all_entities(self, entity_type: str):
            if entity_type == ENTITY_TYPE_STUDENT:
                return [MockEntity(id=1, name="João Silva", type=ENTITY_TYPE_STUDENT),
                        MockEntity(id=2, name="Maria Oliveira", type=ENTITY_TYPE_STUDENT)]
            return []

        def get_grades_by_assessment_and_student(self, assessment_id: int, student_id: int):
            # Grades for Turma Alpha
            if assessment_id == 101 and student_id == 1: return MockGrade(id=1, assessment_id=101, student_id=1, score=8.0)
            if assessment_id == 102 and student_id == 1: return MockGrade(id=2, assessment_id=102, student_id=1, score=4.0)
            if assessment_id == 101 and student_id == 2: return MockGrade(id=3, assessment_id=101, student_id=2, score=6.0)
            # Maria did not do Trabalho A (assessment_id=102)

            # Grades for Turma Beta (student IDs might overlap if not careful with mock data, but assume distinct for now)
            if assessment_id == 201 and student_id == 1: return MockGrade(id=4, assessment_id=201, student_id=1, score=1.5) # João in Beta's quiz
            return None

    app = QApplication(sys.argv)
    db_mock = MockDBManager()
    gradebook_view = GradebookView(db_manager=db_mock)
    gradebook_view.setWindowTitle("Teste Boletim da Turma")
    gradebook_view.setGeometry(100, 100, 900, 600)
    gradebook_view.show()
    # Manually select a group to trigger load for testing, as initial selection might be "Selecione..."
    # gradebook_view.group_filter_combo.setCurrentIndex(1) # Select "Turma Alpha"
    sys.exit(app.exec())
