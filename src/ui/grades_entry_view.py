import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QApplication, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont

from src.core.database_manager import DatabaseManager
from src.core.models import Assessment, StudentGroup, Entity, Grade, ENTITY_TYPE_STUDENT # Constants

class GradesEntryView(QWidget):
    grades_saved = pyqtSignal() # Emitted when grades are successfully saved

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_assessment: Optional[Assessment] = None
        self.current_assessment_id: Optional[int] = None
        self.students_data: list[tuple[Entity, Optional[Grade]]] = [] # List of (student, existing_grade)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Title and Assessment Info
        self.title_label = QLabel("Lançamento de Notas")
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        self.assessment_info_label = QLabel("Selecione uma avaliação para lançar notas.")
        self.assessment_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.assessment_info_label.setStyleSheet("font-style: italic; font-size: 11pt;")
        main_layout.addWidget(self.assessment_info_label)

        # Grades Table
        self.grades_table = QTableWidget()
        self.grades_table.setColumnCount(3)
        self.grades_table.setHorizontalHeaderLabels(["Aluno (Nome)", "Nota Obtida", "Observações"])
        self.grades_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.grades_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.grades_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.grades_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection) # No row selection needed
        self.grades_table.cellChanged.connect(self._on_cell_changed)
        main_layout.addWidget(self.grades_table)

        # Save Button
        self.save_button = QPushButton("Salvar Notas Lançadas")
        self.save_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.save_button.setMinimumHeight(35)
        self.save_button.clicked.connect(self._save_grades)
        self.save_button.setEnabled(False) # Enabled when data is loaded

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

    def load_assessment_data(self, assessment_id: int):
        self.current_assessment_id = assessment_id
        self.current_assessment = self.db_manager.get_assessment(assessment_id)

        if not self.current_assessment:
            QMessageBox.critical(self, "Erro", f"Avaliação com ID {assessment_id} não encontrada.")
            self.assessment_info_label.setText("Avaliação não encontrada.")
            self.grades_table.setRowCount(0)
            self.save_button.setEnabled(False)
            return

        group = self.db_manager.get_student_group(self.current_assessment.student_group_id)
        group_name = group.name if group else "Desconhecida"

        self.assessment_info_label.setText(
            f"<b>Avaliação:</b> {self.current_assessment.title} (Max: {self.current_assessment.max_value:.2f})<br>"
            f"<b>Turma:</b> {group_name}<br>"
            f"<i style='color:grey;'>Listando todos os alunos cadastrados. Preencha apenas para os relevantes.</i>"
        )

        # Fetch all students (simplification as per plan)
        all_students = self.db_manager.get_all_entities(entity_type=ENTITY_TYPE_STUDENT)
        self.students_data = [] # Clear previous data

        self.grades_table.blockSignals(True) # Block signals during population
        self.grades_table.setRowCount(len(all_students))

        for row, student in enumerate(all_students):
            existing_grade = self.db_manager.get_grades_by_assessment_and_student(
                self.current_assessment_id, student.id
            )
            self.students_data.append((student, existing_grade)) # Store for saving

            # Student Name Item (Non-editable)
            name_item = QTableWidgetItem(student.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setData(Qt.ItemDataRole.UserRole, student.id) # Store student_id
            self.grades_table.setItem(row, 0, name_item)

            # Score Item (Editable)
            score_item = QTableWidgetItem()
            if existing_grade:
                score_item.setText(f"{existing_grade.score:.2f}") # Format score
                score_item.setData(Qt.ItemDataRole.UserRole, existing_grade.id) # Store grade_id if exists
            self.grades_table.setItem(row, 1, score_item)
            self._validate_score_cell(row, 1) # Initial validation for existing scores

            # Observations Item (Editable)
            obs_item = QTableWidgetItem(existing_grade.observations if existing_grade else "")
            self.grades_table.setItem(row, 2, obs_item)

        self.grades_table.blockSignals(False) # Unblock signals
        self.save_button.setEnabled(True)


    def _on_cell_changed(self, row: int, column: int):
        if column == 1: # "Nota Obtida" column
            self._validate_score_cell(row, column)

    def _validate_score_cell(self, row: int, column: int) -> bool:
        if column != 1 or not self.current_assessment:
            return True # Not a score cell or no assessment loaded

        item = self.grades_table.item(row, column)
        if not item: return True # Should not happen

        score_text = item.text().strip()
        is_valid = True

        if not score_text: # Empty score is considered valid (means no grade or remove grade)
            item.setBackground(QColor("white")) # Default background
            return True

        try:
            score = float(score_text.replace(",", ".")) # Allow comma as decimal separator
            if not (0 <= score <= self.current_assessment.max_value):
                is_valid = False
        except ValueError:
            is_valid = False

        if is_valid:
            item.setBackground(QColor("white")) # Default background
        else:
            item.setBackground(QColorConstants. হালকালাল) # Light red for invalid
        return is_valid

    def _save_grades(self):
        if not self.current_assessment_id or not self.current_assessment:
            QMessageBox.warning(self, "Erro", "Nenhuma avaliação carregada para salvar notas.")
            return

        errors_found = []
        success_count = 0

        for row in range(self.grades_table.rowCount()):
            student_item = self.grades_table.item(row, 0)
            score_item = self.grades_table.item(row, 1)
            obs_item = self.grades_table.item(row, 2)

            if not student_item or not score_item or not obs_item: continue # Should not happen

            student_id = student_item.data(Qt.ItemDataRole.UserRole)
            student_name = student_item.text()

            score_text = score_item.text().strip().replace(",", ".")
            observations = obs_item.text().strip()

            existing_grade_id = score_item.data(Qt.ItemDataRole.UserRole) # grade_id stored here

            if not score_text and not observations and not existing_grade_id:
                # Skip empty rows if no existing grade and no new data
                continue

            score_value: Optional[float] = None
            if score_text:
                try:
                    score_value = float(score_text)
                    if not (0 <= score_value <= self.current_assessment.max_value):
                        errors_found.append(f"Nota para {student_name} ({score_text}) fora do intervalo permitido (0-{self.current_assessment.max_value:.2f}).")
                        self._validate_score_cell(row, 1) # Re-highlight
                        continue
                except ValueError:
                    errors_found.append(f"Nota para {student_name} ({score_text}) não é um número válido.")
                    self._validate_score_cell(row, 1) # Re-highlight
                    continue

            # If score_text is empty, score_value remains None.
            # This means if a grade exists, it should be deleted if score is cleared.
            # Or, if score is optional, it could be updated with None.
            # For this system, let's assume clearing score means removing the grade or not adding one.

            try:
                if existing_grade_id:
                    if score_value is not None: # Update existing grade
                        self.db_manager.update_grade(
                            grade_id=existing_grade_id,
                            score=score_value,
                            observations=observations
                        )
                        success_count += 1
                    else: # Score cleared for an existing grade - delete it
                        self.db_manager.delete_grade(existing_grade_id)
                        score_item.setData(Qt.ItemDataRole.UserRole, None) # Clear stored grade_id
                        success_count +=1 # Count deletion as a success
                elif score_value is not None: # Add new grade (only if score is provided)
                    new_grade = self.db_manager.add_grade(
                        assessment_id=self.current_assessment_id,
                        student_id=student_id,
                        score=score_value,
                        observations=observations
                    )
                    if new_grade and new_grade.id:
                        score_item.setData(Qt.ItemDataRole.UserRole, new_grade.id) # Store new grade_id
                    success_count += 1
                # If no existing_grade_id and score_value is None, do nothing (no grade to add/update/delete)
            except Exception as e:
                errors_found.append(f"Erro ao salvar para {student_name}: {e}")

        if errors_found:
            QMessageBox.warning(self, "Erros no Lançamento", "\n".join(errors_found))
        elif success_count > 0:
            QMessageBox.information(self, "Sucesso", f"{success_count} registros de notas salvos/atualizados com sucesso.")
            self.grades_saved.emit()
            self.load_assessment_data(self.current_assessment_id) # Refresh data
        else:
            QMessageBox.information(self, "Nenhuma Alteração", "Nenhuma nota foi alterada ou adicionada.")


if __name__ == '__main__':
    from datetime import datetime
    # Mocking (similar to AssessmentDialog's test)
    class MockStudentGroup:
        def __init__(self, id, name): self.id = id; self.name = name
    class MockAssessment:
        def __init__(self, id, title, student_group_id, max_value, date=None):
            self.id = id; self.title = title; self.student_group_id = student_group_id
            self.max_value = max_value; self.date = date or datetime.now()
    class MockEntity: # For Student
        def __init__(self, id, name, type): self.id = id; self.name = name; self.type = type
    class MockGrade:
        def __init__(self, id, assessment_id, student_id, score, observations=""):
            self.id = id; self.assessment_id = assessment_id; self.student_id = student_id
            self.score = score; self.observations = observations

    class MockDBManager:
        def get_assessment(self, assessment_id: int):
            if assessment_id == 1:
                return MockAssessment(id=1, title="Prova 1", student_group_id=10, max_value=10.0)
            return None
        def get_student_group(self, group_id: int):
            if group_id == 10: return MockStudentGroup(id=10, name="Turma Mock Alpha")
            return None
        def get_all_entities(self, entity_type: str):
            if entity_type == ENTITY_TYPE_STUDENT:
                return [MockEntity(id=101, name="Alice Silva", type=ENTITY_TYPE_STUDENT),
                        MockEntity(id=102, name="Bruno Costa", type=ENTITY_TYPE_STUDENT),
                        MockEntity(id=103, name="Carla Dias", type=ENTITY_TYPE_STUDENT)]
            return []
        def get_grades_by_assessment_and_student(self, assessment_id: int, student_id: int):
            if assessment_id == 1 and student_id == 101:
                return MockGrade(id=1001, assessment_id=1, student_id=101, score=7.5, observations="Bom esforço")
            if assessment_id == 1 and student_id == 102: # Bruno has no grade yet
                return None
            return None # Default no grade

        def add_grade(self, assessment_id, student_id, score, observations):
            print(f"MockDB: Add Grade: assess_id={assessment_id}, stud_id={student_id}, score={score}, obs='{observations}'")
            # Return a mock grade with a new ID
            return MockGrade(id=hash((assessment_id, student_id)), assessment_id=assessment_id, student_id=student_id, score=score, observations=observations)

        def update_grade(self, grade_id, score, observations):
            print(f"MockDB: Update Grade: grade_id={grade_id}, score={score}, obs='{observations}'")
            return True

        def delete_grade(self, grade_id: int) -> bool:
            print(f"MockDB: Delete Grade: grade_id={grade_id}")
            return True

    app = QApplication(sys.argv)
    # Define QColorConstants.হালকালাল for the test if not available globally
    # For testing, let's use a standard light red
    QColorConstants = type('QColorConstants', (), {'হালকালাল': QColor(255, 200, 200)})

    db_mock = MockDBManager()
    grades_view = GradesEntryView(db_manager=db_mock)
    grades_view.load_assessment_data(assessment_id=1) # Load data for Assessment 1
    grades_view.setWindowTitle("Teste Lançamento de Notas")
    grades_view.setGeometry(100, 100, 800, 600)
    grades_view.show()
    sys.exit(app.exec())
