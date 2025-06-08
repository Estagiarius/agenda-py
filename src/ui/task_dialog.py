import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QDateEdit, QPushButton, QDialogButtonBox, QMessageBox,
    QCheckBox, QApplication
)
from PyQt6.QtCore import Qt, QDate, QDateTime
from typing import Optional
from datetime import datetime, date

from src.core.models import Task

class TaskDialog(QDialog):
    def __init__(self, task: Optional[Task] = None, parent=None):
        super().__init__(parent)
        self.task = task # Armazena a tarefa original se estiver editando

        if self.task:
            self.setWindowTitle("Editar Tarefa")
        else:
            self.setWindowTitle("Adicionar Nova Tarefa")

        self.setMinimumWidth(450) # Aumentar um pouco a largura para os campos

        # Layouts
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows) # Para melhor ajuste

        # Campos do formulário
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setAcceptRichText(False)
        self.description_edit.setFixedHeight(100)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])

        # Due Date com QCheckBox
        self.due_date_checkbox = QCheckBox("Definir Data de Vencimento")
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.due_date_edit.setEnabled(False) # Inicialmente desabilitado
        self.due_date_checkbox.toggled.connect(self.due_date_edit.setEnabled)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Open", "In Progress", "Completed"])
        
        # parent_event_id_edit - Opcional, não incluído nesta fase

        form_layout.addRow("Título:", self.title_edit)
        form_layout.addRow("Descrição:", self.description_edit)
        form_layout.addRow("Prioridade:", self.priority_combo)
        form_layout.addRow(self.due_date_checkbox) # Checkbox na sua própria linha
        form_layout.addRow("Data de Vencimento:", self.due_date_edit) # QDateEdit abaixo
        form_layout.addRow("Status:", self.status_combo)

        main_layout.addLayout(form_layout)

        # Botões
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        # Popular campos se estiver editando ou definir padrões
        if self.task:
            self.title_edit.setText(self.task.title)
            self.description_edit.setPlainText(self.task.description or "")
            self.priority_combo.setCurrentText(self.task.priority or "Medium")
            
            if self.task.due_date:
                self.due_date_checkbox.setChecked(True)
                self.due_date_edit.setDate(QDate(self.task.due_date.year, self.task.due_date.month, self.task.due_date.day))
                self.due_date_edit.setEnabled(True)
            else:
                self.due_date_checkbox.setChecked(False)
                self.due_date_edit.setDate(QDate.currentDate()) # Padrão para hoje se habilitado
                self.due_date_edit.setEnabled(False)

            self.status_combo.setCurrentText(self.task.status or "Open")
        else:
            # Valores padrão para nova tarefa
            self.priority_combo.setCurrentText("Medium")
            self.due_date_checkbox.setChecked(False) # Por padrão, sem data de vencimento
            self.due_date_edit.setDate(QDate.currentDate())
            self.due_date_edit.setEnabled(False)
            self.status_combo.setCurrentText("Open")

    def get_task_data(self) -> Optional[Task]:
        title = self.title_edit.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Campo Obrigatório", "O título da tarefa não pode estar vazio.")
            return None

        description = self.description_edit.toPlainText().strip()
        priority = self.priority_combo.currentText()
        
        due_date: Optional[datetime] = None
        if self.due_date_checkbox.isChecked():
            q_date = self.due_date_edit.date()
            # Convert QDate to datetime.datetime (at start of day)
            due_date = datetime(q_date.year(), q_date.month(), q_date.day())
            
        status = self.status_combo.currentText()
        
        # parent_event_id - não tratado nesta fase

        # Se estiver editando, use o ID existente e os timestamps de criação/atualização originais
        task_id = self.task.id if self.task else None
        created_at = self.task.created_at if self.task and self.task.created_at else None
        # updated_at será atualizado pelo trigger do DB, não precisa ser passado aqui
        # a menos que queiramos manter o valor original se o DB não o atualizar (o que não é o caso aqui)

        return Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status=status,
            parent_event_id=self.task.parent_event_id if self.task else None, # Manter o parent_event_id se já existir
            created_at=created_at
            # updated_at não é necessário aqui, o trigger cuida disso
        )

    def validate_and_accept(self):
        """Valida os dados antes de aceitar o diálogo."""
        self.task_data_to_save = self.get_task_data() # Armazena temporariamente
        if self.task_data_to_save:
            self.accept()
        # Se get_task_data() retornou None, é porque a validação falhou e uma QMessageBox já foi mostrada.

# Bloco para teste independente
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Teste para adicionar nova tarefa
    print("Testando diálogo de Adicionar Tarefa:")
    dialog_add = TaskDialog()
    if dialog_add.exec() == QDialog.DialogCode.Accepted:
        new_task = dialog_add.task_data_to_save
        if new_task:
            print("  Nova Tarefa:")
            print(f"    Título: {new_task.title}")
            print(f"    Prioridade: {new_task.priority}")
            print(f"    Data Venc.: {new_task.due_date.strftime('%d/%m/%Y') if new_task.due_date else 'N/A'}")
            print(f"    Status: {new_task.status}")
            print(f"    Descrição: {new_task.description}")
    else:
        print("  Criação de nova tarefa cancelada.")

    # Teste para editar tarefa existente
    print("\nTestando diálogo de Editar Tarefa:")
    sample_due_date = datetime(2024, 9, 15)
    existing_task = Task(
        id=1, 
        title="Tarefa Existente para Edição", 
        description="Descrição original da tarefa.",
        priority="High",
        due_date=sample_due_date,
        status="In Progress",
        created_at=datetime.now()
    )
    dialog_edit = TaskDialog(task=existing_task)
    if dialog_edit.exec() == QDialog.DialogCode.Accepted:
        edited_task = dialog_edit.task_data_to_save
        if edited_task:
            print("  Tarefa Editada:")
            print(f"    ID: {edited_task.id}")
            print(f"    Título: {edited_task.title}")
            print(f"    Prioridade: {edited_task.priority}")
            print(f"    Data Venc.: {edited_task.due_date.strftime('%d/%m/%Y') if edited_task.due_date else 'N/A'}")
            print(f"    Status: {edited_task.status}")
    else:
        print("  Edição de tarefa cancelada.")
        
    sys.exit(0)
