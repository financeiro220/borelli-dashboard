import streamlit as st
import pandas as pd
import warnings
import os
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Borelli Dashboard V2", layout="wide")

# Atualização automática a cada 10 minutos na tela do usuário
st_autorefresh(interval=10 * 60 * 1000, key="datarefresh_local")

st.title("🍦 Gelateria Borelli - Dashboard de KPIs (Local)")
st.subheader("Acompanhamento operacional em tempo real")
st.markdown("---")

# =========================================================================
# 📂 CAMINHO DIRETORIO LOCAL DA MAQUINA ONDE O ROBO SALVA O ARQUIVO
# =========================================================================
caminho_arquivo_local = r"G:\Drives compartilhados\Rh - Financeiro\AUTOMAÇÃO PAINEL BORELLI\vendas.xlsx"

try:
    if not os.path.exists(caminho_arquivo_local):
        st.markdown("### 🏪 Status Operacional")
        st.info("⏳ Aguardando o robô gerar o primeiro relatório do dia no Google Drive...")
        st.warning(f"Não foi possível localizar o arquivo no caminho: {caminho_arquivo_local}. Certifique-se de que o Google Drive para computador está ativo (Disco G:).")
    else:
        df = pd.read_excel(caminho_arquivo_local, engine="openpyxl", header=None, skiprows=1)
        
        if df.shape[1] < 20:
            st.markdown("### 🏪 Status Operacional")
            st.info("✨ Conectado ao arquivo de vendas com sucesso!")
            st.warning("🍦 Nenhuma venda registrada ainda hoje ou a estrutura de colunas está sendo montada pelo robô.")
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

            lojas = df["LOJA"].dropna().unique()
            
            for loja in lojas:
                if "LOJA" in str(loja): continue
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
                        st.metric(label="Itens Vendidos", value=f"{itens_t2:.0f} un", delta=f"{itens_t2 - t2_meta['itens']:.0f} vs Meta ({t2_meta['itens']})")
                    else:
                        st.info("Turno 2 em andamento ou sem dados registrados.")
                        
                st.markdown("---")

except Exception as e:
    st.error(f"Erro ao ler arquivo: {e}")
