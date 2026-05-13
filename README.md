# Prya — Assistente Python Local

Assistente de código Python que roda 100% offline na sua máquina.
Powered by DeepSeek Coder V2 via Ollama.

## O que é

Prya é um assistente de código privado e local. Nenhum dado sai da sua máquina.
Sem API keys, sem custos, sem internet.

## Funcionalidades

- Geração de funções Python sob demanda
- Análise de código com detecção de bugs e sugestões de melhoria
- Memória de conversa — lembra o contexto da sessão atual
- Streaming em tempo real — resposta aparece sendo digitada
- Syntax highlight automático em blocos de código
- Botão copiar em cada bloco de código
- Interface web local dark mode

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com) instalado e rodando
- Modelo DeepSeek Coder V2 baixado

## Instalação

**1. Clone o repositório**
```bash
git clone https://github.com/Guimaraes-Davi/prya.git
cd prya
```

**2. Instale as dependências Python**
```bash
pip install flask requests
```

**3. Instale o Ollama e baixe o modelo**
```bash
# Instale o Ollama em https://ollama.com
ollama pull deepseek-coder-v2
```

**4. Inicie a Prya**
```bash
python run.py
```

Acessa `http://localhost:5000` no navegador.

## Como usar

**Gerar código:**

Escreva uma função Python que lê um CSV e retorna uma lista de dicionários

**Analisar bugs:**

Analise esse código e me diga o que está errado:
[cole seu código aqui]

**Contexto persistente:**
A Prya lembra o que você disse antes na mesma sessão.
Você pode pedir adaptações sem repetir o contexto:

Agora adapte essa função para aceitar também arquivos YAML

## Arquitetura

Você digita
↓
Flask recebe a mensagem
↓
Histórico de conversa é montado (janela de 20 mensagens)
↓
Ollama API processa com DeepSeek Coder V2
↓
Resposta chega em streaming
↓
Interface renderiza em tempo real com syntax highlight

## Roadmap

- [x] V1 — Chat com memória e análise de código
- [ ] V2 — RAG com documentação local (pasta `dados/`)
- [ ] V3 — Modo editor com análise de arquivo ao vivo

## Observações

- Prya roda exclusivamente local — não há deploy online por design
- A pasta `dados/` é ignorada pelo Git — use para documentação privada
- Memória de conversa é volátil — reiniciar o servidor limpa o histórico (V2 vai persistir)
- Velocidade depende do hardware — sem GPU dedicada espere 2-5s por resposta

## Uso e Distribuição

Prya é uma ferramenta de uso privado e exclusivo. O repositório está público para fins de portfólio e demonstração técnica, mas não foi projetado para uso facilitado por terceiros.

Para rodar localmente é necessário:
- Instalar e configurar o Ollama manualmente
- Baixar o modelo DeepSeek Coder V2 (~9GB)
- Configurar a pasta `dados/` com contexto próprio

Sem esses passos, a aplicação não opera de forma útil.

## Autor

Davi Guimarães