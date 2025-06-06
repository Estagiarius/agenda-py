import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame,
    QPushButton, QScrollArea, QSizePolicy, QApplication # QApplication for clipboard
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QMouseEvent, QColor, QPalette # Let's assume we might use an icon
from datetime import datetime, timedelta # Added datetime and timedelta

from src.core.models import Notification, Event # Added Event
from src.ui.toast_notification import ToastNotification # Import ToastNotification
from src.core.notification_service import NotificationService # Import NotificationService
from src.ui.agenda_view import AgendaView
from src.ui.tasks_view import TasksView
from src.ui.questions_view import QuestionsView
from src.ui.quiz_section_widget import QuizSectionWidget
from src.ui.entities_view import EntitiesView
from src.ui.settings_view import SettingsView 
from src.core.database_manager import DatabaseManager


class NotificationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NotificationPanel")
        self.db_manager = db_manager # Store db_manager instance

        # Signal to notify MainWindow to refresh UI
        self.refresh_needed = pyqtSignal()

        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0) # Panel itself has no margins
        main_v_layout.setSpacing(5)

        # Styling for the panel
        self.setStyleSheet("""
            NotificationPanel {
                background-color: #f0f0f0; /* Light grey background for the panel */
                border: 1px solid #cccccc;
                border-radius: 0px; /* No radius if it's part of main flow */
            }
        """)

        # Scroll Area for notification items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #ffffff; }") # White background for items
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.scroll_content_widget = QWidget() # This widget will contain the actual notification items
        self.scroll_layout = QVBoxLayout(self.scroll_content_widget)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Notifications added from top
        self.scroll_layout.setSpacing(8) # Spacing between notification items

        self.scroll_area.setWidget(self.scroll_content_widget)
        main_v_layout.addWidget(self.scroll_area)

        # Bottom buttons layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5, 5, 5, 5)

        self.mark_all_read_button = QPushButton("Marcar todas como lidas")
        self.mark_all_read_button.clicked.connect(self.handle_mark_all_as_read)
        button_layout.addWidget(self.mark_all_read_button)

        self.view_all_button = QPushButton("Ver todas as notificações")
        self.view_all_button.setEnabled(False) # For now
        self.view_all_button.clicked.connect(lambda: print("View all notifications clicked (not implemented)"))
        button_layout.addWidget(self.view_all_button)

        main_v_layout.addLayout(button_layout)

        self.setMinimumWidth(350) # Increased width
        self.setMaximumHeight(450) # Increased height

    def clear_notifications(self):
        """Clears all notification items from the scroll layout."""
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def load_notifications(self, notifications: list[Notification]):
        self.clear_notifications()
        if not notifications:
            placeholder = QLabel("Nenhuma notificação recente.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #888888; font-style: italic; padding: 20px;")
            self.scroll_layout.addWidget(placeholder)
            return

        for notification_obj in notifications:
            item_widget = MainWindow.NotificationItemWidget(notification_obj) # Use MainWindow as scope
            item_widget.notification_clicked.connect(self.handle_item_widget_clicked)
            self.scroll_layout.addWidget(item_widget)

    @pyqtSlot(int) # Ensure this slot is recognized
    def handle_item_widget_clicked(self, notification_id: int):
        # This is a bit of a workaround. Ideally, NotificationItemWidget handles its own DB update
        # and then signals a general refresh. Or MainWindow handles all DB interaction.
        # For now, let's assume MainWindow handles it.
        # This means this signal from NotificationItemWidget needs to reach MainWindow.
        # So, NotificationPanel should relay this signal or MainWindow connects directly.
        # Let's adjust: NotificationPanel will emit a signal that MainWindow connects to.
        self.item_clicked_passthrough.emit(notification_id)


    # Signal to be emitted by NotificationPanel when an item is clicked
    item_clicked_passthrough = pyqtSignal(int)


    def handle_mark_all_as_read(self):
        if self.db_manager:
            success = self.db_manager.mark_all_notifications_as_read()
            if success:
                self.refresh_needed.emit() # Signal MainWindow to refresh
            else:
                print("Falha ao marcar todas as notificações como lidas no DB.")
        else:
            print("DB Manager não disponível no Painel de Notificações.")


class MainWindow(QMainWindow):
    class NotificationItemWidget(QWidget):
        notification_clicked = pyqtSignal(int) # Signal with notification ID

        def __init__(self, notification: Notification, parent=None):
            super().__init__(parent)
            self.notification = notification
            self.setAutoFillBackground(True) # Important for background color changes

            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8) # Padding within item
            layout.setSpacing(4)

            self.title_label = QLabel(notification.title)
            self.title_label.setStyleSheet("font-weight: bold; font-size: 13px;")

            self.description_label = QLabel(notification.description)
            self.description_label.setWordWrap(True)
            self.description_label.setStyleSheet("font-size: 12px;")

            timestamp_str = notification.timestamp.strftime("%Y-%m-%d %H:%M") if notification.timestamp else "N/A"
            self.timestamp_label = QLabel(timestamp_str)
            self.timestamp_label.setStyleSheet("font-size: 10px; color: #777777; font-style: italic;")

            layout.addWidget(self.title_label)
            layout.addWidget(self.description_label)
            layout.addWidget(self.timestamp_label)

            self.set_read_style(notification.is_read)

            # Basic hover effect (can be done with eventFilter or stylesheet if preferred)
            self.setToolTip(f"Clique para { 'abrir e marcar como lida' if not notification.is_read else 'abrir' }.\nID: {notification.id}")


        def set_read_style(self, is_read: bool):
            self.notification.is_read = is_read # Update internal state
            palette = self.palette()
            if is_read:
                palette.setColor(QPalette.ColorRole.Window, QColor("#e8f0fe")) # Light blue for read
                self.title_label.setStyleSheet("font-weight: normal; font-size: 13px; color: #555;")
            else:
                palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff")) # White for unread
                self.title_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #000;")
            self.setPalette(palette)

        def mousePressEvent(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.LeftButton:
                self.notification_clicked.emit(self.notification.id)
                # Visual change happens after refresh from MainWindow based on DB state.
                # If immediate visual feedback before DB confirm is needed:
                # if not self.notification.is_read:
                #     self.set_read_style(True)
            super().mousePressEvent(event)

    def __init__(self, db_manager: DatabaseManager, parent=None): # db_manager como parâmetro
        super().__init__(parent) # Chamada única ao super

        self.db_manager = db_manager # Usar o db_manager passado
        # QApplication.instance().aboutToQuit.connect(self.cleanup_db_connection) # Pode ser mantido

        self.setWindowTitle("Agenda Pessoal") # Chamada única
        self.setGeometry(100, 100, 1024, 768)

        # --- Overall Layout Structure ---
        overall_central_widget = QWidget()
        self.setCentralWidget(overall_central_widget)
        top_level_layout = QVBoxLayout(overall_central_widget)
        top_level_layout.setContentsMargins(0, 0, 0, 0)
        top_level_layout.setSpacing(0)

        # --- Header Area ---
        header_widget = QWidget()
        header_widget.setObjectName("HeaderWidget")
        header_widget.setStyleSheet("#HeaderWidget { background-color: #e8e8e8; border-bottom: 1px solid #d0d0d0; }")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5) # Add some padding
        header_layout.setSpacing(10)

        header_title = QLabel("Agenda Pessoal") # Optional: Add a title to the header
        header_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header_title)
        header_layout.addStretch() # Pushes notification items to the right

        self.notification_icon_button = QPushButton("🔔") # Bell character
        self.notification_icon_button.setFixedSize(QSize(30, 30))
        self.notification_icon_button.setStyleSheet("QPushButton { border: none; font-size: 20px; }")
        self.notification_icon_button.setToolTip("Mostrar notificações")
        header_layout.addWidget(self.notification_icon_button)

        self.notification_counter_label = QLabel("0")
        self.notification_counter_label.setStyleSheet("""
            QLabel {
                background-color: red;
                color: white;
                font-size: 10px;
                font-weight: bold;
                border-radius: 7px; /* Make it round */
                padding: 1px 4px;
                min-width: 14px; /* Ensure it's somewhat circular even with single digit */
                min-height: 14px;
                text-align: center; /* Not directly supported, but padding helps */
            }
        """)
        self.notification_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center text
        self.notification_counter_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.notification_counter_label.hide() # Initially hidden
        header_layout.addWidget(self.notification_counter_label)

        top_level_layout.addWidget(header_widget)

        # --- Notification Panel (initially hidden, placed in the main flow) ---
        self.notification_panel = NotificationPanel(db_manager=self.db_manager) # Pass db_manager
        self.notification_panel.setVisible(False) # Start hidden
        self.notification_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_level_layout.addWidget(self.notification_panel)

        # Connect signals from NotificationPanel
        self.notification_panel.refresh_needed.connect(self.refresh_notifications_ui)
        self.notification_panel.item_clicked_passthrough.connect(self.handle_notification_item_clicked)


        # --- Main Content Area (nav menu + content stack) ---
        main_content_widget = QWidget() # This will now hold nav_menu and content_stack
        main_layout = QHBoxLayout(main_content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.nav_menu = QListWidget()
        self.nav_menu.setFixedWidth(200) # Largura fixa para o menu
        self.nav_menu.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border-right: 1px solid #d0d0d0;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #c0c0c0;
                color: black; /* Cor do texto quando selecionado */
            }
        """)


        # Área de Conteúdo (Páginas)
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: white;") # Fundo branco para a área de conteúdo

        # Adicionar menu e conteúdo ao main_layout (dentro do main_content_widget)
        main_layout.addWidget(self.nav_menu)
        main_layout.addWidget(self.content_stack)

        top_level_layout.addWidget(main_content_widget) # Add main content area to the top level
        top_level_layout.setStretch(2, 1) # Ensure main_content_widget takes remaining space

        # Itens do Menu e Páginas Correspondentes
        # Agora passamos o db_manager para todas as views principais
        self.add_menu_item("Agenda", AgendaView(self.db_manager)) 
        self.add_menu_item("Tarefas", TasksView(self.db_manager)) 
        self.add_menu_item("Banco de Perguntas", QuestionsView(self.db_manager))
        self.add_menu_item("Quiz", QuizSectionWidget(self.db_manager))
        self.add_menu_item("Entidades", EntitiesView(self.db_manager))
        self.add_menu_item("Configurações", SettingsView(self.db_manager)) # Substituído Placeholder

        # Conectar sinal do menu para mudar a página no QStackedWidget
        self.nav_menu.currentItemChanged.connect(self.change_page)

        # Connect notification icon click
        self.notification_icon_button.clicked.connect(self.toggle_notification_panel)

        # Selecionar o primeiro item por padrão
        if self.nav_menu.count() > 0:
            self.nav_menu.setCurrentRow(0)

        # Initialize notification count and timer
        self._update_notification_badge_count() # Renamed original method
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.perform_periodic_checks) # New slot
        self.notification_timer.start(60000) # 60 seconds, adjust as needed

        self.toast_shown_for_event_ids = set() # For tracking toasts shown for events this session
        self.active_toasts = [] # Optional: to keep track of active toast objects

        # Initialize NotificationService
        self.notification_service = NotificationService(self.db_manager)


    def show_toast_notification(self, title: str, message: str, duration: int = 7000):
        """Creates and shows a toast notification."""
        # Remove any toasts that might have been closed manually from active_toasts
        # This is a simple cleanup, more robust would involve signals from toast on close
        self.active_toasts = [t for t in self.active_toasts if t.isVisible()]

        toast = ToastNotification(title, message, duration, parent=self)
        self.active_toasts.append(toast)
        toast.show_toast()
        # To prevent too many toasts on screen, could limit self.active_toasts count here

    def add_menu_item(self, name: str, page_widget: QWidget):
        """Adiciona um item ao menu de navegação e a página correspondente ao QStackedWidget."""
        list_item = QListWidgetItem(name)
        # list_item.setIcon(QIcon.fromTheme("nome-do-icone")) # Exemplo
        self.nav_menu.addItem(list_item)
        
        # Se for um QLabel placeholder, centralizar e estilizar
        is_complex_view = isinstance(page_widget, (AgendaView, TasksView, QuestionsView, QuizSectionWidget, EntitiesView, SettingsView))
        if isinstance(page_widget, QLabel) and not is_complex_view:
            page_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_widget.setStyleSheet("font-size: 18px; color: #333;")

        self.content_stack.addWidget(page_widget)

    def change_page(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        """Muda a página visível no QStackedWidget com base no item selecionado no menu."""
        if current_item:
            index = self.nav_menu.row(current_item)
            self.content_stack.setCurrentIndex(index)

    def toggle_notification_panel(self):
        """Mostra ou esconde o painel de notificações e carrega/atualiza o conteúdo."""
        if self.notification_panel.isVisible():
            self.notification_panel.hide()
        else:
            self.notification_panel.show()
            self.load_notifications_into_panel() # Load/refresh content when shown

    def load_notifications_into_panel(self):
        """Carrega as notificações recentes no painel."""
        if not self.db_manager: # pragma: no cover
            print("DB Manager não disponível em load_notifications_into_panel")
            return
        try:
            # Fetch recent notifications, e.g., unread first, then read, limited count
            # For simplicity, let's get a mix for now, prioritizing unread.
            # A more sophisticated query might be needed in db_manager or logic here.
            unread_notifications = self.db_manager.get_notifications(unread_only=True, limit=10)
            num_to_fetch_read = 10 - len(unread_notifications)
            read_notifications = []
            if num_to_fetch_read > 0:
                read_notifications = self.db_manager.get_notifications(unread_only=False, limit=num_to_fetch_read)
                # Filter out any that might have been in unread_notifications if get_notifications unread_only=False includes unread
                read_ids = {n.id for n in unread_notifications}
                read_notifications = [n for n in read_notifications if n.id not in read_ids]

            # Combine and sort by timestamp again if necessary, or ensure db_manager does
            # For now, simple concatenation, then sort by timestamp desc.
            # The get_notifications already sorts by timestamp desc.
            # So, if unread are fetched first, they will be at the top if timestamps are close.
            # Or, fetch all (limit 20), then sort in Python:
            all_recent = self.db_manager.get_notifications(limit=20) # Fetch more and let panel sort or display as is
            self.notification_panel.load_notifications(all_recent)

        except Exception as e: # pragma: no cover
            print(f"Erro ao carregar notificações no painel: {e}")
            self.notification_panel.clear_notifications() # Clear on error
            # Optionally, show an error message in the panel

    def refresh_notifications_ui(self):
        """Atualiza a contagem de notificações e o painel se estiver visível."""
        self.update_notification_count() # Update the badge in the header
        if self.notification_panel.isVisible():
            self.load_notifications_into_panel() # Reload notifications in the panel

    @pyqtSlot(int)
    def handle_notification_item_clicked(self, notification_id: int):
        """Lida com o clique em um item de notificação."""
        print(f"Notification item {notification_id} clicked in MainWindow.")
        if self.db_manager:
            self.db_manager.mark_notification_as_read(notification_id)
            self.refresh_notifications_ui()
            # Futuramente: navegar para a view relevante se applicable
            # Ex: if notification_type == 'task_deadline' and related_item_id:
            #      self.go_to_task(related_item_id)
        QApplication.clipboard().setText(f"Notification ID: {notification_id}") # Copy ID for testing

    def _update_notification_badge_count(self): # Renamed from update_notification_count
        """Atualiza o contador de notificações (sineta) no header."""
        if not self.db_manager: # pragma: no cover
            print("DB Manager não disponível em _update_notification_badge_count")
            return
        try:
            unread_count = self.db_manager.get_unread_notification_count()
            if unread_count > 0:
                self.notification_counter_label.setText(str(unread_count if unread_count < 100 else "99+"))
                self.notification_counter_label.show()
            else:
                self.notification_counter_label.hide()
                self.notification_counter_label.setText("0")
        except Exception as e: # pragma: no cover
            print(f"Erro ao atualizar contagem de notificações (badge): {e}")
            self.notification_counter_label.hide()

    def perform_periodic_checks(self):
        """Realiza verificações periódicas: atualiza badge, gera notificações no DB e checa por eventos para toasts."""
        current_time_str = datetime.now().strftime('%H:%M:%S')
        print(f"[{current_time_str}] Performing periodic checks...")

        # 1. Update notification badge count (based on DB notifications)
        self._update_notification_badge_count()

        # 2. Generate DB notifications via NotificationService
        if self.notification_service:
            try:
                print(f"[{current_time_str}] Gerando lembretes de evento (DB)...")
                self.notification_service.generate_event_reminders()
                print(f"[{current_time_str}] Gerando lembretes de tarefa (DB)...")
                self.notification_service.generate_task_deadline_reminders()
            except Exception as e: # pragma: no cover
                print(f"Erro ao gerar notificações pelo NotificationService: {e}")

        # 3. Existing logic to show TOASTS for very imminent events (can be refined or merged later)
        # This part is about immediate on-screen toasts, distinct from DB notification generation.
        if not self.db_manager: # pragma: no cover
            print("DB Manager não disponível para checar eventos para toasts.")
            return

        try:
            now = datetime.now()
            todays_events: List[Event] = self.db_manager.get_events_by_date(now.date())

            # This window is for *immediate* toasts, e.g., event starts in 0-10 mins.
            # The NotificationService might have created DB notifications for 15-min reminders already.
            immediate_toast_window = timedelta(minutes=10)

            for event in todays_events:
                if event.id is None or not event.start_time:
                    continue
                if event.id in self.toast_shown_for_event_ids: # Check if toast was already shown THIS SESSION
                    continue

                time_to_event = event.start_time - now

                if timedelta(minutes=0) < time_to_event <= immediate_toast_window:
                    print(f"Evento '{event.title}' (ID: {event.id}) está começando em breve. Mostrando TOAST.")
                    self.show_toast_notification(
                        title=f"Lembrete Imediato: {event.title}",
                        message=f"Começa às {event.start_time.strftime('%H:%M')}."
                    )
                    self.toast_shown_for_event_ids.add(event.id)
        except Exception as e: # pragma: no cover
            print(f"Erro durante checagem de eventos para toasts: {e}")

    def cleanup_db_connection(self):
        """Fecha a conexão com o banco de dados."""
        print("Fechando conexão com o banco de dados...")
        if self.db_manager:
            self.db_manager.close()

    def closeEvent(self, event):
        """Sobrescreve o evento de fechamento da janela para limpar recursos."""
        self.cleanup_db_connection()
        super().closeEvent(event)


if __name__ == '__main__':
    # Este bloco é para testar a MainWindow diretamente.
    # O ponto de entrada principal da aplicação é src/main.py
    # Este bloco é para teste direto, mas agora MainWindow requer um db_manager.
    print("Para testar MainWindow diretamente, execute src/main.py.")
    print("Este if __name__ == '__main__' em main_window.py não iniciará a UI completa.")
    
    # Se ainda quiser testar isoladamente (exigirá um db_manager mock ou real):
    # app = QApplication(sys.argv)
    # # Criar um db_manager real para teste (cuidado com o caminho do DB)
    # test_db_path = os.path.join(os.path.dirname(__file__), "..", "data", "agenda_test_main_window.db")
    # os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    # print(f"Usando DB de teste para MainWindow: {test_db_path}")
    # db_manager_instance = DatabaseManager(database_path=test_db_path)
    # if not db_manager_instance.conn:
    #     print(f"Falha ao conectar ao DB de teste {test_db_path}. Saindo.")
    #     sys.exit(1)
    #
    # main_window = MainWindow(db_manager=db_manager_instance)
    # main_window.show()
    # exit_code = app.exec()
    # db_manager_instance.close() # Fechar conexão do DB de teste
    # sys.exit(exit_code)
    pass # Evita iniciar a UI incompleta por padrão.
