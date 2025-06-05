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
    QTabBar::tab {
        color: black;
    }
    QLabel {
        color: black;
    }
    QCheckBox {
        color: black;
    }
    QRadioButton {
        color: black;
    }
    QGroupBox {
        color: black;
    }
    /* Add any other specific widget styles if necessary, ensuring they are appropriate for a light theme */
"""
            app.setStyleSheet(stylesheet)
            # app.setStyleSheet("") # Já está no início da função, não precisa repetir aqui
            print("INFO: Tema 'Claro' aplicado.")

        elif theme_name == "dark":
            dark_palette = QPalette()

            # Cores base do tema escuro
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25)) # Fundo de widgets de entrada (QLineEdit, QTextEdit)
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53)) # Usado em QTableView, QTreeView
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(42, 42, 42)) # Um pouco mais escuro que Window
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255)) # Texto em widgets de entrada
            
            # Botões
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(66, 66, 66)) # Cor de fundo do botão
            dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255)) # Texto do botão
            
            # Destaques e Links
            dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0)) # Usado para texto que precisa se destacar
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218)) # Cor padrão para links
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218)) # Cor de fundo de itens selecionados
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255)) # Texto de itens selecionados (branco é mais comum que preto aqui)

            # Cores para estados desabilitados (crucial para usabilidade)
            disabled_text_color = QColor(127, 127, 127)
            disabled_button_color = QColor(45, 45, 45)
            
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text_color)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text_color)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text_color)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, disabled_button_color)
            # Para QLineEdit, QComboBox desabilitados, o Base pode precisar ser ajustado para Disabled também
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(40,40,40)) 
            # PlaceholderText Color (não é um ColorRole direto, geralmente controlado por stylesheet ou widget específico)
            # dark_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(120,120,120)) # Exemplo

            app.setPalette(dark_palette)
            
            # Exemplo de stylesheet global que pode complementar um tema escuro
            # (focado em QLineEdit, QComboBox, QTableWidget, etc. que podem não herdar todas as cores da paleta perfeitamente)
            # app.setStyleSheet("""
            #     QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QDateTimeEdit {
            #         background-color: #191919; /* Cor de Base do tema escuro */
            #         color: #FFFFFF; /* Cor de Texto do tema escuro */
            #         border: 1px solid #353535; /* Cor de Borda sutil */
            #     }
            #     QTableView, QTableWidget {
            #         background-color: #191919;
            #         alternate-background-color: #353535;
            #         gridline-color: #4A4A4A;
            #     }
            #     QHeaderView::section {
            #         background-color: #353535;
            #         color: #FFFFFF;
            #         border: 1px solid #4A4A4A;
            #     }
            #     QPushButton {
            #         background-color: #424242;
            #         color: #FFFFFF;
            #         border: 1px solid #5A5A5A;
            #     }
            #     QPushButton:hover {
            #         background-color: #5A5A5A;
            #     }
            #     QPushButton:pressed {
            #         background-color: #303030;
            #     }
            #     QPushButton:disabled {
            #         background-color: #2D2D2D;
            #         color: #7F7F7F;
            #     }
            #     QCheckBox::indicator:unchecked { background-color: #191919; border: 1px solid #353535; }
            #     QCheckBox::indicator:checked { background-color: #2A82DA; border: 1px solid #2A82DA; }
            #     QRadioButton::indicator:unchecked { background-color: #191919; border: 1px solid #353535; }
            #     QRadioButton::indicator:checked { background-color: #2A82DA; border: 1px solid #2A82DA; }
            # """)
            print("INFO: Tema 'Escuro' aplicado (via paleta).")
            
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
