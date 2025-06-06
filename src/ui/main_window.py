import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
# from PyQt6.QtGui import QIcon

from src.core.models import Event # Added for type hinting
from datetime import date # Added for type hinting

from src.ui.agenda_view import AgendaView
from src.ui.tasks_view import TasksView
from src.ui.questions_view import QuestionsView
from src.ui.quiz_section_widget import QuizSectionWidget
from src.ui.entities_view import EntitiesView
from src.ui.settings_view import SettingsView
from src.ui.todays_classes_view import TodaysClassesView
from src.ui.class_registry_view import ClassRegistryView # Added
from src.core.database_manager import DatabaseManager

class MainWindow(QMainWindow):
    def __init__(self, db_manager: DatabaseManager, parent=None): # db_manager como parâmetro
        super().__init__(parent) # Chamada única ao super

        self.db_manager = db_manager # Usar o db_manager passado
        # QApplication.instance().aboutToQuit.connect(self.cleanup_db_connection) # Pode ser mantido

        self.setWindowTitle("Agenda Pessoal") # Chamada única
        self.setGeometry(100, 100, 1024, 768)

        # Widget central e layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remover margens do layout principal
        main_layout.setSpacing(0) # Remover espaçamento entre menu e conteúdo

        # Menu de Navegação (Lateral)
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

        # Adicionar menu e conteúdo ao layout principal
        main_layout.addWidget(self.nav_menu)
        main_layout.addWidget(self.content_stack)
        # main_layout.setStretch(1, 1) # Faz o content_stack expandir (já deve ser o comportamento padrão)

        # Itens do Menu e Páginas Correspondentes
        # Agora passamos o db_manager para todas as views principais
        self.add_menu_item("Agenda", AgendaView(self.db_manager))

        # Integrating TodaysClassesView (Diário de Classe)
        todays_classes_view_instance = TodaysClassesView(self.db_manager)
        self.add_menu_item("Diário de Classe", todays_classes_view_instance)

        self.add_menu_item("Tarefas", TasksView(self.db_manager)) 
        self.add_menu_item("Banco de Perguntas", QuestionsView(self.db_manager))
        self.add_menu_item("Quiz", QuizSectionWidget(self.db_manager))
        self.add_menu_item("Entidades", EntitiesView(self.db_manager))
        self.add_menu_item("Configurações", SettingsView(self.db_manager))

        # Create ClassRegistryView but don't add to menu; it's accessed contextually
        self.class_registry_view = ClassRegistryView(self.db_manager)
        self.content_stack.addWidget(self.class_registry_view)

        # Conectar sinal do menu para mudar a página no QStackedWidget
        self.nav_menu.currentItemChanged.connect(self.change_page)

        # Selecionar o primeiro item por padrão
        if self.nav_menu.count() > 0:
            self.nav_menu.setCurrentRow(0)

    def add_menu_item(self, name: str, page_widget: QWidget):
        """Adiciona um item ao menu de navegação e a página correspondente ao QStackedWidget."""
        list_item = QListWidgetItem(name)
        # list_item.setIcon(QIcon.fromTheme("nome-do-icone")) # Exemplo
        self.nav_menu.addItem(list_item)
        
        # Se for um QLabel placeholder, centralizar e estilizar
        # Updated to include TodaysClassesView and ClassRegistryView in complex views
        is_complex_view = isinstance(page_widget, (AgendaView, TodaysClassesView, ClassRegistryView, TasksView, QuestionsView, QuizSectionWidget, EntitiesView, SettingsView))
        if isinstance(page_widget, QLabel) and not is_complex_view:
            page_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_widget.setStyleSheet("font-size: 18px; color: #333;")

        self.content_stack.addWidget(page_widget)

    def change_page(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        """Muda a página visível no QStackedWidget com base no item selecionado no menu."""
        if current_item:
            # Check if the selected item is one of the main menu items that has a direct page
            # This prevents trying to find an index for a view not in nav_menu (like ClassRegistryView)
            # if it were somehow selected programmatically in nav_menu.
            # However, change_page is usually only called by user interaction with nav_menu.
            index = self.nav_menu.row(current_item)
            if index != -1 and index < self.content_stack.count(): # Basic sanity check
                 # Check if the target widget is TodaysClassesView or ClassRegistryView, and call refresh
                widget_to_show = self.content_stack.widget(index)
                if hasattr(widget_to_show, 'refresh_view'):
                    # print(f"DEBUG: Calling refresh_view for {widget_to_show.objectName()}")
                    widget_to_show.refresh_view()
                self.content_stack.setCurrentIndex(index)
    
    def show_class_registry_view(self, event: Event, class_date: date):
        """Switches to the ClassRegistryView and loads the specified class and date."""
        if self.class_registry_view:
            self.class_registry_view.set_class_and_date(event, class_date)
            self.content_stack.setCurrentWidget(self.class_registry_view)
            # Update window title or add to a breadcrumb if desired
            self.setWindowTitle(f"Diário de Classe - {event.title} ({class_date.strftime('%d/%m/%Y')})")

    def cleanup_db_connection(self):
        """Fecha a conexão com o banco de dados."""
        print("Fechando conexão com o banco de dados...")
        if self.db_manager:
            self.db_manager.close()

    def closeEvent(self, event_param): # Renamed event to event_param to avoid conflict with core.models.Event
        """Sobrescreve o evento de fechamento da janela para limpar recursos."""
        self.cleanup_db_connection()
        super().closeEvent(event_param)

    # Slot to handle returning to the main view (e.g., TodaysClassesView)
    def return_to_previous_view(self, default_view_name: str = "Diário de Classe"):
        """Returns to a specified main view, typically after an action in a sub-view."""
        self.setWindowTitle("Agenda Pessoal") # Reset window title

        # Find the index of the default_view_name in the nav_menu
        for i in range(self.nav_menu.count()):
            if self.nav_menu.item(i).text() == default_view_name:
                self.nav_menu.setCurrentRow(i) # This will trigger change_page
                # Ensure the view is refreshed if it's TodaysClassesView
                widget_to_show = self.content_stack.widget(i)
                if isinstance(widget_to_show, TodaysClassesView):
                    widget_to_show.refresh_view()
                return
        # Fallback if the named view is not found (should not happen with correct names)
        if self.nav_menu.count() > 0:
            self.nav_menu.setCurrentRow(0)


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
