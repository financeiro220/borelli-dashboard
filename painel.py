import streamlit as st
import pandas as pd
import warnings
import os
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore", category=UserWarning)

# Configuração da página
st.set_page_config(page_title="Borelli Dashboard V2", layout="wide")

# Atualização automática (10 minutos)
st_autorefresh(interval=10 * 60 * 1000, key="datarefresh_xlsx_gdrive_open")

# --- CSS CUSTOMIZADO PARA MELHORAR O VISUAL ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1e3d33;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 8px; }
    h1, h2, h3 { color: #1e3d33 !important; }
    hr { margin-top: 0; margin-bottom: 1rem; border-top: 2px solid #1e3d33; }
    .bandeira-italia {
        height: 5px;
        width: 100%;
        background: linear-gradient(90deg, #009246 33%, #ffffff 33%, #ffffff 66%, #ce2b37 66%);
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO COM LOGO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    # Tenta carregar o logo se ele existir na pasta do GitHub
    if os.path.exists("logo_borelli.png"):
        st.image("logo_borelli.png", width=120)
    else:
        st.title("🍦") # Placeholder se o logo não for encontrado

with col_titulo:
    st.title("Gelateria Borelli - Dashboard Operacional")
    st.caption("Acompanhamento de KPIs em tempo real • Sincronizado com Google Drive")

placeholder_filtro = st.empty()
st.write("")

# --- LOGICA DE DADOS ---
FILE_ID = "1utUgrbSx6paqhPJL029eyMnW32KGt7sG"
URL_RESOLVIDA = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/gviz/tq?tqx=out:csv"

try:
    df = pd.read_csv(URL_RESOLVIDA, header=None, skiprows=1)

    if df.shape[1] < 20:
        st.info("✨ Conectado ao Drive. Aguardando registros de hoje...")
    else:
        df = df.iloc[:, :25]
        df.columns = [
            "IDLOJA", "LOJA", "CAIXA", "VENDA", "DATA/HORA", "TEMPO_ATEND",
            "COD_OPERADOR", "OPERADOR", "COD_PRODUTO", "PRODUTO", "VALOR",
            "TAXA_ENTREGA", "NOME_CLIENTE", "CPF", "PONTOS_ANTES", "PONTOS_ADQ",
            "PONTOS_TOT", "PONTOS_APP", "OBS", "DESCONTO", "VALOR_CANCELADO",
            "JUST_DESC", "JUST_CANC", "QUANTIDADE", "UND"
        ]

        # Tratamento de valores
        for col in ["VALOR", "QUANTIDADE"]:
            df[col] = df[col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)

        df["DATA/HORA"] = pd.to_datetime(df["DATA/HORA"], dayfirst=True, errors='coerce')
        df["HORA_MINUTO"] = df["DATA/HORA"].dt.strftime("%H:%M")

        def classificar_turno(hora):
            if pd.isna(hora): return "Sem Horário"
            if "11:00" <= hora <= "16:30": return "Turno 1 (11h-16h30)"
            if "16:31" <= hora <= "22:30": return "Turno 2 (16h31-22h30)"
            return "Fora de Turno"

        df["TURNO"] = df["HORA_MINUTO"].apply(classificar_turno)

        metas = {
            "Turno 1 (11h-16h30)": {"tk": 30.00, "pa": 1.50, "itens": 50},
            "Turno 2 (16h31-22h30)": {"tk": 35.00, "pa": 1.65, "itens": 120}
        }

        # Filtro de Lojas
        todas_lojas = [l for l in df["LOJA"].dropna().unique() if "LOJA" not in str(l) and "INATIVO" not in str(l).upper()]
        
        # Lógica de nomes amigáveis
        NOMES_CONHECIDOS = {"ESTACAO": "Estação", "PANTANAL": "Pantanal"}
        rotulo_para_loja = {"Ver Todas as Lojas": None}
        for loja in todas_lojas:
            ultima = str(loja).strip().split()[-1].upper()
            rotulo = NOMES_CONHECIDOS.get(ultima, ultima.title())
            rotulo_para_loja[rotulo] = loja

        # --- BARRA DE FILTRO COM SENHA ---
        opcoes = list(rotulo_para_loja.keys())
        if "loja_filtro_ativo" not in st.session_state: st.session_state.loja_filtro_ativo = "Ver Todas as Lojas"
        
        with placeholder_filtro.container():
            cols = st.columns(len(opcoes))
            for i, opt in enumerate(opcoes):
                if cols[i].button(opt, key=f"f_{opt}", use_container_width=True, type="primary" if st.session_state.loja_filtro_ativo == opt else "secondary"):
                    if opt != st.session_state.loja_filtro_ativo:
                        st.session_state.loja_filtro_pendente = opt

            if st.session_state.get("loja_filtro_pendente"):
                p = st.session_state.loja_filtro_pendente
                st.write("")
                c1, c2, c3 = st.columns([2,1,1])
                senha = c1.text_input(f"🔒 Senha para acessar {p}:", type="password")
                if c2.button("Confirmar", type="primary", use_container_width=True):
                    if senha == "borelli2026":
                        st.session_state.loja_filtro_ativo = p
                        st.session_state.loja_filtro_pendente = None
                        st.rerun()
                    else: st.error("Senha incorreta.")
                if c3.button("Cancelar", use_container_width=True):
                    st.session_state.loja_filtro_pendente = None
                    st.rerun()

        loja_selecionada = rotulo_para_loja[st.session_state.loja_filtro_ativo]
        lista_lojas = [loja_selecionada] if loja_selecionada else todas_lojas

        # --- RENDERIZAÇÃO DOS DADOS ---
        for loja in lista_lojas:
            st.markdown('<div class="bandeira-italia"></div>', unsafe_allow_html=True)
            st.header(f"📍 {loja}")
            
            df_loja = df[df["LOJA"] == loja]
            col_t1, col_t2 = st.columns(2)

            # TURNO 1
            with col_t1:
                st.subheader("⏱️ Turno 1 (11:00 - 16:30)")
                g1 = df_loja[df_loja["TURNO"] == "Turno 1 (11h-16h30)"]
                if not g1.empty:
                    fat = g1["VALOR"].sum()
                    vds = g1["VENDA"].nunique()
                    itns = g1["QUANTIDADE"].sum()
                    tk = fat/vds if vds>0 else 0
                    pa = itns/vds if vds>0 else 0
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Faturamento", f"R$ {fat:,.2f}")
                    m2.metric("Ticket Médio", f"R$ {tk:.2f}", f"{tk - metas['Turno 1 (11h-16h30)']['tk']:.2f}")
                    m3.metric("PA", f"{pa:.2f}", f"{pa - metas['Turno 1 (11h-16h30)']['pa']:.2f}")
                    
                    m4, m5 = st.columns(2)
                    m4.metric("Atendimentos", f"{vds}")
                    m5.metric("Itens Vendidos", f"{itns:.0f}", f"{itns - metas['Turno 1 (11h-16h30)']['itens']:.0f}")
                else: st.info("Aguardando dados do Turno 1...")

            # TURNO 2
            with col_t2:
                st.subheader("⏱️ Turno 2 (16:31 - 22:30)")
                g2 = df_loja[df_loja["TURNO"] == "Turno 2 (16h31-22h30)"]
                if not g2.empty:
                    fat = g2["VALOR"].sum()
                    vds = g2["VENDA"].nunique()
                    itns = g2["QUANTIDADE"].sum()
                    tk = fat/vds if vds>0 else 0
                    pa = itns/vds if vds>0 else 0
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Faturamento", f"R$ {fat:,.2f}")
                    m2.metric("Ticket Médio", f"R$ {tk:.2f}", f"{tk - metas['Turno 2 (16h31-22h30)']['tk']:.2f}")
                    m3.metric("PA", f"{pa:.2f}", f"{pa - metas['Turno 2 (16h31-22h30)']['pa']:.2f}")
                    
                    m4, m5 = st.columns(2)
                    m4.metric("Atendimentos", f"{vds}")
                    m5.metric("Itens Vendidos", f"{itns:.0f}", f"{itns - metas['Turno 2 (16h31-22h30)']['itens']:.0f}")
                else: st.info("Aguardando dados do Turno 2...")
            st.write("")

except Exception as e:
    st.error(f"Erro na conexão de dados: {e}")
