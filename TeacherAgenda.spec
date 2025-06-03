# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# --- Caminhos da Aplicação ---
# Adiciona src ao sys.path para ajudar o PyInstaller a encontrar os módulos
# Isso é similar ao --paths=./src, mas mais explícito no spec.
# No entanto, pathex em Analysis é o local preferido para isso.
# sys.path.append(os.path.join(os.path.dirname(__file__), 'src')) # Pode ser redundante se pathex for usado

# --- Análise Principal ---
a = Analysis(
    ['src/main.py'],
    pathex=[os.path.join(os.path.dirname(__file__), 'src'), os.path.dirname(__file__)], # Adiciona src e o diretório raiz do projeto
    binaries=[],
    datas=[
        # Copia a pasta 'data' e seu conteúdo para dentro do bundle,
        # na raiz do diretório da aplicação empacotada.
        ('data', 'data')
    ],
    hiddenimports=[
        'PyQt6.sip',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtSvg', 
        'PyQt6.QtXml', 
        # Adicionar outros módulos que podem ser importados dinamicamente se necessário
        # 'pkg_resources.py2_warn', # Exemplo de hidden import comum
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# --- Coleta de Módulos PyQt6 ---
# Tenta garantir que todos os plugins e componentes do PyQt6 sejam incluídos.
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Coletar arquivos de dados do PyQt6 (como traduções, plugins de plataforma)
a.datas += collect_data_files('PyQt6', include_py_files=True)

# Coletar bibliotecas dinâmicas do PyQt6 (importante para plugins como xcb)
# Isso pode ser mais eficaz do que apenas --collect-data PyQt6
binaries_pyqt = collect_dynamic_libs('PyQt6')
if binaries_pyqt:
    a.binaries += binaries_pyqt
    print(f"INFO: Bibliotecas dinâmicas do PyQt6 coletadas: {binaries_pyqt}")


# --- Geração do Executável ---
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [], # a.binaries já são coletados pelo COLLECT abaixo, não precisa aqui
    exclude_binaries=True, # Evita duplicar binários no EXE se já estiverem no COLLECT
    name='TeacherAgenda',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False, # Remoção de símbolos, pode ser True para produção menor, mas False para depuração
    upx=True, # Compressão UPX, pode ser False se UPX não estiver disponível ou causar problemas
    console=False, # False para --windowed (sem console visível)
    # windowed=True, # Redundante se console=False
    icon=None, # Caminho para um arquivo .ico/.png se tiver um ícone (ex: 'assets/icon.ico')
)

# O objeto COLLECT reúne todos os arquivos no diretório de saída
coll = COLLECT(
    exe,
    a.binaries, # Inclui binários encontrados pela análise e hooks
    a.zipfiles, # Arquivos PYZ
    a.datas,    # Arquivos de dados (incluindo os do PyQt6 e a pasta 'data')
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TeacherAgenda', # Nome do diretório de saída em dist/
)
