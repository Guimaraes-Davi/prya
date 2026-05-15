import json
from pathlib import Path

# ── Configuração ───────────────────────────────────────────────────────────────
TAMANHO_JANELA    = 20   # máximo de mensagens (pares user + assistant)
RAIZ              = Path(__file__).parent.parent
ARQUIVO_HISTORICO = RAIZ / "dados" / "historico.json"


# ── Persistência ──────────────────────────────────────────────────────────────

def _carregar_historico() -> list[dict]:
    """Carrega o histórico do disco ao iniciar. Retorna lista vazia se não existir."""
    try:
        if ARQUIVO_HISTORICO.exists():
            dados = json.loads(ARQUIVO_HISTORICO.read_text(encoding="utf-8"))
            # Valida que é uma lista de dicts com role/content
            if isinstance(dados, list) and all(
                isinstance(m, dict) and "role" in m and "content" in m
                for m in dados
            ):
                return dados[-TAMANHO_JANELA:]
    except Exception:
        pass
    return []


def _salvar_historico() -> None:
    """Persiste o histórico atual em disco (best-effort)."""
    try:
        ARQUIVO_HISTORICO.parent.mkdir(parents=True, exist_ok=True)
        ARQUIVO_HISTORICO.write_text(
            json.dumps(_historico, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass  # falha silenciosa — nunca impede o chat de funcionar


# ── Estado em memória (carregado do disco na inicialização) ───────────────────
_historico: list[dict] = _carregar_historico()


# ── API pública ───────────────────────────────────────────────────────────────

def adicionar_mensagem(role: str, content: str) -> None:
    """Adiciona uma mensagem, aplica a janela deslizante e persiste."""
    _historico.append({"role": role, "content": content})

    # Descarta as mensagens mais antigas quando ultrapassa o limite
    if len(_historico) > TAMANHO_JANELA:
        excesso = len(_historico) - TAMANHO_JANELA
        del _historico[:excesso]

    _salvar_historico()


def obter_historico() -> list[dict]:
    """Retorna uma cópia do histórico atual."""
    return list(_historico)


def limpar_historico() -> None:
    """Apaga o histórico em memória e remove o arquivo persistido."""
    _historico.clear()
    try:
        if ARQUIVO_HISTORICO.exists():
            ARQUIVO_HISTORICO.unlink()
    except Exception:
        pass
