import sys
from typing import Optional  # Adicionado Dict

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget, QListWidget,
    QListWidgetItem, QLabel, QSplitter, QPushButton, QMessageBox,
    QScrollArea, QFormLayout, QDialog  # Adicionado QScrollArea, QFormLayout and QDialog
)

from src.core.database_manager import DatabaseManager
from src.ui.event_dialog import EventDialog


class AgendaView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_selected_event_id: Optional[int] = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) 
        main_layout.setSpacing(10) 

        # --- Lado Esquerdo: Calendário e Lista de Eventos ---
        left_layout_widget = QWidget()
        left_v_layout = QVBoxLayout(left_layout_widget) 
        left_v_layout.setContentsMargins(0,0,0,0)
        left_v_layout.setSpacing(10)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        left_v_layout.addWidget(self.calendar)

        action_buttons_layout = QHBoxLayout()
        self.add_event_button = QPushButton("Adicionar Evento")
        self.add_event_button.clicked.connect(self._add_event_dialog)
        action_buttons_layout.addWidget(self.add_event_button)

        self.edit_event_button = QPushButton("Editar Evento")
        self.edit_event_button.clicked.connect(self._edit_event_dialog)
        self.edit_event_button.setEnabled(False) 
        action_buttons_layout.addWidget(self.edit_event_button)

        self.delete_event_button = QPushButton("Excluir Evento")
        self.delete_event_button.clicked.connect(self._delete_event)
        self.delete_event_button.setEnabled(False) 
        action_buttons_layout.addWidget(self.delete_event_button)
        
        left_v_layout.addLayout(action_buttons_layout)

        self.events_list = QListWidget()
        self.events_list.currentItemChanged.connect(self._on_event_selected)
        self.events_list.setStyleSheet("QListWidget::item { padding: 5px; }")
        left_v_layout.addWidget(self.events_list)
        
        # --- Lado Direito: Detalhes do Evento com QLabels ---
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.setContentsMargins(0,0,0,0)

        details_title_label = QLabel("Detalhes do Evento")
        details_title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        right_panel_layout.addWidget(details_title_label)

        # ScrollArea para os detalhes
        details_scroll_area = QScrollArea()
        details_scroll_area.setWidgetResizable(True)
        details_scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f9f9f9; }") # Estilo similar ao QTextEdit anterior
        
        self.event_details_widget = QWidget() # Widget que conterá o QFormLayout
        details_form_layout = QFormLayout(self.event_details_widget)
        details_form_layout.setContentsMargins(10, 10, 10, 10)
        details_form_layout.setSpacing(8)
        details_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        details_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Inicializar QLabels para cada campo de detalhe
        self.detail_title_label = QLabel("-")
        self.detail_description_label = QLabel("-")
        self.detail_description_label.setWordWrap(True)
        self.detail_start_time_label = QLabel("-")
        self.detail_end_time_label = QLabel("-")
        self.detail_event_type_label = QLabel("-")
        self.detail_location_label = QLabel("-")
        self.detail_participants_label = QLabel("-")
        self.detail_participants_label.setWordWrap(True)

        # Adicionar QLabels ao QFormLayout
        details_form_layout.addRow("<b>Título:</b>", self.detail_title_label)
        details_form_layout.addRow("<b>Tipo:</b>", self.detail_event_type_label)
        details_form_layout.addRow("<b>Início:</b>", self.detail_start_time_label)
        details_form_layout.addRow("<b>Fim:</b>", self.detail_end_time_label)
        details_form_layout.addRow("<b>Local:</b>", self.detail_location_label)
        
        # Descrição e Participantes podem precisar de mais espaço ou formatação especial
        desc_title = QLabel("<b>Descrição:</b>")
        desc_title.setAlignment(Qt.AlignmentFlag.AlignTop) # Alinhar o rótulo "Descrição" ao topo
        details_form_layout.addRow(desc_title, self.detail_description_label)
        
        part_title = QLabel("<b>Participantes:</b>")
        part_title.setAlignment(Qt.AlignmentFlag.AlignTop)
        details_form_layout.addRow(part_title, self.detail_participants_label)

        details_scroll_area.setWidget(self.event_details_widget)
        right_panel_layout.addWidget(details_scroll_area)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_layout_widget)
        splitter.addWidget(right_panel_widget) 
        splitter.setSizes([350, 650]) 

        main_layout.addWidget(splitter)

        self._clear_details_labels() # Limpa os labels inicialmente
        self._on_date_selected() 

    def _clear_details_labels(self):
        """Limpa o texto de todos os QLabels de detalhes."""
        self.detail_title_label.setText("-")
        self.detail_description_label.setText("-")
        self.detail_start_time_label.setText("-")
        self.detail_end_time_label.setText("-")
        self.detail_event_type_label.setText("-")
        self.detail_location_label.setText("-")
        self.detail_participants_label.setText("Nenhum participante listado ou evento não selecionado.")
        # Adicionar um placeholder mais informativo se a área ficar muito vazia
        self.event_details_widget.setToolTip("Selecione um evento para ver os detalhes.")


    def _refresh_event_list_for_selected_date(self):
        """Atualiza a lista de eventos para a data atualmente selecionada no calendário."""
        selected_qdate = self.calendar.selectedDate()
        selected_date = selected_qdate.toPyDate()
        
        self.events_list.clear()
        # Não limpa os detalhes aqui, pois pode ser chamado após uma edição/deleção
        # e queremos manter o contexto ou limpá-lo seletivamente.

        events = self.db_manager.get_events_by_date(selected_date)

        if not events:
            item = QListWidgetItem("Nenhum evento para esta data.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.events_list.addItem(item)
            self.current_selected_event_id = None # Nenhum evento para selecionar
            self.edit_event_button.setEnabled(False)
            self.delete_event_button.setEnabled(False)
            self._clear_details_labels() # Limpa detalhes se não há eventos
            # _clear_details_labels() já define um texto padrão/placeholder
        else:
            for event_idx, event_obj in enumerate(events): # Renomeado para evitar conflito com models.Event
                if event_obj.start_time:
                    display_text = f"{event_obj.start_time.strftime('%H:%M')} - {event_obj.title}"
                else:
                    display_text = f"Horário Indef. - {event_obj.title}"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, event_obj.id)
                self.events_list.addItem(item)
            
            # Tentar manter o evento selecionado se ainda existir, ou selecionar o primeiro
            if self.current_selected_event_id:
                items = self.events_list.findItems(str(self.current_selected_event_id), Qt.MatchFlag.MatchExactly) # Isso não vai funcionar, ID está em UserRole
                # Precisamos iterar para encontrar pelo ID
                found_item_to_select = None
                for i in range(self.events_list.count()):
                    list_item = self.events_list.item(i)
                    if list_item and list_item.data(Qt.ItemDataRole.UserRole) == self.current_selected_event_id:
                        found_item_to_select = list_item
                        break
                if found_item_to_select:
                    self.events_list.setCurrentItem(found_item_to_select)
                else: # O evento selecionado anteriormente não está mais na lista (ex: mudou de data)
                    self.current_selected_event_id = None
                    self.events_list.setCurrentRow(0) # Seleciona o primeiro por padrão
            elif self.events_list.count() > 0 : # Se não havia seleção prévia, seleciona o primeiro
                 self.events_list.setCurrentRow(0)


    def _on_date_selected(self):
        """Chamado quando a data no calendário é alterada."""
        self.current_selected_event_id = None # Reseta a seleção de evento ao mudar de data
        self._clear_details_labels() # Limpa os detalhes ao mudar de data
        self._refresh_event_list_for_selected_date()
        # A seleção do primeiro item na lista (se houver) será tratada por _refresh_event_list...
        # que então chamará _on_event_selected.

    def _on_event_selected(self, current_item: Optional[QListWidgetItem], previous_item: Optional[QListWidgetItem]):
        self._clear_details_labels() # Limpa os labels antes de popular ou se não houver item
        if not current_item or current_item.data(Qt.ItemDataRole.UserRole) is None:
            self.current_selected_event_id = None
            self.edit_event_button.setEnabled(False)
            self.delete_event_button.setEnabled(False)
            # _clear_details_labels() já define um texto padrão/placeholder.
            return

        self.current_selected_event_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        if self.current_selected_event_id is None: # Checagem adicional, embora o if acima deva pegar
            self.edit_event_button.setEnabled(False)
            self.delete_event_button.setEnabled(False)
            # _clear_details_labels() já foi chamado no início.
            return

        event_obj = self.db_manager.get_event_by_id(self.current_selected_event_id)

        if event_obj:
            self.edit_event_button.setEnabled(True)
            self.delete_event_button.setEnabled(True)

            self.detail_title_label.setText(event_obj.title or "-")
            self.detail_event_type_label.setText(event_obj.event_type or "-")
            
            start_time_str = event_obj.start_time.strftime('%d/%m/%Y %H:%M') if event_obj.start_time else "-"
            self.detail_start_time_label.setText(start_time_str)
            
            end_time_str = event_obj.end_time.strftime('%d/%m/%Y %H:%M') if event_obj.end_time else "-"
            self.detail_end_time_label.setText(end_time_str)

            self.detail_location_label.setText(event_obj.location or "-")
            # Para a descrição, usar setTextFormat(Qt.TextFormat.RichText) se quiser manter quebras de linha simples como <br>
            # ou processar o texto para substituir \n por <br> se o QLabel suportar HTML básico.
            # Por simplicidade, vamos apenas setar o texto. WordWrap já está ativo.
            self.detail_description_label.setText(event_obj.description or "-")

            # Mostrar entidades vinculadas
            linked_entities = self.db_manager.get_entities_for_event(event_obj.id) # type: ignore
            if linked_entities:
                participants_html = "" # Usar HTML para formatação de lista no QLabel
                for entity, role in linked_entities:
                    participants_html += f"<li>{entity.name} ({entity.type}) - <i>{role}</i></li>"
                if participants_html: # Adiciona tags de lista se houver itens
                     self.detail_participants_label.setText(f"<ul>{participants_html}</ul>")
                else: # Caso raro de lista vazia após a checagem inicial
                    self.detail_participants_label.setText("Nenhum participante listado.")
            else:
                self.detail_participants_label.setText("Nenhum participante listado.")
            
            # Recorrência não está nos labels atuais, mas se estivesse, seria aqui.
            # Ex: self.detail_recurrence_label.setText(event_obj.recurrence_rule if event_obj.recurrence_rule else "-")
        else:
            # _clear_details_labels() já foi chamado no início e define placeholders.
            self.edit_event_button.setEnabled(False)
            self.delete_event_button.setEnabled(False)


    def _add_event_dialog(self):
        print("[AgendaView] _add_event_dialog called")
        # Passar db_manager para o EventDialog
        dialog = EventDialog(db_manager=self.db_manager, parent=self)
        if dialog.exec() == QDialog.accepted: # Changed to QDialog.Accepted
            print("[AgendaView] EventDialog accepted")
            # Acessar os dados salvos no diálogo
            event_data, selected_entities_map = dialog.event_data_to_save
            print(f"[AgendaView] Received event_data: {event_data}")
            print(f"[AgendaView] Received selected_entities_map: {selected_entities_map}")
            
            if event_data:
                print(f"[AgendaView] Calling db_manager.add_event with: {event_data}")
                new_event = self.db_manager.add_event(event_data)
                print(f"[AgendaView] Result from add_event: {new_event}")
                if new_event and new_event.id:
                    print(f"[AgendaView] Event added successfully (ID: {new_event.id}). Linking entities...")
                    # Salvar associações
                    for entity_id, role in selected_entities_map.items():
                        print(f"[AgendaView] Calling db_manager.link_entity_to_event for event_id={new_event.id}, entity_id={entity_id}, role={role}")
                        self.db_manager.link_entity_to_event(new_event.id, entity_id, role)
                    
                    QMessageBox.information(self, "Sucesso", f"Evento '{new_event.title}' adicionado com ID: {new_event.id}.")
                    if new_event.start_time:
                        self.calendar.setSelectedDate(QDate(new_event.start_time.year, new_event.start_time.month, new_event.start_time.day))
                    self.current_selected_event_id = new_event.id 
                    self._refresh_event_list_for_selected_date() 
                else:
                    print(f"[AgendaView] Failed to add event or event ID missing. new_event: {new_event}")
                    QMessageBox.critical(self, "Erro", "Falha ao adicionar o evento no banco de dados.")
    
    def _edit_event_dialog(self):
        if not self.current_selected_event_id:
            QMessageBox.warning(self, "Nenhum Evento Selecionado", "Por favor, selecione um evento para editar.")
            return

        event_to_edit = self.db_manager.get_event_by_id(self.current_selected_event_id)
        if not event_to_edit:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar o evento para edição.")
            self._load_tasks() # Deveria ser _refresh_event_list_for_selected_date ou _load_events
            return

        # Passar db_manager para o EventDialog
        dialog = EventDialog(db_manager=self.db_manager, event=event_to_edit, parent=self)
        if dialog.exec() == QDialog.accepted: # Changed to QDialog.Accepted
            
            event_data, selected_entities_map = dialog.event_data_to_save
            
            if event_data and event_data.id is not None: 
                if self.db_manager.update_event(event_data):
                    # Atualizar associações:
                    existing_linked_entities = self.db_manager.get_entities_for_event(event_data.id)
                    for entity, _ in existing_linked_entities:
                        if entity.id is not None:
                             self.db_manager.unlink_entity_from_event(event_data.id, entity.id)
                    
                    for entity_id, role in selected_entities_map.items():
                        self.db_manager.link_entity_to_event(event_data.id, entity_id, role)

                    QMessageBox.information(self, "Sucesso", f"Evento '{event_data.title}' atualizado.")
                    if event_data.start_time:
                         self.calendar.setSelectedDate(QDate(event_data.start_time.year, event_data.start_time.month, event_data.start_time.day))
                    self.current_selected_event_id = event_data.id 
                    self._refresh_event_list_for_selected_date()
                else:
                    QMessageBox.critical(self, "Erro", "Falha ao atualizar o evento no banco de dados.")

    def _delete_event(self):
        if not self.current_selected_event_id:
            QMessageBox.warning(self, "Nenhum Evento Selecionado", "Por favor, selecione um evento para excluir.")
            return

        event_to_delete = self.db_manager.get_event_by_id(self.current_selected_event_id)
        if not event_to_delete: # Deve ser raro, mas por segurança
            QMessageBox.critical(self, "Erro", "Evento não encontrado.")
            self._refresh_event_list_for_selected_date() # Atualiza a lista
            return

        reply = QMessageBox.question(self, "Confirmar Exclusão", 
                                     f"Tem certeza que deseja excluir o evento '{event_to_delete.title}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_event(self.current_selected_event_id):
                QMessageBox.information(self, "Sucesso", f"Evento '{event_to_delete.title}' excluído.")
                self.current_selected_event_id = None 
                self._clear_details_labels()
                self._refresh_event_list_for_selected_date() 
            else:
                QMessageBox.critical(self, "Erro", "Falha ao excluir o evento no banco de dados.")

    def _load_tasks(self):
        pass


# Bloco para teste independente da AgendaView (opcional)
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication

    # Primeiro, certifique-se de que o banco de dados e as tabelas existem,
    # e que há dados de exemplo.
    # O if __name__ == '__main__' em database_manager.py pode cuidar disso se executado.
    # python src/core/database_manager.py
    
    app = QApplication(sys.argv)
    
    # Crie uma instância do DatabaseManager
    # O DatabaseManager tentará criar o db e as tabelas se não existirem
    # e também adicionará um evento de exemplo para o dia atual.
    db_manager_instance = DatabaseManager(db_path='data/agenda.db')
    
    if not db_manager_instance.conn:
        print("Falha ao conectar ao banco de dados. A AgendaView pode não funcionar corretamente.")
        # Você pode querer sair ou mostrar uma mensagem de erro aqui
    else:
        # Para garantir que o evento de exemplo seja adicionado se o DB acabou de ser criado:
        # (O construtor do DBManager já chama _create_tables, mas add_sample_event é no if __name__ main)
        # Se o database_manager.py não foi executado separadamente, chame explicitamente:
        # db_manager_instance.add_sample_event() # Comentado pois o __main__ do DBManager já faz isso
        pass

    agenda_widget = AgendaView(db_manager_instance)
    
    # Para testar, crie uma janela simples para hospedar a AgendaView
    test_window = QWidget()
    test_layout = QVBoxLayout(test_window)
    test_layout.addWidget(agenda_widget)
    test_window.setWindowTitle("Teste da AgendaView")
    test_window.setGeometry(100, 100, 900, 700)
    test_window.show()
    
    exit_code = app.exec()
    
    # Fechar a conexão com o banco de dados ao sair
    if db_manager_instance.conn:
        db_manager_instance.close()
        print("Conexão com o DB fechada após o teste da AgendaView.")
        
    sys.exit(exit_code)