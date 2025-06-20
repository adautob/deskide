# No arquivo ai_chat_widget.py

import sys
import re # Importar o módulo re
import html # Importar o módulo html para escapar caracteres especiais
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal as Signal, QThread, QObject, pyqtSlot

# **Importar a biblioteca do Gemini**
import google.generativeai as genai

# Classe Worker para chamar a API do Gemini em uma thread separada
class GeminiWorker(QObject):
    # Sinais para comunicar com a thread principal
    finished = Signal() # Sinal emitido quando a tarefa termina
    response_ready = Signal(str) # Sinal emitido quando a resposta da IA está pronta
    error = Signal(str) # Sinal emitido em caso de erro

    def __init__(self, chat_session, user_message):
        super().__init__()
        self.chat_session = chat_session
        self.user_message = user_message

    @pyqtSlot() # Decorador para indicar que este método é um slot (será chamado na thread)
    def run(self):
        """Executa a chamada para a API do Gemini."""
        try:
            print(f"Worker: Enviando mensagem para a API: {self.user_message}") # Debug print
            # Enviar a mensagem do usuário para a sessão de chat do Gemini
            response = self.chat_session.send_message(self.user_message)
            print(f"Worker: Resposta da API recebida: {response}") # Debug print

            # Extrair o texto da resposta
            ai_text = ""
            try:
                # Tenta obter o texto diretamente. Lida com ContentEmpty ou outros erros.
                if response and hasattr(response, 'text'):
                    ai_text = response.text
                else:
                     ai_text = f"Resposta da IA não contém texto (ou está vazia): {response}"

            except Exception as e:
                ai_text = f"Erro ao extrair texto da resposta da IA: {e}\nResposta completa: {response}"


            print(f"Worker: Texto da IA extraído: {ai_text}") # Debug print
            self.response_ready.emit(ai_text) # Emite o sinal com a resposta

        except Exception as e:
            print(f"Worker: Erro na chamada da API: {e}") # Debug print
            self.error.emit(f"Erro na comunicação com a IA: {e}") # Emite o sinal de erro

        finally:
            print("Worker: Tarefa finalizada.") # Debug print
            self.finished.emit() # Emite o sinal de finalização


class AIChatWidget(QWidget):
    thinking_status = Signal(bool)

    def __init__(self, parent=None, api_key=None):
        super().__init__(parent)

        # **Configurar a API do Gemini (precisa da chave)**
        self.api_key = api_key
        self.model = None
        self.chat_session = None # A sessão de chat do Gemini

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Inicializar o modelo de conversação (chat)
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest') # Use o modelo apropriado
                self.chat_session = self.model.start_chat(history=[]) # Iniciar uma nova sessão de chat com histórico vazio
                print("API do Gemini configurada e sessão de chat iniciada.") # Debug print
            except Exception as e:
                print(f"Erro ao configurar a API do Gemini ou iniciar sessão de chat: {e}")
                self.append_message("Sistema", f"Erro ao configurar a API do Gemini: {e}. O chat de IA não estará funcional.")
                self.api_key = None # Invalidar a chave se a configuração falhar
        else:
            print("Chave de API do Gemini não fornecida. O chat de IA não estará funcional.")
            self.append_message("Sistema", "Chave de API do Gemini não fornecida. O chat de IA não estará funcional.")

        # **Compilar a expressão regular para blocos de código e armazenar como variável de instância**
        self.code_block_pattern = re.compile(r'(?:\w+)?\n(.*?)\n', re.DOTALL)

        self.initUI()
        self.thinking_status.connect(self.update_send_button_status)

        # Conectar o sinal finished do worker ao slot handle_api_task_finished (precisa ser conectado DEPOIS que o worker for criado)
        # Esta conexão agora é feita dentro de send_message


    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        main_layout.addWidget(self.history_display)

        input_layout = QHBoxLayout()
        main_layout.addLayout(input_layout)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Digite sua mensagem para a IA aqui...")
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        self.append_message("IA", "Olá! Como posso ajudar com seu código hoje?")

    # **Método append_message modificado para formatar blocos de código**
    def append_message(self, sender, message):
        formatted_message = f"<b>{sender}:</b> "

        # Processar a mensagem para formatar blocos de código
        code_block_pattern = re.compile(r'(?:\w+)?\n(.*?)\n', re.DOTALL)
        # Usar a variável de instância para a expressão regular
        last_end = 0
        parts = []

        for match in self.code_block_pattern.finditer(message): # <-- Usar self.code_block_pattern
            start, end = match.span()
            #code_block_full_match = match.group(1) # Não usado diretamente na versão refinada
            code_content = match.group(2) # O conteúdo dentro do bloco de código (grupo 1 na regex refinada)


            # Adicionar texto antes do bloco de código (como HTML normal)
            text_before_code = message[last_end:start]
            # Substituir quebras de linha por <br> para garantir quebras de linha no HTML
            parts.append(text_before_code.replace('\n', '<br>'))


            # Adicionar o bloco de código formatado (usando tags HTML básicas para fonte monoespaçada e pré-formatado)
            # Escapar caracteres HTML especiais dentro do código (como <, >, &)
            import html
            escaped_code_content = html.escape(code_content)

            # Usar <pre> e <code> para pré-formatar e garantir fonte monoespaçada
            # Estilo para fundo claro e padding
            formatted_code = f"<pre><code style='font-family: \"Courier New\", Consolas, monospace; background-color: #f4f4f4; padding: 5px;'>{escaped_code_content}</code></pre>"
            parts.append(formatted_code)

            last_end = end # Atualizar o final da última correspondência

        # Adicionar qualquer texto após o último bloco de código
        text_after_code = message[last_end:]
        # Substituir quebras de linha por <br> para garantir quebras de linha no HTML
        parts.append(text_after_code.replace('\n', '<br>'))


        # Combinar todas as partes
        content_html = "".join(parts)

        # **Debug print para inspecionar o HTML gerado**
        print(f"HTML gerado para mensagem de {sender}: {formatted_message + content_html + '<br>'}")

        # Adicionar a mensagem formatada ao histórico (combinando remetente e conteúdo)
        self.history_display.append(formatted_message + content_html + "<br>") # Adiciona a mensagem completa
        self.history_display.ensureCursorVisible()


    def send_message(self):
        if not self.chat_session:
             self.append_message("Sistema", "Sessão de chat da IA não iniciada. Verifique sua chave de API.")
             return

        user_text = self.user_input.text().strip()
        if user_text:
            self.append_message("Você", user_text)
            self.user_input.clear()
            self.user_input.setDisabled(True)
            self.send_button.setDisabled(True)
            self.thinking_status.emit(True)

            # **Criar Worker e Thread para chamar a API**
            self.thread = QThread()
            self.worker = GeminiWorker(self.chat_session, user_text)
            self.worker.moveToThread(self.thread)

            # Conectar sinais do worker e da thread
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            # Conectar o sinal finished do worker ao slot handle_api_task_finished para reabilitar a UI
            self.worker.finished.connect(self.handle_api_task_finished)


            # Conectar sinais de resposta/erro do worker aos slots no widget principal
            self.worker.response_ready.connect(self.receive_ai_response)
            self.worker.error.connect(self.handle_ai_error)

            self.thread.start()

            print(f"Mensagem do usuário enviada para processamento da API (via Worker).")


    @pyqtSlot(str)
    def receive_ai_response(self, ai_text):
        print(f"Recebendo resposta da IA: {ai_text}")
        # append_message agora lida com a formatação
        self.append_message("IA", ai_text)
        # Reabilitação da UI agora é agendada em handle_api_task_finished


    @pyqtSlot(str)
    def handle_ai_error(self, error_message):
        print(f"Erro da API da IA: {error_message}")
        self.append_message("Sistema", f"Erro na comunicação com a IA: {error_message}")
        # Reabilitação da UI agora é agendada em handle_api_task_finished


    @pyqtSlot()
    def handle_api_task_finished(self):
        print("--> Início handle_api_task_finished")
        try:
            print("Agendando reabilitação da UI com QTimer.singleShot(0).")
            # **Agendar a reabilitação da UI na próxima iteração do loop de eventos**
            QTimer.singleShot(0, self._re_enable_ui)

        except Exception as e:
            print(f"Erro durante agendamento da reabilitação da UI: {e}")
        print("<-- Fim handle_api_task_finished")


    @pyqtSlot() # Novo slot para a reabilitação da UI agendada
    def _re_enable_ui(self):
         print("--> Início _re_enable_ui")
         try:
             print("Executando reabilitação da UI: user_input e send_button.")
             self.user_input.setDisabled(False)
             self.send_button.setDisabled(False)
             self.user_input.setFocus()
             self.thinking_status.emit(False)
             print("UI reabilitada com sucesso em _re_enable_ui.")
         except Exception as e:
             print(f"Erro durante execução da reabilitação da UI em _re_enable_ui: {e}")
         print("<-- Fim _re_enable_ui")


    @pyqtSlot(bool)
    def update_send_button_status(self, thinking):
        if thinking:
            self.send_button.setText("Pensando...")
            self.send_button.setDisabled(True)
            self.user_input.setDisabled(True)
        else:
            self.send_button.setText("Enviar")
            self.send_button.setDisabled(False)
            self.user_input.setDisabled(False)
            # self.user_input.setFocus() # Não definir foco aqui, pois pode interferir com outras ações


# Exemplo básico de uso (para teste individual do widget)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Substitua "SUA_CHAVE_DE_API" pela sua chave real para teste individual
    # Gerencie sua chave de API de forma segura (variáveis de ambiente, arquivo de configuração)
    # NUNCA inclua sua chave diretamente no código fonte compartilhado.
    # Exemplo: ler de uma variável de ambiente
    # import os
    # api_key = os.environ.get("GEMINI_API_KEY")
    api_key = "AIzaSyBZl62T-QP2U8aVtvcWY5k8Y2Dv4veeZeQ" # Substitua ou use o método seguro

    chat_widget = AIChatWidget(api_key=api_key)
    chat_widget.setWindowTitle("Chat de IA Básico com Gemini")
    chat_widget.resize(400, 600)
    chat_widget.show()
    sys.exit(app.exec_())