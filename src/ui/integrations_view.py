from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QHBoxLayout, QSpacerItem, QSizePolicy, QMessageBox, QCheckBox, QComboBox
from PyQt6.QtGui import QPixmap # Keep for future, though not used for text logos
from PyQt6.QtCore import Qt, QTimer

class IntegrationsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IntegrationsView")
        self.service_states = {}
        self.service_widgets = {}
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Corrected Qt.AlignTop to Qt.AlignmentFlag.AlignTop

        title_label = QLabel("Gerenciamento de Integrações")
        title_label.setObjectName("IntegrationsTitle") # For styling
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Corrected Qt.AlignCenter to Qt.AlignmentFlag.AlignCenter
        main_layout.addWidget(title_label)

        self.services_layout = QVBoxLayout()
        main_layout.addLayout(self.services_layout)

        self._add_service_ui("Google Calendar", "google_calendar_logo.png")
        self._add_service_ui("Outlook Calendar", "outlook_calendar_logo.png")
        self._add_service_ui("Google Classroom", "google_classroom_logo.png")

        main_layout.addStretch(1)

        print("IntegrationsView UI initialized with new structure")

    def _add_service_ui(self, service_name, logo_filename):
        group_box = QGroupBox(service_name)
        group_box.setObjectName(f"groupBox_{service_name.lower().replace(' ', '_')}")

        service_group_layout = QVBoxLayout(group_box)
        header_layout = QHBoxLayout()

        simple_logo_text = "".join([word[0] for word in service_name.split() if word]) + "L"
        logo_label = QLabel(simple_logo_text)
        logo_label.setFixedSize(32, 32)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Corrected Qt.AlignCenter to Qt.AlignmentFlag.AlignCenter
        logo_label.setStyleSheet("border: 1px solid #cccccc; background-color: #f0f0f0; border-radius: 4px; font-weight: bold;")
        header_layout.addWidget(logo_label)

        description_label = QLabel(f"Integre com {service_name} para sincronizar seus dados.")
        description_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(description_label)

        status_label = QLabel("Desconectado")
        status_label.setObjectName(f"status_{service_name.lower().replace(' ', '_')}")
        status_label.setMinimumWidth(80)
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) # Corrected alignment flags
        header_layout.addWidget(status_label)

        header_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        connect_button = QPushButton("Conectar")
        connect_button.setObjectName(f"connect_{service_name.lower().replace(' ', '_')}")
        connect_button.clicked.connect(lambda checked, s_name=service_name: self._handle_connect_disconnect(s_name))
        header_layout.addWidget(connect_button)

        service_group_layout.addLayout(header_layout)

        sync_options_widget = QWidget()
        sync_options_widget.setObjectName(f"sync_options_{service_name.lower().replace(' ', '_')}")
        sync_options_inner_layout = QVBoxLayout(sync_options_widget)
        sync_options_inner_layout.setContentsMargins(5,5,5,5)

        # Clear the placeholder label if it was added (idempotent removal)
        for i in reversed(range(sync_options_inner_layout.count())) :
            widget_item = sync_options_inner_layout.itemAt(i)
            if widget_item is not None:
                widget = widget_item.widget()
                if widget is not None and isinstance(widget, QLabel) and "Opções de Sincronização serão exibidas aqui" in widget.text():
                    widget.deleteLater()
                    sync_options_inner_layout.takeAt(i) # Remove item from layout

        # Add specific sync options
        if service_name in ["Google Calendar", "Outlook Calendar"]:
            cb_sync_to = QCheckBox(f"Sincronizar eventos da Agenda para o {service_name}.")
            cb_sync_to.setObjectName(f"cb_sync_to_{service_name.lower().replace(' ', '_')}")
            sync_options_inner_layout.addWidget(cb_sync_to)

            cb_import_from = QCheckBox(f"Importar eventos do {service_name} para a Agenda.")
            cb_import_from.setObjectName(f"cb_import_from_{service_name.lower().replace(' ', '_')}")
            sync_options_inner_layout.addWidget(cb_import_from)

            cal_selection_layout = QHBoxLayout()
            cal_label = QLabel("Sincronizar com o calendário:")
            cal_selection_layout.addWidget(cal_label)

            combo_calendars = QComboBox()
            combo_calendars.setObjectName(f"combo_calendars_{service_name.lower().replace(' ', '_')}")
            combo_calendars.addItem(f"Calendário Principal ({service_name})", userData="primary")
            combo_calendars.addItem("Trabalho", userData="work_id_123")
            combo_calendars.addItem("Pessoal", userData="personal_id_456")
            combo_calendars.setMinimumWidth(200)
            cal_selection_layout.addWidget(combo_calendars)
            cal_selection_layout.addStretch()
            sync_options_inner_layout.addLayout(cal_selection_layout)

            self.service_widgets[service_name]['cb_sync_to'] = cb_sync_to
            self.service_widgets[service_name]['cb_import_from'] = cb_import_from
            self.service_widgets[service_name]['combo_calendars'] = combo_calendars

            save_sync_button = QPushButton("Salvar Configurações de Sincronização")
            save_sync_button.setObjectName(f"save_sync_{service_name.lower().replace(' ', '_')}")
            save_sync_button.clicked.connect(lambda checked, s_name=service_name: self._save_sync_settings(s_name))
            sync_options_inner_layout.addWidget(save_sync_button)
            self.service_widgets[service_name]['save_sync_button'] = save_sync_button
        else:
            no_options_label = QLabel(f"Não há opções de sincronização detalhadas para {service_name}.")
            no_options_label.setStyleSheet("font-style: italic; color: #555555;")
            sync_options_inner_layout.addWidget(no_options_label)

        sync_options_inner_layout.addStretch()
        sync_options_widget.setVisible(False) # Visibility handled by _update_service_ui

        service_group_layout.addWidget(sync_options_widget)

        self.services_layout.addWidget(group_box)

        self.service_widgets[service_name] = {
            'group_box': group_box,
            'status_label': status_label,
            'connect_button': connect_button,
            'sync_options_widget': sync_options_widget
        }

        self.service_states[service_name] = {'connected': False}
        self._update_service_ui(service_name)

    def _handle_connect_disconnect(self, service_name):
        current_state = self.service_states.get(service_name, {'connected': False})
        is_connected = current_state['connected']

        if is_connected:
            confirm_msg = f"Tem certeza que deseja desconectar de {service_name} e remover as configurações de sincronização?"
            reply = QMessageBox.question(self, f"Desconectar {service_name}", confirm_msg,
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.service_states[service_name]['connected'] = False
                print(f"Desconectado de {service_name}.")
            else:
                return # User cancelled disconnection
            self._update_service_ui(service_name) # Update UI after disconnection or if user cancelled (no state change then)
        else:  # Currently disconnected, so action is to connect
            print(f"Iniciando conexão com {service_name}...")

            widgets = self.service_widgets.get(service_name)
            if not widgets:
                print(f"Error: Widgets not found for {service_name} during connection attempt.")
                return

            widgets['status_label'].setText(f"Aguardando {service_name}...")
            widgets['status_label'].setStyleSheet("color: #007bff; font-weight: bold;") # Blue for "processing"
            widgets['connect_button'].setEnabled(False)
            widgets['connect_button'].setToolTip(f"Processando conexão com {service_name}...")

            # Simulate OAuth delay
            QTimer.singleShot(2500, lambda s_name=service_name: self._finalize_mock_connection(s_name))
            # Note: _update_service_ui is NOT called here directly, it's called by _finalize_mock_connection

    def _finalize_mock_connection(self, service_name):
        print(f"Finalizando conexão simulada para {service_name}.")
        if service_name in self.service_states:
            self.service_states[service_name]['connected'] = True
            # _update_service_ui will re-enable the button and set proper text/styles
            self._update_service_ui(service_name)
            print(f"{service_name} conectado (simulado após delay).")
        else:
            print(f"Error: Service state for {service_name} not found in _finalize_mock_connection.")

    def _save_sync_settings(self, service_name):
        widgets = self.service_widgets.get(service_name)
        if not widgets:
            print(f"Error: Widgets not found for {service_name} in _save_sync_settings.")
            return

        # Example of how to retrieve values (not used in this mock)
        sync_to_checked = widgets.get('cb_sync_to').isChecked() if widgets.get('cb_sync_to') else "N/A"
        import_from_checked = widgets.get('cb_import_from').isChecked() if widgets.get('cb_import_from') else "N/A"
        selected_calendar_data = widgets.get('combo_calendars').currentData() if widgets.get('combo_calendars') else "N/A"

        QMessageBox.information(self, "Configurações de Sincronização",
                                f"As configurações de sincronização para {service_name} foram salvas (simulado).\n"
                                f"Sincronizar para: {sync_to_checked}\n"
                                f"Importar de: {import_from_checked}\n"
                                f"Calendário: {selected_calendar_data}")
        print(f"Configurações de sincronização para {service_name} salvas (simulado).")

    def _update_service_ui(self, service_name):
        widgets = self.service_widgets.get(service_name)
        state = self.service_states.get(service_name, {'connected': False})

        if not widgets:
            print(f"Warning: Widgets not found for service {service_name} in _update_service_ui")
            return

        widgets['connect_button'].setEnabled(True) # Ensure button is re-enabled

        if state['connected']:
            widgets['connect_button'].setText("Desconectar")
            widgets['connect_button'].setToolTip(f"Revogar acesso e desconectar de {service_name}.")
            widgets['status_label'].setText("Conectado")
            widgets['status_label'].setStyleSheet("color: #28a745; font-weight: bold;") # Green color for connected
            if widgets['sync_options_widget']:
                widgets['sync_options_widget'].setVisible(True)
        else:
            widgets['connect_button'].setText("Conectar")
            widgets['connect_button'].setToolTip(f"Conectar com {service_name}.")
            widgets['status_label'].setText("Desconectado")
            widgets['status_label'].setStyleSheet("color: #dc3545; font-weight: bold;") # Red color for disconnected
            if widgets['sync_options_widget']:
                widgets['sync_options_widget'].setVisible(False)

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    view = IntegrationsView()
    view.setGeometry(100, 100, 700, 500) # Adjusted size for better visualization
    view.setWindowTitle("Teste de Visão de Integrações")
    view.show()
    sys.exit(app.exec())
