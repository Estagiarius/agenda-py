import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QLabel, QMessageBox, QComboBox 
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication # Adicionado QApplication

from src.core.database_manager import DatabaseManager
from src.ui.theme_manager import ThemeManager # Adicionado ThemeManager

class SettingsView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Título da View
        title_label = QLabel("Configurações da Aplicação")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Layout do formulário para as configurações
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight) # Alinhar labels à direita

        # Campo de Exemplo: Nome de Usuário Padrão
        self.default_username_edit = QLineEdit()
        self.default_username_edit.setPlaceholderText("Ex: usuário_padrao")
        form_layout.addRow("Nome de Usuário Padrão:", self.default_username_edit)
        
        # Campo para Seleção de Tema
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Padrão do Sistema", userData="system")
        self.theme_combo.addItem("Claro", userData="light")
        self.theme_combo.addItem("Escuro", userData="dark")
        form_layout.addRow("Tema da Aplicação:", self.theme_combo)

        main_layout.addLayout(form_layout)
        main_layout.addStretch() 

        # Botão Salvar
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.save_button.clicked.connect(self._save_settings)
        
        # Layout para o botão, para centralizá-lo ou alinhá-lo
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Carregar configurações iniciais
        self._load_settings()

    def _load_settings(self):
        """Carrega as configurações do banco de dados e preenche os campos da UI."""
        # Carregar Nome de Usuário Padrão
        default_username = self.db_manager.get_setting('default_username', '') 
        self.default_username_edit.setText(default_username or "") 

        # Carregar preferência de tema
        current_theme_value = self.db_manager.get_setting('theme_preference', 'system')
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current_theme_value:
                self.theme_combo.setCurrentIndex(i)
                break
        
        print("Configurações carregadas.")

    def _save_settings(self):
        """Salva as configurações atuais no banco de dados."""
        username_value = self.default_username_edit.text().strip()
        self.db_manager.set_setting('default_username', username_value)

        # Salvar preferência de tema
        selected_theme_value = self.theme_combo.currentData()
        if selected_theme_value: 
            self.db_manager.set_setting('theme_preference', selected_theme_value)
            
            # Aplicar o tema imediatamente
            app_instance = QApplication.instance()
            if app_instance: # Garante que QApplication.instance() não é None
                ThemeManager.apply_theme(app_instance, selected_theme_value)
            else:
                print("ERRO: QApplication.instance() retornou None. Não foi possível aplicar o tema dinamicamente.")

        QMessageBox.information(self, "Configurações Salvas", 
                                "Suas configurações foram salvas e o tema foi aplicado!")
        print("Configurações salvas e tema aplicado.")

# Bloco para teste independente
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # CUIDADO: Este teste pode criar/modificar 'temp_settings_test.db' no diretório atual.
    db_manager_instance = DatabaseManager(db_path='temp_settings_test.db')
    if not db_manager_instance.conn:
        QMessageBox.critical(None, "DB Error", "Não foi possível conectar ao banco de dados para teste.")
        sys.exit(1)

    # Adicionar uma configuração de exemplo para o teste de carregamento
    db_manager_instance.set_setting('default_username', 'usuario_teste_inicial')

    settings_widget = SettingsView(db_manager_instance)
    settings_widget.setWindowTitle("Teste da SettingsView")
    settings_widget.setGeometry(100, 100, 500, 200) # Ajustar tamanho conforme necessário
    settings_widget.show()
    
    exit_code = app.exec()
    
    # Opcional: Limpar o banco de dados de teste
    # import os
    # if os.path.exists('temp_settings_test.db'):
    #     os.remove('temp_settings_test.db')
    #     print("Banco de dados de teste temporário removido.")

    sys.exit(exit_code)
