import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, 
    QDateTimeEdit, QPushButton, QDialogButtonBox, QMessageBox,
    QListWidget, QListWidgetItem, QCheckBox, QLabel, QScrollArea, QWidget as QtWidget, # Renomeado QWidget
    QSpacerItem, QSizePolicy # Added QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QDateTime
from typing import Optional, List, Tuple, Dict # Added Dict

from src.core.models import Event, Entity # Adicionado Entity
from src.core.database_manager import DatabaseManager # Necessário para carregar entidades

class EventDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, event: Optional[Event] = None, parent=None): # db_manager adicionado
        super().__init__(parent)
        self.db_manager = db_manager
        self.event = event
        self.all_available_entities: List[Entity] = []
        self.selected_entity_map: Dict[int, str] = {} # entity_id -> role (para este evento)
        self.event_data_to_save: Optional[Tuple[Event, Dict[int, str]]] = None # To store event and entity map

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

    def _clear_layout(self, layout):
        """Remove todos os widgets de um layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else: # Se for um layout, remover recursivamente
                    sub_layout = item.layout()
                    if sub_layout is not None:
                        self._clear_layout(sub_layout)

    def _load_and_display_entities(self):
        """Carrega entidades do banco de dados e as exibe como checkboxes."""
        # 1. Clear any existing widgets from self.participants_layout
        self._clear_layout(self.participants_layout)

        # 2. Fetch all entities using self.db_manager.get_all_entities()
        try:
            self.all_available_entities = self.db_manager.get_all_entities()
        except Exception as e:
            print(f"Erro ao carregar entidades: {e}")
            self.all_available_entities = []
            error_label = QLabel("Não foi possível carregar as entidades.")
            self.participants_layout.addWidget(error_label)
            # Add a spacer to push the error label to the top
            self.participants_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
            return

        # 3. QLabel "Participantes:" is handled by the main layout structure.
        # We focus on populating the checkboxes here.

        linked_entity_ids = set()
        # 4. If editing an event
        if self.event and self.event.id is not None:
            try:
                linked_entities = self.db_manager.get_entities_for_event(self.event.id)
                linked_entity_ids = {entity.id for entity in linked_entities if entity.id is not None}
            except Exception as e:
                print(f"Erro ao carregar entidades para o evento: {e}")

        if not self.all_available_entities:
            no_entities_label = QLabel("Nenhuma entidade disponível para seleção.")
            self.participants_layout.addWidget(no_entities_label)
        else:
            # 5. Iterate through self.all_available_entities
            for entity in self.all_available_entities:
                if entity.id is None: continue

                checkbox_text = f"{entity.name} ({entity.type})"
                checkbox = QCheckBox(checkbox_text)
                # Store the entity.id as data in the checkbox
                checkbox.setProperty("entity_id", entity.id)

                if entity.id in linked_entity_ids:
                    checkbox.setChecked(True)

                self.participants_layout.addWidget(checkbox)

        # 6. Add a QSpacerItem to self.participants_layout to push items to the top
        self.participants_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

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
        """Valida os dados, reconstrói o mapa de entidades selecionadas e aceita o diálogo."""
        # Clear and rebuild selected_entity_map based on checkbox states
        self.selected_entity_map.clear()
        for i in range(self.participants_layout.count()):
            widget_item = self.participants_layout.itemAt(i)
            if widget_item:
                widget = widget_item.widget()
                if isinstance(widget, QCheckBox) and widget.isChecked():
                    entity_id = widget.property("entity_id")
                    if entity_id is not None:
                        # Default role, pode ser expandido no futuro para permitir seleção de roles
                        self.selected_entity_map[entity_id] = "Participante"

        event_data = self.get_event_data() # Retorna um objeto Event ou None

        if event_data:
            # Estrutura self.event_data_to_save como (Event, Dict[int, str])
            self.event_data_to_save = (event_data, self.selected_entity_map)
            self.accept() # Fecha o diálogo com QDialog.Accepted
        else:
            # get_event_data já mostrou um QMessageBox de aviso.
            # self.event_data_to_save não é definido, e o diálogo permanece aberto.
            pass

# Bloco para teste independente do EventDialog
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    from datetime import datetime # Required for sample event

    # Mock DatabaseManager e entidades para teste
    class MockDBManager:
        def get_all_entities(self) -> List[Entity]:
            return [
                Entity(id=1, name="Alice", type="Pessoa", description="Advogada", created_at=datetime.now(), updated_at=datetime.now()),
                Entity(id=2, name="Caso XYZ", type="Processo", description="Disputa Contratual", created_at=datetime.now(), updated_at=datetime.now()),
                Entity(id=3, name="Bob", type="Pessoa", description="Cliente", created_at=datetime.now(), updated_at=datetime.now()),
            ]
        def get_entities_for_event(self, event_id: int) -> List[Entity]:
            if event_id == 1: # Simula que o evento 1 tem Alice e Caso XYZ vinculados
                return [
                    Entity(id=1, name="Alice", type="Pessoa", description="Advogada", created_at=datetime.now(), updated_at=datetime.now()),
                    Entity(id=2, name="Caso XYZ", type="Processo", description="Disputa Contratual", created_at=datetime.now(), updated_at=datetime.now()),
                ]
            return []

    mock_db = MockDBManager()
    app = QApplication(sys.argv)

    # Teste para adicionar novo evento
    # É necessário passar o db_manager para o construtor
    dialog_add = EventDialog(db_manager=mock_db)
    if dialog_add.exec() == QDialog.Accepted: # Usar QDialog.Accepted
        event_tuple = dialog_add.event_data_to_save
        if event_tuple:
            new_event, selected_entities = event_tuple
            print("Novo Evento (do diálogo de adição):")
            print(f"  Título: {new_event.title}")
            print(f"  Início: {new_event.start_time}")
            print(f"  Fim: {new_event.end_time}")
            print(f"  Tipo: {new_event.event_type}")
            print(f"  Local: {new_event.location}")
            print(f"  Descrição: {new_event.description}")
            print(f"  Entidades Selecionadas: {selected_entities}")
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
        created_at=datetime.now(), # Deve ser datetime
        updated_at=datetime.now()  # Deve ser datetime
    )
    # É necessário passar o db_manager para o construtor
    dialog_edit = EventDialog(db_manager=mock_db, event=existing_event)
    if dialog_edit.exec() == QDialog.Accepted: # Usar QDialog.Accepted
        event_tuple = dialog_edit.event_data_to_save
        if event_tuple:
            edited_event, selected_entities = event_tuple
            print("\nEvento Editado:")
            print(f"  ID: {edited_event.id}")
            print(f"  Título: {edited_event.title}")
            print(f"  Início: {edited_event.start_time}")
            print(f"  Entidades Selecionadas: {selected_entities}")
            # ... e outros campos conforme necessário
    else:
        print("\nEdição de evento cancelada.")
        
    # sys.exit(app.exec()) # Para rodar a aplicação de fato e ver os diálogos
    sys.exit(0) # Sair sem iniciar o loop de eventos principal para testes simples (como estava)
