import streamlit as st
import numpy as np
import plotly.graph_objects as go
import os
import csv
from datetime import datetime
import uuid

# ==========================================
# Configuração da Página
# ==========================================
st.set_page_config(page_title="Peak Identification", layout="wide")

# ==========================================
# Gerenciamento de Estado (Memória da Sessão)
# ==========================================
if "questionario_concluido" not in st.session_state:
    st.session_state.questionario_concluido = False

# Gera um Hash único de 8 caracteres para anonimizar o usuário
if "hash_pesquisador" not in st.session_state:
    st.session_state.hash_pesquisador = str(uuid.uuid4())[:8].upper()

if "picos_marcados" not in st.session_state:
    st.session_state.picos_marcados = set()

if "espectro_atual" not in st.session_state:
    st.session_state.espectro_atual = 0

# ==========================================
# Carregamento dos Dados
# ==========================================
@st.cache_data
def carregar_dados():
    dados_ruidosos = np.load('espectros_complexos_ruidosos.npy')
    eixo_x = np.linspace(0, 1000, 1000)
    return dados_ruidosos, eixo_x

dados_ruidosos, eixo_x = carregar_dados()
total_espectros = len(dados_ruidosos)

# ==========================================
# TELA 1: Questionário Inicial
# ==========================================
if not st.session_state.questionario_concluido:
    st.title("📋 Initial Questionnaire")
    st.markdown("This is an experiment to evaluate how humans deal with peak identification. \n The objective is to compare human answers with an algorithm we are developing.")
    st.markdown("Before starting the peak identification process, please fill in the information below for analysis purposes.")
    
    st.info(f"🔒 Your anonymous ID for this session is: **{st.session_state.hash_pesquisador}**")
    
    with st.form("form_perfil"):
        
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            titulacao = st.selectbox(
                "What is your current academic qualification?",
                [
                    "Bachelor's Degree (in progress or completed)",
                    "Master's Degree",
                    "Ph.D."
                ],
                index=None,
                placeholder="Select an option..."
            )

            area_atuacao = st.selectbox(
                "What is your primary field of research?",
                [
                    "Materials Science",
                    "Chemistry",
                    "Physics",
                    "Engineering",
                    "Biology",
                    "Geology",
                    "Other"
                ],
                index=None,
                placeholder="Select an option or type a new one...",
                accept_new_options=True 
            )
            
        with col_form2:
            experiencia_espectroscopia = st.radio(
               "What is your level of experience with spectral analysis (e.g., NMR, Impedance Spectroscopy, Raman)?",
                [
                    "Beginner (I have basic theoretical knowledge but little practical experience)",
                    "Intermediate (I have practical experience with common spectroscopy techniques)",
                    "Advanced (I routinely use spectroscopy techniques in my research or professional work)",
                    "Expert (I have extensive experience and deep expertise in spectroscopy)"
                ],
                index=None
            )

            frequencia_ajuste = st.select_slider(
                "How often do you perform curve fitting in your research?",
                options=[
                    "Never",
                    "Rarely",
                    "Monthly",
                    "Weekly",
                    "Daily"
                ]
            )

        botao_iniciar = st.form_submit_button("Save and Start Analysis")
        
        if botao_iniciar:
            if titulacao is None or area_atuacao is None or experiencia_espectroscopia is None:
                st.error("Please, fill in all mandatory fields before proceeding.")
            else:
                perfil = {
                    "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "hash_pesquisador": st.session_state.hash_pesquisador,
                    "titulacao": titulacao,
                    "area_atuacao": area_atuacao,
                    "experiencia": experiencia_espectroscopia,
                    "frequencia_ajuste": frequencia_ajuste
                }
                
                arquivo_perfis = "perfil_pesquisadores.csv"
                arquivo_existe = os.path.isfile(arquivo_perfis)
                with open(arquivo_perfis, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=perfil.keys())
                    if not arquivo_existe:
                        writer.writeheader()
                    writer.writerow(perfil)
                
                st.session_state.questionario_concluido = True
                st.rerun()

# ==========================================
# TELA 2: Análise e Identificação de Picos
# ==========================================
else:
    st.title("🎯 Challenge: Lorentzian Peak Identification")
    
    st.markdown(f"**Researcher (Anonymous ID):** `{st.session_state.hash_pesquisador}`")
    
    if st.button("Logout / New User"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("""
    **Instructions:**
    1. Navigate through the graph below.
    2. **Click directly on the curve** where you identify a peak. A red line will appear.
    3. Once you have marked all peaks for this spectrum, click on **Submit Answers**.
    """)

    col1, col2 = st.columns([1, 2])
    with col1:
        espectro_selecionado = st.selectbox("Select the Spectrum:", range(total_espectros))

    if espectro_selecionado != st.session_state.espectro_atual:
        st.session_state.espectro_atual = espectro_selecionado
        st.session_state.picos_marcados = set()
        st.rerun()

    espectro_y = dados_ruidosos[espectro_selecionado]

    fig = go.Figure()
    
    # 1. Aumentamos o tamanho (size=8) e opacidade dos marcadores para facilitar o clique
    fig.add_trace(go.Scatter(
        x=eixo_x, y=np.real(espectro_y),
        mode='lines+markers', 
        marker=dict(size=8, opacity=0.4), 
        name='Real Part', 
        line=dict(color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=eixo_x, y=np.imag(espectro_y),
        mode='lines', 
        name='Imaginary Part', 
        line=dict(color='#ff7f0e', dash='dot')
    ))

    # Desenha as linhas dos picos já marcados
    for pico_x in st.session_state.picos_marcados:
        fig.add_vline(x=pico_x, line_width=2, line_dash="dash", line_color="red")

    # ==========================================
    # CORREÇÃO CRUCIAL AQUI
    # ==========================================
    fig.update_layout(
        title=f"Spectrum {espectro_selecionado}",
        xaxis_title="X-Axis", yaxis_title="Intensity",
        hovermode="closest", # <--- Alterado de 'x unified' para 'closest'
        dragmode="zoom", 
        clickmode="event+select"
    )

    evento_grafico = st.plotly_chart(
        fig, 
        use_container_width=True, 
        on_select="rerun", 
        selection_mode="points", # Mantém a ordem para aceitar cliques em pontos
        key=f"grafico_espectro_{espectro_selecionado}"
    )

    # Lógica de extração segura dos cliques
    if evento_grafico and len(evento_grafico.selection.points) > 0:
        teve_mudanca = False
        for ponto in evento_grafico.selection.points:
            x_val = ponto["x"]
            if x_val not in st.session_state.picos_marcados:
                st.session_state.picos_marcados.add(x_val)
                teve_mudanca = True
                
        if teve_mudanca:
            st.rerun()

    # ==========================================
    st.subheader("Summary of your Analysis")
    picos_ordenados = sorted(list(st.session_state.picos_marcados))
    
    if picos_ordenados:
        st.write("Visually marked positions:", [round(p, 2) for p in picos_ordenados])
    else:
        st.info("Click on the graph to mark the peaks.")

    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        if st.button("🗑️ Clear All"):
            st.session_state.picos_marcados = set()
            st.rerun()

    with col_btn2:
        if st.button("✅ Submit Answers"):
            if not picos_ordenados:
                st.warning("You haven't marked any peaks!")
            else:
                resposta = {
                    "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "hash_pesquisador": st.session_state.hash_pesquisador, 
                    "espectro_id": espectro_selecionado,
                    "qtd_picos": len(picos_ordenados),
                    "valores_x": str([round(p, 3) for p in picos_ordenados])
                }
                
                arquivo_respostas = "coleta_pesquisadores.csv"
                arquivo_existe = os.path.isfile(arquivo_respostas)
                with open(arquivo_respostas, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=resposta.keys())
                    if not arquivo_existe:
                        writer.writeheader()
                    writer.writerow(resposta)
                    
                st.success(f"Excellent! Answers for Spectrum {espectro_selecionado} saved successfully.")
                st.session_state.picos_marcados = set()
                st.rerun()