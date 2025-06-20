# No arquivo terminal_widget.py

import sys
import subprocess
from PyQt5.QtWidgets import QPlainTextEdit, QApplication, QVBoxLayout # Adicionado QApplication para o bloco __main__
from PyQt5.QtCore import QProcess, QTextCodec, QByteArray, QIODevice, QTimer, Qt, QPoint # Adicionada QPoint
from PyQt5.QtCore import pyqtSignal as Signal # Importação corrigida
import threading
import os

class CustomTerminalWidget(QPlainTextEdit):
    # Sinal para emitir a saída do terminal de forma segura para a UI thread
    output_received = Signal(str)


    def __init__(self, parent=None, shell_program=None):
        super().__init__(parent)

        # Tentar encontrar o shell bash ou cmd/powershell no Windows
        if shell_program is None:
            if sys.platform.startswith('linux') or sys.platform == 'darwin':
                shell_program = "bash"
            elif sys.platform == 'win32':
                # No Windows, tentar cmd.exe ou powershell.exe
                shell_program = "cmd.exe"
                # shell_program = "powershell.exe" # Opcional: tentar Powershell
            else:
                shell_program = "sh" # Fallback para sh

        self.shell_program = shell_program
        self.process = None
        self.command_start_position = 0 # Rastreia o início da linha de comando

        self.setReadOnly(True) # Inicialmente somente para exibição
        self.appendPlainText(f"Iniciando terminal com: {self.shell_program}...\n")

        # Conecta o sinal output_received ao slot para exibir a saída
        self.output_received.connect(self.appendPlainText)

        self.start_shell()


    def start_shell(self):
        try:
            # Inicia o subprocesso do shell
            # stdout e stderr são redirecionados para PIPE
            # stdin também é redirecionado para PIPE para que possamos enviar comandos
            # cwd (current working directory) pode ser definido se necessário para iniciar na pasta do projeto
            # cwd=os.getcwd() # Exemplo: iniciar na pasta atual do script

            self.process = subprocess.Popen(
                self.shell_program,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Decodifica stdout/stderr como texto
                bufsize=1, # Buffer de linha para stdout/stderr
                universal_newlines=True # Sinônimo para text em versões mais recentes
                # shell=True # Use shell=True se precisar que o comando seja executado através do shell do sistema (pode ser necessário para alguns comandos)
            )

            # Lê a saída do stdout e stderr em threads separadas para não bloquear a UI
            # daemon=True para encerrar as threads automaticamente com o programa
            import threading
            threading.Thread(target=self.read_output, args=(self.process.stdout, False), daemon=True).start()
            threading.Thread(target=self.read_output, args=(self.process.stderr, True), daemon=True).start()

            # **Após iniciar o shell, tornar o widget editável e definir a posição inicial da linha de comando**
            # Usar singleShot para garantir que isso rode na UI thread após a inicialização da janela
            QTimer.singleShot(100, self.after_shell_start) # Pequeno atraso para a UI thread estar pronta


        except FileNotFoundError:
            self.appendPlainText(f"Erro: Programa do shell '{self.shell_program}' não encontrado.")
            self.setReadOnly(False) # Permitir edição para ver a mensagem de erro e tentar digitar
        except Exception as e:
            self.appendPlainText(f"Erro ao iniciar o shell: {e}")
            self.setReadOnly(False) # Permitir edição para ver a mensagem de erro e tentar digitar


    def after_shell_start(self):
         # Método chamado na UI thread após um pequeno atraso para inicializar a entrada
         self.setReadOnly(False)
         self.moveCursor(self.textCursor().End) # Move o cursor para o final
         self.command_start_position = self.textCursor().position() # Salva a posição do cursor
         # Opcional: Adicionar um prompt inicial se o shell não enviar um imediatamente
         # self.insertPlainText("$ ")
         # self.command_start_position = self.textCursor().position() # Atualiza após adicionar o prompt


    def read_output(self, pipe, is_stderr):
        # Lê a saída do pipe e emite um sinal para a UI thread
        try:
            # Iterar sobre as linhas do pipe até que ele seja fechado
            for line in iter(pipe.readline, ''):
                # Emitir a linha para a UI thread para exibição
                self.output_received.emit(line)

            # Se o pipe fechar (processo terminou), emitir uma mensagem de término
            self.output_received.emit(f"\nProcesso do shell ({self.shell_program}) encerrado.\n")


        except Exception as e:
            # Emitir erro para a UI thread também
            self.output_received.emit(f"\nErro na leitura do pipe ({'stderr' if is_stderr else 'stdout'}): {e}\n")


    # Slot conectado ao sinal output_received
    def appendPlainText(self, text):
        # Adiciona texto ao widget e rola para o final
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.ensureCursorVisible() # Garante que o cursor (e o texto adicionado) esteja visível


    # Método para enviar comandos para o shell
    def send_command(self, command):
        if self.process and self.process.stdin:
            try:
                # Adiciona a linha digitada e uma nova linha visualmente antes de enviar
                # Isso simula o usuário digitando Enter
                self.appendPlainText(command + '\n') # Adiciona o comando digitado e uma quebra de linha
                self.process.stdin.write(command + '\n') # Envia o comando com uma quebra de linha
                self.process.stdin.flush() # Garante que o comando seja enviado imediatamente
                self.setReadOnly(True) # Torna somente leitura enquanto espera a resposta

            except Exception as e:
                self.appendPlainText(f"Erro ao enviar comando: {e}\n")
                self.setReadOnly(False) # Tornar editável novamente em caso de erro
                self.moveCursor(self.textCursor().End)
                self.command_start_position = self.textCursor().position() # Redefinir posição de início

        else:
            self.appendPlainText("Shell não iniciado ou stdin não disponível.\n")


    # Lidar com eventos de teclado
    def keyPressEvent(self, event):
        if self.process and self.process.stdin and not self.isReadOnly():
            cursor = self.textCursor()
            # Obter a posição do cursor em relação ao início do documento
            cursor_position_in_document = cursor.position()

            # Se a tecla Enter for pressionada
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # Obter o texto da linha atual a partir da posição de início do comando
                cursor.movePosition(cursor.End) # Move para o final
                cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor) # Seleciona a linha atual
                current_line_with_prompt = cursor.selectedText()

                # Extrair o texto digitado pelo usuário (após self.command_start_position)
                # Calcula o deslocamento do cursor desde o início do documento
                # E subtrai a posição de início do comando
                command_text = current_line_with_prompt[self.command_start_position - cursor.block().position() - (self.command_start_position - cursor_position_in_document):]


                self.send_command(command_text.strip()) # Envia o comando (remove espaços em branco no início/fim)


            # Lidar com Backspace
            elif event.key() == Qt.Key_Backspace:
                 # Apenas apagar se o cursor estiver após a posição de início do comando
                 if cursor_position_in_document > self.command_start_position:
                     cursor.deletePreviousChar()
                     # Não chamar super().keyPressEvent para evitar comportamento padrão
                 # else: ignorar backspace antes do início do comando

            # TODO: Implementar movimentação básica do cursor na linha de comando
            # Evitar que o cursor vá para linhas anteriores ou antes do início do comando
            elif event.key() == Qt.Key_Left:
                if cursor_position_in_document > self.command_start_position:
                    super().keyPressEvent(event) # Permite mover para a esquerda
            elif event.key() == Qt.Key_Right:
                 super().keyPressEvent(event) # Permite mover para a direita
            elif event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
                 # TODO: Implementar histórico de comandos
                 pass # Ignora teclas de seta para cima/baixo por enquanto
            elif event.key() == Qt.Key_Delete:
                 # TODO: Implementar tecla Delete
                 pass # Ignora tecla Delete por enquanto

            else:
                # Para outras teclas (caracteres normais), adicionar o texto na posição do cursor
                # e manter o cursor no final da linha de comando
                super().keyPressEvent(event) # Permite a inserção de texto
                # self.moveCursor(self.textCursor().End) # Manter cursor no final (pode ser intrusivo)


        else:
            # Comportamento padrão para teclas quando o terminal não está editável ou processo não iniciado
            super().keyPressEvent(event)


    # Lidar com o fechamento do widget (terminar o processo do shell)
    def closeEvent(self, event):
        if self.process:
            try:
                self.process.terminate() # Tenta encerrar o processo gracefully
                self.process.wait(timeout=1) # Espera um pouco pelo encerramento
            except subprocess.TimeoutExpired:
                self.process.kill() # Se não encerrar, mata o processo
            except Exception as e:
                print(f"Erro ao encerrar processo do shell: {e}") # Imprime no console de depuração


        super().closeEvent(event)


# Exemplo básico de uso (para teste individual do widget)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Tentar detectar o shell apropriado
    shell_to_use = None
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        shell_to_use = "bash"
    elif sys.platform == 'win32':
        shell_to_use = "cmd.exe"
        # shell_to_use = "powershell.exe" # Opcional: tentar Powershell
    else:
        shell_to_use = "sh" # Fallback para sh

    terminal = CustomTerminalWidget(shell_program=shell_to_use)
    terminal.setWindowTitle("Terminal Básico")
    terminal.resize(600, 400)
    terminal.show()

    sys.exit(app.exec_())
