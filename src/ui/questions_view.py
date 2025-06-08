import sys
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLabel, QMessageBox, QHeaderView, QLineEdit, QDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional, List

from src.core.database_manager import DatabaseManager
from src.core.models import Question
from src.ui.question_dialog import QuestionDialog # Importado QuestionDialog

class QuestionsView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_selected_question_id: Optional[int] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        title_label = QLabel("Banco de Perguntas")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Filtros
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Assunto:"))
        self.subject_filter_edit = QLineEdit()
        self.subject_filter_edit.setPlaceholderText("Filtrar por assunto...")
        self.subject_filter_edit.textChanged.connect(self._load_questions)
        filter_layout.addWidget(self.subject_filter_edit)

        filter_layout.addWidget(QLabel("Dificuldade:"))
        self.difficulty_filter_combo = QComboBox()
        self.difficulty_filter_combo.addItems(["Todas", "Fácil", "Médio", "Difícil"])
        self.difficulty_filter_combo.currentIndexChanged.connect(self._load_questions)
        filter_layout.addWidget(self.difficulty_filter_combo)
        
        main_layout.addLayout(filter_layout)

        # Tabela de Perguntas
        self.questions_table = QTableWidget()
        self.questions_table.setColumnCount(5) # Texto, Assunto, Dificuldade, Opções, Resposta
        self.questions_table.setHorizontalHeaderLabels(["Texto da Pergunta", "Assunto", "Dificuldade", "Opções", "Resposta"])
        self.questions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.questions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.questions_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.questions_table.verticalHeader().setVisible(False)
        self.questions_table.itemSelectionChanged.connect(self._on_question_selected)
        
        header = self.questions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Texto
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Assunto
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Dificuldade
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Opções
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Resposta
        main_layout.addWidget(self.questions_table)

        # Botões de Ação
        action_buttons_layout = QHBoxLayout()
        self.add_question_button = QPushButton("Adicionar Pergunta")
        self.add_question_button.clicked.connect(self._add_question_dialog) # Conectado
        action_buttons_layout.addWidget(self.add_question_button)

        self.edit_question_button = QPushButton("Editar Pergunta")
        self.edit_question_button.clicked.connect(self._edit_question_dialog) # Conectado
        self.edit_question_button.setEnabled(False)
        action_buttons_layout.addWidget(self.edit_question_button)

        self.delete_question_button = QPushButton("Excluir Pergunta")
        self.delete_question_button.clicked.connect(self._delete_question)
        self.delete_question_button.setEnabled(False)
        action_buttons_layout.addWidget(self.delete_question_button)
        
        main_layout.addLayout(action_buttons_layout)
        self._load_questions()

    def _load_questions(self):
        self.questions_table.setRowCount(0)
        self.current_selected_question_id = None
        self._update_action_buttons_state()

        subject_filter = self.subject_filter_edit.text().strip()
        if not subject_filter: # Se vazio, não filtrar por assunto
            subject_filter = None
            
        difficulty_filter = self.difficulty_filter_combo.currentText()
        if difficulty_filter == "Todas":
            difficulty_filter = None
        
        questions = self.db_manager.get_all_questions(subject=subject_filter, difficulty=difficulty_filter)

        for question in questions:
            row_position = self.questions_table.rowCount()
            self.questions_table.insertRow(row_position)

            text_item = QTableWidgetItem(question.text)
            if question.id is not None:
                 text_item.setData(Qt.ItemDataRole.UserRole, question.id)

            subject_item = QTableWidgetItem(question.subject or "N/A")
            difficulty_item = QTableWidgetItem(question.difficulty or "N/A")
            
            options_str = ", ".join(question.options) if question.options else "N/A"
            options_item = QTableWidgetItem(options_str)
            
            answer_item = QTableWidgetItem(question.answer)

            self.questions_table.setItem(row_position, 0, text_item)
            self.questions_table.setItem(row_position, 1, subject_item)
            self.questions_table.setItem(row_position, 2, difficulty_item)
            self.questions_table.setItem(row_position, 3, options_item)
            self.questions_table.setItem(row_position, 4, answer_item)
        
        if self.questions_table.rowCount() > 0:
            self.questions_table.selectRow(0)

    def _on_question_selected(self):
        selected_items = self.questions_table.selectedItems()
        if not selected_items:
            self.current_selected_question_id = None
        else:
            first_item_in_row = selected_items[0]
            question_id_data = first_item_in_row.data(Qt.ItemDataRole.UserRole)
            if question_id_data is not None:
                self.current_selected_question_id = int(question_id_data)
            else:
                self.current_selected_question_id = None
        self._update_action_buttons_state()

    def _update_action_buttons_state(self):
        has_selection = self.current_selected_question_id is not None
        self.edit_question_button.setEnabled(has_selection)
        self.delete_question_button.setEnabled(has_selection)

    def _delete_question(self):
        if not self.current_selected_question_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione uma pergunta para excluir.")
            return

        question = self.db_manager.get_question_by_id(self.current_selected_question_id)
        if not question:
            QMessageBox.critical(self, "Erro", "Pergunta não encontrada.")
            self._load_questions()
            return

        reply = QMessageBox.question(self, "Confirmar Exclusão",
                                     f"Tem certeza que deseja excluir a pergunta: '{question.text[:80]}...'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_question(self.current_selected_question_id):
                QMessageBox.information(self, "Sucesso", "Pergunta excluída.")
                self._load_questions()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao excluir a pergunta.")

    def _add_question_dialog(self):
        dialog = QuestionDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            question_data = dialog.question_data_to_save # Usar o dado validado e armazenado
            if question_data:
                new_question = self.db_manager.add_question(question_data)
                if new_question and new_question.id:
                    QMessageBox.information(self, "Sucesso", f"Pergunta '{new_question.text[:50]}...' adicionada.")
                    self._load_questions()
                    # Tentar selecionar a pergunta recém-adicionada
                    for row in range(self.questions_table.rowCount()):
                        item = self.questions_table.item(row, 0) # Item do texto (coluna 0)
                        if item and item.data(Qt.ItemDataRole.UserRole) == new_question.id:
                            self.questions_table.selectRow(row)
                            break
                else:
                    QMessageBox.critical(self, "Erro", "Falha ao adicionar a pergunta no banco de dados.")

    def _edit_question_dialog(self):
        if not self.current_selected_question_id:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione uma pergunta para editar.")
            return

        question_to_edit = self.db_manager.get_question_by_id(self.current_selected_question_id)
        if not question_to_edit:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar a pergunta para edição.")
            self._load_questions() # Recarrega para garantir consistência
            return

        dialog = QuestionDialog(question=question_to_edit, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            question_data = dialog.question_data_to_save
            if question_data:
                if self.db_manager.update_question(question_data):
                    QMessageBox.information(self, "Sucesso", f"Pergunta '{question_data.text[:50]}...' atualizada.")
                    self._load_questions()
                    # Tentar re-selecionar a pergunta editada
                    for row in range(self.questions_table.rowCount()):
                        item = self.questions_table.item(row, 0)
                        if item and item.data(Qt.ItemDataRole.UserRole) == question_data.id:
                            self.questions_table.selectRow(row)
                            break
                else:
                    QMessageBox.critical(self, "Erro", "Falha ao atualizar a pergunta no banco de dados.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    db_manager_instance = DatabaseManager(db_path='data/agenda.db')

    # python -m src.core.database_manager # Executar para popular o DB
    if not db_manager_instance.conn:
        print("Falha ao conectar ao DB.")
        sys.exit(1)
    
    # Adicionar algumas perguntas de exemplo se não houver
    if not db_manager_instance.get_all_questions():
        print("Populando com perguntas de exemplo para teste da QuestionsView...")
        db_manager_instance.add_question(Question(text="Qual a cor do céu em um dia limpo?", subject="Natureza", difficulty="Fácil", options=["Verde", "Azul", "Vermelho"], answer="Azul"))
        db_manager_instance.add_question(Question(text="Quantos lados tem um triângulo?", subject="Matemática", difficulty="Fácil", options=["3", "4", "5"], answer="3"))


    questions_widget = QuestionsView(db_manager_instance)
    questions_widget.setWindowTitle("Teste da QuestionsView")
    questions_widget.setGeometry(100, 100, 1000, 600)
    questions_widget.show()
    
    exit_code = app.exec()
    if db_manager_instance.conn:
        db_manager_instance.close()
    sys.exit(exit_code)
