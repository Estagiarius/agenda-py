#!/bin/bash

# -----------------------------------------------------------------------------
# Script de Build para TeacherAgenda (Linux)
#
# Este script usa PyInstaller para empacotar a aplicação Python/Qt TeacherAgenda
# em um executável standalone para Linux.
#
# Pré-requisitos:
#   - Python 3 instalado e no PATH (o script tenta python3.10 e depois python3).
#   - pip (gerenciador de pacotes Python).
#   - Opcional, mas recomendado: UPX para compressão (se upx=True no .spec).
#
# Como usar:
#   1. Torne este script executável:
#      chmod +x build_linux.sh
#   2. Execute o script a partir da raiz do projeto:
#      ./build_linux.sh
# -----------------------------------------------------------------------------

# Navega para o diretório onde o script está localizado
# Isso garante que caminhos relativos (como ./src, ./data, TeacherAgenda.spec) funcionem corretamente.
cd "$(dirname "$0")" || exit

# Nome da Aplicação (deve corresponder ao nome no arquivo .spec e usado em dist/)
APP_NAME="TeacherAgenda"
# Script Principal (usado para mensagens informativas, o .spec define o entrypoint)
MAIN_SCRIPT_INFO="src/main.py" 

# --- Configuração do Interpretador Python ---
echo "--- Configurando Interpretador Python ---"
PYTHON_INTERP_LIST=("python3.10" "python3") 
PYTHON_INTERP=""

for interp in "${PYTHON_INTERP_LIST[@]}"; do
    if command -v "$interp" &> /dev/null; then
        PYTHON_INTERP="$interp"
        break
    fi
done

if [ -z "$PYTHON_INTERP" ]; then
    echo "Erro: Nenhum interpretador Python (python3.10 ou python3) encontrado."
    echo "Por favor, instale o Python 3.10+ e adicione-o ao seu PATH."
    exit 1
fi

echo "Usando o interpretador Python: $PYTHON_INTERP"
$PYTHON_INTERP --version

# --- Verificação e Instalação de Dependências ---
echo "Verificando e instalando/atualizando dependências..."

# Atualizar pip, se necessário
$PYTHON_INTERP -m pip install --upgrade pip

# Instalar PyInstaller e PyQt6 (ou verificar se já estão instalados)
# Usamos o requirements.txt para PyQt6 e instalamos PyInstaller separadamente
if [ -f "requirements.txt" ]; then
    $PYTHON_INTERP -m pip install --upgrade -r requirements.txt
else
    echo "Aviso: requirements.txt não encontrado. Tentando instalar PyQt6 diretamente."
    $PYTHON_INTERP -m pip install --upgrade PyQt6
fi
$PYTHON_INTERP -m pip install --upgrade pyinstaller

# --- Execução do PyInstaller ---
echo "Iniciando a construção com PyInstaller..."

# Opções do PyInstaller:
# --name: Nome do executável e do diretório de saída.
# --noconfirm: Substitui o diretório de saída sem pedir confirmação.
# --windowed: Cria um aplicativo GUI sem console (para Windows e macOS). No Linux, geralmente não tem efeito visível por padrão.
# --paths=./src: Adiciona o diretório src ao PYTHONPATH para o PyInstaller encontrar os módulos.
# --collect-data=PyQt6: Tenta coletar todos os dados necessários para o PyQt6 (plugins, etc.).
#                        Alternativamente, poderia ser --collect-all PyQt6, mas pode ser excessivo.
#                        Pode ser necessário ajustar dependendo da versão e do ambiente.
# --clean: Limpa o cache do PyInstaller e arquivos temporários antes de construir.
# Adicionar --onedir para um diretório ou --onefile para um único executável (pode ser mais lento para iniciar).
# Por padrão, --onedir é usado.
# A linha de comando do PyInstaller agora usa o arquivo .spec

$PYTHON_INTERP -m PyInstaller TeacherAgenda.spec --noconfirm
# As opções como --name, --paths, --collect-data, --windowed são gerenciadas dentro do TeacherAgenda.spec
# A opção --clean aqui garante que o build comece limpo, removendo saídas de builds anteriores.
# A opção --noconfirm no comando sobrescreve o diretório dist/TeacherAgenda sem perguntar.

# Verificar se o PyInstaller foi bem-sucedido
if [ $? -eq 0 ]; then
    echo ""
    echo "-------------------------------------------------------------------"
    echo "Build do PyInstaller concluído com sucesso!"
    echo "O executável e os arquivos relacionados estão em: dist/$APP_NAME"
    echo "-------------------------------------------------------------------"

    # --- Pós-Build: Copiar/Criar diretório de dados ---
    # Esta seção foi removida porque o arquivo .spec agora lida com a inclusão da pasta 'data'.
    # O .spec com datas=[('data', 'data')] coloca a pasta 'data' DENTRO do diretório dist/$APP_NAME.
    # A lógica em main.py (os.path.dirname(sys.executable)) deve encontrar 'data/' corretamente.
    
    echo ""
    echo "Para executar a aplicação, navegue até o diretório:"
    echo "  cd dist/$APP_NAME"
    echo "E execute:"
    echo "  ./$APP_NAME"
    echo ""
    echo "Lembre-se que pode ser necessário ajustar o PATH ou LD_LIBRARY_PATH se houver problemas com bibliotecas dinâmicas,"
    echo "especialmente para o plugin da plataforma Qt (xcb) em alguns sistemas Linux."
    echo "O uso de ambientes virtuais (venv) é recomendado para desenvolvimento e pode simplificar a gestão de dependências."

else
    echo ""
    echo "-------------------------------------------------------------------"
    echo "Erro: Build do PyInstaller falhou."
    echo "Verifique a saída acima para detalhes do erro."
    echo "-------------------------------------------------------------------"
    exit 1
fi

exit 0
