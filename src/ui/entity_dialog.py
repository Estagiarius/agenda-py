import sys
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, 
    QComboBox, QPushButton, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any

from src.core.models import Entity, StudentGroup, ENTITY_TYPE_STUDENT_GROUP, ENTITY_TYPE_PROFESSOR, ENTITY_TYPE_STUDENT
from src.core.database_manager import DatabaseManager


class EntityDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, entity_type: str, entity_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.student_group: Optional[StudentGroup] = None # For editing StudentGroup
        self.entity: Optional[Entity] = None # For editing generic Entity

        self.setMinimumWidth(450) # Increased width for more fields

        # Layouts
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # --- Common Widgets ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        # --- Type-Specific Widgets & Setup ---
        if self.entity_type == ENTITY_TYPE_STUDENT_GROUP:
            self.setWindowTitle("Adicionar/Editar Turma" if self.entity_id else "Adicionar Nova Turma")

            self.turma_name_edit = QLineEdit()
            self.teacher_combo = QComboBox()

            self.form_layout.addRow("Nome da Turma:", self.turma_name_edit)
            self.form_layout.addRow("Professor Responsável:", self.teacher_combo)

            self._populate_teachers_combo()

            if self.entity_id:
                self.student_group = self.db_manager.get_student_group(self.entity_id)
                if self.student_group:
                    self.turma_name_edit.setText(self.student_group.name)
                    if self.student_group.teacher_id:
                        for i in range(self.teacher_combo.count()):
                            if self.teacher_combo.itemData(i) == self.student_group.teacher_id:
                                self.teacher_combo.setCurrentIndex(i)
                                break
                    else:
                        self.teacher_combo.setCurrentIndex(0) # "Nenhum"
                else:
                    QMessageBox.critical(self, "Erro", f"Turma com ID {self.entity_id} não encontrada.")
                    # Consider closing the dialog or handling this more gracefully
                    self.turma_name_edit.setEnabled(False)
                    self.teacher_combo.setEnabled(False)

        else: # Generic Entity Handling (Professor, Aluno, Contato, Outro)
            self.setWindowTitle("Editar Entidade" if self.entity_id else "Adicionar Nova Entidade")

            self.name_edit = QLineEdit()
            self.type_combo = QComboBox()
            # Populate with known entity types, allowing "Outro" or custom
            known_types = [ENTITY_TYPE_PROFESSOR.capitalize(), ENTITY_TYPE_STUDENT.capitalize(), "Contato", "Outro"]
            # Ensure current entity_type is in list if editing
            if self.entity_id and self.entity_type.capitalize() not in known_types:
                known_types.insert(0, self.entity_type.capitalize())
            self.type_combo.addItems(known_types)
            self.type_combo.setCurrentText(self.entity_type.capitalize())
            if self.entity_type not in [ENTITY_TYPE_PROFESSOR, ENTITY_TYPE_STUDENT]: # Make it editable for "Contato", "Outro"
                 self.type_combo.setEditable(True)
            else: # Cannot change type for Professor/Aluno this way to avoid data integrity issues with StudentGroup teacher_id
                 self.type_combo.setEnabled(False)


            self.details_json_edit = QTextEdit()
            self.details_json_edit.setPlaceholderText("Insira detalhes como um objeto JSON. Ex: {\"email\": \"nome@exemplo.com\"}")
            self.details_json_edit.setFixedHeight(100)

            self.form_layout.addRow("Nome:", self.name_edit)
            self.form_layout.addRow("Tipo:", self.type_combo)
            self.form_layout.addRow("Detalhes (JSON):", self.details_json_edit)

            if self.entity_id:
                self.entity = self.db_manager.get_entity_by_id(self.entity_id)
                if self.entity:
                    self.name_edit.setText(self.entity.name)
                    # Type combo is already set or disabled
                    if self.entity.details_json:
                        try:
                            details_str = json.dumps(self.entity.details_json, indent=4)
                            self.details_json_edit.setPlainText(details_str)
                        except TypeError:
                            self.details_json_edit.setPlainText(str(self.entity.details_json))
                    else:
                        self.details_json_edit.setPlainText("{}")
                else:
                    QMessageBox.critical(self, "Erro", f"Entidade com ID {self.entity_id} não encontrada.")
                    self.name_edit.setEnabled(False)
                    self.details_json_edit.setEnabled(False)
            else: # Adding new generic entity
                self.details_json_edit.setPlainText("{}")
        
        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.button_box)

    def _populate_teachers_combo(self):
        self.teacher_combo.clear()
        self.teacher_combo.addItem("Nenhum", None) # UserData is None for no teacher
        professors = self.db_manager.get_all_entities(entity_type=ENTITY_TYPE_PROFESSOR)
        for prof in professors:
            self.teacher_combo.addItem(prof.name, prof.id)

    def get_entity_data(self) -> Optional[Dict[str, Any]]: # Return a dict to be processed by save_entity
        data = {}
        if self.entity_type == ENTITY_TYPE_STUDENT_GROUP:
            name = self.turma_name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Campo Obrigatório", "O nome da turma não pode estar vazio.")
                return None
            data['name'] = name
            data['teacher_id'] = self.teacher_combo.currentData()
        else: # Generic Entity
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Campo Obrigatório", "O nome da entidade não pode estar vazio.")
                return None

            # For generic entities, type is taken from type_combo (or entity_type if disabled)
            # If type_combo is editable, it can be a new type.
            # If disabled (e.g. for professor/aluno), use self.entity_type.
            current_type_text = self.type_combo.currentText().strip().lower() # Standardize to lower for comparison
            if not current_type_text and self.type_combo.isEditable():
                 QMessageBox.warning(self, "Campo Obrigatório", "O tipo da entidade não pode estar vazio.")
                 return None

            data['name'] = name
            data['type'] = current_type_text if self.type_combo.isEditable() and current_type_text else self.entity_type

            details_str = self.details_json_edit.toPlainText().strip()
            details_dict: Dict[str, Any] = {}
            if details_str:
                try:
                    details_dict = json.loads(details_str)
                    if not isinstance(details_dict, dict):
                        QMessageBox.warning(self, "JSON Inválido", "O campo 'Detalhes' deve ser um objeto JSON.")
                        return None
                except json.JSONDecodeError as e:
                    QMessageBox.warning(self, "JSON Inválido", f"Erro ao decodificar JSON: {e}")
                    return None
            data['details_json'] = details_dict
        
        return data


    def validate_and_accept(self):
        form_data = self.get_entity_data()
        if form_data:
            try:
                if self.entity_type == ENTITY_TYPE_STUDENT_GROUP:
                    if self.entity_id: # Editing StudentGroup
                        success = self.db_manager.update_student_group(
                            self.entity_id,
                            name=form_data['name'],
                            teacher_id=form_data['teacher_id']
                        )
                        if success:
                            QMessageBox.information(self, "Sucesso", "Turma atualizada com sucesso.")
                        else:
                            QMessageBox.warning(self, "Falha", "Não foi possível atualizar a turma.")
                            return # Do not accept if update failed
                    else: # Adding StudentGroup
                        added_group = self.db_manager.add_student_group(
                            name=form_data['name'],
                            teacher_id=form_data['teacher_id']
                        )
                        if added_group:
                            QMessageBox.information(self, "Sucesso", "Turma adicionada com sucesso.")
                            self.entity_id = added_group.id # Store new ID
                        else:
                            QMessageBox.warning(self, "Falha", "Não foi possível adicionar a turma.")
                            return # Do not accept if add failed
                else: # Generic Entity
                    if self.entity_id: # Editing Entity
                        # Create an Entity object for update
                        entity_to_update = Entity(id=self.entity_id, name=form_data['name'], type=form_data['type'], details_json=form_data['details_json'])
                        # Preserve created_at if available on the original entity
                        if self.entity and self.entity.created_at:
                            entity_to_update.created_at = self.entity.created_at

                        success = self.db_manager.update_entity(entity_to_update)
                        if success:
                            QMessageBox.information(self, "Sucesso", "Entidade atualizada com sucesso.")
                        else:
                            QMessageBox.warning(self, "Falha", "Não foi possível atualizar a entidade.")
                            return
                    else: # Adding Entity
                        entity_to_add = Entity(name=form_data['name'], type=form_data['type'], details_json=form_data['details_json'])
                        added_entity = self.db_manager.add_entity(entity_to_add)
                        if added_entity:
                            QMessageBox.information(self, "Sucesso", "Entidade adicionada com sucesso.")
                            self.entity_id = added_entity.id # Store new ID
                        else:
                            QMessageBox.warning(self, "Falha", "Não foi possível adicionar a entidade.")
                            return
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar: {e}")


# Bloco para teste independente (requer ajustes para a nova assinatura do construtor)
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    # Este teste precisa de um DatabaseManager funcional.
    # Para um teste rápido de UI, você pode mockar o db_manager.

    # --- Mock DatabaseManager para teste de UI ---
    class MockDBManager:
        def get_all_entities(self, entity_type: str):
            if entity_type == ENTITY_TYPE_PROFESSOR:
                return [Entity(id=1, name="Prof. Teste 1", type=ENTITY_TYPE_PROFESSOR),
                        Entity(id=2, name="Prof. Teste 2", type=ENTITY_TYPE_PROFESSOR)]
            return []
        def get_student_group(self, group_id: int):
            if group_id == 1:
                return StudentGroup(id=1, name="Turma A Existente", teacher_id=1)
            return None
        def get_entity_by_id(self, entity_id: int):
            if entity_id == 1:
                 return Entity(id=1, name="Prof. Exemplo", type=ENTITY_TYPE_PROFESSOR, details_json={"email": "prof@example.com"})
            return None
        def update_student_group(self, group_id, name, teacher_id): print(f"Mock: Update SG {group_id} {name} {teacher_id}"); return True
        def add_student_group(self, name, teacher_id): print(f"Mock: Add SG {name} {teacher_id}"); return StudentGroup(id=99, name=name, teacher_id=teacher_id)
        def update_entity(self, entity): print(f"Mock: Update E {entity.id} {entity.name}"); return True
        def add_entity(self, entity): print(f"Mock: Add E {entity.name}"); return Entity(id=99, name=entity.name, type=entity.type)

    app = QApplication(sys.argv)
    mock_db = MockDBManager()

    print("Testando diálogo Adicionar Turma:")
    dialog_add_turma = EntityDialog(db_manager=mock_db, entity_type=ENTITY_TYPE_STUDENT_GROUP)
    if dialog_add_turma.exec() == QDialog.DialogCode.Accepted:
        print(f"  Turma adicionada/editada ID: {dialog_add_turma.entity_id}")
    else:
        print("  Criação de nova turma cancelada.")

    print("\nTestando diálogo Editar Turma:")
    dialog_edit_turma = EntityDialog(db_manager=mock_db, entity_type=ENTITY_TYPE_STUDENT_GROUP, entity_id=1)
    if dialog_edit_turma.exec() == QDialog.DialogCode.Accepted:
         print(f"  Turma ID: {dialog_edit_turma.entity_id} salva.")
    else:
        print("  Edição de turma cancelada.")
        
    print("\nTestando diálogo Adicionar Professor:")
    dialog_add_prof = EntityDialog(db_manager=mock_db, entity_type=ENTITY_TYPE_PROFESSOR)
    if dialog_add_prof.exec() == QDialog.DialogCode.Accepted:
        print(f"  Professor adicionado/editado ID: {dialog_add_prof.entity_id}")
    else:
        print("  Criação de novo professor cancelada.")

    print("\nTestando diálogo Editar Professor:")
    dialog_edit_prof = EntityDialog(db_manager=mock_db, entity_type=ENTITY_TYPE_PROFESSOR, entity_id=1)
    if dialog_edit_prof.exec() == QDialog.DialogCode.Accepted:
        print(f"  Professor ID: {dialog_edit_prof.entity_id} salvo.")
    else:
        print("  Edição de professor cancelada.")

    sys.exit(app.exec())
