import streamlit as st
import pandas as pd
import warnings
import os
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore", category=UserWarning)

# Configuração da página para garantir o layout correto
st.set_page_config(page_title="Borelli Dashboard V2", layout="wide")

# Atualização automática a cada 10 minutos na tela do usuário
st_autorefresh(interval=10 * 60 * 1000, key="datarefresh_xlsx_gdrive_open")

# =========================================================================
# 🎨 ESTILIZAÇÃO CUSTOMIZADA PARA MODO ESCURO (DARK MODE)
# =========================================================================
st.markdown("""
    <style>
    /* Remove fundos brancos e força o design dark elegante */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
    }
    /* Faixa decorativa com as cores da Itália abaixo de cada loja */
    .bandeira-italia {
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, #009246 33%, #ffffff 33%, #ffffff 66%, #ce2b37 66%);
        margin-top: 15px;
        margin-bottom: 15px;
        border-radius: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 🍦 CABEÇALHO COMPATÍVEL COM LOGO LOCAL (NA RAIZ DO PROJETO)
# =========================================================================
col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    # Procura o ficheiro logo_borelli.png na raiz do repositório
    if os.path.exists("logo_borelli.png"):
        st.image("logo_borelli.png", width=120)
    else:
        # Mostra apenas um espaço vazio elegante enquanto faz o upload do ficheiro correto
        st.write("")

with col_titulo:
    st.markdown("<h1 style='margin-top: 10px;'>Gelateria Borelli - Dashboard Operacional</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888888; margin-top: -15px;'>Acompanhamento de KPIs em tempo real • Sincronizado com Google Drive</p>", unsafe_allow_html=True)

placeholder_filtro = st.empty()
st.write("")

# =========================================================================
# LINK DE CONEXÃO COM O GOOGLE DRIVE
# =========================================================================
FILE_ID = "1utUgrbSx6paqhPJL029eyMnW32KGt7sG"
URL_RESOLVIDA = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/gviz/tq?tqx=out:csv"

try:
    df = pd.read_csv(URL_RESOLVIDA, header=None, skiprows=1)

    if df.shape[1] < 20:
        st.info("✨ Conectado ao Drive com sucesso! Aguardando os primeiros registros de vendas de hoje...")
    else:
        df = df.iloc[:, :25]
        df.columns = [
            "IDLOJA", "LOJA", "CAIXA", "VENDA", "DATA/HORA", "TEMPO_ATEND",
            "COD_OPERADOR", "OPERADOR", "COD_PRODUTO", "PRODUTO", "VALOR",
            "TAXA_ENTREGA", "NOME_CLIENTE", "CPF", "PONTOS_ANTES", "PONTOS_ADQ",
            "PONTOS_TOT", "PONTOS_APP", "OBS", "DESCONTO", "VALOR_CANCELADO",
            "JUST_DESC", "JUST_CANC", "QUANTIDADE", "UND"
        ]

        # Tratamento rápido e vetorizado de valores numéricos
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

        todas_lojas = [l for l in df["LOJA"].dropna().unique() if "LOJA" not in str(l) and "INATIVO" not in str(l).upper()]
        
        NOMES_CONHECIDOS = {"ESTACAO": "Estação", "PANTANAL": "Pantanal"}
        rotulo_para_loja = {"Ver Todas as Lojas": None}
        for loja in todas_lojas:
            ultima = str(loja).strip().split()[-1].upper()
            rotulo = NOMES_CONHECIDOS.get(ultima, ultima.title())
            rotulo_para_loja[rotulo] = loja

        # --- CONTROLE FILTRO DE LOJA COM SENHA ---
        opcoes = list(rotulo_para_loja.keys())
        if "loja_filtro_ativo" not in st.session_state: 
            st.session_state.loja_filtro_ativo = "Ver Todas as Lojas"
        
        with placeholder_filtro.container():
            cols = st.columns(len(opcoes))
            for i, opt in enumerate(opcoes):
                if cols[i].button(opt, key=f"f_{opt}", use_container_width=True, type="primary" if st.session_state.loja_filtro_ativo == opt else "secondary"):
                    if opt != st.session_state.loja_filtro_ativo:
                        st.session_state.loja_filtro_pendente = opt

            if st.session_state.get("loja_filtro_pendente"):
                p = st.session_state.loja_filtro_pendente
                st.write("")
                c1, c2, c3 = st.columns([2, 1, 1])
                senha = c1.text_input(f"🔒 Digite a senha para liberar o filtro '{p}':", type="password")
                if c2.button("Confirmar", type="primary", use_container_width=True):
                    if senha == "borelli2026":
                        st.session_state.loja_filtro_ativo = p
                        st.session_state.loja_filtro_pendente = None
                        st.rerun()
                    else: 
                        st.error("Senha incorreta.")
                if c3.button("Cancelar", use_container_width=True):
                    st.session_state.loja_filtro_pendente = None
                    st.rerun()

        loja_selecionada = rotulo_para_loja[st.session_state.loja_filtro_ativo]
        lista_lojas = [loja_selecionada] if loja_selecionada else todas_lojas

        # =========================================================================
        # 📊 APRESENTAÇÃO DOS DADOS OPERACIONAIS (ESTILO CLEAN DARK)
        # =========================================================================
        for loja in lista_lojas:
            st.markdown('<div class="bandeira-italia"></div>', unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #ffffff; margin-bottom: 20px;'>📍 {loja}</h2>", unsafe_allow_html=True)
            
            df_loja = df[df["LOJA"] == loja]
            col_t1, col_t2 = st.columns(2)

            # --- VISUALIZAÇÃO DO TURNO 1 ---
            with col_t1:
                st.markdown("<h3 style='color: #009246;'>⏱️ Turno 1 (11:00 às 16:30)</h3>", unsafe_allow_html=True)
                g1 = df_loja[df_loja["TURNO"] == "Turno 1 (11h-16h30)"]
                
                if not g1.empty:
                    fat = g1["VALOR"].sum()
                    vds = g1["VENDA"].nunique()
                    itns = g1["QUANTIDADE"].sum()
                    tk = fat/vds if vds > 0 else 0
                    pa = itns/vds if vds > 0 else 0
                    
                    # Linha 1 de KPIs (Faturamento, Ticket Médio, PA)
                    m1, m2, m3 = st.columns(3)
                    m1.metric(label="Faturamento Total", value=f"R$ {fat:,.2f}")
                    m2.metric(label="Ticket Médio", value=f"R$ {tk:.2f}", delta=f"{tk - metas['Turno 1 (11h-16h30)']['tk']:.2f} vs Meta")
                    m3.metric(label="PA (Prod/Atend)", value=f"{pa:.2f}", delta=f"{pa - metas['Turno 1 (11h-16h30)']['pa']:.2f} vs Meta")
                    
                    # Linha 2 de KPIs (Atendimentos, Itens)
                    m4, m5, _ = st.columns(3)
                    m4.metric(label="Clientes Atendidos", value=f"{vds}")
                    m5.metric(label="Itens Vendidos", value=f"{itns:.0f} un", delta=f"{itns - metas['Turno 1 (11h-16h30)']['itens']:.0f} vs Meta")
                else: 
                    st.info("Aguardando lançamentos operacionais para o Turno 1.")

            # --- VISUALIZAÇÃO DO TURNO 2 ---
            with col_t2:
                st.markdown("<h3 style='color: #ce2b37;'>⏱️ Turno 2 (16:31 às 22:30)</h3>", unsafe_allow_html=True)
                g2 = df_loja[df_loja["TURNO"] == "Turno 2 (16h31-22h30)"]
                
                if not g2.empty:
                    fat = g2["VALOR"].sum()
                    vds = g2["VENDA"].nunique()
                    itns = g2["QUANTIDADE"].sum()
                    tk = fat/vds if vds > 0 else 0
                    pa = itns/vds if vds > 0 else 0
                    
                    # Linha 1 de KPIs
                    m1, m2, m3 = st.columns(3)
                    m1.metric(label="Faturamento Total", value=f"R$ {fat:,.2f}")
                    m2.metric(label="Ticket Médio", value=f"R$ {tk:.2f}", delta=f"{tk - metas['Turno 2 (16h31-22h30)']['tk']:.2f} vs Meta")
                    m3.metric(label="PA (Prod/Atend)", value=f"{pa:.2f}", delta=f"{pa - metas['Turno 2 (16h31-22h30)']['pa']:.2f} vs Meta")
                    
                    # Linha 2 de KPIs
                    m4, m5, _ = st.columns(3)
                    m4.metric(label="Clientes Atendidos", value=f"{vds}")
                    m5.metric(label="Itens Vendidos", value=f"{itns:.0f} un", delta=f"{itns - metas['Turno 2 (16h31-22h30)']['itens']:.0f} vs Meta")
                else: 
                    st.info("Turno 2 em andamento ou aguardando sincronização de dados.")
            st.write("")

except Exception as e:
    st.error(f"Erro crítico na leitura ou processamento dos dados do Drive: {e}")
