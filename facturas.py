import streamlit as st
import io
import logging
import os
from datetime import datetime
from supabase import create_client, Client
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================
# CONFIGURAÇÕES DO SUPABASE
# ==========================
SUPABASE_URL = "https://qdjcokczpvfkqbpaezhn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkamNva2N6cHZma3FicGFlemhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc2MDg2NDIsImV4cCI6MjA3MzE4NDY0Mn0.HC2M4bEfhT4xa7CIvc27Us8rHMp1T3k634gR7GBQuMg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================
# FUNÇÕES DE AUTENTICAÇÃO
# ==========================
def autenticar(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        logging.error(f"Erro ao autenticar: {e}")
        return None


def autenticar_utilizador():
    st.title("Fortaleza Digital, EI| Autenticação")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Entrar"):
        user = autenticar(email, password)
        if user and getattr(user, "user", None):
            st.session_state["user"] = user
            st.success(f"Bem-vindo, {user.user.email}!")
            st.rerun()
        else:
            st.error("Falha no login. Verifique suas credenciais.")


# ==========================
# FUNÇÕES DE DADOS
# ==========================
def carregar_itens():
    try:
        response = supabase.table("itens").select("id, nome, preco").execute()
        if response.data and len(response.data) > 0:
            return response.data
        st.warning("⚠️ Nenhum item encontrado na tabela 'itens'.")
        return []
    except Exception as e:
        st.error(f"Erro ao carregar itens da base de dados: {e}")
        st.info("A carregar itens de exemplo para teste...")
        return [
            {"id": 1, "nome": "Hemograma", "preco": 500},
            {"id": 2, "nome": "Raio-X", "preco": 1500},
            {"id": 3, "nome": "Ecografia", "preco": 2000},
        ]


def salvar_cotacao_supabase(empresa, itens, total):
    try:
        data = {
            "data_cotacao": datetime.now().isoformat(),
            "nome_empresa": empresa["nome"],
            "nuit_empresa": empresa["nuit"],
            "endereco_empresa": empresa["endereco"],
            "email_empresa": empresa["email"],
            "itens_cotacao": itens,
            "total_cotacao": total,
            "user_id": getattr(st.session_state["user"].user, "id", None)
        }
        supabase.table("cotacoes").insert(data).execute()
        st.success("✅ Cotação salva com sucesso no Supabase!")
    except Exception as e:
        logging.error(f"Erro ao salvar cotação no Supabase: {e}")
        st.error("❌ Erro ao salvar cotação na base de dados.")


# ==========================
# GERAR PDF
# ==========================
def gerar_pdf_cotacao(empresa, itens):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []

    # Logo
    logo_path = "images/logo.png"
    if os.path.exists(logo_path):
        imagem_logo = Image(logo_path, width=80, height=80)
        elementos.append(imagem_logo)
    else:
        st.warning("⚠️ Logo não encontrada no diretório 'images/'.")

    estilos = getSampleStyleSheet()
    estilo_normal = ParagraphStyle(name="NormalPersonalizado", parent=estilos["Normal"], fontName="Courier", fontSize=10)
    estilo_bold = ParagraphStyle(name="BoldPersonalizado", parent=estilos["Normal"], fontName="Courier-Bold", fontSize=10)

    # Dados da empresa 
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("Fortaleza Digital. EI", estilo_normal))
    elementos.append(Paragraph("Matola, Intaka, Rua do Mulawuze Q .Nº1, C. Nº 7", estilo_normal))
    elementos.append(Paragraph("NUIT: 401937684", estilo_normal))
    elementos.append(Paragraph("Contacto: +258 87 741 0943", estilo_normal))
    elementos.append(Spacer(1, 12))

    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(f"<b>Cotação para prestação de serviços para</b> {empresa['nome']}", estilo_bold))
    elementos.append(Paragraph(f"NUIT: {empresa['nuit']}", estilo_normal))
    elementos.append(Paragraph(f"Endereço: {empresa['endereco']}", estilo_normal))
    elementos.append(Paragraph(f"Email: {empresa['email']}", estilo_normal))
    elementos.append(Spacer(1, 12))

    # Tabela de itens
    data = [["Nr", "Descrição", "Qtd", "Preço Unit", "Preço Total", "IVA"]]
    total_sem_iva = 0
    for idx, item in enumerate(itens, 1):
        preco_total = item["quantidade"] * item["preco"]
        total_sem_iva += preco_total
        data.append([
            str(idx),
            item["nome"],
            str(item["quantidade"]),
            f"MZN {item['preco']:.2f}",
            f"MZN {preco_total:.2f}",
            "16%"
        ])
    iva = total_sem_iva * 0.16
    total_com_iva = total_sem_iva + iva

    tabela_itens = Table(data, colWidths=[30, 150, 50, 80, 80, 40])
    tabela_itens.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),  # Cabeçalho
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),  # Qtd, preços e totais
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 10)
    ]))
    elementos.append(tabela_itens)
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(f"Subtotal (sem IVA): MZN {total_sem_iva:.2f}", estilo_bold))
    elementos.append(Paragraph(f"IVA (16%): MZN {iva:.2f}", estilo_bold))
    elementos.append(Paragraph(f"Total Geral: MZN {total_com_iva:.2f}", estilo_bold))

    elementos.append(Paragraph("Esta cotação tem a validade de 05 dias.", estilo_normal))
    elementos.append(Spacer(1, 12))
    # Dados bancários 
    elementos.append(Paragraph("<b>DADOS BANCÁRIOS</b>", estilo_bold))
    elementos.append(Paragraph("EMOLA - Conta: 87 741 0943 - Nelinho Rodrigues", estilo_normal))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue(), total_com_iva


# ==========================
# PÁGINAS
# ==========================
def pagina_inicio():
    st.image("images/logo.png", width=150)
    st.write("Use o menu à esquerda para gerir pacientes, agendar consultas e gerar relatórios.")
    st.divider()
    st.markdown("""
    © 2025 Fortaleza Digital  | Todos os direitos reservados.  
    Versão: 1.0  
    Desenvolvedor: **Salomão Paulino Machaieie**
    """)


def pagina_cotacoes():
    st.title("Cotação para prestação de serviços")
    st.subheader("Informações da Empresa Requisitante")

    # Campos da empresa
    for campo in ["nome_empresa", "nuit_empresa", "endereco_empresa", "email_empresa"]:
        if campo not in st.session_state:
            st.session_state[campo] = ""

    st.session_state.nome_empresa = st.text_input("Nome da Empresa:", st.session_state.nome_empresa)
    st.session_state.nuit_empresa = st.text_input("NUIT da Empresa:", st.session_state.nuit_empresa)
    st.session_state.endereco_empresa = st.text_input("Endereço da Empresa:", st.session_state.endereco_empresa)
    st.session_state.email_empresa = st.text_input("Email da Empresa:", st.session_state.email_empresa)

    # Itens disponíveis
    if "itens_cotacao" not in st.session_state:
        st.session_state.itens_cotacao = []
    if "itens_disponiveis" not in st.session_state:
        st.session_state.itens_disponiveis = carregar_itens()

    itens_nomes = [e["nome"] for e in st.session_state.itens_disponiveis]

    # Formulário para adicionar itens
    with st.form("add_item_form", clear_on_submit=True):
        col1, col2 = st.columns([0.7, 0.3])
        item_selecionado = col1.selectbox("Selecione o Item:", itens_nomes if itens_nomes else ["Nenhum disponível"])
        quantidade = col2.number_input("Quantidade:", 1, 100, 1)
        adicionar_item = st.form_submit_button("Adicionar Item à Cotação")

    if adicionar_item and itens_nomes and item_selecionado != "Nenhum disponível":
        item = next((e for e in st.session_state.itens_disponiveis if e["nome"] == item_selecionado), None)
        if item:
            st.session_state.itens_cotacao.append({
                "id": item["id"],
                "nome": item["nome"],
                "preco": item["preco"],
                "quantidade": quantidade
            })
            st.success(f"'{item['nome']}' adicionado à cotação!")

    # Lista de itens adicionados
    st.subheader("Itens na Cotação Atual:")
    total_cotacao = 0
    for i, item in enumerate(st.session_state.itens_cotacao, 1):
        subtotal = item["preco"] * item["quantidade"]
        total_cotacao += subtotal
        st.write(f"{i}. {item['quantidade']} x {item['nome']} ({item['preco']:.2f} MZN/un) = {subtotal:.2f} MZN")

    if st.session_state.itens_cotacao:
        st.markdown(f"**Total da Cotação: {total_cotacao:.2f} MZN**")
    else:
        st.info("Nenhum item adicionado à cotação.")

    # Gerar PDF
    if st.button("Gerar PDF e Salvar Cotação"):
        campos = [st.session_state.nome_empresa, st.session_state.nuit_empresa,
                  st.session_state.endereco_empresa, st.session_state.email_empresa]
        if any(campo.strip() == "" for campo in campos):
            st.warning("⚠️ Preencha todos os campos da empresa.")
            return
        if not st.session_state.itens_cotacao:
            st.warning("⚠️ Adicione pelo menos um item à cotação.")
            return

        empresa_dados = {
            "nome": st.session_state.nome_empresa,
            "nuit": st.session_state.nuit_empresa,
            "endereco": st.session_state.endereco_empresa,
            "email": st.session_state.email_empresa
        }

        pdf_bytes, total = gerar_pdf_cotacao(empresa_dados, st.session_state.itens_cotacao)
        salvar_cotacao_supabase(empresa_dados, st.session_state.itens_cotacao, total)

        st.download_button(
            label="⬇️ Baixar Cotação PDF",
            data=pdf_bytes,
            file_name=f"cotacao_{st.session_state.nome_empresa.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )


# ==========================
# LÓGICA PRINCIPAL
# ==========================
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    autenticar_utilizador()
    st.stop()

st.sidebar.image("images/logo.png", width=150)
st.sidebar.write("### Menu")
menu_options = {"🏠 Início": pagina_inicio, "🧾 Gerar Cotações": pagina_cotacoes, "🚪 Logout": None}
opcao_selecionada = st.sidebar.radio("Navegar", list(menu_options.keys()))
st.session_state["opcao_menu"] = opcao_selecionada

if opcao_selecionada == "🚪 Logout":
    try:
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao fazer logout: {e}")
else:
    func_pagina = menu_options.get(opcao_selecionada)
    if func_pagina:
        func_pagina()
