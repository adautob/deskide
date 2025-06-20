# No arquivo ai_chat_widget.py

import sys
import re
import html
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal as Signal, QThread, QObject, pyqtSlot

# **Importar QWebEngineView**
from PyQt5.QtWebEngineWidgets import QWebEngineView
# **Importar a biblioteca markdown**
import markdown

# Importar a biblioteca do Gemini e protos
import google.generativeai as genai
import google.generativeai.protos as genai_protos


# Classe Worker para chamar a API do Gemini em uma thread separada
class GeminiWorker(QObject):
    # ... (código da classe GeminiWorker) ...


    class AIChatWidget(QWidget):
    thinking_status = Signal(bool)

    def __init__(self, parent=None, api_key=None):
        super().__init__(parent)

        # **Configurar a API do Gemini**
        self.api_key = api_key
        self.model = None
        self.chat_session = None # A sessão de chat do Gemini

        # **Histórico da conversa em texto simples**
        self.conversation_history = [] # Lista de dicionários: [{'sender': 'IA', 'text': 'Olá! ...'}, ...]


        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
                self.chat_session = self.model.start_chat(history=[])
                print("API do Gemini configurada e sessão de chat iniciada.")
            except Exception as e:
                print(f"Erro ao configurar a API do Gemini ou iniciar sessão de chat: {e}")
                self.append_message_internal("Sistema", f"Erro ao configurar a API do Gemini: {e}. O chat de IA não estará funcional.")
                self.api_key = None
        else:
            print("Chave de API do Gemini não fornecida. O chat de IA não estará funcional.")
            self.append_message_internal("Sistema", "Chave de API do Gemini não fornecida. O chat de IA não estará funcional.")


        # A expressão regular para blocos de código não é mais necessária para a formatação aqui
        # self.code_delimiter_pattern = re.compile(r'(?:\w+)?\n.*?', re.DOTALL)
        # self.code_content_pattern = re.compile(r'(?:\w+)?\n(.*?)\n', re.DOTALL)


        self.initUI()
        self.thinking_status.connect(self.update_send_button_status)


    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # **Substituir QTextEdit por QWebEngineView**
        self.history_display = QWebEngineView()
        # self.history_display.setReadOnly(True) # QWebEngineView não tem setReadOnly direto assim
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

        # Adicionar uma mensagem inicial no histórico (usando o novo método interno)
        self.append_message_internal("IA", "Olá! Como posso ajudar com seu código hoje?")


    # Método interno para adicionar mensagens ao histórico em texto simples e atualizar o display
    def append_message_internal(self, sender, text):
        # Adiciona a mensagem ao histórico em texto simples
        self.conversation_history.append({'sender': sender, 'text': text})
        print(f"Mensagem adicionada ao histórico interno: {sender}: {text[:50]}...") # Debug print

        # **Atualizar o display (QWebEngineView) com o histórico completo**
        self.update_display()


    # Método para reconstruir e exibir o histórico no QWebEngineView
    def update_display(self):
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: sans-serif; margin: 10px; }
                .message { margin-bottom: 10px; padding: 8px; border-radius: 5px; }
                .user-message { background-color: #e0f2f7; text-align: right; }
                .ai-message { background-color: #f1f8e9; text-align: left; }
                .sender { font-weight: bold; margin-bottom: 5px; }
                pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; font-family: "Courier New", Consolas, monospace; }
                code { font-family: "Courier New", Consolas, monospace; }
            </style>
        </head>
        <body>
        """

        for message in self.conversation_history:
            sender = message['sender']
            text = message['text']

            # Convert Markdown text to HTML
            # Use fenced code blocks extension for markdown (like python\ncode)
            html_text = markdown.markdown(text, extensions=['fenced_code'])

            # Apply basic styling based on sender
            message_class = "user-message" if sender == "Você" else "ai-message"

            html_content += f"""
            <div class="message {message_class}">
                <div class="sender">{sender}:</div>
                <div class="text">{html_text}</div>
            </div>
            """

        html_content += "</body></html>"

        print("Atualizando QWebEngineView com HTML gerado.") # Debug print
        self.history_display.setHtml(html_content)


    # O método append_message original não é mais usado para adicionar ao display
    # Ele agora adiciona ao histórico interno e chama update_display
    def append_message(self, sender, message):
        # Este método agora apenas chama o método interno
        self.append_message_internal(sender, message)


    def send_message(self):
        if not self.chat_session:
             self.append_message("Sistema", "Sessão de chat da IA não iniciada. Verifique sua chave de API.")
             return

        user_text = self.user_input.text().strip()
        if user_text:
            self.append_message("Você", user_text) # Adiciona ao histórico interno e atualiza display
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
        # Adiciona a resposta ao histórico interno e atualiza o display
        self.append_message_internal("IA", ai_text)
        # Reabilitação da UI agora é agendada em handle_api_task_finished


    @pyqtSlot(str)
    def handle_ai_error(self, error_message):
        print(f"Erro da API da IA: {error_message}")
        self.append_message_internal("Sistema", f"Erro na comunicação com a IA: {error_message}")
        # Reabilitação da UI agora é agendada em handle_api_task_finished


    @pyqtSlot()
    def handle_api_task_finished(self):
        print("--> Início handle_api_task_finished")
        try:
            print("Agendando reabilitação da UI com QTimer.singleShot(0).")
            QTimer.singleShot(0, self._re_enable_ui)

        except Exception as e:
            print(f"Erro durante agendamento da reabilitação da UI: {e}")
        print("<-- Fim handle_api_task_finished")


    @pyqtSlot()
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


