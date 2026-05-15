"""
Módulo RAG — indexação e busca de contexto via ChromaDB.

Dependências necessárias:
    pip install chromadb pypdf
"""

import requests
from pathlib import Path

# ── Caminhos ──────────────────────────────────────────────────────────────────
RAIZ          = Path(__file__).parent.parent
PASTA_DADOS   = RAIZ / "dados"
PASTA_CHROMA  = RAIZ / "chroma_db"
NOME_COLECAO  = "prya_contexto"
EXTENSOES     = {".txt", ".md", ".pdf"}

# Modelo de embedding leve disponível no Ollama (não carrega RAM extra)
MODELO_EMBED  = "nomic-embed-text"
OLLAMA_EMBED  = "http://localhost:11434/api/embeddings"

# ── Carregamento opcional do ChromaDB ─────────────────────────────────────────
try:
    import chromadb
    _CHROMADB_OK = True
except ImportError:
    _CHROMADB_OK = False

_cliente = None  # inicializado na primeira chamada (lazy)


class _OllamaEmbedding:
    """
    Embedding function compatível com ChromaDB >= 0.6.

    O ChromaDB chama métodos diferentes dependendo do contexto:
      - __call__(input)        -> indexação via add()
      - embed_documents(input) -> indexação (interface alternativa)
      - embed_query(input)     -> busca via query() com query_texts
      - name()                 -> validação da coleção ao reabrir

    Todos os métodos usam keyword argument 'input' para compatibilidade
    com a interface interna do ChromaDB 0.6+.
    """

    @classmethod
    def name(cls) -> str:
        return "ollama-nomic-embed-text"

    def __call__(self, input: list) -> list:  # noqa: A002
        return self._gerar_embeddings(input)

    def embed_documents(self, input: list) -> list:  # noqa: A002
        """Chamado pelo ChromaDB na indexação (via add)."""
        return self._gerar_embeddings(input)

    def embed_query(self, input) -> list:  # noqa: A002
        """Chamado pelo ChromaDB na busca.
        ChromaDB 1.x passa lista; versões antigas passam string.
        """
        if isinstance(input, list):
            return self._gerar_embeddings(input)
        return self._gerar_embeddings([input])[0]

    def _gerar_embeddings(self, textos: list) -> list:
        """Gera vetores de embedding via Ollama API para cada texto."""
        vetores = []
        for texto in textos:
            resp = requests.post(
                OLLAMA_EMBED,
                json={"model": MODELO_EMBED, "prompt": texto},
                timeout=30,
            )
            resp.raise_for_status()
            vetores.append(resp.json()["embedding"])
        return vetores


def _obter_cliente():
    """Retorna o cliente ChromaDB, criando-o na primeira vez."""
    global _cliente
    if not _CHROMADB_OK:
        return None
    if _cliente is None:
        PASTA_CHROMA.mkdir(parents=True, exist_ok=True)
        _cliente = chromadb.PersistentClient(path=str(PASTA_CHROMA))
    return _cliente


def _obter_colecao():
    """
    Retorna (ou cria) a coleção de contextos, usando embeddings do Ollama.
    Se houver conflito de embedding function, apaga e recria.
    """
    cliente = _obter_cliente()
    if cliente is None:
        return None

    ef = _OllamaEmbedding()
    try:
        return cliente.get_or_create_collection(
            name=NOME_COLECAO,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception:
        try:
            cliente.delete_collection(NOME_COLECAO)
        except Exception:
            pass
        return cliente.get_or_create_collection(
            name=NOME_COLECAO,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )


# ── Leitura de arquivos ────────────────────────────────────────────────────────

def _ler_pdf(caminho: Path) -> str:
    """Extrai texto de um PDF usando pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(caminho))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        return ""
    except Exception:
        return ""


def _ler_arquivo(caminho: Path) -> str:
    """Lê o conteúdo de um arquivo de texto ou PDF."""
    if caminho.suffix.lower() == ".pdf":
        return _ler_pdf(caminho)
    return caminho.read_text(encoding="utf-8", errors="ignore")


# ── Chunking ──────────────────────────────────────────────────────────────────

def _dividir_em_chunks(texto: str, tamanho: int = 500, sobreposicao: int = 50) -> list:
    """Divide o texto em chunks com sobreposição para o RAG."""
    chunks = []
    inicio = 0
    passo = tamanho - sobreposicao
    while inicio < len(texto):
        chunk = texto[inicio : inicio + tamanho].strip()
        if chunk:
            chunks.append(chunk)
        inicio += passo
    return chunks


# ── API pública ────────────────────────────────────────────────────────────────

def indexar_dados() -> int:
    """
    Lê todos os .txt, .md e .pdf de dados/, divide em chunks e salva no ChromaDB.
    Retorna o total de chunks indexados.
    Apaga e recria a coleção a cada chamada (reindexação completa).
    """
    cliente = _obter_cliente()
    if cliente is None:
        raise RuntimeError("ChromaDB não está instalado. Execute: pip install chromadb")

    try:
        cliente.delete_collection(NOME_COLECAO)
    except Exception:
        pass

    colecao = cliente.get_or_create_collection(
        name=NOME_COLECAO,
        embedding_function=_OllamaEmbedding(),
        metadata={"hnsw:space": "cosine"},
    )

    documentos, ids, metadados = [], [], []

    if not PASTA_DADOS.exists():
        return 0

    for arquivo in sorted(PASTA_DADOS.iterdir()):
        if not arquivo.is_file():
            continue
        if arquivo.suffix.lower() not in EXTENSOES:
            continue

        try:
            texto = _ler_arquivo(arquivo)
        except Exception:
            continue

        if not texto.strip():
            continue

        chunks = _dividir_em_chunks(texto)
        for i, chunk in enumerate(chunks):
            documentos.append(chunk)
            ids.append(f"{arquivo.name}__{i}")
            metadados.append({"fonte": arquivo.name, "indice": i})

    if documentos:
        LOTE = 500
        for offset in range(0, len(documentos), LOTE):
            colecao.add(
                documents=documentos[offset : offset + LOTE],
                ids=ids[offset : offset + LOTE],
                metadatas=metadados[offset : offset + LOTE],
            )

    return len(documentos)


def buscar_contexto(pergunta: str, n: int = 3) -> list:
    """
    Busca os N chunks mais relevantes para a pergunta.
    Retorna lista vazia se não há documentos indexados ou ChromaDB indisponível.
    """
    colecao = _obter_colecao()
    if colecao is None:
        return []

    total = colecao.count()
    if total == 0:
        return []

    resultado = colecao.query(
        query_texts=[pergunta],
        n_results=min(n, total),
    )

    return resultado.get("documents", [[]])[0]


def contexto_disponivel() -> bool:
    """
    Retorna True se há documentos indexados na coleção.
    Função módulo-nível — chamada diretamente por routes.py e ollama.py.
    """
    try:
        colecao = _obter_colecao()
        if colecao is None:
            print("[CONTEXTO] ChromaDB indisponível")
            return False
        count = colecao.count()
        print(f"[CONTEXTO] Collection count: {count}")
        return count > 0
    except Exception as e:
        print(f"[CONTEXTO] Erro: {e}")
        return False


def listar_arquivos_dados() -> list:
    """Retorna os nomes dos arquivos indexáveis presentes em dados/."""
    if not PASTA_DADOS.exists():
        return []
    return [
        f.name for f in sorted(PASTA_DADOS.iterdir())
        if f.is_file() and f.suffix.lower() in EXTENSOES
    ]