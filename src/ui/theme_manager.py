from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

class ThemeManager:
    @staticmethod
    def apply_theme(app: QApplication, theme_name: str):
        """
        Aplica um tema à aplicação.
        :param app: A instância da QApplication.
        :param theme_name: O nome do tema a ser aplicado ("system", "light", ou "dark").
        """
        
        # Limpar stylesheet global anterior para evitar conflitos,
        # a menos que um tema específico defina a sua.
        app.setStyleSheet("")

        if theme_name == "system":
            # Restaura a paleta padrão do estilo atual do sistema
            # Uma nova QPalette() vazia herda as cores do sistema por padrão.
            # Ou, para ser mais explícito, podemos usar a paleta do estilo.
            # system_palette = QApplication.style().standardPalette() 
            # app.setPalette(system_palette)
            app.setPalette(QPalette()) # Reverte para a paleta padrão do sistema
            print("INFO: Tema 'Padrão do Sistema' aplicado.")

        elif theme_name == "light":
            # Para um tema claro explícito, uma QPalette() padrão geralmente já é clara.
            # Podemos ajustar cores específicas se necessário, mas começar com o padrão é bom.
            light_palette = QPalette()
            # Exemplo de ajuste (opcional, a paleta padrão já é clara):
            light_palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240)) # Mantendo este ajuste de exemplo
            light_palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0)) # Texto principal preto
            light_palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0)) # Texto em campos de entrada
            light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0)) # Texto de botões preto
            light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0,0,0)) # Texto de tooltips preto
            # Cores base para ToolTip e Base podem ser definidas se o padrão não for bom
            light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255)) # Fundo de campos de entrada (geralmente branco)
            light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220)) # Fundo de tooltips (amarelo claro)
            # HighlightedText deve contrastar com Highlight
            light_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215)) # Cor de seleção/foco (azul)
            light_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255)) # Texto selecionado/em foco (branco)
            # BrightText para alertas ou texto especial
            light_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0)) # Texto brilhante (vermelho)

            app.setPalette(light_palette)
            stylesheet = """
    QWidget { color: black !important; } /* Broadest rule, attempt to catch all text */

    /* Specific overrides where QWidget might be too broad or need refinement */
    QLabel {
        color: black !important;
        background-color: transparent !important; /* Ensure no weird background colors are inherited */
    }
    QCheckBox, QRadioButton, QGroupBox, QToolTip {
        color: black !important;
        background-color: transparent !important;
    }
    QPushButton {
        color: black !important;
        /* background-color: #f0f0f0 !important; Optional: set a specific light button color */
        /* border: 1px solid #adadad !important;  Optional: set a specific light button border */
    }
    QTabBar::tab {
        color: black !important;
        /* background: #e1e1e1 !important; Optional: specific tab background */
    }
    QTabBar::tab:selected {
        color: black !important; /* Ensure selected tab text is also black */
        /* background: #cde8ff !important; Optional: specific selected tab background */
    }

    /* Styles for QListWidget (navigation menu) */
    QListWidget {
        font-size: 14px !important; /* Example: Enforce font size if needed */
        color: black !important;    /* Default text color for the widget itself */
    }
    QListWidget::item {
        color: black !important;    /* Text color for non-selected items */
    }

    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        color: black !important;
        background-color: white !important; /* Explicitly set background for input fields */
        border: 1px solid #adadad !important; /* Typical light theme border for input fields */
        selection-background-color: #0078d7 !important; /* Standard blue selection */
        selection-color: white !important; /* White text for selected blue background */
    }
    QComboBox QAbstractItemView { /* Dropdown list of QComboBox */
        color: black !important;
        background-color: white !important;
        selection-background-color: #0078d7 !important;
        selection-color: white !important;
    }
    QMenu {
        color: black !important;
        background-color: #f0f0f0 !important; /* Light background for menus */
        border: 1px solid #adadad !important;
    }
    QMenu::item {
        color: black !important;
        background-color: transparent !important;
    }
    QMenu::item:selected {
        color: black !important; /* Or white if background is dark blue */
        background-color: #0078d7 !important; /* Blue highlight for selected menu item */
        /* color: white !important; */ /* If using dark blue highlight, text should be white */
    }
    QMenuBar {
        color: black !important;
        background-color: #f0f0f0 !important;
    }
    QMenuBar::item {
        color: black !important;
        background-color: transparent !important;
    }
    QMenuBar::item:selected {
        color: black !important; /* Or white if background is dark blue */
        background-color: #0078d7 !important; /* Blue highlight */
        /* color: white !important; */
    }
    QTableView, QTreeView, QListView { /* Note: QListView is different from QListWidget */
        color: black !important; /* Default text color for items */
        background-color: white !important;
        alternate-background-color: #f0f0f0 !important; /* For alternating row colors if enabled */
        selection-background-color: #0078d7 !important;
        selection-color: white !important;
    }
    QHeaderView::section {
        color: black !important;
        background-color: #e1e1e1 !important;
        border: 1px solid #adadad !important;
    }
    QToolButton {
        color: black !important;
    }
"""
            app.setStyleSheet(stylesheet)
            # app.setStyleSheet("") # Já está no início da função, não precisa repetir aqui
            print("INFO: Tema 'Claro' aplicado.")

        elif theme_name == "dark":
            dark_palette = QPalette()

            # Cores base do tema escuro (Original Dark Gray)
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(42, 42, 42))
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            
            # Botões (Original Dark Gray)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(66, 66, 66))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            
            # Destaques e Links (Original Dark Gray)
            dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218)) # Standard link blue
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218)) # Standard highlight blue
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

            # Cores para estados desabilitados (Original Dark Gray)
            disabled_text_color = QColor(127, 127, 127)
            disabled_button_color = QColor(45, 45, 45)
            
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text_color)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text_color)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text_color)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, disabled_button_color)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(40,40,40)) 

            app.setPalette(dark_palette)
            # No specific stylesheet for the original dark theme was mentioned, keeping it minimal.
            print("INFO: Tema 'Escuro (Cinza)' aplicado (via paleta).")

        elif theme_name == "dark_blue":
            dark_blue_palette = QPalette()

            # Cores base do tema escuro azulado
            dark_blue_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 70))
            dark_blue_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            dark_blue_palette.setColor(QPalette.ColorRole.Base, QColor(40, 40, 80))
            dark_blue_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 75))
            dark_blue_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(42, 42, 42)) # Kept original, can be adjusted
            dark_blue_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            dark_blue_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))

            # Botões
            dark_blue_palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 90))
            dark_blue_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            
            # Destaques e Links
            dark_blue_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0)) # Kept original
            dark_blue_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218)) # Standard link blue
            dark_blue_palette.setColor(QPalette.ColorRole.Highlight, QColor(60, 60, 120))
            dark_blue_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

            # Cores para estados desabilitados
            disabled_text_color = QColor(150, 150, 170)
            disabled_button_color = QColor(45, 45, 45) # Same as before, check visibility with blue

            dark_blue_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text_color)
            dark_blue_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text_color)
            dark_blue_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text_color)
            dark_blue_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, disabled_button_color)
            dark_blue_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(35,35,75))

            app.setPalette(dark_blue_palette)
            # Optional: Add any specific stylesheet for dark_blue if needed, similar to the commented out one.
            # For now, no specific stylesheet is applied for dark_blue, relying on QPalette.
            print("INFO: Tema 'Azul Escuro' aplicado (via paleta).")
            
        else:
            print(f"AVISO: Nome de tema desconhecido '{theme_name}'. Usando padrão do sistema.")
            app.setPalette(QPalette()) # Reverte para padrão em caso de erro
            
    @staticmethod
    def set_placeholder_text_color(palette: QPalette, color: QColor):
        """
        Define a cor do texto de placeholder.
        Nota: QPalette.ColorRole.PlaceholderText só está disponível a partir do Qt 5.12.
        Se estiver usando uma versão anterior via PyQt, isso pode não ter efeito
        e o estilo via stylesheet seria necessário para QLineEdit etc.
        Para Qt6, isso deve funcionar.
        """
        try:
            palette.setColor(QPalette.ColorRole.PlaceholderText, color)
        except AttributeError:
            print("AVISO: QPalette.ColorRole.PlaceholderText não disponível. Cor do placeholder não definida via paleta.")

if __name__ == '__main__':
    # Exemplo de como usar (não executa a UI completa, apenas testa a lógica da paleta)
    
    # Simular uma QApplication
    class MockApplication:
        def __init__(self):
            self._palette = QPalette()
            self._stylesheet = ""

        def palette(self):
            print("MockApplication.palette() chamada")
            return self._palette

        def setPalette(self, p: QPalette):
            print("MockApplication.setPalette() chamada")
            self._palette = p
            # Aqui você pode imprimir algumas cores da paleta para verificar
            # print(f"  Window color: {p.color(QPalette.ColorRole.Window).name()}")
            # print(f"  WindowText color: {p.color(QPalette.ColorRole.WindowText).name()}")

        def style(self): # Adicionar mock para style()
            class MockStyle:
                def standardPalette(self):
                    print("MockStyle.standardPalette() chamada")
                    return QPalette() # Retorna uma paleta padrão
            return MockStyle()

        def setStyleSheet(self, sheet: str):
            print(f"MockApplication.setStyleSheet() chamada com: '{sheet[:50]}...'")
            self._stylesheet = sheet
            
        def font(self): # Adicionar mock para font()
            from PyQt6.QtGui import QFont
            return QFont()


    mock_app = MockApplication()

    print("\n--- Testando Tema Light ---")
    ThemeManager.apply_theme(mock_app, "light") # type: ignore 
    # Testar algumas cores (exemplo)
    # print(f"Cor da Janela (Light): {mock_app.palette().color(QPalette.ColorRole.Window).name()}")


    print("\n--- Testando Tema Dark ---")
    ThemeManager.apply_theme(mock_app, "dark") # type: ignore
    # Testar algumas cores (exemplo)
    # print(f"Cor da Janela (Dark): {mock_app.palette().color(QPalette.ColorRole.Window).name()}")
    # print(f"Cor do Texto da Janela (Dark): {mock_app.palette().color(QPalette.ColorRole.WindowText).name()}")
    # print(f"Cor do Base (Dark): {mock_app.palette().color(QPalette.ColorRole.Base).name()}")
    # print(f"Cor do Botão (Dark): {mock_app.palette().color(QPalette.ColorRole.Button).name()}")
    # print(f"Cor do Highlight (Dark): {mock_app.palette().color(QPalette.ColorRole.Highlight).name()}")


    print("\n--- Testando Tema System ---")
    ThemeManager.apply_theme(mock_app, "system") # type: ignore
    # Testar algumas cores (exemplo)
    # print(f"Cor da Janela (System): {mock_app.palette().color(QPalette.ColorRole.Window).name()}")

    print("\n--- Testando Tema Inválido ---")
    ThemeManager.apply_theme(mock_app, "invalid_theme") # type: ignore
    # Testar se voltou para o padrão
    # print(f"Cor da Janela (Inválido, deve ser padrão): {mock_app.palette().color(QPalette.ColorRole.Window).name()}")
    
    # Teste com set_placeholder_text_color (se ColorRole.PlaceholderText estiver disponível)
    # p = QPalette()
    # ThemeManager.set_placeholder_text_color(p, QColor(100,100,100))
    # placeholder_color = p.color(QPalette.ColorRole.PlaceholderText) # type: ignore
    # print(f"Cor do PlaceholderText: {placeholder_color.name() if placeholder_color.isValid() else 'Inválido/Não Suportado'}")
