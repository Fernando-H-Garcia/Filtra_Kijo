# gui_qt/manual.py — Manual Qt (QDialog + QTextBrowser) v4.3.0
import os
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QTextBrowser, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont
from core.config import VERSION

def _resource_path(relative_path: str) -> str:
    try:
        base = sys._MEIPASS  # type: ignore
    except Exception:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, relative_path)

def _html_header(title: str) -> str:
    return f'<h1 style="color:#4F46E5; font-size:26px; margin-bottom:10px;">{title}</h1>'

def _h2(text: str) -> str:
    return f'<h2 style="color:#111827; font-size:18px; margin-top:22px; margin-bottom:8px;">{text}</h2>'

def _h3(text: str) -> str:
    return f'<h3 style="color:#4338CA; font-size:14px; margin-top:14px; margin-bottom:6px;">{text}</h3>'

def _p(text: str) -> str:
    return f'<p style="color:#1F2937; font-size:12px; line-height:1.6; margin:6px 0;">{text}</p>'

def _bullet(text: str) -> str:
    return f'<p style="color:#1F2937; font-size:12px; margin:4px 0 4px 18px;">&#8226; {text}</p>'

def _ex(text: str) -> str:
    return f'<div style="background:#ECFDF5; border-left:3px solid #10B981; padding:6px 10px; margin:6px 0; font-family:Consolas, monospace; font-size:11px; color:#065F46;">{text}</div>'

def _notice(text: str) -> str:
    return f'<p style="color:#4F46E5; font-size:12px; font-weight:bold; margin:8px 0;">{text}</p>'

def _sep() -> str:
    return '<hr style="border:none; border-top:1px solid #E5E7EB; margin:16px 0;" />'

def _build_sections():
    v = VERSION
    sections = {}
    sections["🚀 Início Rápido"] = (
        _html_header(f"🚀 Bem-vindo ao Filtra KIJO V{v}") +
        _p("O Filtra KIJO serve para filtrar dados dentro de arquivos KIJO (GPRS). Imagine que você tem um arquivo com milhares de linhas e precisa encontrar apenas as linhas onde uma determinada coluna tem um valor específico — é exatamente isso que este programa faz.") +
        _sep() + _h2("Como funciona em 4 passos:") +
        _bullet('1&#65039;&#8419; <b>ABRIR</b> — Clique no botão "📂 Abrir Arquivo" (canto superior direito) e selecione um ou mais arquivos .txt do KIJO.') +
        _bullet('2&#65039;&#8419; <b>FILTRAR</b> — Crie uma regra clicando em "+ Nova Regra". Defina a posição (coluna), o operador e o valor desejado.') +
        _bullet('3&#65039;&#8419; <b>PROCESSAR</b> — Clique em "⚡ Iniciar Processamento", escolha o formato (TXT ou CSV) e a pasta de destino.') +
        _bullet('4&#65039;&#8419; <b>RESULTADO</b> — O programa gera um novo arquivo contendo somente as linhas que passaram no filtro.') +
        _sep() + _h2("Exemplo prático:") +
        _p("Suponha que você quer encontrar todas as linhas onde a coluna 5 tem o valor \"100\":") +
        _ex("→ Posição: 5<br>→ Operador: Igual a<br>→ Valor: 100") +
        _p("O programa vai ler todas as linhas do arquivo, verificar a coluna 5 de cada uma, e exportar apenas aquelas onde o valor é \"100\".")
    )
    sections["📂 Abrindo Arquivos"] = (
        _html_header("📂 Abrindo Arquivos") +
        _h2("Como selecionar arquivos:") +
        _bullet('1. Clique no botão "📂 Abrir Arquivo" no canto superior direito.') +
        _bullet('2. Na janela que abrir, navegue até a pasta dos seus arquivos KIJO.') +
        _bullet('3. Selecione um ou mais arquivos .txt (segure Ctrl para selecionar vários).') +
        _bullet('4. Clique em "Abrir".') +
        _p("Após selecionar, o programa mostrará no topo da tela quantos arquivos foram carregados (ex: \"✅ 15 arquivos selecionados\").") +
        _notice("💡 O programa lembra automaticamente a última pasta de onde você abriu e salvou arquivos. Ao reabrir o aplicativo, ele voltará direto para as mesmas pastas.") +
        _sep() + _h2("Como ver quais arquivos foram selecionados:") +
        _p("Passe o mouse sobre o texto \"✅ X arquivos selecionados\" no topo da tela. Um balão (tooltip) aparecerá mostrando o nome de cada arquivo.") +
        _notice("💡 Se a lista for longa, use a rodinha do mouse para rolar dentro do balão.") +
        _sep() + _h3("Posso processar vários arquivos de uma vez?") +
        _p("Sim! Quando você seleciona múltiplos arquivos, o programa processa todos eles em sequência e combina os resultados em um único arquivo de saída. Isso é útil quando seus dados estão divididos em vários arquivos.")
    )
    sections["🎯 Como Criar Filtros"] = (
        _html_header("🎯 Como Criar Filtros") +
        _h2("O que é um filtro?") +
        _p("Um filtro é uma regra que diz ao programa: \"quero apenas as linhas onde a coluna X tem o valor Y\". Você pode criar quantos filtros quiser.") +
        _sep() + _h2("Passo a passo para criar um filtro:") +
        _bullet('1. Clique em "+ Nova Regra" na área central da tela.') +
        _bullet('2. Um card (cartão) aparecerá com uma condição em branco.') +
        _bullet('3. Preencha os três campos:') +
        _ex("→ Posição: o número da coluna no KIJO (ex: 5)<br>→ Operador: escolha na lista (ex: \"Igual a\")<br>→ Valor: o que você quer buscar (ex: 100)") +
        _sep() + _h2("O que é \"Posição\"?") +
        _p("Cada linha do arquivo KIJO é dividida em colunas separadas por vírgula. A \"Posição\" é o número da coluna que você quer verificar.") +
        _h3("Exemplo de uma linha KIJO:") +
        _ex("KIJO71,ABC123,2024,01,15,100,200,DADOS,...<br>Pos:  1       2     3   4  5  6   7    8") +
        _p("Neste exemplo, se você quiser filtrar pelo valor \"100\", deve colocar Posição = 6, porque \"100\" está na 6ª coluna.") +
        _sep() + _h2("Adicionando várias condições ao mesmo filtro:") +
        _p("Dentro de cada card de regra, clique em \"+ Adicionar Condição\" para adicionar mais condições. Todas as condições dentro do mesmo card devem ser verdadeiras para a linha ser incluída (lógica E).") +
        _h3("Exemplo: buscar linhas onde a coluna 3 é \"2024\" E a coluna 6 é maior que 50:") +
        _ex("Condição 1 → Posição: 3 | Operador: Igual a     | Valor: 2024<br>Condição 2 → Posição: 6 | Operador: Maior que   | Valor: 50") +
        _sep() + _h2("Usando múltiplos filtros (lógica OU):") +
        _p("Se você criar mais de um card de regra (clicando em \"+ Nova Regra\" novamente), o programa exportará linhas que atendam a QUALQUER um dos filtros. Ou seja, entre filtros diferentes a lógica é OU.") +
        _h3("Exemplo:") +
        _ex("Filtro 1: Posição 5 → Igual a → 100<br>Filtro 2: Posição 5 → Igual a → 200<br>Resultado: exporta linhas onde coluna 5 é 100 OU 200.") +
        _sep() + _h2("Como remover uma condição ou filtro:") +
        _bullet("Para remover uma condição: clique no botão ✕ ao lado dela.") +
        _bullet("Para remover o filtro inteiro: clique no botão ✕ no canto superior direito do card.")
    )
    sections["⚙️ Configurar Saída"] = (
        _html_header("⚙️ Configurando Colunas de Saída") +
        _p("Agora, você pode escolher exatamente quais colunas deseja exportar para cada filtro individualmente! Isso permite que regras diferentes no mesmo processamento gerem formatos de colunas totalmente diferentes.") +
        _sep() + _h2("Como funciona o fluxo de configuração:") +
        _bullet("1. Selecione os arquivos de entrada primeiro. A criação de regras ficará bloqueada até carregar pelo menos um arquivo.") +
        _bullet("2. Crie uma regra/filtro normalmente.") +
        _bullet("3. No cabeçalho do card da regra, clique no botão \"⚙️ Configurar Saída\".") +
        _bullet("4. O sistema irá realizar uma busca super rápida (em segundo plano) pelos seus arquivos e encontrar a PRIMEIRA ocorrência que atenda a essa regra.") +
        _bullet("5. Uma janela pop-up será exibida com uma tabela listando cada coluna encontrada na linha e uma caixa de seleção (checkbox).") +
        _bullet("6. Conforme você seleciona ou desmarca as caixas de colunas, uma PRÉVIA em tempo real no final da janela mostra exatamente como a linha ficará salva no arquivo final!") +
        _sep() + _h2("Vantagens:") +
        _bullet("Economia de espaço e clareza: Remova campos irrelevantes que só poluem sua planilha ou TXT.") +
        _bullet("Formatação sob medida: O Filtro A pode exportar as colunas 1, 2 e 5; enquanto o Filtro B no mesmo processamento pode exportar 1, 3 e 4. Suas sequências originais e integridade dos dados são mantidas.")
    )
    sections["🔎 Operadores (Detalhado)"] = (
        _html_header("🔎 Operadores — Guia Detalhado") +
        _p("Ao criar uma condição, você escolhe um operador na lista suspensa. Abaixo está a explicação de cada um com exemplos práticos.") +
        _sep() + _h2("\"Igual a\"") + _p("Seleciona linhas onde o valor da coluna é exatamente igual ao que você digitou.") +
        _h3("Exemplo: Posição 3 | Igual a | 2024") +
        _ex("Linha: KIJO71,ABC,2024,01  →  coluna 3 = \"2024\"  ✅ Incluída<br>Linha: KIJO1B,ABC,2023,01  →  coluna 3 = \"2023\"  ❌ Excluída<br>Linha: KIJO1D,ABC,2024X,01 →  coluna 3 = \"2024X\" ❌ Excluída") +
        _notice("💡 Funciona tanto com números quanto com textos. A comparação é exata (\"2024\" não é igual a \"2024X\").") +
        _sep() + _h2("\"Diferente de\"") + _p("Seleciona linhas onde o valor da coluna é qualquer coisa DIFERENTE do que você digitou.") +
        _h3("Exemplo: Posição 3 | Diferente de | 2023") +
        _ex("Linha com coluna 3 = \"2024\"  ✅ Incluída (é diferente de 2023)<br>Linha com coluna 3 = \"2023\"  ❌ Excluída (é igual a 2023)") +
        _sep() + _h2("\"Maior que\"") + _p("Seleciona linhas onde o valor numérico da coluna é MAIOR que o informado.") +
        _h3("Exemplo: Posição 6 | Maior que | 50") +
        _ex("Coluna 6 = 100   ✅ Incluída (100 > 50)<br>Coluna 6 = 50    ❌ Excluída (50 não é maior que 50)<br>Coluna 6 = 30    ❌ Excluída (30 < 50)") +
        _p('<span style="color:#B45309; font-weight:bold;">⚠️ Funciona apenas com valores numéricos. Se a coluna contiver texto, a linha será ignorada.</span>') +
        _sep() + _h2("\"Menor que\"") + _p("Seleciona linhas onde o valor numérico da coluna é MENOR que o informado.") +
        _h3("Exemplo: Posição 6 | Menor que | 200") +
        _ex("Coluna 6 = 100   ✅ Incluída (100 < 200)<br>Coluna 6 = 200   ❌ Excluída (200 não é menor que 200)<br>Coluna 6 = 300   ❌ Excluída (300 > 200)") +
        _sep() + _h2("\"Maior ou igual a\"") + _p("Seleciona linhas onde o valor numérico é MAIOR OU IGUAL ao informado.") +
        _h3("Exemplo: Posição 6 | Maior ou igual a | 50") +
        _ex("Coluna 6 = 100   ✅ Incluída (100 >= 50)<br>Coluna 6 = 50    ✅ Incluída (50 >= 50)<br>Coluna 6 = 30    ❌ Excluída (30 < 50)") +
        _sep() + _h2("\"Menor ou igual a\"") + _p("Seleciona linhas onde o valor numérico é MENOR OU IGUAL ao informado.") +
        _h3("Exemplo: Posição 6 | Menor ou igual a | 200") +
        _ex("Coluna 6 = 100   ✅ Incluída (100 <= 200)<br>Coluna 6 = 200   ✅ Incluída (200 <= 200)<br>Coluna 6 = 300   ❌ Excluída (300 > 200)") +
        _sep() + _h2("\"Contém\"") + _p("Seleciona linhas onde o valor da coluna contém o texto informado em qualquer parte (não precisa ser exato).") +
        _h3("Exemplo: Posição 2 | Contém | ABC") +
        _ex("Coluna 2 = \"ABC123\"    ✅ Incluída (contém \"ABC\")<br>Coluna 2 = \"XYZABC99\"  ✅ Incluída (contém \"ABC\")<br>Coluna 2 = \"XYZ999\"    ❌ Excluída (não contém \"ABC\")") +
        _notice("💡 Útil quando você quer buscar por parte de um código ou nome.") +
        _sep() + _h2("Buscar por valores vazios:") +
        _p("Se você quiser encontrar linhas onde uma coluna está VAZIA, use o operador \"Igual a\" e deixe o campo Valor em branco.") +
        _ex("Posição: 8 | Operador: Igual a | Valor: (vazio)") +
        _p('<span style="color:#B45309; font-weight:bold;">⚠️ Se a linha não possuir a coluna informada (ex: filtrar coluna 8 mas a linha só tem 7 colunas), essa linha será automaticamente excluída do resultado.</span>')
    )
    sections["💾 Salvando Regras"] = (
        _html_header("💾 Salvando e Reutilizando Regras") +
        _p("Se você usa os mesmos filtros com frequência, pode salvá-los na Biblioteca de Regras para não precisar recriá-los toda vez.") +
        _sep() + _h2("Como salvar uma regra:") +
        _bullet("1. Crie uma regra e configure todas as condições desejadas.") +
        _bullet("2. No topo do card da regra, digite um nome descritivo (ex: \"Filtro Equipamento ABC\").") +
        _bullet("3. Clique no ícone de disquete 💾 dentro do card.") +
        _bullet("4. A regra será salva e aparecerá no painel \"📜 Regras Salvas\" à direita da tela.") +
        _sep() + _h2("Como usar uma regra salva:") +
        _p("Basta clicar no nome da regra no painel \"📜 Regras Salvas\" à direita. Um novo card será criado automaticamente na área central, já preenchido com todas as condições que foram salvas.") +
        _notice("💡 Você pode usar uma regra salva e ainda modificá-la antes de processar. As alterações só serão salvas se você clicar no 💾 novamente.") +
        _sep() + _h2("Como excluir uma regra salva:") +
        _p("No painel \"📜 Regras Salvas\", passe o mouse sobre a regra e clique no ícone de lixeira 🗑 à direita do nome. Ou clique direito e escolha Excluir.") +
        _sep() + _h2("Onde as regras ficam armazenadas?") +
        _p("As regras são salvas automaticamente no arquivo \"filtros_salvos.json\" na mesma pasta do programa. Enquanto esse arquivo existir, suas regras estarão disponíveis mesmo após fechar e reabrir o programa.")
    )
    sections["📤 Exportando Resultados"] = (
        _html_header("📤 Exportando Resultados") +
        _p("Após configurar seus filtros, veja como exportar os resultados:") +
        _sep() + _h2("Passo a passo:") +
        _bullet("1. Clique no botão \"⚡ Iniciar Processamento\" na parte inferior da tela.") +
        _bullet("2. Uma janela aparecerá com as opções de saída.") +
        _ex("→ Campo de nome único: digite o nome desejado caso queira salvar tudo em um só arquivo.<br>→ Agrupamento Dinâmico: Se marcar a opção de 'Separar regras de filtro', a janela expande mostrando as regras em Grupos (Cartões). Você pode mover regras de um grupo para o outro e escolher o nome do arquivo de destino para cada grupo!") +
        _bullet("3. Escolha o formato:") +
        _ex("→ 📄 TXT (Original): mantém o formato original do KIJO.<br>→ 📊 CSV (Excel): gera um arquivo que abre direto no Excel.") +
        _bullet("4. Escolha a pasta onde o arquivo será salvo.") +
        _notice("💡 Se algum arquivo já existir na pasta, o programa avisará e pedirá confirmação antes de substituir.") +
        _bullet("5. O processamento começará e você verá:") +
        _ex("→ Um cronômetro mostrando o tempo decorrido.<br>→ Uma barra de progresso.<br>→ A contagem de linhas encontradas ao finalizar.") +
        _sep() + _h2("Qual formato escolher?") +
        _p("📄 TXT — Use quando quiser manter o formato original do KIJO, por exemplo para reimportar em outro sistema ou compartilhar com alguém que usa o mesmo programa.") +
        _p("📊 CSV — Use quando quiser abrir os dados no Excel para análise, criar gráficos ou tabelas dinâmicas. O CSV separa cada coluna automaticamente.") +
        _sep() + _h2("Dica de Performance:") +
        _p("O Filtra KIJO utiliza o motor Polars, que é extremamente rápido. Você pode processar arquivos de centenas de megabytes sem problemas. O processamento acontece em segundo plano, então a tela não trava.")
    )
    sections["🔍 Analisando Duplicadas"] = (
        _html_header("🔍 Analisando Duplicadas") +
        _p("Além da filtragem convencional, o programa agora possui uma ferramenta dedicada para identificar e extrair KIJOs duplicados. Isso é muito útil para limpar relatórios ou encontrar loops.") +
        _sep() + _h2("Como funciona a análise:") +
        _bullet("1. Selecione um ou mais arquivos KIJO.") +
        _bullet("2. Clique no botão laranja \"🔍 Analisar Duplicadas\" (não é necessário criar filtros).") +
        _bullet("3. Escolha a pasta onde o resultado será salvo.") +
        _bullet("4. O programa vai ler tudo e exportar APENAS as linhas onde o conteúdo do 'KIJO' é idêntico.") +
        _sep() + _h2("Como o arquivo final é organizado?") +
        _p("O arquivo de saída agrupa todas as duplicadas sequencialmente. Para ajudar na investigação, o programa insere o NOME do arquivo original no início da linha, permitindo que você rastreie de onde cada cópia veio. As datas, ips e horas originais são mantidas perfeitamente.") +
        _sep() + _h2("Uso de Memória RAM") +
        _p("A pesquisa de duplicadas é um processo intensivo e pode usar bastante memória RAM enquanto ocorre, pois memoriza todos os milhões de identificadores de KIJO na memória ao mesmo tempo. Mas não se preocupe: assim que o processamento for concluído, o sistema limpa à força essa memória e devolve o espaço integralmente para o Windows.")
    )
    sections["❓ Perguntas Frequentes"] = (
        _html_header("❓ Perguntas Frequentes") +
        _h2("O programa travou?") +
        _p("Provavelmente não! Durante o processamento de arquivos grandes, a tela pode parecer lenta, mas o processamento continua em segundo plano. Observe o cronômetro e a barra de progresso — se estiverem avançando, tudo está funcionando.") +
        _sep() + _h2("Posso processar mais de um arquivo ao mesmo tempo?") +
        _p("Sim! Selecione vários arquivos ao abrir (segure Ctrl e clique em cada um). O programa processará todos em sequência e combinará os resultados em um único arquivo de saída.") +
        _sep() + _h2("Minha coluna não existe na linha — o que acontece?") +
        _p("Se você filtrar pela coluna 8, mas uma linha do arquivo tem apenas 7 colunas, essa linha será automaticamente excluída do resultado. Isso é intencional: o programa só analisa dados que realmente existem.") +
        _sep() + _h2("Como sei qual é o número da Posição (coluna)?") +
        _p("Abra o arquivo .txt em um editor de texto (como o Bloco de Notas) e conte as colunas separadas por vírgula. A primeira coluna é a posição 1, a segunda é a posição 2, e assim por diante.") +
        _h3("Exemplo:") +
        _ex("KIJO1B,ABC123,2024,01,15,100<br>1=KIJO1B  2=ABC123  3=2024  4=01  5=15  6=100") +
        _sep() + _h2("Posso combinar vários operadores no mesmo filtro?") +
        _p("Sim! Cada card de regra pode ter múltiplas condições. Todas devem ser verdadeiras ao mesmo tempo (lógica E).") +
        _h3("Exemplo: buscar linhas onde coluna 3 = \"2024\" E coluna 6 > 50:") +
        _ex("Condição 1 → Posição: 3 | Igual a     | 2024<br>Condição 2 → Posição: 6 | Maior que   | 50") +
        _sep() + _h2("Qual a diferença entre múltiplas condições e múltiplos filtros?") +
        _bullet("Condições no MESMO card: a linha deve atender a TODAS (lógica E).") +
        _bullet("Cards DIFERENTES: a linha deve atender a PELO MENOS UM (lógica OU).") +
        _sep() + _h2("Minhas regras salvas desapareceram!") +
        _p("As regras ficam no arquivo \"filtros_salvos.json\" na pasta do programa. Se esse arquivo for apagado ou movido, as regras serão perdidas. Para fazer backup, copie esse arquivo para outro local.")
    )
    return sections

SECTIONS = _build_sections()
ORDER = [
    "🚀 Início Rápido",
    "📂 Abrindo Arquivos",
    "🎯 Como Criar Filtros",
    "⚙️ Configurar Saída",
    "🔎 Operadores (Detalhado)",
    "💾 Salvando Regras",
    "📤 Exportando Resultados",
    "🔍 Analisando Duplicadas",
    "❓ Perguntas Frequentes",
]

class ManualDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Guia do Usuário - Filtra KIJO V{VERSION}")
        self.resize(1100, 800)
        icon_path = _resource_path("fk_icon.ico")
        alt = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "fk_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        elif os.path.exists(alt):
            self.setWindowIcon(QIcon(alt))
        self.setModal(False)
        self._setup_ui()
        self._load_section(ORDER[0])

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left menu 260px #1F2937
        menu_frame = QFrame()
        menu_frame.setFixedWidth(260)
        menu_frame.setStyleSheet("QFrame { background-color: #1F2937; border: none; }")
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setContentsMargins(10, 20, 10, 20)
        menu_layout.setSpacing(2)

        title = QLabel("📖 MANUAL")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; background-color: transparent; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        menu_layout.addWidget(title)
        menu_layout.addSpacing(10)

        self._menu_buttons = {}
        for name in ORDER:
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #D1D5DB;
                    text-align: left;
                    padding: 10px 12px;
                    border: none;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #374151;
                    border-radius: 4px;
                }
            """)
            btn.clicked.connect(lambda checked=False, n=name: self._load_section(n))
            menu_layout.addWidget(btn)
            self._menu_buttons[name] = btn

        menu_layout.addStretch()
        main_layout.addWidget(menu_frame)

        # Right content
        self._browser = QTextBrowser()
        self._browser.setStyleSheet("""
            QTextBrowser {
                background-color: #FFFFFF;
                color: #1F2937;
                border: none;
                padding: 20px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
        """)
        self._browser.setOpenExternalLinks(False)
        main_layout.addWidget(self._browser, stretch=1)

    def _load_section(self, name: str):
        for n, btn in self._menu_buttons.items():
            if n == name:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4F46E5;
                        color: white;
                        text-align: left;
                        padding: 10px 12px;
                        border: none;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #4338CA;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #D1D5DB;
                        text-align: left;
                        padding: 10px 12px;
                        border: none;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #374151;
                        border-radius: 4px;
                    }
                """)
        html = SECTIONS.get(name, "<p>Seção não encontrada</p>")
        wrapped = f'<div style="padding:10px 20px;">{html}</div>'
        self._browser.setHtml(wrapped)
        self._browser.verticalScrollBar().setValue(0)

    def show_manual(self):
        self.show()
        self.raise_()
        self.activateWindow()
