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
from src.ui.assessments_view import AssessmentsView
from src.ui.grades_entry_view import GradesEntryView
from src.ui.gradebook_view import GradebookView # Added
from src.ui.settings_view import SettingsView 
from src.core.database_manager import DatabaseManager

class MainWindow(QMainWindow):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)

        self.db_manager = db_manager
        self.setWindowTitle("Agenda Pessoal")
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
        self.agenda_view = AgendaView(self.db_manager)
        self.tasks_view = TasksView(self.db_manager)
        self.questions_view = QuestionsView(self.db_manager)
        self.quiz_view = QuizSectionWidget(self.db_manager)
        self.entities_view = EntitiesView(self.db_manager)
        self.assessments_view = AssessmentsView(self.db_manager)
        self.grades_entry_view = GradesEntryView(self.db_manager)
        self.gradebook_view = GradebookView(self.db_manager) # Instantiate GradebookView
        self.settings_view = SettingsView(self.db_manager)

        self.add_menu_item("Agenda", self.agenda_view)
        self.add_menu_item("Tarefas", self.tasks_view)
        self.add_menu_item("Perguntas", self.questions_view)
        self.add_menu_item("Quiz", self.quiz_view)
        self.add_menu_item("Entidades", self.entities_view)
        self.add_menu_item("Avaliações", self.assessments_view)
        self.add_menu_item("Boletim", self.gradebook_view) # Add GradebookView to menu
        self.add_menu_item("Configurações", self.settings_view)

        # Add GradesEntryView to the stack but not to the nav menu (already done for grades_entry_view)
        # self.content_stack.addWidget(self.grades_entry_view) # Already added if following pattern
        # self.page_map = {widget: i for i, widget in enumerate(self.content_stack.widget(i) for i in range(self.content_stack.count()))}
        # Rebuild page_map after all widgets are added
        self._build_page_map()


        # Conectar sinal do menu para mudar a página no QStackedWidget
        self.nav_menu.currentItemChanged.connect(self._on_nav_menu_changed)

        # Conectar sinal da AssessmentsView para navegação para GradesEntryView
        self.assessments_view.request_grades_entry_view.connect(self._show_grades_entry_page)
        # Conectar sinal da GradesEntryView para voltar para AssessmentsView após salvar (ou um botão "Voltar")
        self.grades_entry_view.grades_saved.connect(self._return_to_assessments_view_after_save)


        # Selecionar o primeiro item por padrão
        if self.nav_menu.count() > 0:
            self.nav_menu.setCurrentRow(0)

    def add_menu_item(self, name: str, page_widget: QWidget):
        """Adiciona um item ao menu de navegação e a página correspondente ao QStackedWidget."""
        list_item = QListWidgetItem(name)
        self.nav_menu.addItem(list_item)
        
        # Se for um QLabel placeholder, centralizar e estilizar
        is_complex_view = not isinstance(page_widget, QLabel) # Invertido para clareza
        if isinstance(page_widget, QLabel) and not is_complex_view: # Esta condição se torna redundante
             pass # Não deve acontecer com as views atuais
        elif is_complex_view:
            # Adiciona ao stack apenas se for uma view complexa (não QLabel placeholder)
            # Esta lógica está um pouco confusa, simplificando: addWidget sempre
            pass # page_widget já é adicionado abaixo de qualquer forma

        # Adiciona todas as páginas (exceto GradesEntryView que é adicionada manualmente)
        if name != "Lançar Notas": # Evitar adicionar a view de lançamento de notas no mapeamento de menu direto
            self.content_stack.addWidget(page_widget)


    def _on_nav_menu_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        """Muda a página visível no QStackedWidget com base no item selecionado no menu."""
        if current_item:
            # Encontrar o widget associado ao nome do item de menu
            # Isso requer que os nomes dos itens de menu correspondam a como as views foram adicionadas
            # O QStackedWidget usa índices. A ordem de add_menu_item e addWidget deve ser consistente.

            # Use page_map to find the target widget's index
            target_widget_name = current_item.text()
            target_widget_instance = None

            # This mapping needs to be robust. Let's find the widget instance by its name in the menu.
            # Assuming add_menu_item adds widgets to content_stack in the same order as to nav_menu.
            # Or, better, store the widget itself or its direct index in ListWidgetItem's data.
            # For now, let's try to find the widget by iterating through what add_menu_item added.

            # Find the widget associated with the current_item text.
            # This is a bit fragile; a direct mapping from item to widget would be better.
            # For now, we find the index in nav_menu and assume it corresponds to an index in content_stack
            # for views that are in the nav_menu.
            nav_index = self.nav_menu.row(current_item)
            if nav_index < (self.content_stack.count() -1 if self.grades_entry_view in self.content_stack.children() else self.content_stack.count()):
                # The -1 for grades_entry_view is tricky if it's not always the last one or always present.
                # Let's use a more direct approach for page switching.
                # The widget itself can be stored as data in QListWidgetItem, or map names to widgets.

                # Simplified: Find widget by its position in nav_menu matching content_stack
                # This assumes that widgets added via add_menu_item are in the same order in content_stack
                # (excluding manually added ones like grades_entry_view).

                # Let's refine add_menu_item to store the widget or its index.
                # For now, we'll rely on the index from nav_menu if the item is known.
                # This is where self.page_widget_map created in _build_page_map is useful.

                found_widget = self.menu_item_to_widget_map.get(current_item)
                if found_widget:
                    self.content_stack.setCurrentWidget(found_widget)
                    if hasattr(found_widget, 'refresh_view'): # Call refresh if view has it
                        found_widget.refresh_view()
                else:
                     print(f"Alerta: Widget não encontrado no mapeamento para o item de menu '{current_item.text()}'.")


    def _show_grades_entry_page(self, assessment_id: int):
        """Mostra a página de lançamento de notas para a avaliação especificada."""
        # Ensure "Avaliações" is visually selected in the nav menu without causing a recursive switch.
        # This is tricky if setCurrentRow itself triggers _on_nav_menu_changed which then switches page.
        # A common way is to have a flag or temporarily disconnect signals.

        # Temporarily disconnect the signal to prevent _on_nav_menu_changed from firing
        try:
            self.nav_menu.currentItemChanged.disconnect(self._on_nav_menu_changed)
        except TypeError: # Signal was not connected
            pass

        for i in range(self.nav_menu.count()):
            if self.nav_menu.item(i).text() == "Avaliações":
                self.nav_menu.setCurrentRow(i)
                break

        # Reconnect the signal
        self.nav_menu.currentItemChanged.connect(self._on_nav_menu_changed)

        self.grades_entry_view.load_assessment_data(assessment_id)
        self.content_stack.setCurrentWidget(self.grades_entry_view)


    def _return_to_assessments_view_after_save(self):
        """Retorna para a tela de AssessmentsView, tipicamente após salvar notas."""
        # Find the QListWidgetItem corresponding to AssessmentsView to set it current
        # This will trigger _on_nav_menu_changed, which should handle showing AssessmentsView
        # and calling its refresh_view method.
        target_widget_instance = self.assessments_view
        for i in range(self.nav_menu.count()):
            item = self.nav_menu.item(i)
            # Check if this item corresponds to the assessments_view instance
            # This requires a way to map item to widget, e.g. storing widget in item.data()
            # or checking item.text()
            if item.text() == "Avaliações": # Assuming "Avaliações" is the text for assessments_view
                self.nav_menu.setCurrentItem(item) # This will trigger _on_nav_menu_changed
                # _on_nav_menu_changed should call refresh_view on the target widget
                break

        # Fallback if not found by text (e.g. if text changes or for more robust solution)
        # if self.assessments_view in self.page_map:
        #    self.content_stack.setCurrentWidget(self.assessments_view)
        #    if hasattr(self.assessments_view, 'refresh_view'):
        #        self.assessments_view.refresh_view()


    def _build_page_map(self):
        """Builds a map from QListWidgetItems to their corresponding QWidget pages."""
        self.menu_item_to_widget_map = {}
        # This assumes add_menu_item adds to nav_menu and addWidget to content_stack in sync for menu items.
        # And that GradesEntryView is added to content_stack but not nav_menu.

        # Map items in nav_menu to widgets in content_stack
        # This requires careful ordering or storing widget reference in QListWidgetItem.data

        # Let's assume widgets added by add_menu_item are in order.
        # `add_menu_item` should be the sole responsible for adding to both `nav_menu` and `content_stack` (for menu items)
        # For now, let's try to map based on the order they were added.
        # This is still a bit fragile. A better way is in add_menu_item:
        # list_item.setData(Qt.ItemDataRole.UserRole, page_widget)
        # Then in _on_nav_menu_changed: page_widget = current_item.data(Qt.ItemDataRole.UserRole)

        # Simplified mapping for now, assuming direct correspondence for items added via add_menu_item
        # This map helps _on_nav_menu_changed to directly get the widget.
        idx = 0
        if self.agenda_view: self.menu_item_to_widget_map[self.nav_menu.findItems("Agenda", Qt.MatchFlag.MatchExactly)[0]] = self.agenda_view; idx+=1
        if self.tasks_view: self.menu_item_to_widget_map[self.nav_menu.findItems("Tarefas", Qt.MatchFlag.MatchExactly)[0]] = self.tasks_view; idx+=1
        if self.questions_view: self.menu_item_to_widget_map[self.nav_menu.findItems("Perguntas", Qt.MatchFlag.MatchExactly)[0]] = self.questions_view; idx+=1
        if self.quiz_view: self.menu_item_to_widget_map[self.nav_menu.findItems("Quiz", Qt.MatchFlag.MatchExactly)[0]] = self.quiz_view; idx+=1
        if self.entities_view: self.menu_item_to_widget_map[self.nav_menu.findItems("Entidades", Qt.MatchFlag.MatchExactly)[0]] = self.entities_view; idx+=1
        if self.assessments_view: self.menu_item_to_widget_map[self.nav_menu.findItems("Avaliações", Qt.MatchFlag.MatchExactly)[0]] = self.assessments_view; idx+=1
        if self.gradebook_view: self.menu_item_to_widget_map[self.nav_menu.findItems("Boletim", Qt.MatchFlag.MatchExactly)[0]] = self.gradebook_view; idx+=1
        if self.settings_view: self.menu_item_to_widget_map[self.nav_menu.findItems("Configurações", Qt.MatchFlag.MatchExactly)[0]] = self.settings_view; idx+=1


    def cleanup_db_connection(self):
        """Fecha a conexão com o banco de dados."""
        # Assumindo que AssessmentsView é um item de menu e podemos encontrá-lo
        for i in range(self.nav_menu.count()):
            if self.nav_menu.item(i).text() == "Avaliações":
                self.nav_menu.setCurrentRow(i) # Isso chamará _on_nav_menu_changed
                # AssessmentsView deve recarregar seus dados, o que pode ser feito em seu método showEvent ou similar
                # ou AssessmentsView.refresh_view() pode ser chamado aqui se necessário.
                if hasattr(self.assessments_view, 'refresh_view'):
                    self.assessments_view.refresh_view()
                break

    def cleanup_db_connection(self):
        print("Fechando conexão com o banco de dados...")
        if self.db_manager:
            self.db_manager.close()

    def closeEvent(self, event):
        """Sobrescreve o evento de fechamento da janela para limpar recursos."""
        # QApplication.instance().aboutToQuit.disconnect(self.cleanup_db_connection) # Desconectar se conectado
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
