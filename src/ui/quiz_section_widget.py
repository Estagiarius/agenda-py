from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import pyqtSlot

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtCore import pyqtSlot

from src.core.database_manager import DatabaseManager
from src.core.models import QuizConfig
from src.ui.quiz_config_view import QuizConfigView
from src.ui.quiz_taking_view import QuizTakingView
from src.ui.quiz_results_view import QuizResultsView # Importado QuizResultsView

class QuizSectionWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        self.stacked_widget = QStackedWidget()

        # View de Configuração do Quiz (índice 0)
        self.quiz_config_view = QuizConfigView(self.db_manager)
        self.quiz_config_view.start_quiz_signal.connect(self.start_quiz) # Conectar novo sinal
        self.stacked_widget.addWidget(self.quiz_config_view)

        # View de Realização do Quiz (índice 1)
        # Será preenchida dinamicamente quando um quiz for iniciado
        
        # View de Resultados do Quiz (índice 2)
        # Será preenchida dinamicamente quando um quiz for finalizado
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.stacked_widget)

        self.stacked_widget.setCurrentIndex(0) # Começa na configuração

    @pyqtSlot(QuizConfig) # Tipo do argumento do sinal
    def start_quiz(self, quiz_config_with_id: QuizConfig):
        """Inicia a visualização de realização do quiz com a configuração fornecida."""
        
        # Remover view anterior de "realizar quiz", se houver, para evitar múltiplas instâncias
        # Isso é importante se o usuário puder voltar e iniciar outro quiz.
        if self.stacked_widget.count() > 1: # Se já tem mais que a config view
            # Assumindo que QuizTakingView é sempre o último adicionado antes de resultados
            # Se houver uma view de resultados, a lógica de índice pode precisar ser mais robusta.
            # Por agora, se só temos config e taking, o índice 1 é o taking.
            current_widget_at_index_1 = self.stacked_widget.widget(1)
            if isinstance(current_widget_at_index_1, QuizTakingView):
                 self.stacked_widget.removeWidget(current_widget_at_index_1)
                 current_widget_at_index_1.deleteLater()

        self.quiz_taking_view = QuizTakingView(self.db_manager, quiz_config_with_id)
        self.quiz_taking_view.quiz_finished_signal.connect(self.show_quiz_results) # Conectar ao slot de resultados
        
        new_index = self.stacked_widget.addWidget(self.quiz_taking_view)
        self.stacked_widget.setCurrentIndex(new_index)

    @pyqtSlot(int) # ID da tentativa de quiz
    def show_quiz_results(self, attempt_id: int):
        """Cria e mostra a view de resultados do quiz."""
        # Remover a QuizTakingView antes de adicionar a ResultsView
        if hasattr(self, 'quiz_taking_view') and self.quiz_taking_view:
            self.stacked_widget.removeWidget(self.quiz_taking_view)
            self.quiz_taking_view.deleteLater()
            delattr(self, 'quiz_taking_view')
        
        # Remover view de resultados anterior, se houver
        # Isso garante que cada resultado seja uma nova view.
        # Ou poderíamos ter uma única instância de QuizResultsView e apenas atualizar seus dados.
        # Por simplicidade de estado, criar uma nova é mais fácil.
        if hasattr(self, 'quiz_results_view_instance') and self.quiz_results_view_instance:
            self.stacked_widget.removeWidget(self.quiz_results_view_instance)
            self.quiz_results_view_instance.deleteLater()
            delattr(self, 'quiz_results_view_instance')

        self.quiz_results_view_instance = QuizResultsView(self.db_manager, attempt_id)
        self.quiz_results_view_instance.back_to_config_signal.connect(self.go_to_config_view) # Conectar o sinal
        
        new_index = self.stacked_widget.addWidget(self.quiz_results_view_instance)
        self.stacked_widget.setCurrentIndex(new_index)

    @pyqtSlot() # Slot para o sinal de QuizResultsView
    def go_to_config_view(self):
        """Volta para a tela de configuração do Quiz."""
        # Remover a view de resultados atual, se existir
        if hasattr(self, 'quiz_results_view_instance') and self.quiz_results_view_instance:
            if self.stacked_widget.indexOf(self.quiz_results_view_instance) != -1:
                 self.stacked_widget.removeWidget(self.quiz_results_view_instance)
            self.quiz_results_view_instance.deleteLater()
            delattr(self, 'quiz_results_view_instance')
        
        # Remover também a QuizTakingView se por acaso ainda existir
        if hasattr(self, 'quiz_taking_view') and self.quiz_taking_view:
            if self.stacked_widget.indexOf(self.quiz_taking_view) != -1:
                self.stacked_widget.removeWidget(self.quiz_taking_view)
            self.quiz_taking_view.deleteLater()
            delattr(self, 'quiz_taking_view')
            
        self.stacked_widget.setCurrentIndex(0) # Índice 0 é QuizConfigView
