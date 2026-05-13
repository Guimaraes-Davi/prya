TAMANHO_JANELA = 20  # número máximo de mensagens mantidas (pares usuário + assistente)

# Histórico global da sessão — lista de dicts {role, content}
_historico: list[dict] = []


def adicionar_mensagem(role: str, content: str) -> None:
    """Adiciona uma mensagem ao histórico e aplica a janela deslizante."""
    _historico.append({"role": role, "content": content})

    # Descarta as mensagens mais antigas quando ultrapassa o limite
    if len(_historico) > TAMANHO_JANELA:
        excesso = len(_historico) - TAMANHO_JANELA
        del _historico[:excesso]


def obter_historico() -> list[dict]:
    """Retorna uma cópia do histórico atual."""
    return list(_historico)


def limpar_historico() -> None:
    """Apaga todo o histórico (novo chat)."""
    _historico.clear()
