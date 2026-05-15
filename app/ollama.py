import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO     = "deepseek-coder-v2"

SYSTEM_PROMPT_BASE = (
    "Você é o Prya, um assistente especializado em código Python. "
    "Responda SEMPRE em português do Brasil. "
    "Ao gerar código, adicione comentários em português. "
    "Seja direto, preciso e didático."
)


def _montar_system_prompt(pergunta: str) -> str:
    """
    Monta o system prompt final.
    Se houver documentos indexados, busca chunks relevantes e os injeta.
    """
    try:
        from .contexto import buscar_contexto, contexto_disponivel
        if contexto_disponivel():
            chunks = buscar_contexto(pergunta, n=3)
            if chunks:
                contexto_texto = "\n\n---\n\n".join(chunks)
                return (
                    SYSTEM_PROMPT_BASE
                    + "\n\nUse OBRIGATORIAMENTE o contexto abaixo para responder. "
                    + "Se a resposta estiver no contexto, NUNCA invente alternativas.\n\n"
                    + "=== CONTEXTO ===\n"
                    + contexto_texto
                    + "\n=== FIM DO CONTEXTO ==="
                )
    except Exception:
        pass  # contexto indisponível não impede o chat

    return SYSTEM_PROMPT_BASE


def chamar_ollama(historico: list[dict]) -> str:
    """Envia o histórico ao Ollama e retorna a resposta completa."""
    pergunta = next(
        (m["content"] for m in reversed(historico) if m["role"] == "user"), ""
    )
    mensagens = [{"role": "system", "content": _montar_system_prompt(pergunta)}] + historico

    payload = {"model": MODELO, "messages": mensagens, "stream": True}
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
    pergunta = next(
        (m["content"] for m in reversed(historico) if m["role"] == "user"), ""
    )
    mensagens = [{"role": "system", "content": _montar_system_prompt(pergunta)}] + historico

    payload = {"model": MODELO, "messages": mensagens, "stream": True}

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
            if not r.ok:
                try:
                    corpo = r.json()
                    msg_erro = corpo.get("error", r.text)
                except Exception:
                    msg_erro = r.text or f"HTTP {r.status_code}"
                yield f"Erro do Ollama: {msg_erro}"
                return
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