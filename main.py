import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QMenuBar, QMenu, QAction, QTreeView, QSplitter, QFileDialog)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDir, Qt, QFileInfo
from PyQt5.QtWidgets import QFileSystemModel
import os # Importação necessária para exclusão

from editor import CodeEditor

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Minha IDE Simples - Sem Título') # Define o título inicial
        self.setGeometry(100, 100, 1000, 800) # Ajusta o tamanho da janela

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Splitter para dividir o File Explorer e o Editor
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # File Explorer
        self.file_system_model = QFileSystemModel()
        # Inicializa com o diretório atual do projeto
        initial_folder = QDir.currentPath()
        self.file_system_model.setRootPath(initial_folder)
        self.file_system_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files) # Filtra arquivos e diretórios

        self.file_tree_view = QTreeView()
        self.file_tree_view.setModel(self.file_system_model)
        self.file_tree_view.setRootIndex(self.file_system_model.index(initial_folder)) # Define o índice raiz inicial
        self.file_tree_view.doubleClicked.connect(self.open_file_from_explorer) # Conecta o double click

        # Oculta colunas desnecessárias (tamanho, tipo, data)
        for i in range(1, 4):
            self.file_tree_view.hideColumn(i)

        splitter.addWidget(self.file_tree_view)

        # Editor de texto
        self.editor = CodeEditor()
        splitter.addWidget(self.editor)

        # Define a proporção inicial do splitter
        splitter.setSizes([200, 800]) # 200px para o file explorer, 800px para o editor

        # Variáveis para rastrear o arquivo e a pasta atuais
        self.current_file_path = None
        self.current_folder_path = initial_folder # Armazena a pasta atualmente exibida no explorer


        # Barra de Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&Arquivo') # Use & para atalho (Alt+A)
        project_menu = menubar.addMenu('&Projeto') # Novo menu para ações do projeto

        # Ações de arquivo
        new_action = QAction('&Novo', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_file_action = QAction('&Abrir Arquivo...', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)

        save_action = QAction('&Salvar', self)
        save_action.setShortcut('Ctrl+S')
        file_menu.addAction(save_action)

        # **Adiciona a ação "Salvar como..."**
        save_as_action = QAction('Salvar &como...', self) # Use & para atalho (Alt+C)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        save_action.triggered.connect(self.save_file) # Esta linha conecta a ação ao método


        # Ações do menu Projeto
        open_folder_action = QAction('&Abrir Pasta...', self)
        open_folder_action.triggered.connect(self.open_folder)
        project_menu.addAction(open_folder_action)


        self.show()

    # Placeholder methods for file operations
    def new_file(self):
        print("Action \'Novo\' triggered")
        self.editor.clear() # Limpa o conteúdo do editor
        self.current_file_path = None # Reseta o caminho do arquivo atual

        default_file_name_base = "sem titulo"
        file_extension = ".txt"
        file_number = 1
        new_file_path = ""
        file_exists = True

        # Usar a pasta atual do File Explorer como diretório para o novo arquivo
        target_dir = self.current_folder_path if self.current_folder_path else QDir.currentPath()


        # Loop para encontrar um nome de arquivo disponível na pasta alvo
        while file_exists:
            if file_number == 1:
                new_file_name = default_file_name_base + file_extension
            else:
                new_file_name = f"{default_file_name_base} {file_number}{file_extension}"

            new_file_path = QDir(target_dir).filePath(new_file_name)
            file_exists = QFileInfo(new_file_path).exists()
            file_number += 1

        try:
            # Tenta criar e salvar um arquivo vazio com o nome encontrado
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write("") # Salva um arquivo vazio
            self.current_file_path = new_file_path # Atualiza o caminho do arquivo atual
            self.setWindowTitle(f'Minha IDE Simples - {QFileInfo(self.current_file_path).fileName()}') # Atualiza o título da janela
            print(f"Novo arquivo criado: {self.current_file_path}")

            # Atualizar o File Explorer para mostrar o novo arquivo na pasta correta
            index = self.file_system_model.index(self.current_file_path)
            if index.isValid():
                 self.file_tree_view.setCurrentIndex(index)
                 # Opcional: Expandir o diretório pai para garantir que o arquivo esteja visível
                 self.file_tree_view.expand(index.parent())


        except Exception as e:
            print(f"Erro ao criar novo arquivo: {e}")
            # Em caso de erro, você pode querer voltar ao estado de "sem título"
            self.current_file_path = None
            self.setWindowTitle('Minha IDE Simples - Sem Título')


    def open_file(self):
        options = QFileDialog.Options()
        # Usar self.current_folder_path como o diretório inicial para o diálogo de abrir
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", options=options)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor.setPlainText(content)
                    self.current_file_path = file_path # Atualiza o caminho do arquivo atual
                    self.setWindowTitle(f'Minha IDE Simples - {QFileInfo(self.current_file_path).fileName()}') # Atualiza o título ao abrir
                    print(f"Arquivo aberto: {self.current_file_path}")

                    # Opcional: Selecionar o arquivo no File Explorer
                    index = self.file_system_model.index(file_path)
                    if index.isValid():
                         self.file_tree_view.setCurrentIndex(index)
                         # Opcional: Expandir o diretório pai no File Explorer
                         self.file_tree_view.expand(index.parent())
                         # Atualiza a pasta atual do explorer para a pasta do arquivo aberto
                         self.current_folder_path = QFileInfo(file_path).dir().absolutePath()


            except Exception as e:
                print(f"Erro ao abrir o arquivo: {e}")
        else:
            print("Operação de abrir arquivo cancelada.")

    def save_file(self):
        # Usar regex para verificar se o nome do arquivo atual corresponde ao padrão "sem titulo"
        is_untitled = False
        original_file_path = self.current_file_path # Armazena o caminho original antes de potencial mudança

        if self.current_file_path:
            file_info = QFileInfo(self.current_file_path)
            file_name = file_info.fileName()
            import re
            pattern = r"^sem titulo(\s\d+)?\.txt$"
            if re.match(pattern, file_name):
                is_untitled = True

        if self.current_file_path and not is_untitled:
            # Salvar em arquivo existente (não "sem titulo")
            try:
                content = self.editor.toPlainText()
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Arquivo salvo: {self.current_file_path}")
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")
        else:
            # "Salvar como" para arquivos sem título ou sem caminho definido
            options = QFileDialog.Options()

            # Sugerir o nome atual se for um arquivo "sem titulo"
            initial_file_name = ""
            if self.current_file_path: # Verificar se self.current_file_path não é None antes de tentar obter o nome
                 file_info = QFileInfo(self.current_file_path)
                 file_name = file_info.fileName()
                 # Re-verificar o padrão aqui para garantir que sugere apenas para "sem titulo"
                 import re
                 pattern = r"^sem titulo(\s\d+)?\.txt$"
                 if re.match(pattern, file_name):
                     initial_file_name = file_name


            # Usar self.current_folder_path como o diretório inicial para o diálogo de salvar
            file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", initial_file_name, options=options)

            if file_path:
                try:
                    content = self.editor.toPlainText()

                    # Implementar exclusão do arquivo antigo "sem titulo" se o nome mudou
                    # Usar original_file_path para a verificação
                    if is_untitled and original_file_path and file_path != original_file_path and os.path.exists(original_file_path):
                        try:
                            os.remove(original_file_path)
                            print(f"Arquivo antigo excluído: {original_file_path}")
                        except Exception as e:
                            print(f"Erro ao excluir arquivo antigo: {e}")


                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    self.current_file_path = file_path # Atualiza o caminho do arquivo atual
                    self.setWindowTitle(f'Minha IDE Simples - {QFileInfo(self.current_file_path).fileName()}') # Atualiza o título
                    print(f"Arquivo salvo: {self.current_file_path}")
                    # Atualizar o File Explorer pode ser necessário para refletir a renomeação/novo arquivo
                    # Define a raiz do modelo e da view para a pasta onde o arquivo foi salvo
                    saved_file_dir = QFileInfo(file_path).dir().absolutePath()
                    self.file_system_model.setRootPath(saved_file_dir)
                    self.file_tree_view.setRootIndex(self.file_system_model.index(saved_file_dir))
                    self.current_folder_path = saved_file_dir # Atualiza a pasta atual do explorer


                except Exception as e:
                    print(f"Erro ao salvar o arquivo: {e}")
            else:
                print("Operação de salvar cancelada.")

    # **Novo método para "Salvar como"**
    def save_file_as(self):
        print("Action \'Salvar como...\' triggered")
        options = QFileDialog.Options()

        # Sugerir o nome do arquivo atual (se houver) como nome inicial
        initial_file_name = ""
        if self.current_file_path:
            initial_file_name = QFileInfo(self.current_file_path).fileName()


        # Abrir o diálogo de salvar sempre
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo como", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", initial_file_name, options=options)

        if file_path:
            try:
                content = self.editor.toPlainText()

                # Para "Salvar como", geralmente não excluímos o arquivo original
                # a menos que seja um caso específico de renomear um "sem titulo"
                # A lógica de exclusão para "sem titulo" ao salvar já está em save_file
                # Se precisar de lógica de exclusão aqui, seria para casos diferentes


                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.current_file_path = file_path # Atualiza o caminho do arquivo atual para o novo
                self.setWindowTitle(f'Minha IDE Simples - {QFileInfo(self.current_file_path).fileName()}') # Atualiza o título
                print(f"Arquivo salvo como: {self.current_file_path}")
                # Atualizar o File Explorer para refletir o novo arquivo/caminho
                saved_file_dir = QFileInfo(file_path).dir().absolutePath()
                self.file_system_model.setRootPath(saved_file_dir)
                self.file_tree_view.setRootIndex(self.file_system_model.index(saved_file_dir))
                self.current_folder_path = saved_file_dir # Atualiza a pasta atual do explorer


            except Exception as e:
                print(f"Erro ao salvar arquivo como: {e}")
        else:
            print("Operação de salvar como cancelada.")


    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Abrir Pasta", QDir.currentPath())
        if folder_path:
            self.file_system_model.setRootPath(folder_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(folder_path))
            self.current_folder_path = folder_path # Atualiza a pasta atual do explorer
            # Opcional: Limpar o editor e resetar o arquivo atual ao abrir uma nova pasta
            self.editor.clear()
            self.current_file_path = None
            self.setWindowTitle('Minha IDE Simples - Sem Título')
            print(f"Pasta aberta: {folder_path}")


    def open_file_from_explorer(self, index):
        if self.file_system_model.isDir(index):
            return # Não faz nada se for um diretório

        file_path = self.file_system_model.filePath(index)
        print(f"Abrir arquivo do explorer: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.editor.setPlainText(content)
                self.current_file_path = file_path # Atualiza o caminho do arquivo atual
                self.setWindowTitle(f'Minha IDE Simples - {QFileInfo(self.current_file_path).fileName()}') # Atualiza o título ao abrir do explorer
                # Atualiza a pasta atual do explorer para a pasta do arquivo aberto
                self.current_folder_path = QFileInfo(file_path).dir().absolutePath()

        except Exception as e:
            print(f"Erro ao abrir o arquivo: {e}")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IDE()
    sys.exit(app.exec_())
