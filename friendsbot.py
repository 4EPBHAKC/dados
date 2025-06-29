import logging
import requests
import json
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import re

# === CONFIGURAÇÕES ===
TOKEN = '8174136874:AAFLzwNH_8MM6zcw-I227a1PimOU2PbKOzs'

RAW_URLS = [
    "https://raw.githubusercontent.com/4EPBHAKC/dados/refs/heads/main/dados.json",
    "",  # pode adicionar mais URLs
    ""
]

ARQUIVO_LOCAL = ""  # arquivo local para testes, deixe vazio se não usar

# === DESATIVANDO LOGS EXCESSIVOS ===
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("telegram.ext").setLevel(logging.CRITICAL)
logging.getLogger().setLevel(logging.ERROR)

# === FUNÇÕES ===

def carregar_base():
    base_total = []

    for url in RAW_URLS:
        if url.strip():
            try:
                resposta = requests.get(url, timeout=5)
                resposta.raise_for_status()
                base_total.extend(resposta.json())
            except Exception:
                pass  # Silencia erros de carregamento

    if ARQUIVO_LOCAL and os.path.exists(ARQUIVO_LOCAL):
        try:
            with open(ARQUIVO_LOCAL, "r", encoding="utf-8") as f:
                base_total.extend(json.load(f))
        except Exception:
            pass

    return base_total

def buscar_por_tipo(termo, tipo):
    base = carregar_base()
    termo = termo.lower()
    return [entry for entry in base if entry.get("type") == tipo and termo in entry.get("identifier", "").lower()]

def buscar_por_url(termo):
    base = carregar_base()
    termo = termo.lower()
    return [entry for entry in base if termo in entry.get("url", "").lower()]

def formatar_txt(resultados):
    linhas = []
    for r in resultados:
        linha = (
            f"🔑 Identificador: {r.get('identifier', '')}\n"
            f"🔐 Senha: {r.get('password', '')}\n"
            f"🌐 URL: {r.get('url', '')}\n"
        )
        linhas.append(linha)
    texto = "\n" + "\n".join(linhas)
    return BytesIO(texto.encode('utf-8'))

# Função para limpar e garantir nome válido para arquivo
def limpar_nome_arquivo(nome: str) -> str:
    # Permite letras, números, . _ - ; substitui o resto por _
    return re.sub(r'[^a-zA-Z0-9._-]', '_', nome)

# Handlers do bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🔍 Nossa API OSINT / BOT é poderosa, rápida e garante privacidade total.\n\n"
        "🧩 Principais Endpoints disponíveis:\n"
        "/email <email>\n"
        "/username <nome>\n"
        "/url <domínio>\n\n"
        "🔗 Consultando múltiplas fontes de dados."
    )
    await update.message.reply_text(msg)

async def executar_busca(update: Update, context: ContextTypes.DEFAULT_TYPE, tipo: str):
    if not context.args:
        await update.message.reply_text(f"❗ Forneça um {tipo} para buscar.")
        return
    termo = " ".join(context.args)
    resultados = buscar_por_tipo(termo, tipo)
    await responder_com_resultado(update, resultados, tipo, termo)

async def buscar_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await executar_busca(update, context, "email")

async def buscar_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await executar_busca(update, context, "username")

async def buscar_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Forneça um domínio ou URL.")
        return
    termo = " ".join(context.args)
    resultados = buscar_por_url(termo)
    await responder_com_resultado(update, resultados, "url", termo)

async def responder_com_resultado(update: Update, resultados, tipo, termo):
    if resultados:
        txt = formatar_txt(resultados)
        nome_arquivo_limpo = limpar_nome_arquivo(termo)
        txt.name = f"{nome_arquivo_limpo}.txt"
        await update.message.reply_document(InputFile(txt))
    else:
        await update.message.reply_text("Nenhum vazamento encontrado.")

# === MAIN ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("email", buscar_email))
    app.add_handler(CommandHandler("username", buscar_username))
    app.add_handler(CommandHandler("url", buscar_url))

    print("Bot rodando silenciosamente...")
    app.run_polling()