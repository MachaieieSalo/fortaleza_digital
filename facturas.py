import streamlit as st
import io
import logging
from supabase import create_client, Client
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================
# CONFIGURAÇÕES DO SUPABASE
# ==========================
SUPABASE_URL = "https://qdjcokczpvfkqbpaezhn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkamNva2N6cHZma3FicGFlemhuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzYwODY0MywiZXhwIjoyMDczMTg0NjQzfQ.2QhJnqiEG9k4UKmArDe6S4UY8Tkl2WmztamUn7I7wwk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================
# FUNÇÃO DE LOGIN
# ==========================
def autenticar(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        logging.error(f"Erro ao autenticar: {e}")
        return None


# ==========================
# CARREGAR ITENS DA TABELA
# ==========================
def carregar_itens():
    try:
        response = supabase.table("itens").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Erro ao carregar itens: {e}")
        st.error("Erro ao carregar itens.")
        return []


# ==========================
# GERAR PDF
# ==========================
def gerar_pdf_cotacao(empresa, itens):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []

    # Logo
    try:
        logo_path = "logo.png"
        imagem_logo = Image(logo_path, width=80, height=80)
        tabela_logo = Table([[imagem_logo]], colWidths=[100], rowHeights=[80])
        tabela_logo.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ]))
        elementos.append(tabela_logo)
    except Exception as e:
        logging.warning(f"Logo não encontrado: {e}")

    estilos = getSampleStyleSheet()
    estilo_normal = ParagraphStyle(
        name="NormalPersonalizado", parent=estilos["Normal"],
        fontName="Courier", fontSize=10, leading=12
    )
    estilo_bold = ParagraphStyle(
        name="BoldPersonalizado", parent=estilos["Normal"],
        fontName="Courier-Bold", fontSize=10, leading=12
    )

    # Dados da empresa
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(f"<b>Cotação de Exames Clínicos para</b> {empresa['nome']}", estilo_bold))
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
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elementos.append(tabela_itens)
    elementos.append(Spacer(1, 12))

    # Totais
    elementos.append(Paragraph(f"Subtotal (sem IVA): MZN {total_sem_iva:.2f}", estilo_bold))
    elementos.append(Paragraph(f"IVA (16%): MZN {iva:.2f}", estilo_bold))
    elementos.append(Paragraph(f"Total Geral: MZN {total_com_iva:.2f}", estilo_bold))

    # Gerar PDF
    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================
# INTERFACE STREAMLIT
# ==========================
st.title("Fortaleza Digital")

# Login
if "user" not in st.session_state:
    st.text("Bem Vindo PCA Nelinho Rodrigues")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Entrar"):
        user = autenticar(email, password)
        if user:
            st.session_state["user"] = user
            st.success("Login bem-sucedido!")
        else:
            st.error("Falha no login.")
else:
    st.success(f"Utilizador autenticado: {st.session_state['user'].user.email}")

    # Carregar itens do Supabase
    itens = carregar_itens()

    if itens:
        empresa = {
            "nome": "Empresa XPTO",
            "nuit": "401937684",
            "endereco": "Boane, B.2, Q.3 Av. Namaacha, Rua 1º de Maio C. Nº 59",
            "email": "empresa@exemplo.com"
        }

        pdf_bytes = gerar_pdf_cotacao(empresa, itens)

        st.download_button(
            label="⬇️ Baixar PDF",
            data=pdf_bytes,
            file_name="cotacao.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Nenhum item encontrado na tabela `itens`.")


