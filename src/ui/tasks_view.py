import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLabel, QMessageBox, QHeaderView, QDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional, List

from src.core.database_manager import DatabaseManager
from src.core.models import Task
from src.ui.task_dialog import TaskDialog # Importado TaskDialog

class TasksView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_selected_task_id: Optional[int] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Título
        title_label = QLabel("Gerenciador de Tarefas")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Filtros
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Todas", "Open", "In Progress", "Completed"])
        self.status_filter_combo.currentIndexChanged.connect(self._load_tasks)
        filter_layout.addWidget(self.status_filter_combo)
        
        # Adicionar mais filtros (ex: Prioridade) aqui no futuro, se necessário
        filter_layout.addStretch() # Empurra os filtros para a esquerda
        main_layout.addLayout(filter_layout)

        # Tabela de Tarefas
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(4) # Título, Prioridade, Data de Vencimento, Status
        self.tasks_table.setHorizontalHeaderLabels(["Título", "Prioridade", "Vencimento", "Status"])
        self.tasks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Não editável diretamente
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Selecionar linha inteira
        self.tasks_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection) # Apenas uma linha por vez
        self.tasks_table.verticalHeader().setVisible(False) # Esconder cabeçalho vertical (números das linhas)
        self.tasks_table.itemSelectionChanged.connect(self._on_task_selected)
        
        # Ajustar largura das colunas
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Título
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Prioridade
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Vencimento
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Status
        main_layout.addWidget(self.tasks_table)

        # Botões de Ação
        action_buttons_layout = QHBoxLayout()
        self.add_task_button = QPushButton("Adicionar Tarefa")
        self.add_task_button.clicked.connect(self._add_task_dialog) # Conectado
        action_buttons_layout.addWidget(self.add_task_button)

        self.edit_task_button = QPushButton("Editar Tarefa")
        self.edit_task_button.clicked.connect(self._edit_task_dialog) # Conectado
        self.edit_task_button.setEnabled(False)
        action_buttons_layout.addWidget(self.edit_task_button)

        self.delete_task_button = QPushButton("Excluir Tarefa")
        self.delete_task_button.clicked.connect(self._delete_task)
        self.delete_task_button.setEnabled(False)
        action_buttons_layout.addWidget(self.delete_task_button)
        
        self.toggle_status_button = QPushButton("Marcar como...") # Texto será dinâmico
        self.toggle_status_button.clicked.connect(self._toggle_task_status)
        self.toggle_status_button.setEnabled(False)
        action_buttons_layout.addWidget(self.toggle_status_button)

        main_layout.addLayout(action_buttons_layout)

        # Carregar tarefas inicialmente
        self._load_tasks()

    def _load_tasks(self):
        self.tasks_table.setRowCount(0) # Limpar tabela
        self.current_selected_task_id = None # Resetar seleção
        self._update_action_buttons_state() # Desabilitar botões de ação

        status_filter = self.status_filter_combo.currentText()
        if status_filter == "Todas":
            status_filter = None
        
        # Adicionar filtro de prioridade aqui se implementado
        
        tasks = self.db_manager.get_all_tasks(status=status_filter)

        for task in tasks:
            row_position = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row_position)

            title_item = QTableWidgetItem(task.title)
            # Armazenar o ID da tarefa no item do título (coluna 0)
            if task.id is not None:
                 title_item.setData(Qt.ItemDataRole.UserRole, task.id)

            priority_item = QTableWidgetItem(task.priority)
            due_date_str = task.due_date.strftime("%d/%m/%Y %H:%M") if task.due_date else "N/A"
            due_date_item = QTableWidgetItem(due_date_str)
            status_item = QTableWidgetItem(task.status)

            # Centralizar texto em algumas colunas para melhor aparência
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            due_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tasks_table.setItem(row_position, 0, title_item)
            self.tasks_table.setItem(row_position, 1, priority_item)
            self.tasks_table.setItem(row_position, 2, due_date_item)
            self.tasks_table.setItem(row_position, 3, status_item)
        
        if self.tasks_table.rowCount() > 0:
            self.tasks_table.selectRow(0) # Seleciona a primeira linha por padrão, se houver tarefas

    def _on_task_selected(self):
        selected_items = self.tasks_table.selectedItems()
        if not selected_items: # Nenhuma linha selecionada
            self.current_selected_task_id = None
        else:
            # Obter o ID da tarefa armazenado no item da primeira coluna da linha selecionada
            first_item_in_row = selected_items[0] # O item da primeira coluna (Título)
            task_id_data = first_item_in_row.data(Qt.ItemDataRole.UserRole)
            if task_id_data is not None:
                self.current_selected_task_id = int(task_id_data)
            else:
                self.current_selected_task_id = None # Caso não haja ID (não deve acontecer)
        
        self._update_action_buttons_state()

    def _update_action_buttons_state(self):
        has_selection = self.current_selected_task_id is not None
        self.edit_task_button.setEnabled(has_selection)
        self.delete_task_button.setEnabled(has_selection)
        self.toggle_status_button.setEnabled(has_selection)

        if has_selection:
            task = self.db_manager.get_task_by_id(self.current_selected_task_id)
            if task:
                if task.status == "Completed":
                    self.toggle_status_button.setText("Marcar como Aberta")
                else: # Open ou In Progress
                    self.toggle_status_button.setText("Marcar como Concluída")
            else: # Tarefa não encontrada (improvável se ID está selecionado)
                 self.toggle_status_button.setText("Marcar como...")
                 self.edit_task_button.setEnabled(False)
                 self.delete_task_button.setEnabled(False)
                 self.toggle_status_button.setEnabled(False)

    # --- Slots para botões de Ação ---
    def _add_task_dialog(self):
        dialog = TaskDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.task_data_to_save # Usar o dado validado e armazenado
            if task_data:
                new_task = self.db_manager.add_task(task_data)
                if new_task and new_task.id:
                    QMessageBox.information(self, "Sucesso", f"Tarefa '{new_task.title}' adicionada com ID: {new_task.id}.")
                    self._load_tasks()
                    # Tentar selecionar a tarefa recém-adicionada
                    for row in range(self.tasks_table.rowCount()):
                        item = self.tasks_table.item(row, 0) # Item do título (coluna 0)
                        if item and item.data(Qt.ItemDataRole.UserRole) == new_task.id:
                            self.tasks_table.selectRow(row)
                            break
                else:
                    QMessageBox.critical(self, "Erro", "Falha ao adicionar a tarefa no banco de dados.")

    def _edit_task_dialog(self):
        if not self.current_selected_task_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione uma tarefa para editar.")
            return

        task_to_edit = self.db_manager.get_task_by_id(self.current_selected_task_id)
        if not task_to_edit:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar a tarefa para edição.")
            self._load_tasks() # Recarrega para garantir consistência
            return

        dialog = TaskDialog(task=task_to_edit, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.task_data_to_save
            if task_data:
                if self.db_manager.update_task(task_data):
                    QMessageBox.information(self, "Sucesso", f"Tarefa '{task_data.title}' atualizada.")
                    self._load_tasks()
                    # Tentar re-selecionar a tarefa editada
                    for row in range(self.tasks_table.rowCount()):
                        item = self.tasks_table.item(row, 0)
                        if item and item.data(Qt.ItemDataRole.UserRole) == task_data.id:
                            self.tasks_table.selectRow(row)
                            break
                else:
                    QMessageBox.critical(self, "Erro", "Falha ao atualizar a tarefa no banco de dados.")

    def _delete_task(self):
        if not self.current_selected_task_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione uma tarefa para excluir.")
            return

        task = self.db_manager.get_task_by_id(self.current_selected_task_id)
        if not task:
            QMessageBox.critical(self, "Erro", "Tarefa não encontrada no banco de dados.")
            self._load_tasks() # Recarrega para refletir estado atual
            return

        reply = QMessageBox.question(self, "Confirmar Exclusão",
                                     f"Tem certeza que deseja excluir a tarefa '{task.title}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_task(self.current_selected_task_id):
                QMessageBox.information(self, "Sucesso", f"Tarefa '{task.title}' excluída.")
                self._load_tasks() # Recarrega a lista
            else:
                QMessageBox.critical(self, "Erro", "Falha ao excluir a tarefa do banco de dados.")
    
    def _toggle_task_status(self):
        if not self.current_selected_task_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione uma tarefa.")
            return
        
        task = self.db_manager.get_task_by_id(self.current_selected_task_id)
        if not task:
            QMessageBox.critical(self, "Erro", "Tarefa não encontrada.")
            self._load_tasks()
            return

        if task.status == "Completed":
            task.status = "Open"
        else:
            task.status = "Completed"
        
        if self.db_manager.update_task(task):
            QMessageBox.information(self, "Sucesso", f"Status da tarefa '{task.title}' atualizado para {task.status}.")
            self._load_tasks() # Recarrega para mostrar a mudança e atualizar o botão
            # Tentar re-selecionar a tarefa que foi alterada
            for row in range(self.tasks_table.rowCount()):
                item = self.tasks_table.item(row, 0) # Item do título onde o ID está
                if item and item.data(Qt.ItemDataRole.UserRole) == self.current_selected_task_id:
                    self.tasks_table.selectRow(row)
                    break
        else:
            QMessageBox.critical(self, "Erro", "Falha ao atualizar o status da tarefa.")


# Bloco para teste independente (opcional)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # É necessário um DatabaseManager funcional para este teste
    db_manager_instance = DatabaseManager(db_path='data/agenda.db')
    
    # Certifique-se de que o DB e as tabelas existem, e talvez adicione dados de exemplo
    # O __main__ do database_manager.py já faz isso.
    # python -m src.core.database_manager # Execute isso antes se o DB não existir/estiver vazio

    if not db_manager_instance.conn:
        print("Falha ao conectar ao DB. Teste da TasksView não pode continuar.")
        sys.exit(1)
    else:
        # Adicionar tarefas de exemplo se não existirem para teste rápido
        if not db_manager_instance.get_all_tasks():
            print("Populando com tarefas de exemplo para teste da TasksView...")
            db_manager_instance.add_task(Task(title="Revisar Documentação", priority="Medium", status="Open", due_date=datetime.now()))
            db_manager_instance.add_task(Task(title="Implementar Feature X", priority="High", status="In Progress"))
            db_manager_instance.add_task(Task(title="Teste Unitário Y", priority="High", status="Completed"))
    
    tasks_widget = TasksView(db_manager_instance)
    tasks_widget.setWindowTitle("Teste da TasksView")
    tasks_widget.setGeometry(100, 100, 800, 600)
    tasks_widget.show()
    
    exit_code = app.exec()
    if db_manager_instance.conn:
        db_manager_instance.close()
    sys.exit(exit_code)
