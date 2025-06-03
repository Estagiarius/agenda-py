import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, 
    QComboBox, QPushButton, QDialogButtonBox, QMessageBox, QHBoxLayout,
    QWidget, QLabel
)
from PyQt6.QtCore import Qt
from typing import Optional, List

from src.core.models import Question

class OptionInputWidget(QWidget):
    """Widget para um campo de opção com botão de remover."""
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.option_edit = QLineEdit(text)
        layout.addWidget(self.option_edit)
        
        self.remove_button = QPushButton("Remover")
        # O sinal clicked será conectado no QuestionDialog
        layout.addWidget(self.remove_button)

    def get_text(self) -> str:
        return self.option_edit.text().strip()

class QuestionDialog(QDialog):
    def __init__(self, question: Optional[Question] = None, parent=None):
        super().__init__(parent)
        self.question = question
        self.option_widgets: List[OptionInputWidget] = []

        if self.question:
            self.setWindowTitle("Editar Pergunta")
        else:
            self.setWindowTitle("Adicionar Nova Pergunta")
        
        self.setMinimumWidth(500)

        # Layout Principal
        main_layout = QVBoxLayout(self)
        
        # Formulário
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.text_edit = QTextEdit() # Pergunta
        self.text_edit.setPlaceholderText("Digite o texto da pergunta aqui...")
        self.text_edit.setFixedHeight(100)
        form_layout.addRow("Pergunta:", self.text_edit)

        self.subject_edit = QLineEdit()
        form_layout.addRow("Assunto:", self.subject_edit)

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Fácil", "Médio", "Difícil"])
        form_layout.addRow("Dificuldade:", self.difficulty_combo)
        
        main_layout.addLayout(form_layout)

        # Gerenciamento de Opções
        options_group_label = QLabel("Opções de Resposta:")
        main_layout.addWidget(options_group_label)
        
        self.options_layout = QVBoxLayout() # Layout vertical para as opções
        main_layout.addLayout(self.options_layout)

        add_option_button = QPushButton("Adicionar Opção")
        add_option_button.clicked.connect(self._add_option_input)
        main_layout.addWidget(add_option_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Campo de Resposta (QComboBox que será populado com as opções)
        self.answer_combo = QComboBox()
        self.answer_combo.setPlaceholderText("Selecione a resposta correta")
        # Atualizar o QComboBox de respostas sempre que as opções mudarem
        # Isso será feito ao adicionar/remover/editar opções e ao popular inicialmente.
        form_layout.addRow("Resposta Correta:", self.answer_combo) # Adicionado ao form_layout

        # Botões OK/Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        # Popular campos e opções
        if self.question:
            self.text_edit.setPlainText(self.question.text)
            self.subject_edit.setText(self.question.subject or "")
            self.difficulty_combo.setCurrentText(self.question.difficulty or "Fácil")
            
            if self.question.options:
                for option_text in self.question.options:
                    self._add_option_input(option_text, is_initial_load=True)
            else: # Se não há opções, adiciona uma vazia
                self._add_option_input(is_initial_load=True)
            
            self._update_answer_combo_options() # Atualiza as opções do ComboBox de resposta
            if self.question.answer and self.question.answer in self.question.options:
                self.answer_combo.setCurrentText(self.question.answer)
        else:
            self._add_option_input(is_initial_load=True) # Começar com uma opção
            self._update_answer_combo_options()

    def _add_option_input(self, text: str = "", is_initial_load: bool = False):
        option_widget = OptionInputWidget(text)
        option_widget.remove_button.clicked.connect(lambda: self._remove_option_input(option_widget))
        option_widget.option_edit.textChanged.connect(self._update_answer_combo_options) # Atualiza ao digitar
        
        self.options_layout.addWidget(option_widget)
        self.option_widgets.append(option_widget)
        
        if not is_initial_load: # Só atualiza se não for carregamento inicial (para evitar chamadas múltiplas)
            self._update_answer_combo_options()

    def _remove_option_input(self, option_widget: OptionInputWidget):
        if len(self.option_widgets) > 1: # Manter pelo menos uma opção
            self.options_layout.removeWidget(option_widget)
            option_widget.deleteLater()
            self.option_widgets.remove(option_widget)
            self._update_answer_combo_options()
        else:
            QMessageBox.warning(self, "Aviso", "Deve haver pelo menos uma opção de resposta.")

    def _update_answer_combo_options(self):
        current_answer = self.answer_combo.currentText() # Salvar resposta atual, se houver
        self.answer_combo.clear()
        
        valid_options = [opt_widget.get_text() for opt_widget in self.option_widgets if opt_widget.get_text()]
        if not valid_options:
            self.answer_combo.setPlaceholderText("Adicione opções válidas")
            self.answer_combo.setEnabled(False)
            return

        self.answer_combo.setEnabled(True)
        self.answer_combo.addItems(valid_options)
        
        if current_answer in valid_options:
            self.answer_combo.setCurrentText(current_answer)
        elif valid_options: # Se a resposta anterior não é mais válida, seleciona a primeira
            self.answer_combo.setCurrentIndex(0)
        else: # Nenhuma opção válida
            self.answer_combo.setPlaceholderText("Adicione opções válidas")


    def get_question_data(self) -> Optional[Question]:
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Campo Obrigatório", "O texto da pergunta não pode estar vazio.")
            return None

        subject = self.subject_edit.text().strip()
        difficulty = self.difficulty_combo.currentText()
        
        options = [opt_widget.get_text() for opt_widget in self.option_widgets if opt_widget.get_text()]
        if not options:
            QMessageBox.warning(self, "Opções Inválidas", "Deve haver pelo menos uma opção de resposta preenchida.")
            return None
        
        answer = self.answer_combo.currentText()
        if not answer : # Se o ComboBox estiver vazio ou com placeholder
             QMessageBox.warning(self, "Resposta Inválida", "Por favor, selecione uma resposta correta entre as opções fornecidas.")
             return None
        if answer not in options: # Checagem extra, embora o ComboBox deva garantir isso
            QMessageBox.warning(self, "Resposta Inválida", "A resposta correta deve ser uma das opções fornecidas.")
            return None

        question_id = self.question.id if self.question else None
        created_at = self.question.created_at if self.question and self.question.created_at else None
        
        return Question(
            id=question_id,
            text=text,
            subject=subject,
            difficulty=difficulty,
            options=options,
            answer=answer,
            created_at=created_at
        )

    def validate_and_accept(self):
        self.question_data_to_save = self.get_question_data()
        if self.question_data_to_save:
            self.accept()

# Bloco para teste independente
if __name__ == '__main__':
    app = QApplication(sys.argv)

    print("Testando diálogo de Adicionar Pergunta:")
    dialog_add = QuestionDialog()
    if dialog_add.exec() == QDialog.DialogCode.Accepted:
        new_q = dialog_add.question_data_to_save
        if new_q:
            print("  Nova Pergunta:")
            print(f"    Texto: {new_q.text}")
            print(f"    Assunto: {new_q.subject}")
            print(f"    Dificuldade: {new_q.difficulty}")
            print(f"    Opções: {new_q.options}")
            print(f"    Resposta: {new_q.answer}")
    else:
        print("  Criação de nova pergunta cancelada.")

    print("\nTestando diálogo de Editar Pergunta:")
    existing_q = Question(
        id=1, 
        text="Qual o comando para listar arquivos em Linux?",
        subject="Sistemas Operacionais",
        difficulty="Fácil",
        options=["dir", "ls", "list", "show"],
        answer="ls",
        created_at=datetime.now()
    )
    dialog_edit = QuestionDialog(question=existing_q)
    if dialog_edit.exec() == QDialog.DialogCode.Accepted:
        edited_q = dialog_edit.question_data_to_save
        if edited_q:
            print("  Pergunta Editada:")
            print(f"    ID: {edited_q.id}")
            print(f"    Texto: {edited_q.text}")
            print(f"    Opções: {edited_q.options}")
            print(f"    Resposta: {edited_q.answer}")
    else:
        print("  Edição de pergunta cancelada.")
        
    sys.exit(0)
