import sys
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QComboBox, QLabel, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional, List

from src.core.database_manager import DatabaseManager
from src.core.models import Entity
from src.ui.entity_dialog import EntityDialog # Importar o diálogo

class EntitiesView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_selected_entity_id: Optional[int] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        title_label = QLabel("Gerenciador de Entidades")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Filtros
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por tipo:"))
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItem("Todos") 
        # Popular com tipos existentes no DB? Poderia ser feito, mas para simplificar:
        self.type_filter_combo.addItems(["Professor", "Aluno", "Contato", "Outro"]) # Tipos comuns
        self.type_filter_combo.setEditable(True) # Permitir digitar outros tipos
        self.type_filter_combo.currentIndexChanged.connect(self._load_entities)
        self.type_filter_combo.lineEdit().editingFinished.connect(self._load_entities) # Para quando edita e pressiona Enter

        filter_layout.addWidget(self.type_filter_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Tabela de Entidades
        self.entities_table = QTableWidget()
        self.entities_table.setColumnCount(3) # Nome, Tipo, Detalhes JSON
        self.entities_table.setHorizontalHeaderLabels(["Nome", "Tipo", "Detalhes (JSON)"])
        self.entities_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.entities_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.entities_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.entities_table.verticalHeader().setVisible(False)
        self.entities_table.itemSelectionChanged.connect(self._on_entity_selected)
        
        header = self.entities_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Nome
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Tipo
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Detalhes
        main_layout.addWidget(self.entities_table)

        # Botões de Ação
        action_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Adicionar Entidade")
        self.add_button.clicked.connect(self._add_entity_dialog)
        action_buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Editar Entidade")
        self.edit_button.clicked.connect(self._edit_entity_dialog)
        self.edit_button.setEnabled(False)
        action_buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Excluir Entidade")
        self.delete_button.clicked.connect(self._delete_entity_dialog)
        self.delete_button.setEnabled(False)
        action_buttons_layout.addWidget(self.delete_button)
        
        main_layout.addLayout(action_buttons_layout)
        self._load_entities()

    def _load_entities(self):
        self.entities_table.setRowCount(0)
        self.current_selected_entity_id = None
        self._update_action_buttons_state()

        entity_type_filter = self.type_filter_combo.currentText()
        if entity_type_filter == "Todos" or not entity_type_filter.strip():
            entity_type_filter = None 
        
        entities = self.db_manager.get_all_entities(entity_type=entity_type_filter)

        for entity in entities:
            row_position = self.entities_table.rowCount()
            self.entities_table.insertRow(row_position)

            name_item = QTableWidgetItem(entity.name)
            if entity.id is not None:
                 name_item.setData(Qt.ItemDataRole.UserRole, entity.id)

            type_item = QTableWidgetItem(entity.type)
            
            details_str = ""
            if entity.details_json:
                try:
                    details_str = json.dumps(entity.details_json) # Mostrar como string compacta na tabela
                except TypeError:
                    details_str = str(entity.details_json) # Fallback

            details_item = QTableWidgetItem(details_str)

            self.entities_table.setItem(row_position, 0, name_item)
            self.entities_table.setItem(row_position, 1, type_item)
            self.entities_table.setItem(row_position, 2, details_item)
        
        if self.entities_table.rowCount() > 0:
            self.entities_table.selectRow(0)

    def _on_entity_selected(self):
        selected_items = self.entities_table.selectedItems()
        if not selected_items:
            self.current_selected_entity_id = None
        else:
            first_item_in_row = selected_items[0] # Item do Nome (coluna 0)
            entity_id_data = first_item_in_row.data(Qt.ItemDataRole.UserRole)
            self.current_selected_entity_id = int(entity_id_data) if entity_id_data is not None else None
        self._update_action_buttons_state()

    def _update_action_buttons_state(self):
        has_selection = self.current_selected_entity_id is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _add_entity_dialog(self):
        dialog = EntityDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entity_data = dialog.entity_data_to_save
            if entity_data:
                new_entity = self.db_manager.add_entity(entity_data)
                if new_entity and new_entity.id:
                    QMessageBox.information(self, "Sucesso", f"Entidade '{new_entity.name}' adicionada.")
                    self._load_entities()
                    # Tentar selecionar a entidade recém-adicionada
                    for row in range(self.entities_table.rowCount()):
                        item = self.entities_table.item(row, 0)
                        if item and item.data(Qt.ItemDataRole.UserRole) == new_entity.id:
                            self.entities_table.selectRow(row)
                            break
                else:
                    QMessageBox.critical(self, "Erro", "Falha ao adicionar a entidade no banco de dados.")

    def _edit_entity_dialog(self):
        if not self.current_selected_entity_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione uma entidade para editar.")
            return

        entity_to_edit = self.db_manager.get_entity_by_id(self.current_selected_entity_id)
        if not entity_to_edit:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar a entidade para edição.")
            self._load_entities()
            return

        dialog = EntityDialog(entity=entity_to_edit, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entity_data = dialog.entity_data_to_save
            if entity_data:
                if self.db_manager.update_entity(entity_data):
                    QMessageBox.information(self, "Sucesso", f"Entidade '{entity_data.name}' atualizada.")
                    self._load_entities()
                    for row in range(self.entities_table.rowCount()):
                        item = self.entities_table.item(row, 0)
                        if item and item.data(Qt.ItemDataRole.UserRole) == entity_data.id:
                            self.entities_table.selectRow(row)
                            break
                else:
                    QMessageBox.critical(self, "Erro", "Falha ao atualizar a entidade no banco de dados.")

    def _delete_entity_dialog(self):
        if not self.current_selected_entity_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione uma entidade para excluir.")
            return

        entity = self.db_manager.get_entity_by_id(self.current_selected_entity_id)
        if not entity: # Deve ser raro, mas por segurança
            QMessageBox.critical(self, "Erro", "Entidade não encontrada.")
            self._load_entities()
            return

        reply = QMessageBox.question(self, "Confirmar Exclusão",
                                     f"Tem certeza que deseja excluir a entidade '{entity.name}'?\n"
                                     "Isso também removerá quaisquer associações desta entidade com eventos.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_entity(self.current_selected_entity_id):
                QMessageBox.information(self, "Sucesso", f"Entidade '{entity.name}' excluída.")
                self._load_entities()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao excluir a entidade.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Execute `python -m src.core.database_manager` antes para popular o DB
    db_manager_instance = DatabaseManager(db_path='data/agenda.db')
    if not db_manager_instance.conn:
        QMessageBox.critical(None, "DB Error", "Não foi possível conectar ao banco de dados.")
        sys.exit(1)
    
    # Adicionar entidades de exemplo se não existirem (o add_sample_data já faz isso)
    # db_manager_instance.add_sample_data() 

    entities_widget = EntitiesView(db_manager_instance)
    entities_widget.setWindowTitle("Teste da EntitiesView")
    entities_widget.setGeometry(100, 100, 800, 600)
    entities_widget.show()
    
    exit_code = app.exec()
    if db_manager_instance.conn:
        db_manager_instance.close()
    sys.exit(exit_code)
