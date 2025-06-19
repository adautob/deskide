import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMenuBar, QMenu, QAction
from editor import CodeEditor

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Minha IDE Simples')
        self.setGeometry(100, 100, 800, 600) # Posição e tamanho da janela

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Editor de texto (inicialmente um QTextEdit simples)
        self.editor = CodeEditor()
        layout.addWidget(self.editor)

        # Aqui você adicionaria outros widgets como navegador de arquivos, terminal, etc.

        # Barra de Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&Arquivo') # Use & para atalho (Alt+A)

        # Ações de arquivo
        new_action = QAction('&Novo', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction('&Abrir...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction('&Salvar', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        self.show()

    # Placeholder methods for file operations
    def new_file(self):
        print("Action 'Novo' triggered")

    def open_file(self):
        print("Action 'Abrir' triggered")

    def save_file(self):
        print("Action 'Salvar' triggered")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IDE()
    sys.exit(app.exec_())
