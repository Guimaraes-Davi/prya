import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "deepseek-coder-v2"

SYSTEM_PROMPT = (
    "Você é o Prya, um assistente especializado em código Python. "
    "Responda SEMPRE em português do Brasil. "
    "Ao gerar código, adicione comentários em português. "
    "Seja direto, preciso e didático."
)


def chamar_ollama(historico: list[dict]) -> str:
    """Envia o histórico ao Ollama e retorna a resposta completa do modelo."""
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}] + historico

    payload = {
        "model": MODELO,
        "messages": mensagens,
        "stream": True,
    }

    resposta_completa = []

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
            r.raise_for_status()
            for linha in r.iter_lines():
                if not linha:
                    continue
                chunk = json.loads(linha)
                trecho = chunk.get("message", {}).get("content", "")
                if trecho:
                    resposta_completa.append(trecho)
                # Ollama sinaliza fim com done=True
                if chunk.get("done"):
                    break
    except requests.exceptions.ConnectionError:
        return "Erro: não foi possível conectar ao Ollama. Verifique se ele está rodando em localhost:11434."
    except requests.exceptions.Timeout:
        return "Erro: o modelo demorou demais para responder. Tente novamente."
    except Exception as e:
        return f"Erro inesperado ao chamar o Ollama: {e}"

    return "".join(resposta_completa)


def chamar_ollama_stream(historico: list[dict]):
    """Gerador que emite os chunks de texto à medida que o modelo os produz."""
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}] + historico

    payload = {
        "model": MODELO,
        "messages": mensagens,
        "stream": True,
    }

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
            r.raise_for_status()
            for linha in r.iter_lines():
                if not linha:
                    continue
                chunk = json.loads(linha)
                trecho = chunk.get("message", {}).get("content", "")
                if trecho:
                    yield trecho
                if chunk.get("done"):
                    break
    except requests.exceptions.ConnectionError:
        yield "Erro: Ollama não está acessível em localhost:11434."
    except Exception as e:
        yield f"Erro: {e}"
