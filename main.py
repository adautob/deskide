import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QMenuBar, QMenu, QAction, QTreeView, QSplitter, QFileDialog)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtWidgets import QFileSystemModel

from editor import CodeEditor

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Minha IDE Simples')
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
        self.file_system_model.setRootPath(QDir.currentPath()) # Define o diretório raiz
        self.file_system_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files) # Filtra arquivos e diretórios

        self.file_tree_view = QTreeView()
        self.file_tree_view.setModel(self.file_system_model)
        self.file_tree_view.setRootIndex(self.file_system_model.index(QDir.currentPath())) # Define o índice raiz
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

        # Variável para rastrear o arquivo atual
        self.current_file_path = None

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
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Ações do menu Projeto
        open_folder_action = QAction('&Abrir Pasta...', self)
        open_folder_action.triggered.connect(self.open_folder)
        project_menu.addAction(open_folder_action)


        self.show()

    # Placeholder methods for file operations
    def new_file(self):
        print("Action \'Novo\' triggered")
        # Implementar lógica para criar novo arquivo no editor e, possivelmente, no file explorer

    def open_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", options=options)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor.setPlainText(content)
                    self.current_file_path = file_path # Atualiza o caminho do arquivo atual
                    print(f"Arquivo aberto: {self.current_file_path}")

                    # Opcional: Selecionar o arquivo no File Explorer
                    index = self.file_system_model.index(file_path)
                    if index.isValid():
                         self.file_tree_view.setCurrentIndex(index)
                         # Opcional: Expandir o diretório pai no File Explorer
                         self.file_tree_view.expand(index.parent())


            except Exception as e:
                print(f"Erro ao abrir o arquivo: {e}")
        else:
            print("Operação de abrir arquivo cancelada.")

    def save_file(self):
        if self.current_file_path:
            try:
                content = self.editor.toPlainText()
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Arquivo salvo: {self.current_file_path}")
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")
        else:
            # Se não houver arquivo atual, solicitar ao usuário onde salvar
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "", "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", options=options)
            if file_path:
                try:
                    content = self.editor.toPlainText()
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.current_file_path = file_path # Atualiza o caminho do arquivo atual
                    print(f"Arquivo salvo: {self.current_file_path}")
                    # Opcional: Atualizar o File Explorer para mostrar o novo arquivo/caminho
                    # self.file_system_model.setRootPath(QDir(file_path).cdUp().absolutePath()) # Pode ser útil ajustar a view
                except Exception as e:
                    print(f"Erro ao salvar o arquivo: {e}")
            else:
                print("Operação de salvar cancelada.")


    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Abrir Pasta", QDir.currentPath())
        if folder_path:
            self.file_system_model.setRootPath(folder_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(folder_path))
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
        except Exception as e:
            print(f"Erro ao abrir o arquivo: {e}")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IDE()
    sys.exit(app.exec_())
