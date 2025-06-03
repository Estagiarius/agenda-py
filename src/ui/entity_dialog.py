import sys
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, 
    QComboBox, QPushButton, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any

from src.core.models import Entity

class EntityDialog(QDialog):
    def __init__(self, entity: Optional[Entity] = None, parent=None):
        super().__init__(parent)
        self.entity = entity

        if self.entity:
            self.setWindowTitle("Editar Entidade")
        else:
            self.setWindowTitle("Adicionar Nova Entidade")
        
        self.setMinimumWidth(400)

        # Layouts
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # Campos do formulário
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Professor", "Aluno", "Contato", "Outro"]) # Adicionar mais tipos se necessário
        self.type_combo.setEditable(True) # Permitir tipos personalizados

        self.details_json_edit = QTextEdit()
        self.details_json_edit.setPlaceholderText("Insira detalhes como um objeto JSON. Ex: {\"email\": \"nome@exemplo.com\", \"sala\": \"102\"}")
        self.details_json_edit.setFixedHeight(100)

        form_layout.addRow("Nome:", self.name_edit)
        form_layout.addRow("Tipo:", self.type_combo)
        form_layout.addRow("Detalhes (JSON):", self.details_json_edit)
        
        main_layout.addLayout(form_layout)

        # Botões
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        # Popular campos se estiver editando
        if self.entity:
            self.name_edit.setText(self.entity.name)
            self.type_combo.setCurrentText(self.entity.type or "")
            if self.entity.details_json:
                try:
                    # Formatar o JSON para melhor visualização no QTextEdit
                    details_str = json.dumps(self.entity.details_json, indent=4)
                    self.details_json_edit.setPlainText(details_str)
                except TypeError: # Caso details_json não seja serializável (improvável se bem formado)
                    self.details_json_edit.setPlainText(str(self.entity.details_json))
            else:
                self.details_json_edit.setPlainText("{}") # Padrão objeto JSON vazio
        else:
            # Valores padrão para nova entidade
            self.type_combo.setCurrentIndex(0) # Padrão para o primeiro item, ex: "Professor"
            self.details_json_edit.setPlainText("{}")


    def get_entity_data(self) -> Optional[Entity]:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Campo Obrigatório", "O nome da entidade não pode estar vazio.")
            return None

        entity_type = self.type_combo.currentText().strip()
        if not entity_type:
            # Poderíamos também validar contra uma lista de tipos permitidos se não fosse editável
            QMessageBox.warning(self, "Campo Obrigatório", "O tipo da entidade não pode estar vazio.")
            return None

        details_str = self.details_json_edit.toPlainText().strip()
        details_dict: Dict[str, Any] = {}
        if details_str: # Apenas tenta parsear se não estiver vazio
            try:
                details_dict = json.loads(details_str)
                if not isinstance(details_dict, dict):
                    QMessageBox.warning(self, "JSON Inválido", "O campo 'Detalhes' deve ser um objeto JSON válido (ex: {\"chave\": \"valor\"}).")
                    return None
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "JSON Inválido", f"Erro ao decodificar JSON no campo 'Detalhes':\n{e}")
                return None
        
        entity_id = self.entity.id if self.entity else None
        created_at = self.entity.created_at if self.entity and self.entity.created_at else None
        
        return Entity(
            id=entity_id,
            name=name,
            type=entity_type,
            details_json=details_dict,
            created_at=created_at
        )

    def validate_and_accept(self):
        self.entity_data_to_save = self.get_entity_data()
        if self.entity_data_to_save:
            self.accept()

# Bloco para teste independente
if __name__ == '__main__':
    app = QApplication(sys.argv)

    print("Testando diálogo de Adicionar Entidade:")
    dialog_add = EntityDialog()
    if dialog_add.exec() == QDialog.DialogCode.Accepted:
        new_entity = dialog_add.entity_data_to_save
        if new_entity:
            print("  Nova Entidade:")
            print(f"    Nome: {new_entity.name}")
            print(f"    Tipo: {new_entity.type}")
            print(f"    Detalhes: {new_entity.details_json}")
    else:
        print("  Criação de nova entidade cancelada.")

    print("\nTestando diálogo de Editar Entidade:")
    existing_entity = Entity(
        id=1, 
        name="Prof. Exemplo", 
        type="Professor",
        details_json={"email": "prof@example.com", "sala": "B102"},
        created_at=datetime.now()
    )
    dialog_edit = EntityDialog(entity=existing_entity)
    if dialog_edit.exec() == QDialog.DialogCode.Accepted:
        edited_entity = dialog_edit.entity_data_to_save
        if edited_entity:
            print("  Entidade Editada:")
            print(f"    ID: {edited_entity.id}")
            print(f"    Nome: {edited_entity.name}")
            print(f"    Detalhes: {edited_entity.details_json}")
    else:
        print("  Edição de entidade cancelada.")
        
    sys.exit(0)
