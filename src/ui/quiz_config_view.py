import sys
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QListWidget, QListWidgetItem, QLabel, QLineEdit, 
    QMessageBox, QHeaderView, QAbstractItemView, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal # Adicionado pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional, List, Set

from src.core.database_manager import DatabaseManager
from src.core.models import Question, QuizConfig

class QuizConfigView(QWidget):
    start_quiz_signal = pyqtSignal(QuizConfig) # Sinal para iniciar o quiz

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_question_ids_for_quiz: Set[int] = set()

        main_layout = QVBoxLayout(self)
        
        title_label = QLabel("Configurar Novo Quiz")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Layout do Splitter para dividir a seleção de perguntas e a configuração do quiz
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- Painel Esquerdo: Seleção de Perguntas ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        available_questions_label = QLabel("Perguntas Disponíveis:")
        available_questions_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(available_questions_label)
        
        # (Filtros para perguntas disponíveis podem ser adicionados aqui no futuro)
        
        self.available_questions_table = QTableWidget()
        self.available_questions_table.setColumnCount(3) # Texto, Assunto, Dificuldade
        self.available_questions_table.setHorizontalHeaderLabels(["Pergunta", "Assunto", "Dificuldade"])
        self.available_questions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.available_questions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.available_questions_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # Múltipla seleção
        self.available_questions_table.verticalHeader().setVisible(False)
        header = self.available_questions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        left_layout.addWidget(self.available_questions_table)
        
        splitter.addWidget(left_panel)

        # --- Painel Direito: Perguntas Selecionadas e Configuração ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        selected_questions_label = QLabel("Perguntas Selecionadas para o Quiz:")
        selected_questions_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(selected_questions_label)
        
        self.selected_questions_list = QListWidget()
        right_layout.addWidget(self.selected_questions_list)

        # Botões de Adicionar/Remover
        add_remove_layout = QHBoxLayout()
        add_button = QPushButton("Adicionar ao Quiz >>")
        add_button.clicked.connect(self._add_selected_to_quiz)
        remove_button = QPushButton("<< Remover do Quiz")
        remove_button.clicked.connect(self._remove_selected_from_quiz)
        add_remove_layout.addWidget(add_button)
        add_remove_layout.addWidget(remove_button)
        right_layout.addLayout(add_remove_layout) # Adiciona ao layout direito, abaixo da lista

        # Nome do Quiz e Botão Salvar
        quiz_name_layout = QHBoxLayout()
        quiz_name_layout.addWidget(QLabel("Nome do Quiz (opcional):"))
        self.quiz_name_edit = QLineEdit()
        self.quiz_name_edit.setPlaceholderText("Ex: Quiz de Geografia Semanal")
        quiz_name_layout.addWidget(self.quiz_name_edit)
        right_layout.addLayout(quiz_name_layout)

        save_button = QPushButton("Salvar Configuração do Quiz")
        save_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        save_button.clicked.connect(self._save_quiz_config)
        right_layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400]) # Tamanhos iniciais
        main_layout.addWidget(splitter)

        self._load_available_questions()

    def _load_available_questions(self):
        self.available_questions_table.setRowCount(0)
        questions = self.db_manager.get_all_questions() # Poderia ter filtros aqui

        for q in questions:
            row_pos = self.available_questions_table.rowCount()
            self.available_questions_table.insertRow(row_pos)
            
            text_item = QTableWidgetItem(q.text)
            if q.id is not None: # Armazena o ID
                text_item.setData(Qt.ItemDataRole.UserRole, q.id)
            
            self.available_questions_table.setItem(row_pos, 0, text_item)
            self.available_questions_table.setItem(row_pos, 1, QTableWidgetItem(q.subject or "N/A"))
            self.available_questions_table.setItem(row_pos, 2, QTableWidgetItem(q.difficulty or "N/A"))

    def _add_selected_to_quiz(self):
        selected_rows = self.available_questions_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Nenhuma Seleção", "Por favor, selecione perguntas da tabela à esquerda.")
            return

        for index in selected_rows:
            id_item = self.available_questions_table.item(index.row(), 0) # Item da primeira coluna (Texto)
            question_id = id_item.data(Qt.ItemDataRole.UserRole)
            question_text = id_item.text()

            if question_id is not None and question_id not in self.selected_question_ids_for_quiz:
                self.selected_question_ids_for_quiz.add(question_id)
                list_item = QListWidgetItem(f"ID: {question_id} - {question_text}")
                list_item.setData(Qt.ItemDataRole.UserRole, question_id) # Armazena o ID no item
                self.selected_questions_list.addItem(list_item)
        
        # Limpar seleção da tabela para evitar re-adição acidental
        self.available_questions_table.clearSelection()


    def _remove_selected_from_quiz(self):
        selected_list_items = self.selected_questions_list.selectedItems()
        if not selected_list_items:
            QMessageBox.information(self, "Nenhuma Seleção", "Por favor, selecione perguntas da lista à direita para remover.")
            return
        
        for item in selected_list_items:
            question_id = item.data(Qt.ItemDataRole.UserRole)
            if question_id is not None and question_id in self.selected_question_ids_for_quiz:
                self.selected_question_ids_for_quiz.remove(question_id)
            
            # Remover da QListWidget
            self.selected_questions_list.takeItem(self.selected_questions_list.row(item))


    def _save_quiz_config(self):
        if not self.selected_question_ids_for_quiz:
            QMessageBox.warning(self, "Quiz Vazio", "Por favor, adicione perguntas ao quiz antes de salvar.")
            return

        quiz_name = self.quiz_name_edit.text().strip() or None # None se vazio
        
        # Convertendo set para list para o modelo QuizConfig
        question_ids_list = list(self.selected_question_ids_for_quiz)
        
        quiz_config = QuizConfig(name=quiz_name, question_ids=question_ids_list)
        
        added_config = self.db_manager.add_quiz_config(quiz_config)
        
        if added_config and added_config.id is not None:
            QMessageBox.information(self, "Sucesso", 
                                   f"Configuração de Quiz '{added_config.name or f'ID: {added_config.id}'}' salva com {len(added_config.question_ids)} perguntas.")
            # Limpar para próxima configuração
            self.quiz_name_edit.clear()
            self.selected_questions_list.clear()
            self.selected_question_ids_for_quiz.clear()
            
            # Emitir o sinal para iniciar o quiz
            self.start_quiz_signal.emit(added_config)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar a configuração do quiz no banco de dados.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # É necessário um DatabaseManager funcional
    # Execute `python -m src.core.database_manager` antes para popular o DB
    db_manager_instance = DatabaseManager(db_path='data/agenda.db') 
    if not db_manager_instance.conn or not db_manager_instance.get_all_questions():
        QMessageBox.critical(None, "Erro de Banco de Dados", 
                             "Banco de dados não encontrado ou sem perguntas. Execute 'python -m src.core.database_manager' primeiro.")
        sys.exit(1)

    quiz_config_widget = QuizConfigView(db_manager_instance)
    quiz_config_widget.setWindowTitle("Teste da QuizConfigView")
    quiz_config_widget.setGeometry(50, 50, 1000, 700) # Aumentar tamanho para teste
    quiz_config_widget.show()
    
    exit_code = app.exec()
    if db_manager_instance.conn:
        db_manager_instance.close()
    sys.exit(exit_code)
