import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QComboBox,
    QDoubleSpinBox, QDialogButtonBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QDate
from typing import Optional

from src.core.database_manager import DatabaseManager
from src.core.models import Assessment, StudentGroup # Assuming these models exist

class AssessmentDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, parent=None,
                 assessment_id: Optional[int] = None,
                 # student_group_id is for pre-selecting when adding a new assessment from a group-filtered view
                 student_group_id: Optional[int] = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.assessment_id = assessment_id
        self.current_assessment: Optional[Assessment] = None
        self.fixed_student_group_id = student_group_id # Store the group ID if passed for a new assessment

        self._init_ui()

        if self.assessment_id:
            self.setWindowTitle("Editar Avaliação")
            self._load_assessment_data()
        else:
            self.setWindowTitle("Nova Avaliação")
            self.date_edit.setDate(QDate.currentDate())
            if self.fixed_student_group_id:
                # Pre-select and disable group combo if adding to a specific group
                self._populate_group_combo(fixed_group_id=self.fixed_student_group_id)
            else:
                # This case (adding assessment without a pre-selected group)
                # is not used by AssessmentsView currently, but good for dialog completeness
                self._populate_group_combo()


    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.title_edit = QLineEdit()
        form_layout.addRow("Título:", self.title_edit)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Data da Aplicação:", self.date_edit)

        self.group_combo = QComboBox()
        form_layout.addRow("Turma:", self.group_combo)

        self.max_value_spinbox = QDoubleSpinBox()
        self.max_value_spinbox.setMinimum(0.01) # Max value must be positive
        self.max_value_spinbox.setMaximum(1000.0) # Arbitrary reasonable maximum
        self.max_value_spinbox.setValue(10.0) # Default max value
        form_layout.addRow("Valor Máximo/Peso:", self.max_value_spinbox)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self._save_assessment)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _populate_group_combo(self, fixed_group_id: Optional[int] = None):
        self.group_combo.clear()
        if fixed_group_id:
            group = self.db_manager.get_student_group(fixed_group_id)
            if group:
                self.group_combo.addItem(group.name, group.id)
                self.group_combo.setEnabled(False) # Disable if group is fixed
            else:
                QMessageBox.warning(self, "Erro", f"Turma com ID {fixed_group_id} não encontrada.")
                # Handle error, maybe disable dialog or just the combo
                self.group_combo.setEnabled(False)
        else:
            # Populate with all groups if no specific group is fixed (e.g., for editing or general add)
            self.group_combo.addItem("Selecione uma Turma...", None)
            all_groups = self.db_manager.get_all_student_groups()
            for group in all_groups:
                self.group_combo.addItem(group.name, group.id)
            self.group_combo.setEnabled(True)


    def _load_assessment_data(self):
        if self.assessment_id:
            self.current_assessment = self.db_manager.get_assessment(self.assessment_id)
            if self.current_assessment:
                self.title_edit.setText(self.current_assessment.title)
                if self.current_assessment.date:
                    self.date_edit.setDate(QDate(self.current_assessment.date))
                else:
                    self.date_edit.setDate(QDate.currentDate()) # Or clear it, or set to a default

                self.max_value_spinbox.setValue(self.current_assessment.max_value)

                # Populate combo for editing: could show all, or just the current one if not changeable
                # For now, populate with the current group and disable changing it.
                # If group changes were allowed, _populate_group_combo() would be called without fixed_group_id
                # and then setCurrentIndex to the assessment's group.
                self._populate_group_combo(fixed_group_id=self.current_assessment.student_group_id)
                # Ensure the correct group is selected (it should be if fixed_group_id logic works)
                for i in range(self.group_combo.count()):
                    if self.group_combo.itemData(i) == self.current_assessment.student_group_id:
                        self.group_combo.setCurrentIndex(i)
                        break
            else:
                QMessageBox.critical(self, "Erro", f"Avaliação com ID {self.assessment_id} não encontrada.")
                self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)


    def _save_assessment(self):
        title = self.title_edit.text().strip()
        date_val_qt = self.date_edit.date()
        # Convert QDate to datetime.date or datetime.datetime as needed by your model/DB manager
        # For simplicity, let's assume db_manager can handle datetime.date
        # The model Assessment uses Optional[datetime], so we convert QDate to datetime
        date_val = date_val_qt.toPyDate() if date_val_qt.isValid() else None

        selected_group_id = self.group_combo.currentData()
        max_value = self.max_value_spinbox.value()

        # Validation
        if not title:
            QMessageBox.warning(self, "Validação Falhou", "O título da avaliação não pode estar vazio.")
            return
        if selected_group_id is None:
            QMessageBox.warning(self, "Validação Falhou", "Por favor, selecione uma turma.")
            return
        if max_value <= 0:
            QMessageBox.warning(self, "Validação Falhou", "O valor máximo/peso deve ser um número positivo.")
            return
        # Date can be optional based on model, so direct validation might not be needed unless it's mandatory.

        # Convert date_val (datetime.date) to datetime.datetime if your model strictly expects it
        # For now, assuming add_assessment/update_assessment can handle datetime.date or None
        # If Assessment model's date is datetime, we might need to add a default time.
        # Let's assume the model is fine with just date or None.
        # If the model's 'date' attribute is datetime, then:
        from datetime import datetime
        assessment_datetime = datetime.combine(date_val, datetime.min.time()) if date_val else None


        try:
            if self.assessment_id: # Editing
                if not self.current_assessment: # Should not happen if UI is built correctly
                    QMessageBox.critical(self, "Erro", "Nenhuma avaliação carregada para edição.")
                    return

                success = self.db_manager.update_assessment(
                    assessment_id=self.assessment_id,
                    title=title,
                    date=assessment_datetime, # Use datetime object
                    student_group_id=selected_group_id, # Group ID might not be editable here if combo is disabled
                    max_value=max_value
                )
                if success:
                    QMessageBox.information(self, "Sucesso", "Avaliação atualizada com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Falha", "Não foi possível atualizar a avaliação no banco de dados.")

            else: # Creating
                new_assessment = self.db_manager.add_assessment(
                    title=title,
                    date=assessment_datetime, # Use datetime object
                    student_group_id=selected_group_id,
                    max_value=max_value
                )
                if new_assessment and new_assessment.id:
                    self.assessment_id = new_assessment.id # Store new ID for potential use
                    QMessageBox.information(self, "Sucesso", "Avaliação adicionada com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Falha", "Não foi possível adicionar a avaliação no banco de dados.")

        except Exception as e:
            # Catch more specific errors like IntegrityError if possible
            QMessageBox.critical(self, "Erro no Banco de Dados", f"Ocorreu um erro: {e}")


if __name__ == '__main__':
    # --- Mock DatabaseManager e Modelos para teste de UI ---
    from datetime import datetime
    class MockStudentGroup:
        def __init__(self, id, name):
            self.id = id
            self.name = name

    class MockAssessment:
        def __init__(self, id, title, student_group_id, max_value, date=None):
            self.id = id
            self.title = title
            self.student_group_id = student_group_id
            self.max_value = max_value
            self.date = date if date else datetime.now() # Ensure date is datetime

    class MockDBManager:
        def get_student_group(self, group_id: int):
            print(f"MockDB: get_student_group for ID {group_id}")
            if group_id == 1: return MockStudentGroup(id=1, name="Turma Mock A")
            if group_id == 2: return MockStudentGroup(id=2, name="Turma Mock B")
            return None

        def get_all_student_groups(self):
            print("MockDB: get_all_student_groups")
            return [MockStudentGroup(id=1, name="Turma Mock A"), MockStudentGroup(id=2, name="Turma Mock B")]

        def get_assessment(self, assessment_id: int):
            print(f"MockDB: get_assessment for ID {assessment_id}")
            if assessment_id == 101:
                return MockAssessment(id=101, title="Prova Mock Edit", student_group_id=1, max_value=10.0, date=datetime(2024,5,10))
            return None

        def add_assessment(self, title, date, student_group_id, max_value):
            print(f"MockDB: add_assessment: {title}, {date}, group_id={student_group_id}, max_val={max_value}")
            return MockAssessment(id=999, title=title, student_group_id=student_group_id, max_value=max_value, date=date)

        def update_assessment(self, assessment_id, title, date, student_group_id, max_value):
            print(f"MockDB: update_assessment: id={assessment_id}, {title}, {date}, group_id={student_group_id}, max_val={max_value}")
            return True

    app = QApplication(sys.argv)
    mock_db = MockDBManager()

    print("Testando diálogo Adicionar Avaliação (com turma pré-selecionada):")
    dialog_add_fixed_group = AssessmentDialog(db_manager=mock_db, student_group_id=1, parent=None)
    if dialog_add_fixed_group.exec() == QDialog.DialogCode.Accepted:
        print(f"  Avaliação adicionada/editada ID: {dialog_add_fixed_group.assessment_id}")
    else:
        print("  Criação de nova avaliação (grupo fixo) cancelada/falhou.")

    print("\nTestando diálogo Adicionar Avaliação (sem turma pré-selecionada - não usado por AssessmentsView):")
    dialog_add_any_group = AssessmentDialog(db_manager=mock_db, parent=None)
    if dialog_add_any_group.exec() == QDialog.DialogCode.Accepted:
        print(f"  Avaliação adicionada/editada ID: {dialog_add_any_group.assessment_id}")
    else:
        print("  Criação de nova avaliação (qualquer grupo) cancelada/falhou.")

    print("\nTestando diálogo Editar Avaliação:")
    dialog_edit = AssessmentDialog(db_manager=mock_db, assessment_id=101, parent=None)
    if dialog_edit.exec() == QDialog.DialogCode.Accepted:
         print(f"  Avaliação ID: {dialog_edit.assessment_id} salva.")
    else:
        print("  Edição de avaliação cancelada/falhou.")

    sys.exit(app.exec())
