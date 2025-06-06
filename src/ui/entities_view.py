import sys
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QComboBox, QLabel, QMessageBox, QHeaderView, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional, List, Dict, Any

from src.core.database_manager import DatabaseManager
from src.core.models import Entity, StudentGroup, ENTITY_TYPE_STUDENT_GROUP, ENTITY_TYPE_PROFESSOR, ENTITY_TYPE_STUDENT # Adicionado StudentGroup e constantes
from src.ui.entity_dialog import EntityDialog

# Constante para o item de filtro "Turmas"
FILTER_TURMAS = "Turmas"

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
        # Adicionar tipos de entidade e "Turmas"
        # Idealmente, os tipos de entidade viriam do DB ou de uma lista mais dinâmica.
        self.type_filter_combo.addItems([ENTITY_TYPE_PROFESSOR.capitalize(), ENTITY_TYPE_STUDENT.capitalize(), FILTER_TURMAS, "Contato", "Outro"])
        self.type_filter_combo.setEditable(True)
        self.type_filter_combo.currentTextChanged.connect(self._load_entities) # Usar currentTextChanged para cobrir edição e seleção

        filter_layout.addWidget(self.type_filter_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Tabela de Entidades/Turmas
        self.entities_table = QTableWidget()
        # Colunas serão configuradas em _setup_table_columns
        self.entities_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.entities_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.entities_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.entities_table.verticalHeader().setVisible(False)
        self.entities_table.itemSelectionChanged.connect(self._on_entity_selected)
        
        header = self.entities_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # Outras colunas serão ajustadas em _setup_table_columns
        main_layout.addWidget(self.entities_table)

        # Botões de Ação
        action_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Adicionar") # Texto será dinâmico
        self.add_button.clicked.connect(self._add_item_dialog)
        action_buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Editar") # Texto será dinâmico
        self.edit_button.clicked.connect(self._edit_item_dialog)
        self.edit_button.setEnabled(False)
        action_buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Excluir") # Texto será dinâmico
        self.delete_button.clicked.connect(self._delete_item_dialog)
        self.delete_button.setEnabled(False)
        action_buttons_layout.addWidget(self.delete_button)
        
        main_layout.addLayout(action_buttons_layout)
        self._load_entities() # Carrega inicialmente com "Todos" ou o primeiro tipo

    def _setup_table_columns(self, entity_type_filter: str):
        self.entities_table.setColumnCount(0) # Limpar colunas existentes
        header = self.entities_table.horizontalHeader()

        if entity_type_filter == FILTER_TURMAS:
            self.entities_table.setColumnCount(2)
            self.entities_table.setHorizontalHeaderLabels(["Nome da Turma", "Professor Responsável"])
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.add_button.setText("Adicionar Turma")
            self.edit_button.setText("Editar Turma")
            self.delete_button.setText("Excluir Turma")
        else:
            self.entities_table.setColumnCount(3)
            self.entities_table.setHorizontalHeaderLabels(["Nome", "Tipo", "Detalhes (JSON)"])
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.add_button.setText("Adicionar Entidade")
            self.edit_button.setText("Editar Entidade")
            self.delete_button.setText("Excluir Entidade")
        self.entities_table.clearSelection()


    def _load_entities(self):
        self.current_selected_entity_id = None # Reset selection
        self.entities_table.setRowCount(0)
        self._update_action_buttons_state()

        entity_type_filter_display = self.type_filter_combo.currentText()
        self._setup_table_columns(entity_type_filter_display) # Configura colunas antes de popular

        if entity_type_filter_display == FILTER_TURMAS:
            student_groups = self.db_manager.get_all_student_groups()
            # Cache para nomes de professores para evitar múltiplas queries idênticas
            teacher_names_cache: Dict[int, str] = {}

            for group in student_groups:
                row_position = self.entities_table.rowCount()
                self.entities_table.insertRow(row_position)

                name_item = QTableWidgetItem(group.name)
                if group.id is not None:
                    name_item.setData(Qt.ItemDataRole.UserRole, group.id)
                self.entities_table.setItem(row_position, 0, name_item)

                teacher_name = "Nenhum"
                if group.teacher_id:
                    if group.teacher_id in teacher_names_cache:
                        teacher_name = teacher_names_cache[group.teacher_id]
                    else:
                        teacher = self.db_manager.get_entity_by_id(group.teacher_id)
                        if teacher:
                            teacher_name = teacher.name
                            teacher_names_cache[group.teacher_id] = teacher_name
                        else:
                            teacher_name = f"ID: {group.teacher_id} (Não encontrado)"

                teacher_item = QTableWidgetItem(teacher_name)
                # Desabilitar edição ou foco para este item, se necessário
                teacher_item.setFlags(teacher_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.entities_table.setItem(row_position, 1, teacher_item)

        else: # Carregar Entidades Genéricas
            actual_filter = entity_type_filter_display.lower()
            if entity_type_filter_display == "Todos" or not entity_type_filter_display.strip():
                actual_filter = None
            
            entities = self.db_manager.get_all_entities(entity_type=actual_filter)
            for entity in entities:
                row_position = self.entities_table.rowCount()
                self.entities_table.insertRow(row_position)

                name_item = QTableWidgetItem(entity.name)
                if entity.id is not None:
                    name_item.setData(Qt.ItemDataRole.UserRole, entity.id)
                self.entities_table.setItem(row_position, 0, name_item)

                type_item = QTableWidgetItem(entity.type.capitalize())
                self.entities_table.setItem(row_position, 1, type_item)

                details_str = json.dumps(entity.details_json) if entity.details_json else "{}"
                details_item = QTableWidgetItem(details_str)
                self.entities_table.setItem(row_position, 2, details_item)
        
        if self.entities_table.rowCount() > 0:
            self.entities_table.selectRow(0) # Selecionar a primeira linha automaticamente
        self._update_action_buttons_state()


    def _on_entity_selected(self):
        selected_items = self.entities_table.selectedItems()
        if not selected_items:
            self.current_selected_entity_id = None
        else:
            # O ID está sempre no primeiro item da linha (coluna 0)
            item_with_id = self.entities_table.item(selected_items[0].row(), 0)
            if item_with_id:
                entity_id_data = item_with_id.data(Qt.ItemDataRole.UserRole)
                self.current_selected_entity_id = int(entity_id_data) if entity_id_data is not None else None
            else: # Deve ser raro, mas em caso de tabela vazia ou problema
                self.current_selected_entity_id = None
        self._update_action_buttons_state()

    def _update_action_buttons_state(self):
        has_selection = self.current_selected_entity_id is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_current_filter_type(self) -> str:
        # Helper para normalizar o tipo de filtro selecionado
        filter_display_text = self.type_filter_combo.currentText()
        if filter_display_text == FILTER_TURMAS:
            return ENTITY_TYPE_STUDENT_GROUP
        elif filter_display_text == "Todos" or not filter_display_text.strip():
            # Se for "Todos", o add dialog deveria idealmente perguntar o tipo
            # ou ser desabilitado, ou abrir um tipo padrão.
            # Por agora, vamos assumir que "Adicionar" para "Todos" adicionará tipo "Outro" ou o primeiro da lista.
            # Para este exemplo, focamos em quando um tipo específico (ou Turmas) é selecionado.
            # Se o filtro for "Todos", a EntityDialog precisaria de um campo de tipo editável.
            # Para este PR, vamos assumir que o _add_item_dialog se baseia no tipo selecionado,
            # e se for "Todos", precisa de um tipo default para EntityDialog.
            # Para simplificar, o botão Adicionar pode usar o tipo padrão do EntityDialog se "Todos" for selecionado.
            # Ou, melhor, buscar o tipo da primeira entidade na lista, ou um tipo padrão como "Outro".
            # Para o escopo desta tarefa, vamos focar em quando o filtro é "Turmas" ou um tipo de Entidade específico.
            return self.type_filter_combo.itemText(1).lower() # Ex: Professor, se for o primeiro após "Todos"
        return filter_display_text.lower() # e.g. "professor", "aluno"

    def _add_item_dialog(self):
        current_filter_display = self.type_filter_combo.currentText()

        entity_type_to_add: str
        if current_filter_display == FILTER_TURMAS:
            entity_type_to_add = ENTITY_TYPE_STUDENT_GROUP
        elif current_filter_display == "Todos" or not current_filter_display.strip():
            # Se "Todos", precisamos de um tipo padrão para o diálogo de entidade genérico
            # Ou o EntityDialog poderia ter um seletor de tipo se nenhum tipo for passado.
            # Vamos usar o primeiro tipo de entidade como padrão (ex: Professor)
            # Ou um tipo genérico "contato" ou "outro"
            entity_type_to_add = ENTITY_TYPE_PROFESSOR # Ou um tipo mais genérico como "contato"
            # QMessageBox.information(self, "Info", "Adicionando entidade do tipo 'Professor' como padrão para filtro 'Todos'.")
        else:
            entity_type_to_add = current_filter_display.lower()

        dialog = EntityDialog(db_manager=self.db_manager, entity_type=entity_type_to_add, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Sucesso", f"{entity_type_to_add.capitalize()} adicionado/atualizado com sucesso.")
            self._load_entities()
            # Tentar selecionar o item recém-adicionado/editado
            if dialog.entity_id:
                for row in range(self.entities_table.rowCount()):
                    item = self.entities_table.item(row, 0)
                    if item and item.data(Qt.ItemDataRole.UserRole) == dialog.entity_id:
                        self.entities_table.selectRow(row)
                        break
        # else: A EntityDialog já mostra mensagens de erro/sucesso internas.

    def _edit_item_dialog(self):
        if not self.current_selected_entity_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um item para editar.")
            return

        current_filter_display = self.type_filter_combo.currentText()
        entity_id_to_edit = self.current_selected_entity_id

        entity_type_to_edit: str
        if current_filter_display == FILTER_TURMAS:
            entity_type_to_edit = ENTITY_TYPE_STUDENT_GROUP
        else:
            # Para entidades genéricas, precisamos saber o tipo exato da entidade selecionada.
            # Isso pode ser armazenado na tabela ou buscado.
            # Assumindo que a coluna 'Tipo' (índice 1) tem o tipo correto.
            selected_row = self.entities_table.currentRow()
            if selected_row < 0: return # Nenhuma linha selecionada

            type_item = self.entities_table.item(selected_row, 1) # Coluna do Tipo
            if not type_item:
                 QMessageBox.critical(self, "Erro", "Não foi possível determinar o tipo da entidade selecionada.")
                 return
            entity_type_to_edit = type_item.text().lower()


        dialog = EntityDialog(db_manager=self.db_manager, entity_type=entity_type_to_edit, entity_id=entity_id_to_edit, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Sucesso", f"{entity_type_to_edit.capitalize()} atualizado com sucesso.")
            self._load_entities()
            # Tentar re-selecionar
            for row in range(self.entities_table.rowCount()):
                item = self.entities_table.item(row, 0) # ID is in column 0 data
                if item and item.data(Qt.ItemDataRole.UserRole) == entity_id_to_edit:
                    self.entities_table.selectRow(row)
                    break
        # else: A EntityDialog já mostra mensagens de erro/sucesso internas.


    def _delete_item_dialog(self):
        if not self.current_selected_entity_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um item para excluir.")
            return

        item_id_to_delete = self.current_selected_entity_id
        current_filter_display = self.type_filter_combo.currentText()
        item_name = ""
        # Obter nome para mensagem de confirmação
        selected_row = self.entities_table.currentRow()
        if selected_row >=0:
            name_item = self.entities_table.item(selected_row, 0)
            if name_item:
                item_name = name_item.text()

        item_type_str = "item" # Genérico
        if current_filter_display == FILTER_TURMAS:
            item_type_str = "turma"
        elif current_filter_display != "Todos":
            item_type_str = f"entidade do tipo '{current_filter_display}'"


        reply = QMessageBox.question(self, "Confirmar Exclusão",
                                     f"Tem certeza que deseja excluir {item_type_str} '{item_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success = False
            if current_filter_display == FILTER_TURMAS:
                success = self.db_manager.delete_student_group(item_id_to_delete)
            else:
                # Para "Todos" ou tipo específico de entidade, precisamos garantir que estamos excluindo uma Entity
                # Se o filtro for "Todos", não sabemos se é StudentGroup ou Entity sem checar o DB
                # Mas como o delete_student_group e delete_entity operam em tabelas diferentes,
                # e current_selected_entity_id é o ID da linha, precisamos ter certeza.
                # O mais seguro é que _load_entities armazene o tipo real junto com o ID se o filtro for "Todos".
                # Por agora, assumimos que se não for FILTER_TURMAS, é uma Entity.
                success = self.db_manager.delete_entity(item_id_to_delete)

            if success:
                QMessageBox.information(self, "Sucesso", f"{item_type_str.capitalize()} '{item_name}' excluído(a).")
                self._load_entities()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir {item_type_str} '{item_name}'.")


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
