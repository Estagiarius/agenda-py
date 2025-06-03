import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from src.core.database_manager import DatabaseManager
from src.core.models import QuizAttempt, Question # Question é necessário para buscar detalhes das perguntas
from typing import Dict, Optional

class QuestionReviewWidget(QFrame):
    """Widget para exibir a revisão de uma única pergunta."""
    def __init__(self, question_text: str, user_answer: str, correct_answer: str, is_correct: bool, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel) # Adiciona uma borda
        
        layout = QVBoxLayout(self)
        
        q_text_label = QLabel(f"<b>Pergunta:</b> {question_text}")
        q_text_label.setWordWrap(True)
        layout.addWidget(q_text_label)
        
        user_answer_label = QLabel(f"Sua resposta: {user_answer}")
        user_answer_label.setWordWrap(True)
        layout.addWidget(user_answer_label)
        
        correct_answer_label = QLabel(f"Resposta correta: {correct_answer}")
        correct_answer_label.setWordWrap(True)
        layout.addWidget(correct_answer_label)
        
        # Feedback visual
        palette = self.palette()
        if is_correct:
            feedback_label = QLabel("Correto!")
            palette.setColor(QPalette.ColorRole.Window, QColor("lightgreen")) # Fundo verde claro
            feedback_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            feedback_label = QLabel("Incorreto.")
            palette.setColor(QPalette.ColorRole.Window, QColor("#FFCCCB")) # Fundo vermelho claro (salmão)
            feedback_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        layout.addWidget(feedback_label)

class QuizResultsView(QWidget):
    back_to_config_signal = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager, attempt_id: int, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.attempt_id = attempt_id
        
        self.attempt: Optional[QuizAttempt] = None
        self.questions: Dict[int, Question] = {} # question_id -> Question object

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        title_label = QLabel("Resultados do Quiz")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        self.score_summary_label = QLabel("Sua Pontuação: Carregando...")
        self.score_summary_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.score_summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.score_summary_label)

        # ScrollArea para a lista de perguntas e respostas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.review_widget_container = QWidget() # Widget dentro do ScrollArea
        self.review_layout = QVBoxLayout(self.review_widget_container) # Layout para os QuestionReviewWidgets
        self.review_layout.setSpacing(10)
        
        scroll_area.setWidget(self.review_widget_container)
        main_layout.addWidget(scroll_area)

        # Botão para voltar
        self.back_button = QPushButton("Voltar para Configuração de Quiz")
        self.back_button.setFont(QFont("Arial", 12))
        self.back_button.clicked.connect(self.back_to_config_signal.emit) # Emitir sinal
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def _load_data(self):
        self.attempt = self.db_manager.get_quiz_attempt_by_id(self.attempt_id)
        
        if not self.attempt:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar a tentativa de quiz com ID {self.attempt_id}.")
            self.score_summary_label.setText("Erro ao carregar dados da tentativa.")
            return

        # Carregar os objetos Question para todas as perguntas na tentativa
        for question_id in self.attempt.user_answers.keys():
            question = self.db_manager.get_question_by_id(question_id)
            if question and question.id is not None: # Checa se question.id não é None
                self.questions[question.id] = question
            else:
                print(f"Aviso: Pergunta com ID {question_id} não encontrada no banco de dados.")
        
        self._populate_results()

    def _populate_results(self):
        if not self.attempt:
            return

        score = self.attempt.score
        total_questions = self.attempt.total_questions
        percentage = (score / total_questions * 100) if total_questions > 0 else 0
        
        self.score_summary_label.setText(f"Sua Pontuação: {score} / {total_questions} ({percentage:.2f}%)")

        # Limpar revisões anteriores (se houver)
        while self.review_layout.count():
            child = self.review_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Adicionar widget de revisão para cada pergunta
        for q_id, user_ans in self.attempt.user_answers.items():
            question_obj = self.questions.get(q_id)
            
            if question_obj:
                q_text = question_obj.text
                correct_ans = question_obj.answer
                is_correct = (user_ans == correct_ans)
                
                review_item_widget = QuestionReviewWidget(q_text, user_ans, correct_ans, is_correct)
                self.review_layout.addWidget(review_item_widget)
            else:
                # Caso a pergunta não tenha sido encontrada (menos provável se o DB estiver consistente)
                missing_q_label = QLabel(f"<i>Detalhes da pergunta ID {q_id} não disponíveis.</i>")
                self.review_layout.addWidget(missing_q_label)
        
        self.review_layout.addStretch() # Adiciona espaço no final para empurrar para cima

if __name__ == '__main__':
    app = QApplication(sys.argv)
    db_man = DatabaseManager("data/agenda.db")

    # Para testar, precisamos de um attempt_id válido.
    # Você pode buscar uma tentativa existente ou adicionar uma.
    # Supondo que existe uma tentativa com ID 1 (verifique seu DB)
    
    # Adicionar dados de exemplo se não existirem
    if not db_man.get_all_quiz_configs():
         QMessageBox.warning(None, "Dados de Teste", "Execute 'python -m src.core.database_manager' para criar dados de exemplo primeiro.")
         # sys.exit(1) # Comentado para permitir execução mesmo sem dados de exemplo, mas a view ficará vazia/com erro.

    # Buscar uma tentativa de exemplo. Se não houver, a view mostrará erro.
    example_attempt_id = 1 
    # Tentar encontrar a primeira tentativa de qualquer config para teste
    all_configs = db_man.get_all_quiz_configs()
    found_attempt_for_test = None
    if all_configs:
        attempts_for_first_config = db_man.get_attempts_for_quiz_config(all_configs[0].id) # type: ignore
        if attempts_for_first_config:
            example_attempt_id = attempts_for_first_config[0].id # type: ignore
            found_attempt_for_test = True
    
    if not found_attempt_for_test:
         QMessageBox.warning(None, "Dados de Teste", f"Nenhuma tentativa de quiz encontrada para teste. A view pode não carregar dados. (Tentativa ID padrão: {example_attempt_id})")


    results_view = QuizResultsView(db_man, attempt_id=example_attempt_id)
    
    def on_back():
        print("Sinal back_to_config_signal recebido!")
        # app.quit() # Comentado para manter a janela aberta

    results_view.back_to_config_signal.connect(on_back)
    
    results_view.setWindowTitle("Teste de Resultados do Quiz")
    results_view.setGeometry(100, 100, 700, 500)
    results_view.show()
    
    sys.exit(app.exec())
