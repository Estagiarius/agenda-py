import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QGroupBox, QMessageBox, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.core.models import QuizConfig, Question, QuizAttempt

class QuizTakingView(QWidget):
    quiz_finished_signal = pyqtSignal(int) # Emite o ID da tentativa de quiz ao finalizar

    def __init__(self, db_manager: DatabaseManager, quiz_config: QuizConfig, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.quiz_config = quiz_config
        
        self.questions: List[Question] = []
        self.current_question_index: int = 0
        self.user_answers: Dict[int, str] = {} # question_id: answer_text

        self._load_questions() # Carrega as perguntas do quiz
        self._setup_ui()

        if self.questions:
            self._display_current_question()
        else:
            QMessageBox.critical(self, "Erro no Quiz", "Nenhuma pergunta válida encontrada para este quiz.")
            # Considerar desabilitar a UI ou fechar a view
            self.question_text_label.setText("Não foi possível carregar as perguntas do quiz.")

    def _load_questions(self):
        """Carrega os objetos Question para o quiz atual."""
        if not self.quiz_config or not self.quiz_config.question_ids:
            return
        for q_id in self.quiz_config.question_ids:
            question = self.db_manager.get_question_by_id(q_id)
            if question:
                self.questions.append(question)
        
        if not self.questions:
            print(f"Aviso: Nenhum objeto Question carregado para QuizConfig ID {self.quiz_config.id} com question_ids {self.quiz_config.question_ids}")


    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20) # Mais margem
        main_layout.setSpacing(15)

        # Título do Quiz (se houver)
        quiz_name = self.quiz_config.name or f"Quiz ID: {self.quiz_config.id}"
        title_label = QLabel(f"Realizando Quiz: {quiz_name}")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Indicador de Progresso
        self.progress_label = QLabel("Pergunta 1 de N") # Será atualizado
        self.progress_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.progress_label)

        # Área da Pergunta (com Scroll, se necessário)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        question_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        self.question_text_label = QLabel("Texto da Pergunta Aqui...")
        self.question_text_label.setFont(QFont("Arial", 14))
        self.question_text_label.setWordWrap(True)
        question_layout.addWidget(self.question_text_label)

        self.options_group_box = QGroupBox("Opções:")
        self.options_layout = QVBoxLayout() # Layout para os RadioButtons
        self.options_group_box.setLayout(self.options_layout)
        question_layout.addWidget(self.options_group_box)
        question_layout.addStretch() # Empurra conteúdo para cima

        # Botões de Navegação
        nav_layout = QHBoxLayout()
        self.next_button = QPushButton("Próxima Pergunta")
        self.next_button.setFont(QFont("Arial", 12))
        self.next_button.clicked.connect(self._next_or_finish)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        main_layout.addLayout(nav_layout)

    def _display_current_question(self):
        if not self.questions or self.current_question_index >= len(self.questions):
            return

        question = self.questions[self.current_question_index]
        
        self.progress_label.setText(f"Pergunta {self.current_question_index + 1} de {len(self.questions)}")
        self.question_text_label.setText(question.text)

        # Limpar opções anteriores
        while self.options_layout.count():
            child = self.options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Adicionar novas opções
        for option_text in question.options:
            radio_button = QRadioButton(option_text)
            radio_button.setFont(QFont("Arial", 12))
            self.options_layout.addWidget(radio_button)
            # Marcar se já respondido anteriormente nesta sessão
            if question.id in self.user_answers and self.user_answers[question.id] == option_text:
                radio_button.setChecked(True)
        
        if self.current_question_index == len(self.questions) - 1:
            self.next_button.setText("Finalizar Quiz")
        else:
            self.next_button.setText("Próxima Pergunta")

    def _get_selected_answer(self) -> Optional[str]:
        """Retorna o texto da opção selecionada."""
        for i in range(self.options_layout.count()):
            widget = self.options_layout.itemAt(i).widget()
            if isinstance(widget, QRadioButton) and widget.isChecked():
                return widget.text()
        return None

    def _next_or_finish(self):
        # Salvar resposta da pergunta atual
        if self.questions and self.current_question_index < len(self.questions):
            current_q_id = self.questions[self.current_question_index].id
            selected_answer = self._get_selected_answer()
            if current_q_id is not None and selected_answer is not None:
                self.user_answers[current_q_id] = selected_answer
            elif current_q_id is not None and selected_answer is None:
                # Se o usuário não selecionou nada, podemos registrar como "não respondido"
                # ou forçar uma seleção. Por ora, não salvar se nada selecionado.
                # Se for obrigatório responder:
                # QMessageBox.warning(self, "Sem Resposta", "Por favor, selecione uma opção.")
                # return 
                pass


        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self._display_current_question()
        else:
            # Finalizar o Quiz
            self._finish_quiz()

    def _finish_quiz(self):
        score = 0
        for q_id, user_answer in self.user_answers.items():
            # Encontrar a pergunta correspondente na lista self.questions
            question_obj = next((q for q in self.questions if q.id == q_id), None)
            if question_obj and question_obj.answer == user_answer:
                score += 1
        
        total_questions = len(self.questions)
        
        attempt = QuizAttempt(
            quiz_config_id=self.quiz_config.id, # type: ignore # sabemos que quiz_config.id não é None aqui
            user_answers=self.user_answers,
            score=score,
            total_questions=total_questions
        )
        
        added_attempt = self.db_manager.add_quiz_attempt(attempt)
        
        if added_attempt and added_attempt.id is not None:
            QMessageBox.information(self, "Quiz Finalizado", 
                                   f"Sua pontuação: {score}/{total_questions}")
            self.quiz_finished_signal.emit(added_attempt.id)
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar sua tentativa de quiz.")
            # Mesmo se falhar ao salvar, podemos querer emitir um sinal ou tratar de outra forma
            # self.quiz_finished_signal.emit(-1) # Sinalizar falha, por exemplo

        # Desabilitar botões ou navegar para fora desta view
        self.next_button.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    db_man = DatabaseManager("data/agenda.db")

    # Criar uma QuizConfig de exemplo para teste
    # Certifique-se que as perguntas com IDs 1, 2, 3 existem no DB
    # (Execute `python -m src.core.database_manager` para popular)
    
    sample_questions_for_test = db_man.get_all_questions()
    if len(sample_questions_for_test) < 2:
        QMessageBox.critical(None, "Erro", "Pelo menos 2 perguntas são necessárias no DB para este teste.")
        sys.exit(1)

    q_ids = [q.id for q in sample_questions_for_test[:2] if q.id] # Pega as duas primeiras
    if not q_ids or len(q_ids) < 2:
         QMessageBox.critical(None, "Erro", "IDs de perguntas de exemplo não encontrados.")
         sys.exit(1)


    test_quiz_config = QuizConfig(id=1, name="Quiz de Teste da UI", question_ids=q_ids)
    # Normalmente, o ID da QuizConfig viria do DB após ser salvo.
    # Para este teste, podemos simular um ID se não formos salvar a config aqui.

    quiz_view = QuizTakingView(db_man, test_quiz_config)
    
    def show_results(attempt_id):
        print(f"Sinal quiz_finished_signal recebido! ID da Tentativa: {attempt_id}")
        # Aqui, você poderia abrir uma nova janela/view para mostrar os resultados detalhados.
        # Por agora, apenas fechamos a aplicação de teste.
        # app.quit() # Comentado para manter a janela aberta após o quiz para inspeção
    
    quiz_view.quiz_finished_signal.connect(show_results)
    
    quiz_view.setWindowTitle("Teste de Realização de Quiz")
    quiz_view.setGeometry(100, 100, 600, 400)
    quiz_view.show()
    
    sys.exit(app.exec())
