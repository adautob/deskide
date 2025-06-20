import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QMenuBar, QMenu, QAction, QTreeView, QSplitter, QFileDialog, QTabWidget)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDir, Qt, QFileInfo
from PyQt5.QtWidgets import QFileSystemModel
import os
import re

from editor import CodeEditor
from terminal_widget import CustomTerminalWidget # Importação do widget de terminal
from ai_chat_widget import AIChatWidget # Importação do widget de chat de IA


class IDE(QMainWindow):
    def __init__(self):
        super().__init__()

        # **Definir sua chave de API do Gemini aqui (use um método seguro para gerenciar chaves em produção)**
        # Por enquanto, use um placeholder ou leia de uma variável de ambiente/arquivo de configuração
        self.gemini_api_key = "AIzaSyBZl62T-QP2U8aVtvcWY5k8Y2Dv4veeZeQ" # SUBSTITUA PELA SUA CHAVE REAL OU MÉTODO SEGURO


        self.initUI()

    def initUI(self):
        self.setWindowTitle('Minha IDE Simples - Sem Título')
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        top_bottom_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(top_bottom_splitter)

        # Splitter superior para dividir o File Explorer e a área de Abas (Editores + Chat)
        top_splitter = QSplitter(Qt.Horizontal)
        top_bottom_splitter.addWidget(top_splitter)

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

        top_splitter.addWidget(self.file_tree_view)

        # **Tab Widget principal para a área de Editores E Chat**
        self.main_tab_widget = QTabWidget() # Cria a instância e atribui a self.main_tab_widget
        self.main_tab_widget.setTabsClosable(True) # Permitir fechar abas (exceto a de chat se não for fechável)
        self.main_tab_widget.tabCloseRequested.connect(self.close_tab)
        self.main_tab_widget.currentChanged.connect(self.update_title_on_tab_change)

        top_splitter.addWidget(self.main_tab_widget) # Adiciona o main_tab_widget ao splitter superior


        # **Adicionar o widget de chat de IA como a primeira aba**
        # Passa a chave de API para o widget de chat
        # Certifique-se que self.gemini_api_key foi definido no __init__
        self.ai_chat_widget = AIChatWidget(api_key=self.gemini_api_key)
        self.main_tab_widget.addTab(self.ai_chat_widget, "Chat de IA")

        # Os CodeEditors (editores de código) serão adicionados como outras abas
        # quando novos arquivos forem criados ou abertos.
        # Podemos adicionar uma aba de editor inicial vazia aqui, se desejado
        # self.new_file() # Chamar new_file para adicionar uma aba de editor inicial

        # Define a proporção inicial do splitter superior
        top_splitter.setSizes([200, 800])

        # Terminal Widget
        # Assumindo que CustomTerminalWidget está importado e funciona
        self.terminal_widget = CustomTerminalWidget()
        top_bottom_splitter.addWidget(self.terminal_widget)

        # Define a proporção inicial do splitter principal (área superior e terminal)
        top_bottom_splitter.setSizes([600, 200])


        # Variáveis para rastrear a pasta atual do explorer
        # current_file_path agora é uma propriedade de cada CodeEditor
        self.current_folder_path = initial_folder


        # Barra de Menu (mantida)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&Arquivo')
        project_menu = menubar.addMenu('&Projeto')

        # Ações de arquivo (mantidas, precisarão ser ajustadas para usar self.main_tab_widget e current_editor())
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
        # save_action.triggered.connect(self.save_file) # Esta linha já deve estar conectada em outro lugar ou não precisa aqui
        file_menu.addAction(save_action)

        save_as_action = QAction('Salvar &como...', self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)


        # Conectar save_action.triggered AO MÉTODO save_file
        # Garantir que esta conexão esteja presente e correta
        save_action.triggered.connect(self.save_file)


        # Ações do menu Projeto (mantidas)
        open_folder_action = QAction('&Abrir Pasta...', self)
        open_folder_action.triggered.connect(self.open_folder)
        project_menu.addAction(open_folder_action)


        self.show()

         # **Carregar e aplicar Qt Style Sheet**
        try:
            with open('style.qss', 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read()) # Aplica o estilo à janela principal (IDE)
                # Ou QApplication.instance().setStyleSheet(f.read()) para aplicar a toda a aplicação

            print("Qt Style Sheet 'style.qss' carregado e aplicado.") # Debug print

        except FileNotFoundError:
            print("Erro: Arquivo 'style.qss' não encontrado.")
        except Exception as e:
            print(f"Erro ao carregar ou aplicar style sheet: {e}")

    # Método auxiliar para obter o widget da aba ativa (pode ser um CodeEditor ou o AIChatWidget)
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

        # Criar um novo editor e adicioná-lo como uma nova aba no main_tab_widget
        editor = CodeEditor() # Cria uma nova instância de CodeEditor
        self.main_tab_widget.addTab(editor, "Sem Título") # Adiciona uma nova aba com o editor e título "Sem Título"
        self.main_tab_widget.setCurrentWidget(editor) # Define a nova aba como ativa

        # O arquivo físico sem título não é mais criado aqui.
        # O salvamento inicial será tratado quando o usuário salvar pela primeira vez.

        # Atualizar o título da janela para refletir a nova aba (inicialmente "Sem Título")
        self.setWindowTitle('Minha IDE Simples - Sem Título')


    # Modificar open_file para aceitar um argumento opcional de file_path
    def open_file(self, file_path=None):
        print("Action \'Abrir Arquivo\' triggered")
        if file_path is None: # Se file_path não foi fornecido (chamado do menu Arquivo -> Abrir Arquivo...)
             options = QFileDialog.Options()
             file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", options=options)

        if file_path: # Se file_path foi obtido (do diálogo ou argumento)
            try:
                # Verificar se o arquivo já está aberto em uma aba no main_tab_widget
                for i in range(self.main_tab_widget.count()):
                     widget = self.main_tab_widget.widget(i)
                     # Precisa verificar se o widget é um CodeEditor antes de acessar current_file_path
                     if isinstance(widget, CodeEditor) and hasattr(widget, 'current_file_path') and widget.current_file_path == file_path:
                         self.main_tab_widget.setCurrentIndex(i) # Ativa a aba existente
                         print(f"Arquivo já aberto em aba: {file_path}")
                         return # Sai do método se o arquivo já está aberto

                # Se o arquivo não estiver aberto, criar uma nova aba no main_tab_widget
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    editor = CodeEditor() # Cria uma nova instância de CodeEditor para a nova aba
                    editor.setPlainText(content)
                    editor.current_file_path = file_path # Define o caminho do arquivo para este editor

                    file_name = QFileInfo(file_path).fileName()
                    self.main_tab_widget.addTab(editor, file_name) # Adiciona nova aba com o nome do arquivo
                    self.main_tab_widget.setCurrentWidget(editor) # Define a nova aba como ativa

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

        current_editor = self.current_editor() # Obtém o editor da aba ativa (retorna None se a aba não for editor)
        if not current_editor: # Se não houver editor ativo (aba de chat ou nenhuma aba)
            print("Nenhum editor ativo para salvar.")
            return # Sai do método

        # Usar regex para verificar se o nome do arquivo atual corresponde ao padrão "sem titulo"
        is_untitled = False
        original_file_path_if_physical = None

        if current_editor.current_file_path:
            file_info = QFileInfo(current_editor.current_file_path)
            file_name = file_info.fileName()
            pattern = r"^sem titulo(\s\d+)?\.txt$"
            if re.match(pattern, file_name):
                is_untitled = True


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

                # Atualizar o File Explorer (sem mudar a raiz)
                index_in_explorer = self.file_system_model.index(current_editor.current_file_path)
                if index_in_explorer.isValid():
                     self.file_tree_view.setCurrentIndex(index_in_explorer)
                     self.file_tree_view.expand(index_in_explorer.parent())


            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")
        else:
            # "Salvar como" para arquivos sem título (current_file_path is None) ou "sem titulo" que já foram salvos
            print("Executando 'Salvar como'") # Debug print
            options = QFileDialog.Options()

            # Sugerir o nome atual se for um arquivo "sem titulo" que já foi salvo
            initial_file_name = ""
            if current_editor.current_file_path:
                 file_info = QFileInfo(current_editor.current_file_path)
                 file_name = file_info.fileName()
                 pattern = r"^sem titulo(\s\d+)?\.txt$"
                 if re.match(pattern, file_name):
                     initial_file_name = file_name


            file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", initial_file_name, options=options)

            print(f"Caminho retornado por getSaveFileName: {file_path}") # Debug print


            if file_path:
                try:
                    content = current_editor.toPlainText()

                    original_file_path = current_editor.current_file_path
                    is_original_untitled = False
                    if original_file_path:
                         file_info = QFileInfo(original_file_path)
                         file_name = file_info.fileName()
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

                    current_editor.current_file_path = file_path # Atualiza o caminho NO EDITOR ATIVO
                    file_name_saved = QFileInfo(file_path).fileName()
                    self.setWindowTitle(f'Minha IDE Simples - {file_name_saved}') # Atualiza o título da janela principal
                    self.main_tab_widget.setTabText(self.main_tab_widget.currentIndex(), file_name_saved) # Atualiza o título da aba
                    print(f"Arquivo salvo: {file_path}")
                    # Atualizar o File Explorer (sem mudar a raiz)
                    index_in_explorer = self.file_system_model.index(file_path)
                    if index_in_explorer.isValid():
                         self.file_tree_view.setCurrentIndex(index_in_explorer)
                         self.file_tree_view.expand(index_in_explorer.parent())


                except Exception as e:
                    print(f"Erro ao salvar o arquivo: {e}")
            else:
                print("Operação de salvar cancelada.")


    # Método para "Salvar como"
    def save_file_as(self):
        print("Action \'Salvar como...\' triggered")

        current_editor = self.current_editor() # Obtém o editor da aba ativa
        if not current_editor: # Se não houver editor ativo
            print("Nenhum editor ativo para salvar como.")
            return

        options = QFileDialog.Options()

        initial_file_name = ""
        if current_editor.current_file_path:
            initial_file_name = QFileInfo(current_editor.current_file_path).fileName()


        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo como", self.current_folder_path, "Todos os Arquivos (*);;Arquivos de Texto (*.txt)", initial_file_name, options=options)

        if file_path:
            try:
                content = current_editor.toPlainText()

                original_file_path = current_editor.current_file_path
                is_original_untitled = False
                if original_file_path:
                     file_info = QFileInfo(original_file_path)
                     file_name = file_info.fileName()
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
                self.setWindowTitle(f'Minha IDE Simples - {file_name_saved}')
                self.main_tab_widget.setTabText(self.main_tab_widget.currentIndex(), file_name_saved)
                print(f"Arquivo salvo como: {file_path}")
                 # Atualizar o File Explorer (sem mudar a raiz)
                index_in_explorer = self.file_system_model.index(file_path)
                if index_in_explorer.isValid():
                     self.file_tree_view.setCurrentIndex(index_in_explorer)
                     self.file_tree_view.expand(index_in_explorer.parent())


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

            # **Limpar abas de editor ao abrir uma nova pasta, mantendo a aba de chat**
            # Itere sobre as abas e remova APENAS as que contêm CodeEditors
            tabs_to_remove = []
            for i in range(self.main_tab_widget.count()):
                 widget = self.main_tab_widget.widget(i)
                 if isinstance(widget, CodeEditor): # Verifica se o widget é um CodeEditor
                      tabs_to_remove.append(i) # Adiciona o índice da aba de editor para remover

            # Remover as abas identificadas (remova em ordem inversa para não invalidar índices)
            for i in reversed(tabs_to_remove):
                 widget_to_close = self.main_tab_widget.widget(i)
                 widget_to_close.deleteLater()
                 self.main_tab_widget.removeTab(i)


            # Opcional: Após fechar as abas de editor, garantir que o Chat de IA esteja visível se for a única aba restante
            # Verifica se a aba de chat de IA ainda existe antes de tentar selecioná-la
            chat_tab_index = -1
            for i in range(self.main_tab_widget.count()):
                 if isinstance(self.main_tab_widget.widget(i), AIChatWidget):
                      chat_tab_index = i
                      break # Encontrou a aba de chat, pode sair do loop

            if chat_tab_index != -1:
                 self.main_tab_widget.setCurrentIndex(chat_tab_index) # Define a aba de chat como ativa


            self.setWindowTitle('Minha IDE Simples - Sem Título') # Título pode ser ajustado


    def open_file_from_explorer(self, index):
        if self.file_system_model.isDir(index):
            return # Não faz nada se for um diretório

        file_path = self.file_system_model.filePath(index)
        print(f"Abrir arquivo do explorer: {file_path}")

        # **Reutilizar a lógica de open_file para abrir em abas**
        # O método open_file já verifica se o arquivo está aberto e abre em uma nova aba se necessário
        self.open_file(file_path) # Chama open_file passando o caminho do arquivo


    # Slot para fechar abas
    def close_tab(self, index):
        print(f"Fechando aba no índice: {index}")
        widget_to_close = self.main_tab_widget.widget(index)
        if widget_to_close:
            # **Adicionar lógica para não fechar a aba do chat de IA pelo botão de fechar**
            if isinstance(widget_to_close, AIChatWidget):
                 print("Tentativa de fechar a aba do Chat de IA bloqueada.")
                 return # Não fecha a aba de chat de IA

            # Você pode adicionar lógica aqui para perguntar ao usuário se deseja salvar
            # antes de fechar, se o conteúdo do editor foi modificado.
            # widget_to_close.document().isModified() # Pode usar isModified() se implementar a flag

            widget_to_close.deleteLater() # Deleta o widget
            self.main_tab_widget.removeTab(index) # Remove a aba

            # Atualizar o título da janela se a aba fechada for a ativa anterior
            if self.main_tab_widget.count() == 0:
                 self.setWindowTitle('Minha IDE Simples - Sem Título')
                 # Não há abas, desmarcar seleção no File Explorer
                 self.file_tree_view.clearSelection()


            else:
                 # Atualizar título para a nova aba ativa
                 self.update_title_on_tab_change(self.main_tab_widget.currentIndex())
        else:
            print(f"Erro: Widget na aba {index} não encontrado.")


    # Slot para atualizar o título da janela ao mudar de aba
    def update_title_on_tab_change(self, index):
        print(f"Mudança de aba para o índice: {index}")
        if index != -1: # Verifica se há alguma aba ativa
             current_widget = self.main_tab_widget.widget(index) # Obtém o widget da aba ativa
             # Verificar se o widget ativo é um CodeEditor antes de tentar acessar current_file_path
             if isinstance(current_widget, CodeEditor) and hasattr(current_widget, 'current_file_path'):
                 if current_widget.current_file_path:
                     file_name = QFileInfo(current_widget.current_file_path).fileName()
                     self.setWindowTitle(f'Minha IDE Simples - {file_name}')
                     # Opcional: Selecionar o arquivo da aba ativa no File Explorer
                     index_in_explorer = self.file_system_model.index(current_widget.current_file_path)
                     if index_in_explorer.isValid():
                          self.file_tree_view.setCurrentIndex(index_in_explorer)
                          self.file_tree_view.expand(index_in_explorer.parent())
                          self.current_folder_path = QFileInfo(current_widget.current_file_path).dir().absolutePath()

                     else: # Arquivo existe mas não está no modelo atual (talvez em outra pasta aberta antes)
                          self.file_tree_view.clearSelection()
                          if current_widget.current_file_path:
                             self.current_folder_path = QFileInfo(current_widget.current_file_path).dir().absolutePath()


                 else: # Aba de editor sem título (novo arquivo)
                     self.setWindowTitle('Minha IDE Simples - Sem Título')
                     self.file_tree_view.clearSelection()
             elif isinstance(current_widget, AIChatWidget):
                 # Se a aba ativa for o chat de IA
                 self.setWindowTitle('Minha IDE Simples - Chat de IA')
                 self.file_tree_view.clearSelection() # Desmarcar seleção no File Explorer ao ir para o chat
                 # Manter a pasta atual do explorer como estava.

             else: # Caso inesperado, widget na aba não é um tipo conhecido
                 self.setWindowTitle('Minha IDE Simples - Tipo de Aba Desconhecido')
                 self.file_tree_view.clearSelection()


        else: # Nenhuma aba ativa
             self.setWindowTitle('Minha IDE Simples - Sem Título')
             self.file_tree_view.clearSelection()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IDE()
    sys.exit(app.exec_())
