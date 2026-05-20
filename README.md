# Prya — Assistente Python Local

Assistente de código Python que roda 100% offline na sua máquina.
Powered by DeepSeek Coder V2 via Ollama.

## Status

**V2 — congelada.** O projeto está funcional e estável. O desenvolvimento ativo continua na V3 (CLI agentic), que está em pausa enquanto outros projetos do portfólio avançam.

## O que é

Prya é um assistente de código privado e local. Nenhum dado sai da sua máquina.
Sem API keys, sem custos, sem internet.

## Funcionalidades

- Chat com memória persistente entre sessões (salva em JSON)
- RAG com ChromaDB — indexa documentação local e injeta contexto nas respostas
- Geração e análise de código Python
- Streaming em tempo real
- Syntax highlight com botão copiar
- Interface web dark mode
- Rota `/indexar` para indexar arquivos da pasta `dados/`
- Rota `/status` para verificar estado da indexação

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python / Flask |
| LLM | Ollama — DeepSeek Coder V2 (15.7B Q4_0) |
| RAG | ChromaDB 1.5+ |
| Embeddings | nomic-embed-text via Ollama API |
| Interface | HTML / CSS / JavaScript |

## Requisitos

- Python 3.10+
- Ollama instalado e rodando
- Modelos baixados: `deepseek-coder-v2` e `nomic-embed-text`
- GPU com VRAM suficiente ou CPU (veja observações abaixo)

## Instalação

```bash
git clone https://github.com/Guimaraes-Davi/prya.git
cd prya
pip install flask requests chromadb
```

## Configuração de hardware

O DeepSeek Coder V2 ocupa ~9.2GB. Com ChromaDB rodando junto, máquinas com
menos de 16GB de RAM precisam forçar CPU para evitar estouro de memória:

```powershell
# PowerShell — antes de iniciar o Ollama
$env:CUDA_VISIBLE_DEVICES="-1"
ollama serve
```

Se sua GPU tiver VRAM suficiente (12GB+), omita o passo acima.

## Como rodar

```bash
# Outro terminal — com Ollama já rodando
python run.py
```

Acessa `http://localhost:5000`.

## RAG — documentação local

Coloque arquivos `.txt`, `.md` ou `.pdf` na pasta `dados/` e indexe:

```bash
# Via curl ou Invoke-RestMethod no PowerShell
curl -X POST http://localhost:5000/indexar
```

Verifique o status da indexação:

```
GET http://localhost:5000/status
```

Após indexar, a Prya usa os documentos como contexto nas respostas.

## Arquitetura

```
app/
├── __init__.py      ← factory Flask
├── ollama.py        ← chamada ao Ollama + injeção de contexto RAG
├── memoria.py       ← histórico com janela de 20 mensagens + persistência JSON
├── contexto.py      ← RAG com ChromaDB + embeddings via nomic-embed-text
└── routes.py        ← rotas Flask (/chat, /indexar, /status, /limpar)
```

## Roadmap

| Versão | Status | Descrição |
|--------|--------|-----------|
| V1.0 | ✅ | Chat com memória + streaming + syntax highlight |
| V1.1 | ✅ | Redesign minimalista — paleta neutra (#121212 / #94dd5f) |
| V2.0 | ✅ | RAG com ChromaDB + nomic-embed-text |
| V2.1 | ✅ | Persistência real do histórico entre reinicializações |
| V3.0 | ⏸ | CLI agentic multi-linguagem (projeto separado, em pausa) |

## Observações

- Prya roda exclusivamente local — sem deploy online por design
- A pasta `dados/` é ignorada pelo Git — use para documentação privada
- Velocidade varia com hardware: CPU espere 15-60s por resposta dependendo do modelo

## Autor

Davi Guimarães — [davi-guimaraes.com](https://davi-guimaraes.com)