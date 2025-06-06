import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTextEdit, QSizePolicy, QDialogButtonBox, QProgressBar, QTableWidget, QAbstractItemView,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer # QTimer for simulating preview
from PyQt6.QtGui import QFont

class StudentImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importar Alunos via Arquivo")
        self.setMinimumSize(600, 450) # Adjusted size
        self.setModal(True)

        self.selected_file_path = None

        main_layout = QVBoxLayout(self)

        # Instructions
        instructions_label = QLabel(
            "<b>Passo 1:</b> Baixe o modelo de planilha (CSV/Excel).<br>"
            "<b>Passo 2:</b> Preencha a planilha com os dados dos alunos.<br>"
            "<b>Passo 3:</b> Faça o upload do arquivo preenchido abaixo.<br>"
            "<b>Passo 4:</b> Verifique a prévia dos dados e confirme a importação."
        )
        instructions_label.setWordWrap(True)
        main_layout.addWidget(instructions_label)

        # Download template button
        self.download_template_button = QPushButton("Baixar Arquivo Modelo (CSV/Excel)")
        self.download_template_button.clicked.connect(self._download_template)
        # Align left or use a QHBoxLayout for more control if needed
        download_layout = QHBoxLayout()
        download_layout.addWidget(self.download_template_button)
        download_layout.addStretch()
        main_layout.addLayout(download_layout)

        main_layout.addSpacing(10)

        # File Upload Section
        upload_layout = QHBoxLayout()
        self.file_path_label = QLabel("Nenhum arquivo selecionado.")
        self.file_path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.select_file_button = QPushButton("Selecionar Arquivo...")
        self.select_file_button.clicked.connect(self._select_file)
        upload_layout.addWidget(QLabel("Arquivo:"))
        upload_layout.addWidget(self.file_path_label)
        upload_layout.addWidget(self.select_file_button)
        main_layout.addLayout(upload_layout)

        # Data Preview Section
        preview_label = QLabel("Prévia dos Dados do Arquivo:")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        main_layout.addWidget(preview_label)

        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3) # Example: Nome, Email, Matrícula
        self.preview_table.setHorizontalHeaderLabels(["Nome Completo", "Email", "Matrícula (Opcional)"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Read-only
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setRowCount(0) # Initially empty
        main_layout.addWidget(self.preview_table)

        # Progress Bar (for simulated import)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False) # Hidden initially
        main_layout.addWidget(self.progress_bar)

        # Dialog Buttons (Confirm, Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel)
        self.confirm_button = self.button_box.button(QDialogButtonBox.StandardButton.Open)
        self.confirm_button.setText("Confirmar Importação")
        self.confirm_button.setEnabled(False) # Disabled until a file is selected and previewed

        self.button_box.accepted.connect(self._try_accept) # Connect to a custom slot
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _download_template(self):
        # Placeholder for actual download logic
        # For now, just shows a message.
        # In a real app, this might trigger a file save dialog or open a URL.
        from PyQt6.QtWidgets import QMessageBox # Local import for less frequent use
        QMessageBox.information(self, "Download Modelo",
                                "Funcionalidade de download do modelo ainda não implementada.\n"
                                "Por favor, crie um arquivo CSV com colunas: Nome Completo, Email, Matrícula")
        print("Download template button clicked (simulated).")

    def _select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Alunos", "",
            "Arquivos de Planilha (*.csv *.xlsx *.xls);;Todos os Arquivos (*)"
        )
        if file_path:
            self.selected_file_path = file_path
            self.file_path_label.setText(file_path.split('/')[-1]) # Show only filename
            self.file_path_label.setToolTip(file_path)
            self._show_preview() # Show preview after selecting file
            self.confirm_button.setEnabled(True) # Enable confirm button
        else:
            self.selected_file_path = None
            self.file_path_label.setText("Nenhum arquivo selecionado.")
            self.file_path_label.setToolTip("")
            self.preview_table.setRowCount(0) # Clear preview
            self.confirm_button.setEnabled(False)

    def _show_preview(self):
        if not self.selected_file_path:
            return

        self.preview_table.setRowCount(0) # Clear previous preview

        # Simulate reading some data for preview
        # In a real app, this would involve parsing the CSV/Excel file
        # For example, read first 5-10 rows.
        mock_data = []
        if self.selected_file_path.endswith(".csv"):
            mock_data = [
                ["João Silva (Exemplo)", "joao.silva@example.com", "JS123"],
                ["Maria Oliveira (Exemplo)", "maria.o@example.com", "MO456"],
                ["Carlos Pereira (Exemplo)", "carlos.p@example.com", ""],
            ]
        elif self.selected_file_path.endswith((".xlsx", ".xls")):
             mock_data = [
                ["Ana Costa (Exemplo Excel)", "ana.costa@example.com", "AC789"],
                ["Bruno Santos (Exemplo Excel)", "bruno.s@example.com", "BS012"],
            ]
        else: # Non-spreadsheet file selected, or other error
            self.preview_table.setRowCount(1)
            error_item = QTableWidgetItem("Não foi possível pré-visualizar este tipo de arquivo ou o arquivo está vazio/corrompido.")
            error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_table.setItem(0,0, error_item)
            self.preview_table.setSpan(0,0,1,self.preview_table.columnCount()) # Span across columns
            return


        if not mock_data:
            self.preview_table.setRowCount(1)
            item = QTableWidgetItem("Nenhum dado encontrado no arquivo para pré-visualização (simulado).")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_table.setItem(0,0, item)
            self.preview_table.setSpan(0,0,1,self.preview_table.columnCount())
            return

        self.preview_table.setRowCount(len(mock_data))
        for row_idx, row_data in enumerate(mock_data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.preview_table.setItem(row_idx, col_idx, item)

        print(f"Preview generated for {self.selected_file_path} (simulated).")

    def _try_accept(self):
        # This is connected to button_box.accepted
        if not self.selected_file_path:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Nenhum Arquivo", "Por favor, selecione um arquivo para importar.")
            return

        # Simulate import process
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Disable buttons during import
        self.button_box.setEnabled(False)
        self.select_file_button.setEnabled(False)
        self.download_template_button.setEnabled(False)

        # Simulate progress
        self.current_progress = 0
        self.import_timer = QTimer(self)
        self.import_timer.timeout.connect(self._update_progress)
        self.import_timer.start(50) # Update progress every 50ms

    def _update_progress(self):
        self.current_progress += 5
        self.progress_bar.setValue(self.current_progress)
        if self.current_progress >= 100:
            self.import_timer.stop()
            self._finish_import()

    def _finish_import(self):
        self.progress_bar.setVisible(False)
        # Re-enable buttons
        self.button_box.setEnabled(True)
        self.select_file_button.setEnabled(True)
        self.download_template_button.setEnabled(True)

        from PyQt6.QtWidgets import QMessageBox # Local import
        # In a real app, you'd pass the imported data or status back
        QMessageBox.information(self, "Importação Concluída",
                                f"Alunos do arquivo '{self.file_path_label.text()}' foram importados com sucesso (simulado).")
        print("Import process finished (simulated).")
        self.accept() # This will close the dialog with QDialog.Accepted state

    def get_selected_file_path(self):
        return self.selected_file_path

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = StudentImportDialog()
    if dialog.exec(): # exec() shows the dialog
        print(f"Dialog accepted. Selected file: {dialog.get_selected_file_path()}")
    else:
        print("Dialog cancelled.")
    sys.exit(app.exec())
