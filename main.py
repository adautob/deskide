import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QMenuBar, QMenu, QAction, QTreeView, QSplitter, QFileDialog, QTabWidget)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDir, Qt, QFileInfo
from PyQt5.QtWidgets import QFileSystemModel
import os
import re

from editor import CodeEditor
from terminal_widget import CustomTerminalWidget

# **Importar o widget de chat de IA**
from ai_chat_widget import AIChatWidget


class IDE(QMainWindow):
    def __init__(self):
        super().__init__()

        # **Definir sua chave de API do Gemini aqui (use um método seguro para gerenciar chaves em produção)**
        # Por enquanto, use um placeholder ou leia de uma variável de ambiente/arquivo de configuração
        self.gemini_api_key = "AIzaSyBZl62T-QP2U8aVtvcWY5k8Y2Dv4veeZeQ" # SUBSTITUA PELA SUA CHAVE REAL OU MÉTODO SEGURO


        self.initUI()

    def initUI(self):
        self.setWindowTitle('Minha IDE Simples - Sem Título')
        self.setGeometry(100, 100, 1200, 800) # Ajusta o tamanho da janela para acomodar o terminal

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal (Vertical)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Splitter principal para dividir a área superior (Explorer+Editor) da área inferior (Terminal)
        top_bottom_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(top_bottom_splitter)


        # Splitter superior para dividir o File Explorer e o Tab Widget (Editores)
        top_splitter = QSplitter(Qt.Horizontal)
        top_bottom_splitter.addWidget(top_splitter) # Adiciona o splitter superior ao splitter principal

        # File Explorer
        self.file_system_model = QFileSystemModel()
        initial_folder = QDir.currentPath()
        self.file_system_model.setRootPath(initial_folder)
        self.file_system_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)

        self.file_tree_view = QTreeView()
        self.file_tree_view.setModel(self.file_system_model)
        self.file_tree_view.setRootIndex(self.file_system_model.index(initial_folder))
        self.file_tree_view.doubleClicked.connect(self.open_file_from_explorer)

        for i in range(1, 4):
            self.file_tree_view.hideColumn(i)

        top_splitter.addWidget(self.file_tree_view) # Adiciona ao splitter superior

        # Tab Widget para os editores
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_title_on_tab_change)

        top_splitter.addWidget(self.tab_widget) # Adiciona ao splitter superior

        # **Adicionar o widget de chat de IA como uma nova aba**
        # Passa a chave de API para o widget de chat
        self.ai_chat_widget = AIChatWidget(api_key=self.gemini_api_key)
        self.main_tab_widget.addTab(self.ai_chat_widget, "Chat de IA")

        # Os CodeEditors (editores de código) serão adicionados como outras abas
        # quando novos arquivos forem criados ou abertos.
        # O método new_file e open_file precisarão usar self.main_tab_widget para adicionar abas.


        # Define a proporção inicial do splitter superior
        top_splitter.setSizes([200, 800])

        # **Terminal Widget**
        self.terminal_widget = CustomTerminalWidget()

        # Define a proporção inicial do splitter principal (área superior e terminal)
        top_bottom_splitter.setSizes([600, 200]) # 600px para a área superior, 200px para o terminal


        # Variáveis para rastrear a pasta atual do explorer
        self.current_folder_path = initial_folder


        # Barra de Menu (mantida)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&Arquivo')
        project_menu = menubar.addMenu('&Projeto')

        # Ações de arquivo (mantidas)
        new_action = QAction('&Novo', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_file_action = QAction('&Abrir Arquivo...', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)

        save_action = QAction('&Salvar', self)
        save_action.triggered.connect(self.save_file) # Esta linha conecta a ação ao método
        save_action.setShortcut('Ctrl+S')
        file_menu.addAction(save_action)

        save_as_action = QAction('Salvar &como...', self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        # Ações do menu Projeto (mantidas)
        open_folder_action = QAction('&Abrir Pasta...', self)
        open_folder_action.triggered.connect(self.open_folder)
        project_menu.addAction(open_folder_action)

        top_splitter.addWidget(self.file_tree_view) # Adiciona ao splitter superior

        # **Tab Widget principal para a área de Editores E Chat**
        self.main_tab_widget = QTabWidget() # Cria a instância e atribui a self.main_tab_widget
        self.main_tab_widget.setTabsClosable(True) # Permite fechar abas
        self.main_tab_widget.tabCloseRequested.connect(self.close_tab)
        self.main_tab_widget.currentChanged.connect(self.update_title_on_tab_change)

        top_splitter.addWidget(self.main_tab_widget) # Adiciona o main_tab_widget ao splitter superior


        # **Adicionar o widget de chat de IA como uma nova aba**
        # Passa a chave de API para o widget de chat
        self.ai_chat_widget = AIChatWidget(api_key=self.gemini_api_key)
        self.main_tab_widget.addTab(self.ai_chat_widget, "Chat de IA")


        self.show()
        

    # Método auxiliar para obter o widget da aba ativa (pode ser um CodeEditor ou o AIChatWidget)
    # Precisará verificar o tipo do widget
    def current_active_widget(self):
        return self.main_tab_widget.currentWidget()

    # Método auxiliar para obter o editor da aba ativa (retorna None se a aba ativa não for um CodeEditor)
    def current_editor(self):
        active_widget = self.current_active_widget()
        if isinstance(active_widget, CodeEditor):
             return active_widget
        return None # Retorna None se a aba ativa não é um CodeEditor


    def new_file(self):
        print("Action \'Novo\' triggered")

        # Criar um novo editor e adicioná-lo como uma nova aba
        editor = CodeEditor() # Cria uma nova instância de CodeEditor
        # editor.current_file_path já é inicializado como None em CodeEditor.__init__
        self.tab_widget.addTab(editor, "Sem Título") # Adiciona uma nova aba com o editor e título "Sem Título"
        self.tab_widget.setCurrentWidget(editor) # Define a nova aba como ativa

        # O arquivo físico sem título não é mais criado aqui.
        # O salvamento inicial será tratado quando o usuário salvar pela primeira vez.

        # Atualizar o título da janela para refletir a nova aba (inicialmente "Sem Título")
        self.setWindowTitle('Minha IDE Simples - Sem Título')


    def open_file(self):
        print("Action \'Abrir Arquivo\' triggered")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", options=options)
        if file_path:
            try:
                # Verificar se o arquivo já está aberto em uma aba
                for i in range(self.tab_widget.count()):
                     # Precisa verificar o current_file_path de cada widget (CodeEditor)
                     if hasattr(self.tab_widget.widget(i), 'current_file_path') and self.tab_widget.widget(i).current_file_path == file_path:
                         self.tab_widget.setCurrentIndex(i) # Ativa a aba existente
                         print(f"Arquivo já aberto em aba: {file_path}")
                         return # Sai do método se o arquivo já está aberto

                # Se o arquivo não estiver aberto, criar uma nova aba
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    editor = CodeEditor()
                    editor.setPlainText(content)
                    editor.current_file_path = file_path # Define o caminho do arquivo para este editor

                    file_name = QFileInfo(file_path).fileName()
                    self.tab_widget.addTab(editor, file_name) # Adiciona nova aba com o nome do arquivo
                    self.tab_widget.setCurrentWidget(editor) # Define a nova aba como ativa

                    self.setWindowTitle(f'Minha IDE Simples - {file_name}') # Atualiza o título da janela
                    print(f"Arquivo aberto em nova aba: {file_path}")

                    # Opcional: Selecionar o arquivo no File Explorer
                    index = self.file_system_model.index(file_path)
                    if index.isValid():
                         self.file_tree_view.setCurrentIndex(index)
                         self.file_tree_view.expand(index.parent())
                         self.current_folder_path = QFileInfo(file_path).dir().absolutePath()


            except Exception as e:
                print(f"Erro ao abrir o arquivo: {e}")
        else:
            print("Operação de abrir arquivo cancelada.")


    def save_file(self):
        print("Método save_file chamado") # Debug print

        current_editor = self.current_editor() # Obtém o editor da aba ativa
        if not current_editor: # Se não houver editor ativo (nenhuma aba aberta)
            print("Nenhum editor ativo para salvar.")
            return # Sai do método

        # Usar regex para verificar se o nome do arquivo atual corresponde ao padrão "sem titulo"
        is_untitled = False
        # Não há arquivo original físico a ser excluído para um novo arquivo "sem título"
        # A lógica de exclusão será para quando o usuário SALVAR COMO um arquivo "sem título"
        # que foi criado anteriormente via "Novo" (se tivéssemos mantido a criação física imediata).
        # Com a nova lógica de "Novo", o arquivo "sem título" só existe na memória até o primeiro salvamento.
        original_file_path_if_physical = None # Usado apenas se tivéssemos criado o arquivo físico em new_file

        if current_editor.current_file_path:
            file_info = QFileInfo(current_editor.current_file_path)
            file_name = file_info.fileName()
            # import re # Já importado no topo
            pattern = r"^sem titulo(\s\d+)?\.txt$"
            if re.match(pattern, file_name):
                is_untitled = True
                # Se for um arquivo "sem título" que já foi salvo UMA VEZ, original_file_path_if_physical seria esse caminho.
                # Mas com a nova lógica de "Novo", is_untitled será True E current_editor.current_file_path será None inicialmente.
                # A lógica de "Salvar como" no else lidará com o primeiro salvamento.
                # Se for um "sem título" que já foi salvo, a lógica do if (salvar existente) se aplicaria.


        print(f"current_file_path do editor ativo: {current_editor.current_file_path}") # Debug print
        print(f"is_untitled para editor ativo: {is_untitled}") # Debug print


        if current_editor.current_file_path and not is_untitled:
            # Salvar em arquivo existente (não "sem titulo")
            print("Tentando salvar em arquivo existente") # Debug print
            try:
                content = current_editor.toPlainText() # Usa o conteúdo do editor ativo
                with open(current_editor.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Arquivo salvo: {current_editor.current_file_path}")
                # Opcional: Marcar a aba como não modificada (precisaria de uma flag de modificação no editor)
                # self.tab_widget.setTabText(self.tab_widget.currentIndex(), QFileInfo(current_editor.current_file_path).fileName())

                # **Atualizar o File Explorer (sem mudar a raiz)**
                # Tentar selecionar o arquivo salvo na árvore, se ele já estiver visível
                index_in_explorer = self.file_system_model.index(current_editor.current_file_path)
                if index_in_explorer.isValid():
                     self.file_tree_view.setCurrentIndex(index_in_explorer)
                     # Opcional: Expandir o diretório pai para garantir que o arquivo esteja visível
                     self.file_tree_view.expand(index_in_explorer.parent())
                     # Não redefinir self.current_folder_path aqui, a menos que a raiz do explorer mude


            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")
        else:
            # "Salvar como" para arquivos sem título (current_file_path is None) ou "sem titulo" que já foram salvos
            print("Executando 'Salvar como'") # Debug print
            options = QFileDialog.Options()

            # Sugerir o nome atual se for um arquivo "sem titulo" que já foi salvo
            initial_file_name = ""
            if current_editor.current_file_path: # Verificar se current_editor.current_file_path não é None
                 file_info = QFileInfo(current_editor.current_file_path)
                 file_name = file_info.fileName()
                 # Re-verificar o padrão aqui para garantir que sugere apenas para "sem titulo"
                 # import re # Já importado no topo
                 pattern = r"^sem titulo(\s\d+)?\.txt$"
                 if re.match(pattern, file_name):
                     initial_file_name = file_name


            # Usar self.current_folder_path como o diretório inicial para o diálogo de salvar
            # O initialFilter (quinto argumento) é o nome sugerido
            file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", initial_file_name, options=options)

            print(f"Caminho retornado por getSaveFileName: {file_path}") # Debug print


            if file_path:
                try:
                    content = current_editor.toPlainText() # Usa o conteúdo do editor ativo

                    # **Exclusão do arquivo "sem título" físico (se ele tivesse sido criado)**
                    # Com a nova lógica de "Novo", não há arquivo físico "sem título" para excluir
                    # até o PRIMEIRO salvamento.
                    # A lógica de exclusão aqui seria para o caso onde você SALVA UM ARQUIVO EXISTENTE
                    # que TINHA um nome "sem título" com um NOVO nome.
                    # A variável original_file_path_if_physical seria usada aqui.
                    # Como não estamos mais criando o arquivo físico em new_file, essa lógica de exclusão complexa
                    # para arquivos "sem título" criados via "Novo" se torna mais simples ou desnecessária aqui.
                    # Se um arquivo foi aberto (e não era "sem título"), o if acima lida com ele.
                    # Se é um novo arquivo ("sem título", current_editor.current_file_path is None), não há arquivo físico a ser excluído antes do primeiro salvamento.


                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    current_editor.current_file_path = file_path # Atualiza o caminho NO EDITOR ATIVO
                    file_name_saved = QFileInfo(file_path).fileName()
                    self.setWindowTitle(f'Minha IDE Simples - {file_name_saved}') # Atualiza o título da janela principal
                    self.tab_widget.setTabText(self.tab_widget.currentIndex(), file_name_saved) # Atualiza o título da aba
                    print(f"Arquivo salvo: {file_path}")
                    # Atualizar o File Explorer (sem mudar a raiz)
                    index_in_explorer = self.file_system_model.index(file_path)
                    if index_in_explorer.isValid():
                         self.file_tree_view.setCurrentIndex(index_in_explorer)
                         self.file_tree_view.expand(index_in_explorer.parent())
                         # Não redefinir self.current_folder_path aqui


                except Exception as e:
                    print(f"Erro ao salvar o arquivo: {e}")
            else:
                print("Operação de salvar cancelada.") # Debug print


    # Método para "Salvar como"
    def save_file_as(self):
        print("Action \'Salvar como...\' triggered")

        current_editor = self.current_editor() # Obtém o editor da aba ativa
        if not current_editor: # Se não houver editor ativo
            print("Nenhum editor ativo para salvar como.")
            return # Sai do método

        options = QFileDialog.Options()

        # Sugerir o nome do arquivo atual (se houver) como nome inicial
        initial_file_name = ""
        if current_editor.current_file_path: # Usa o caminho do editor ativo
            initial_file_name = QFileInfo(current_editor.current_file_path).fileName()


        # Abrir o diálogo de salvar sempre
        # Usar self.current_folder_path como o diretório inicial para o diálogo de salvar
        # O initialFilter (quinto argumento) é o nome sugerido
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo como", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", initial_file_name, options=options)

        if file_path:
            try:
                content = current_editor.toPlainText() # Usa o conteúdo do editor ativo

                # **Exclusão do arquivo original para "Salvar como"**
                # Se o arquivo original NÃO era um arquivo "sem título" e o caminho de salvamento é diferente,
                # NÃO devemos excluir o arquivo original (comportamento padrão de "Salvar como").
                # Se o arquivo original ERA um arquivo "sem título" (com o nome sem tituloX.txt que foi criado fisicamente)
                # e o caminho de salvamento é diferente, precisamos EXCLUIR o arquivo sem título original.
                # Com a nova lógica de "Novo", um arquivo sem título só tem um caminho físico depois do primeiro "Salvar como".
                # Então, se current_editor.current_file_path NÃO é None ANTES de salvar como
                # E o nome do arquivo original corresponde ao padrão "sem titulo"
                # E o novo file_path é diferente do original
                # Então excluímos o original.

                original_file_path = current_editor.current_file_path # Caminho original antes do salvamento
                is_original_untitled = False
                if original_file_path:
                     file_info = QFileInfo(original_file_path)
                     file_name = file_info.fileName()
                     # import re # Já importado no topo
                     pattern = r"^sem titulo(\s\d+)?\.txt$"
                     if re.match(pattern, file_name):
                         is_original_untitled = True


                if is_original_untitled and original_file_path and file_path != original_file_path and os.path.exists(original_file_path):
                     try:
                         os.remove(original_file_path)
                         print(f"Arquivo antigo 'sem título' excluído: {original_file_path}")
                     except Exception as e:
                         print(f"Erro ao excluir arquivo antigo 'sem título': {e}")


                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                current_editor.current_file_path = file_path # Atualiza o caminho do arquivo atual para o novo NO EDITOR ATIVO
                file_name_saved = QFileInfo(file_path).fileName()
                self.setWindowTitle(f'Minha IDE Simples - {file_name_saved}') # Atualiza o título da janela principal
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), file_name_saved) # Atualiza o título da aba
                print(f"Arquivo salvo como: {file_path}")
                 # Atualizar o File Explorer (sem mudar a raiz)
                index_in_explorer = self.file_system_model.index(file_path)
                if index_in_explorer.isValid():
                     self.file_tree_view.setCurrentIndex(index_in_explorer)
                     self.file_tree_view.expand(index_in_explorer.parent())
                     # Não redefinir self.current_folder_path aqui


            except Exception as e:
                print(f"Erro ao salvar arquivo como: {e}")
            else:
                print("Operação de salvar como cancelada.")


    def open_folder(self):
        print("Action \'Abrir Pasta...\' triggered")
        folder_path = QFileDialog.getExistingDirectory(self, "Abrir Pasta", QDir.currentPath())
        if folder_path:
            self.file_system_model.setRootPath(folder_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(folder_path))
            self.current_folder_path = folder_path # Atualiza a pasta atual do explorer
            print(f"Pasta aberta: {folder_path}")

            # **Limpar todas as abas ao abrir uma nova pasta**
            # Você pode querer perguntar ao usuário se deseja salvar antes de fechar abas modificadas
            while self.tab_widget.count() > 0:
                 # Implementar lógica de "Salvar antes de fechar" aqui, se necessário
                 widget_to_close = self.tab_widget.widget(0)
                 widget_to_close.deleteLater()
                 self.tab_widget.removeTab(0)

            self.setWindowTitle('Minha IDE Simples - Sem Título')
            # current_file_path é por editor, então não precisa resetar self.current_file_path aqui.


    def open_file_from_explorer(self, index):
        if self.file_system_model.isDir(index):
            return # Não faz nada se for um diretório

        file_path = self.file_system_model.filePath(index)
        print(f"Abrir arquivo do explorer: {file_path}")

        # **Usar a mesma lógica de open_file para abrir em abas**
        try:
            # Verificar se o arquivo já está aberto em uma aba
            for i in range(self.tab_widget.count()):
                 if hasattr(self.tab_widget.widget(i), 'current_file_path') and self.tab_widget.widget(i).current_file_path == file_path:
                     self.tab_widget.setCurrentIndex(i) # Ativa a aba existente
                     print(f"Arquivo já aberto em aba: {file_path}")
                     return # Sai do método se o arquivo já está aberto

            # Se o arquivo não estiver aberto, criar uma nova aba
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                editor = CodeEditor()
                editor.setPlainText(content)
                editor.current_file_path = file_path # Define o caminho do arquivo para este editor

                file_name = QFileInfo(file_path).fileName()
                self.tab_widget.addTab(editor, file_name) # Adiciona nova aba com o nome do arquivo
                self.tab_widget.setCurrentWidget(editor) # Define a nova aba como ativa

                self.setWindowTitle(f'Minha IDE Simples - {file_name}') # Atualiza o título da janela
                print(f"Arquivo aberto em nova aba: {file_path}")

                # Opcional: Selecionar o arquivo no File Explorer (já deve estar selecionado se clicou nele)
                index_in_explorer = self.file_system_model.index(file_path)
                if index_in_explorer.isValid():
                     self.file_tree_view.setCurrentIndex(index_in_explorer)
                     self.file_tree_view.expand(index_in_explorer.parent())
                     self.current_folder_path = QFileInfo(file_path).dir().absolutePath()


        except Exception as e:
            print(f"Erro ao abrir o arquivo do explorer: {e}")


    # Slot para fechar abas
    def close_tab(self, index):
        print(f"Fechando aba no índice: {index}")
        widget_to_close = self.tab_widget.widget(index)
        if widget_to_close:
            # Você pode adicionar lógica aqui para perguntar ao usuário se deseja salvar
            # antes de fechar, se o conteúdo do editor foi modificado.
            # widget_to_close.document().isModified() # Pode usar isModified() se implementar a flag

            widget_to_close.deleteLater() # Deleta o widget
            self.tab_widget.removeTab(index) # Remove a aba

            # Atualizar o título da janela se a aba fechada for a ativa anterior
            if self.tab_widget.count() == 0:
                 self.setWindowTitle('Minha IDE Simples - Sem Título')
                 # Não há abas, desmarcar seleção no File Explorer
                 self.file_tree_view.clearSelection()
                 # current_file_path é por editor, então não precisa resetar self.current_file_path

            else:
                 # Atualizar título para a nova aba ativa
                 self.update_title_on_tab_change(self.tab_widget.currentIndex())
        else:
            print(f"Erro: Widget na aba {index} não encontrado.")


    # Slot para atualizar o título da janela ao mudar de aba
    def update_title_on_tab_change(self, index):
        print(f"Mudança de aba para o índice: {index}")
        if index != -1: # Verifica se há alguma aba ativa
             current_editor = self.tab_widget.widget(index)
             if current_editor and hasattr(current_editor, 'current_file_path'):
                 if current_editor.current_file_path:
                     file_name = QFileInfo(current_editor.current_file_path).fileName()
                     self.setWindowTitle(f'Minha IDE Simples - {file_name}')
                     # Opcional: Selecionar o arquivo da aba ativa no File Explorer
                     index_in_explorer = self.file_system_model.index(current_editor.current_file_path)
                     if index_in_explorer.isValid():
                          self.file_tree_view.setCurrentIndex(index_in_explorer)
                          self.file_tree_view.expand(index_in_explorer.parent())
                          self.current_folder_path = QFileInfo(current_editor.current_file_path).dir().absolutePath()

                     else: # Arquivo existe mas não está no modelo atual (talvez em outra pasta aberta antes)
                          # Tentar atualizar a raiz do explorer para a pasta do arquivo? Pode ser intrusivo.
                          # Ou apenas desmarcar a seleção no explorer atual.
                          self.file_tree_view.clearSelection()
                          # Manter self.current_folder_path como estava antes da mudança de aba?
                          # Ou atualizar para a pasta do arquivo da aba?
                          if current_editor.current_file_path:
                             self.current_folder_path = QFileInfo(current_editor.current_file_path).dir().absolutePath()


                 else: # Aba sem título (novo arquivo)
                     self.setWindowTitle('Minha IDE Simples - Sem Título')
                     # Desmarcar seleção no File Explorer se for uma aba sem título
                     self.file_tree_view.clearSelection()
                     # Manter a pasta atual do explorer como estava.

             else: # Caso inesperado, widget na aba não é um CodeEditor ou não tem current_file_path
                 self.setWindowTitle('Minha IDE Simples - Erro na Aba')
                 self.file_tree_view.clearSelection()

        else: # Nenhuma aba ativa
             self.setWindowTitle('Minha IDE Simples - Sem Título')
             # Não há abas, desmarcar seleção no File Explorer
             self.file_tree_view.clearSelection()
             # current_file_path é por editor, então não precisa resetar self.current_file_path aqui.


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IDE()
    sys.exit(app.exec_())
