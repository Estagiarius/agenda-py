import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QSize
# from PyQt6.QtGui import QIcon

from src.ui.agenda_view import AgendaView
from src.ui.tasks_view import TasksView
from src.ui.questions_view import QuestionsView
from src.ui.quiz_section_widget import QuizSectionWidget
from src.ui.entities_view import EntitiesView
from src.ui.settings_view import SettingsView 
from src.ui.reports_view import ReportsView # Added ReportsView
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
        self.add_menu_item("Tarefas", TasksView(self.db_manager)) 
        self.add_menu_item("Banco de Perguntas", QuestionsView(self.db_manager))
        self.add_menu_item("Quiz", QuizSectionWidget(self.db_manager))
        self.add_menu_item("Entidades", EntitiesView(self.db_manager))
        self.add_menu_item("Relatórios", ReportsView(self.db_manager)) # Added ReportsView
        self.add_menu_item("Configurações", SettingsView(self.db_manager)) # Substituído Placeholder

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
        is_complex_view = isinstance(page_widget, (AgendaView, TasksView, QuestionsView, QuizSectionWidget, EntitiesView, SettingsView, ReportsView)) # Added ReportsView
        if isinstance(page_widget, QLabel) and not is_complex_view:
            page_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_widget.setStyleSheet("font-size: 18px; color: #333;")

        self.content_stack.addWidget(page_widget)

    def change_page(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        """Muda a página visível no QStackedWidget com base no item selecionado no menu."""
        if current_item:
            index = self.nav_menu.row(current_item)
            self.content_stack.setCurrentIndex(index)
    
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
