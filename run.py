from app import criar_app

app = criar_app()

if __name__ == "__main__":
    # debug=True recarrega automaticamente ao salvar arquivos
    app.run(host="127.0.0.1", port=5000, debug=True)
