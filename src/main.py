import sys
import os 
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.ui.main_window import MainWindow
from src.core.database_manager import DatabaseManager
from src.ui.theme_manager import ThemeManager # Adicionado ThemeManager

def get_application_base_path():
    """Retorna o caminho base para dados, considerando se está empacotado ou em dev."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Rodando em um bundle PyInstaller (--onedir ou --onefile)
        # Para dados persistentes, o diretório do executável é mais apropriado.
        return os.path.dirname(sys.executable)
    else:
        # Rodando em modo de desenvolvimento
        # main.py está em src/, data/ está na raiz (um nível acima de src/)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def main():
    app = QApplication(sys.argv) # app deve ser instanciado antes de qualquer lógica de UI ou DB

    application_path = get_application_base_path()
    data_dir = os.path.join(application_path, "data")
    db_filename = "agenda.db" # Nome do arquivo do banco de dados
    db_path = os.path.join(data_dir, db_filename)

    print(f"INFO: Caminho base da aplicação: {application_path}") # Para debug
    print(f"INFO: Caminho do diretório de dados esperado: {data_dir}") # Para debug
    print(f"INFO: Caminho completo do banco de dados: {db_path}") # Para debug

    # Garantir que o diretório de dados exista, especialmente para a versão empacotada
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            print(f"INFO: Diretório de dados criado em: {data_dir}")
        except OSError as e:
            QMessageBox.critical(None, "Erro Crítico", 
                                 f"Erro ao criar diretório de dados {data_dir}: {e}\n"
                                 "A aplicação pode não funcionar corretamente.")
            # A aplicação provavelmente falhará se não puder criar/acessar o DB.
    
    # Inicializar o DatabaseManager com o caminho dinâmico
    db_manager = DatabaseManager(db_path=db_path)
    
    if not db_manager.conn:
        # Não podemos usar QMessageBox aqui antes de QApplication ser totalmente configurado com um tema,
        # ou pode ter aparência inconsistente ou falhar em alguns ambientes headless.
        # Imprimir no console é mais seguro para erros muito iniciais.
        print(f"ERRO CRÍTICO: Não foi possível conectar ao banco de dados em: {db_path}")
        # QMessageBox.critical(None, "Erro de Banco de Dados", ... ) # Movido para depois da app.exec se necessário
        sys.exit(1)

    # Carregar e aplicar o tema ANTES de criar a MainWindow
    saved_theme_name = db_manager.get_setting('theme_preference', 'light') # 'light' como padrão
    if saved_theme_name: # Garante que não é None
        ThemeManager.apply_theme(app, saved_theme_name)
    else: # Fallback caso get_setting retorne None inesperadamente
        ThemeManager.apply_theme(app, 'light')


    main_window = MainWindow(db_manager=db_manager) 
    main_window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
