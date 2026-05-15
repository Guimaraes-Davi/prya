from flask import Blueprint, Response, jsonify, render_template, request, stream_with_context
from .memoria import adicionar_mensagem, limpar_historico, obter_historico
from .ollama import chamar_ollama_stream

rotas = Blueprint("rotas", __name__)


@rotas.get("/")
def index():
    return render_template("index.html")


@rotas.post("/chat")
def chat():
    """Recebe a mensagem do usuário e devolve a resposta via Server-Sent Events."""
    dados = request.get_json(silent=True)
    if not dados or not dados.get("mensagem", "").strip():
        return jsonify({"erro": "Mensagem vazia."}), 400

    mensagem_usuario = dados["mensagem"].strip()
    adicionar_mensagem("user", mensagem_usuario)

    historico = obter_historico()

    def gerar():
        resposta_acumulada = []
        for trecho in chamar_ollama_stream(historico):
            resposta_acumulada.append(trecho)
            # Newlines no conteúdo quebrariam o protocolo SSE — escapamos aqui
            trecho_seguro = trecho.replace("\n", "\\n")
            yield f"data: {trecho_seguro}\n\n"

        # Salva a resposta completa no histórico após o streaming terminar
        adicionar_mensagem("assistant", "".join(resposta_acumulada))
        yield "data: [FIM]\n\n"

    return Response(
        stream_with_context(gerar()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@rotas.post("/limpar")
def limpar():
    """Apaga o histórico em memória e em disco."""
    limpar_historico()
    return jsonify({"status": "ok"})


@rotas.get("/historico")
def historico():
    """Retorna o histórico atual (útil para debug)."""
    return jsonify(obter_historico())


@rotas.get("/status")
def status():
    """Informa se há arquivos indexáveis em dados/ e se o ChromaDB já foi populado."""
    from .contexto import contexto_disponivel, listar_arquivos_dados
    arquivos = listar_arquivos_dados()
    return jsonify({
        "tem_arquivos": len(arquivos) > 0,
        "arquivos": arquivos,
        "indexado": contexto_disponivel(),
    })


@rotas.post("/indexar")
def indexar():
    """Dispara a indexação completa dos documentos de dados/."""
    from .contexto import indexar_dados, listar_arquivos_dados
    arquivos = listar_arquivos_dados()
    if not arquivos:
        return jsonify({"erro": "Nenhum arquivo .txt, .md ou .pdf encontrado em dados/."}), 400

    try:
        total_chunks = indexar_dados()
        return jsonify({
            "status": "ok",
            "chunks": total_chunks,
            "arquivos": len(arquivos),
        })
    except RuntimeError as e:
        # ChromaDB não instalado
        return jsonify({"erro": str(e)}), 503
    except Exception as e:
        return jsonify({"erro": f"Falha na indexação: {e}"}), 500