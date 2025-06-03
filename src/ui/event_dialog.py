import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, 
    QDateTimeEdit, QPushButton, QDialogButtonBox, QMessageBox,
    QListWidget, QListWidgetItem, QCheckBox, QLabel, QScrollArea, QWidget as QtWidget # Renomeado QWidget
)
from PyQt6.QtCore import Qt, QDateTime
from typing import Optional, List, Tuple

from src.core.models import Event, Entity # Adicionado Entity
from src.core.database_manager import DatabaseManager # Necessário para carregar entidades

class EventDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, event: Optional[Event] = None, parent=None): # db_manager adicionado
        super().__init__(parent)
        self.db_manager = db_manager
        self.event = event
        self.all_available_entities: List[Entity] = []
        self.selected_entity_map: Dict[int, str] = {} # entity_id -> role (para este evento)

        if self.event:
            self.setWindowTitle("Editar Evento")
        else:
            self.setWindowTitle("Adicionar Novo Evento")

        self.setMinimumWidth(500) # Aumentar largura para acomodar participantes

        # Layouts
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Campos do formulário
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setAcceptRichText(False)
        self.description_edit.setFixedHeight(100)

        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setCalendarPopup(True)
        self.start_time_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        
        self.end_time_edit = QDateTimeEdit()
        self.end_time_edit.setCalendarPopup(True)
        self.end_time_edit.setDisplayFormat("dd/MM/yyyy HH:mm")

        self.event_type_edit = QLineEdit() # Poderia ser QComboBox
        self.location_edit = QLineEdit()
        # self.recurrence_rule_edit = QLineEdit() # Opcional por agora

        form_layout.addRow("Título:", self.title_edit)
        form_layout.addRow("Descrição:", self.description_edit)
        form_layout.addRow("Início:", self.start_time_edit)
        form_layout.addRow("Fim:", self.end_time_edit)
        form_layout.addRow("Tipo:", self.event_type_edit)
        form_layout.addRow("Local:", self.location_edit)
        # form_layout.addRow("Recorrência:", self.recurrence_rule_edit) # Ainda opcional

        main_layout.addLayout(form_layout)

        # --- Seção de Participantes/Entidades ---
        participants_label = QLabel("Participantes/Entidades Associadas:")
        main_layout.addWidget(participants_label)
        
        # Usaremos um QScrollArea para o caso de muitas entidades
        scroll_area_participants = QScrollArea()
        scroll_area_participants.setWidgetResizable(True)
        scroll_area_participants.setFixedHeight(150) # Altura fixa para a área de scroll
        
        self.participants_container = QtWidget() # Widget container para o layout das entidades
        self.participants_layout = QVBoxLayout(self.participants_container) # Layout para checkboxes de entidades
        scroll_area_participants.setWidget(self.participants_container)
        main_layout.addWidget(scroll_area_participants)

        self._load_and_display_entities()


        # Botões
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept) # validate_and_accept lidará com get_event_data
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        # Popular campos se estiver editando
        if self.event:
            self.title_edit.setText(self.event.title)
            self.description_edit.setPlainText(self.event.description or "")
            if self.event.start_time:
                self.start_time_edit.setDateTime(self.event.start_time)
            else: # Caso de evento existente sem start_time (improvável com lógica atual)
                self.start_time_edit.setDateTime(QDateTime.currentDateTime())
            
            if self.event.end_time:
                self.end_time_edit.setDateTime(self.event.end_time)
            else: # Se não houver end_time, pode-se deixar em branco ou usar start_time + 1h
                default_end_dt = self.start_time_edit.dateTime().addSecs(3600) # Adiciona 1 hora
                self.end_time_edit.setDateTime(default_end_dt)

            self.event_type_edit.setText(self.event.event_type or "")
            self.location_edit.setText(self.event.location or "")
            # self.recurrence_rule_edit.setText(self.event.recurrence_rule or "")
        else:
            # Valores padrão para novo evento
            self.start_time_edit.setDateTime(QDateTime.currentDateTime())
            self.end_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600)) # Padrão 1 hora depois

    def get_event_data(self) -> Optional[Event]:
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        
        # QDateTimeEdit retorna QDateTime, converter para datetime.datetime
        start_time_qdt = self.start_time_edit.dateTime()
        start_time = start_time_qdt.toPyDateTime()

        end_time_qdt = self.end_time_edit.dateTime()
        end_time = end_time_qdt.toPyDateTime()
        
        # Validação
        if not title:
            QMessageBox.warning(self, "Campo Obrigatório", "O título do evento não pode estar vazio.")
            return None
        
        if end_time < start_time:
            QMessageBox.warning(self, "Data Inválida", "A hora de término não pode ser anterior à hora de início.")
            return None

        event_type = self.event_type_edit.text().strip()
        location = self.location_edit.text().strip()
        # recurrence_rule = self.recurrence_rule_edit.text().strip()

        # Se estiver editando, use o ID existente e os timestamps de criação/atualização originais
        event_id = self.event.id if self.event else None
        created_at = self.event.created_at if self.event and self.event.created_at else None
        updated_at = self.event.updated_at if self.event and self.event.updated_at else None # Será atualizado pelo trigger

        return Event(
            id=event_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
            location=location,
            recurrence_rule=None, # recurrence_rule, # Adicionar quando o campo estiver ativo
            created_at=created_at, 
            updated_at=updated_at 
        )

    def validate_and_accept(self):
        """Valida os dados antes de aceitar o diálogo."""
        self.event_data_to_save = self.get_event_data() # Armazena temporariamente
        if self.event_data_to_save:
            self.accept()
        # Se get_event_data() retornou None, é porque a validação falhou e uma QMessageBox já foi mostrada.
        # O diálogo não será fechado.

# Bloco para teste independente do EventDialog
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Teste para adicionar novo evento
    dialog_add = EventDialog()
    if dialog_add.exec() == QDialog.DialogCode.Accepted:
        new_event = dialog_add.event_data_to_save # Usar o dado armazenado
        if new_event:
            print("Novo Evento (do diálogo de adição):")
            print(f"  Título: {new_event.title}")
            print(f"  Início: {new_event.start_time}")
            print(f"  Fim: {new_event.end_time}")
            print(f"  Tipo: {new_event.event_type}")
            print(f"  Local: {new_event.location}")
            print(f"  Descrição: {new_event.description}")
    else:
        print("Criação de novo evento cancelada.")

    # Teste para editar evento existente
    sample_start_time = datetime(2024, 8, 20, 10, 0, 0)
    sample_end_time = datetime(2024, 8, 20, 12, 0, 0)
    existing_event = Event(
        id=1, 
        title="Evento Existente", 
        description="Esta é uma descrição.",
        start_time=sample_start_time,
        end_time=sample_end_time,
        event_type="Reunião",
        location="Sala 101",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    dialog_edit = EventDialog(event=existing_event)
    if dialog_edit.exec() == QDialog.DialogCode.Accepted:
        edited_event = dialog_edit.event_data_to_save # Usar o dado armazenado
        if edited_event:
            print("\nEvento Editado:")
            print(f"  ID: {edited_event.id}")
            print(f"  Título: {edited_event.title}")
            print(f"  Início: {edited_event.start_time}")
            # ... e outros campos conforme necessário
    else:
        print("\nEdição de evento cancelada.")
        
    sys.exit(0) # Sair sem iniciar o loop de eventos principal para testes simples
