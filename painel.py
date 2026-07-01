import streamlit as st
import pandas as pd
import warnings
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Borelli Dashboard V2", layout="wide")

# Atualização automática a cada 10 minutos na tela do usuário
st_autorefresh(interval=10 * 60 * 1000, key="datarefresh_xlsx_gdrive_open")

# =========================================================================
# CABEÇALHO: título à esquerda + filtro de loja reservado à direita
# (o conteúdo do filtro só é preenchido depois que os dados carregam,
# mas a posição/layout já fica reservada aqui em cima)
# =========================================================================
col_titulo, col_filtro = st.columns([4, 1])
with col_titulo:
    st.title("🍦 Gelateria Borelli - Dashboard")
    st.subheader("Acompanhamento operacional em tempo real")

placeholder_filtro = col_filtro.empty()
st.markdown("---")

# =========================================================================
# LINK CORRIGIDO DE VISUALIZAÇÃO PÚBLICA (BURLE OS BLOQUEIOS CORPORATIVOS)
# =========================================================================
FILE_ID = "1utUgrbSx6paqhPJL029eyMnW32KGt7sG"
# Usando a API de Query do Google, que transforma qualquer .xlsx em dados limpos na nuvem
URL_RESOLVIDA = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/gviz/tq?tqx=out:csv"

try:
    # Lendo os dados como CSV através do motor de renderização pública do Google Sheets
    df = pd.read_csv(URL_RESOLVIDA, header=None, skiprows=1)

    if df.shape[1] < 20:
        st.markdown("### 🏪 Status Operacional")
        st.info("✨ Sistema em nuvem conectado ao Google Drive com sucesso!")
        st.warning("🍦 Nenhuma venda registrada ainda hoje ou estrutura de colunas incompleta.")
    else:
        df = df.iloc[:, :25]
        df.columns = [
            "IDLOJA", "LOJA", "CAIXA", "VENDA", "DATA/HORA", "TEMPO_ATEND",
            "COD_OPERADOR", "OPERADOR", "COD_PRODUTO", "PRODUTO", "VALOR",
            "TAXA_ENTREGA", "NOME_CLIENTE", "CPF", "PONTOS_ANTES", "PONTOS_ADQ",
            "PONTOS_TOT", "PONTOS_APP", "OBS", "DESCONTO", "VALOR_CANCELADO",
            "JUST_DESC", "JUST_CANC", "QUANTIDADE", "UND"
        ]

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

        todas_lojas = [
            loja for loja in df["LOJA"].dropna().unique()
            if "LOJA" not in str(loja) and "INATIVO" not in str(loja).upper()
        ]

        # =====================================================================
        # 🏷️ FILTRO DE LOJA: monta rótulo curto (última palavra do nome) para
        # cada loja, ex: "CUIABA - SHOPPING ESTACAO" -> "Estação"
        # =====================================================================
        NOMES_CONHECIDOS = {
            "ESTACAO": "Estação",
            "PANTANAL": "Pantanal",
        }
        rotulo_para_loja = {"Todas": None}
        for loja in todas_lojas:
            ultima_palavra = str(loja).strip().split()[-1].upper()
            rotulo = NOMES_CONHECIDOS.get(ultima_palavra, ultima_palavra.title())
            rotulo_para_loja[rotulo] = loja

        opcoes_rotulos = list(rotulo_para_loja.keys())

        # Senha exigida toda vez que o usuário tentar trocar o filtro de loja
        # (inclusive ao voltar/ir para "Todas").
        SENHA_FILTRO = "borelli2026"

        # "ativo" é o filtro realmente aplicado nos dados.
        if "loja_filtro_ativo" not in st.session_state:
            st.session_state.loja_filtro_ativo = "Todas"
        if st.session_state.loja_filtro_ativo not in opcoes_rotulos:
            st.session_state.loja_filtro_ativo = "Todas"

        # "pendente" é o botão que o usuário acabou de clicar, aguardando confirmação de senha.
        if "loja_filtro_pendente" not in st.session_state:
            st.session_state.loja_filtro_pendente = None

        with placeholder_filtro.container():
            st.caption("Filtrar loja")

            colunas_botoes = st.columns(len(opcoes_rotulos))
            for i, rotulo in enumerate(opcoes_rotulos):
                is_ativo = rotulo == st.session_state.loja_filtro_ativo
                with colunas_botoes[i]:
                    # Botão do filtro ativo aparece destacado (type="primary"); os demais neutros.
                    if st.button(
                        rotulo,
                        key=f"btn_filtro_{rotulo}",
                        type="primary" if is_ativo else "secondary",
                        use_container_width=True,
                    ):
                        if rotulo != st.session_state.loja_filtro_ativo:
                            st.session_state.loja_filtro_pendente = rotulo
                            st.session_state.pop("senha_filtro_texto", None)

            # Enquanto houver uma troca pendente (qualquer destino, incluindo "Todas"),
            # exige senha antes de aplicar.
            if st.session_state.loja_filtro_pendente is not None:
                pendente = st.session_state.loja_filtro_pendente
                st.warning(f"🔒 Senha necessária para filtrar '{pendente}'")
                senha_digitada = st.text_input(
                    "Senha", type="password", key="senha_filtro_texto", label_visibility="collapsed"
                )
                col_ok, col_cancel = st.columns(2)
                with col_ok:
                    if st.button("Confirmar", key="btn_confirma_filtro", use_container_width=True):
                        if senha_digitada == SENHA_FILTRO:
                            st.session_state.loja_filtro_ativo = pendente
                            st.session_state.loja_filtro_pendente = None
                            st.session_state.pop("senha_filtro_texto", None)
                            st.rerun()
                        else:
                            st.error("Senha incorreta.")
                with col_cancel:
                    if st.button("Cancelar", key="btn_cancela_filtro", use_container_width=True):
                        st.session_state.loja_filtro_pendente = None
                        st.session_state.pop("senha_filtro_texto", None)
                        st.rerun()

        loja_escolhida = rotulo_para_loja[st.session_state.loja_filtro_ativo]
        lojas = [loja_escolhida] if loja_escolhida is not None else todas_lojas
        # =====================================================================

        for loja in lojas:
            st.header(f"📍 {loja}")

            col_turno1, col_turno2 = st.columns(2)
            df_loja = df[df["LOJA"] == loja]

            # --- TURNO 1 ---
            with col_turno1:
                st.markdown("### ⏱️ Turno 1 (11:00 às 16:30)")
                t1_meta = metas["Turno 1 (11h-16h30)"]
                grupo_t1 = df_loja[df_loja["TURNO"] == "Turno 1 (11h-16h30)"]

                if not grupo_t1.empty:
                    fat_t1 = grupo_t1["VALOR"].sum()
                    vendas_t1 = grupo_t1["VENDA"].nunique()
                    itens_t1 = grupo_t1["QUANTIDADE"].sum()
                    tk_t1 = fat_t1 / vendas_t1 if vendas_t1 > 0 else 0
                    pa_t1 = itens_t1 / vendas_t1 if vendas_t1 > 0 else 0

                    st.metric(label="Faturamento Total", value=f"R$ {fat_t1:,.2f}")
                    st.metric(label="Ticket Médio", value=f"R$ {tk_t1:.2f}", delta=f"{tk_t1 - t1_meta['tk']:.2f} vs Meta ({t1_meta['tk']:.2f})")
                    st.metric(label="PA (Produtos/Atend.)", value=f"{pa_t1:.2f}", delta=f"{pa_t1 - t1_meta['pa']:.2f} vs Meta ({t1_meta['pa']:.2f})")
                    st.metric(label="Clientes Atendidos", value=f"{vendas_t1}")
                    st.metric(label="Itens Vendidos", value=f"{itens_t1:.0f} un", delta=f"{itens_t1 - t1_meta['itens']:.0f} vs Meta ({t1_meta['itens']})")
                else:
                    st.info("Sem dados operacionais para o Turno 1.")

            # --- TURNO 2 ---
            with col_turno2:
                st.markdown("### ⏱️ Turno 2 (16:31 às 22:30)")
                t2_meta = metas["Turno 2 (16h31-22h30)"]
                grupo_t2 = df_loja[df_loja["TURNO"] == "Turno 2 (16h31-22h30)"]

                if not grupo_t2.empty:
                    fat_t2 = grupo_t2["VALOR"].sum()
                    vendas_t2 = grupo_t2["VENDA"].nunique()
                    itens_t2 = grupo_t2["QUANTIDADE"].sum()
                    tk_t2 = fat_t2 / vendas_t2 if vendas_t2 > 0 else 0
                    pa_t2 = itens_t2 / vendas_t2 if vendas_t2 > 0 else 0

                    st.metric(label="Faturamento Total", value=f"R$ {fat_t2:,.2f}")
                    st.metric(label="Ticket Médio", value=f"R$ {tk_t2:.2f}", delta=f"{tk_t2 - t2_meta['tk']:.2f} vs Meta ({t2_meta['tk']:.2f})")
                    st.metric(label="PA (Produtos/Atend.)", value=f"{pa_t2:.2f}", delta=f"{pa_t2 - t2_meta['pa']:.2f} vs Meta ({t2_meta['pa']:.2f})")
                    st.metric(label="Clientes Atendidos", value=f"{vendas_t2}")
                    st.metric(label="Itens Vendidos", value=f"{itens_t2:.0f} un", delta=f"{itens_t2 - t2_meta['itens']:.0f} vs Meta ({t2_meta['itens']})")
                else:
                    st.info("Turno 2 em andamento ou sem dados registrados.")

            st.markdown("---")

except Exception as e:
    st.error(f"Erro ao ler os dados transmitidos: {e}")
