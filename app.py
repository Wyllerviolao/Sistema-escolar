import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import date, datetime, timedelta
import calendar
import sqlite3

from database import SessionLocal, engine, Base
from models import Turma, Aluno, Usuario, Nota, FrequenciaDiaria, CalendarioEscolar, DisciplinaEscola, EventoCalendario, RegistroConteudo, GradeHorario

# Inicializa/atualiza as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Correções preventivas e seguras para garantir colunas na base existente
def garantir_colunas_banco():
    colunas_necessarias = [
        ("status", "TEXT DEFAULT 'Ativo'"),
        ("nome_mae", "TEXT"),
        ("cpf", "TEXT"),
        ("raca_cor", "TEXT"),
        ("nis", "TEXT"),
        ("professor_nome", "TEXT")
    ]
    try:
        conn = sqlite3.connect("escola.db")
        cursor = conn.cursor()
        for col_nome, col_tipo in colunas_necessarias:
            try:
                cursor.execute(f"ALTER TABLE alunos ADD COLUMN {col_nome} {col_tipo};")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute(f"ALTER TABLE registros_conteudo ADD COLUMN {col_nome} {col_tipo};")
                conn.commit()
            except sqlite3.OperationalError:
                pass
        conn.close()
    except:
        pass

garantir_colunas_banco()

# Função dinâmica para obter a lista de disciplinas cadastradas na base
def obter_lista_disciplinas():
    db = SessionLocal()
    try:
        regs = db.query(DisciplinaEscola).order_by(DisciplinaEscola.nome).all()
        if not regs:
            padroes = [
                "Filosofia", "Projeto de Vida", "Língua Portuguesa", "Matemática", 
                "História", "Geografia", "Biologia", "Física", "Química", 
                "Educação Física", "Arte", "Inglês", "Sociologia"
            ]
            for p in padroes:
                db.add(DisciplinaEscola(nome=p))
            db.commit()
            regs = db.query(DisciplinaEscola).order_by(DisciplinaEscola.nome).all()
        return [r.nome for r in regs]
    except:
        return [
            "Filosofia", "Projeto de Vida", "Língua Portuguesa", "Matemática", 
            "História", "Geografia", "Biologia", "Física", "Química", 
            "Educação Física", "Arte", "Inglês", "Sociologia"
        ]
    finally:
        db.close()

TODAS_DISCIPLINAS = obter_lista_disciplinas()

# Configuração da página
st.set_page_config(
    page_title="SIGES - Sistema Integrado de Gestão Escolar",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS refinada + Trava de Tradução
st.markdown("""
    <head>
        <meta name="google" content="notranslate">
    </head>
    <style>
    html, body, .stApp {
        -webkit-translate: no !important;
        -moz-translate: no !important;
        -ms-translate: no !important;
        translate: no !important;
    }

    /* Mantém o cabeçalho visível no telemóvel para o botão da barra lateral aparecer */
    @media (max-width: 768px) {
        [data-testid="stHeader"], .stAppHeader, header {
            display: block !important;
            background-color: transparent !important;
        }
    }

    /* No computador, continua a ocultar se preferir o visual limpo */
    @media (min-width: 769px) {
        [data-testid="stHeader"], .stAppHeader, header {
            display: none !important;
            height: 0px !important;
        }
    }

    [data-testid="stsidebar"] {
        min-width: 16rem !important;
        max-width: 16rem !important;
    }

    .block-container {
        padding-top: 0.3rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    </style>
            padding-bottom: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        section[data-testid="stSidebar"] div.element-container {
            margin-bottom: 0.1rem !important;
        }
        section[data-testid="stSidebar"] hr {
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
        }
        div.stButton > button {
            width: 100% !important;
            min-width: 26px !important;
            height: 25px !important;
            padding: 0px !important;
            font-size: 13px !important;
            font-weight: bold !important;
            line-height: 23px !important;
            border-radius: 3px !important;
            border: 1px solid #d0d0d0 !important;
            margin: 0px !important;
        }
        div[data-testid="column"] {
            text-align: center !important;
            padding: 0px 1px !important;
        }
        div[data-testid="column"] p {
            margin: 0px !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
        }
        .nome-aluno-box {
            font-size: 0.78rem !important;
            font-weight: bold !important;
            text-align: left !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            white-space: normal !important;
            line-height: 1.1 !important;
            padding-right: 2px !important;
        }
        .nome-aluno-inativo {
            font-size: 0.75rem !important;
            font-weight: bold !important;
            color: #856404 !important;
            background-color: #fff3cd !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
            text-align: left !important;
            line-height: 1.1 !important;
        }
        .msg-sucesso-block {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 10px 14px !important;
            background-color: #d1e7dd !important;
            color: #0f5132 !important;
            border: 1px solid #badbcc !important;
            border-radius: 8px !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            margin-top: 10px !important;
            width: 100% !important;
            text-align: center !important;
        }
        .welcome-card {
            background-color: #f8f9fa;
            border-left: 5px solid #0d6efd;
            padding: 1.5rem;
            border-radius: 6px;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        .footer-manual {
            text-align: center;
            margin-top: 3rem;
            padding: 1rem;
            border-top: 1px solid #eaeaea;
            color: #6c757d;
            font-size: 0.9rem;
        }
    </style>
""", unsafe_allow_html=True)

# Funções auxiliares
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def gerar_hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha: str, senha_hash: str) -> bool:
    return gerar_hash_senha(senha) == senha_hash

def garantir_usuario_especifico(email_alvo, nome_alvo, perfil_alvo):
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.email == email_alvo.lower()).first()
        if not user:
            novo_user = Usuario(
                nome=nome_alvo,
                email=email_alvo.lower(),
                senha_hash=gerar_hash_senha("123"),
                perfil=perfil_alvo
            )
            db.add(novo_user)
            db.commit()
            db.refresh(novo_user)
            return novo_user
        else:
            return user
    except Exception as e:
        db.rollback()
        return None
    finally:
        db.close()

def inicializar_calendario_padrao():
    db = SessionLocal()
    try:
        qtd = db.query(CalendarioEscolar).filter(CalendarioEscolar.ano_letivo == 2027).count()
        if qtd == 0:
            c1 = CalendarioEscolar(ano_letivo=2027, trimestre="1º Trimestre", data_inicio=date(2027, 2, 1), data_fim=date(2027, 5, 14))
            c2 = CalendarioEscolar(ano_letivo=2027, trimestre="2º Trimestre", data_inicio=date(2027, 5, 17), data_fim=date(2027, 8, 27))
            c3 = CalendarioEscolar(ano_letivo=2027, trimestre="3º Trimestre", data_inicio=date(2027, 8, 30), data_fim=date(2027, 12, 17))
            db.add_all([c1, c2, c3])
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

def sum_trim_simples_isolado(db, aluno_id, disciplina, trimestre_nome):
    notas_reg = db.query(Nota).filter(
        Nota.aluno_id == aluno_id,
        Nota.disciplina == disciplina,
        Nota.trimestre.like(f"{trimestre_nome}%")
    ).all()
    soma_reg = 0.0
    for idx_n in range(1, 5):
        val_n = next((n.valor_nota for n in notas_reg if n.trimestre == f"{trimestre_nome}_N{idx_n}" and n.valor_nota is not None), None)
        val_rp = next((n.valor_nota for n in notas_reg if n.trimestre == f"{trimestre_nome}_RP{idx_n}" and n.valor_nota is not None), None)
        soma_reg += max(float(val_n) if val_n is not None else 0.0, float(val_rp) if val_rp is not None else 0.0)
    val_rt = next((n.valor_nota for n in notas_reg if n.trimestre == f"{trimestre_nome}_RecTrim" and n.valor_nota is not None), 0.0)
    return max(soma_reg, float(val_rt))

def sum_trim_simples(db, aluno_id, disciplina, trimestre_nome):
    notas_reg = db.query(Nota).filter(
        Nota.aluno_id == aluno_id,
        Nota.disciplina == disciplina,
        Nota.trimestre.like(f"{trimestre_nome}%")
    ).all()
    soma_reg = 0.0
    for idx_n in range(1, 5):
        val_n = next((n.valor_nota for n in notas_reg if n.trimestre == f"{trimestre_nome}_N{idx_n}" and n.valor_nota is not None), None)
        val_rp = next((n.valor_nota for n in notas_reg if n.trimestre == f"{trimestre_nome}_RP{idx_n}" and n.valor_nota is not None), None)
        soma_reg += max(float(val_n) if val_n is not None else 0.0, float(val_rp) if val_rp is not None else 0.0)
    
    if trimestre_nome != "3º Trimestre":
        val_rt = next((n.valor_nota for n in notas_reg if n.trimestre == f"{trimestre_nome}_RecTrim" and n.valor_nota is not None), 0.0)
        return max(soma_reg, float(val_rt))
    else:
        reg_rf = next((n for n in notas_reg if n.trimestre == "Rec_Final" and n.valor_nota is not None), None)
        if reg_rf:
            t1 = sum_trim_simples_isolado(db, aluno_id, disciplina, "1º Trimestre")
            t2 = sum_trim_simples_isolado(db, aluno_id, disciplina, "2º Trimestre")
            soma_parcial = t1 + t2 + soma_reg
            if float(reg_rf.valor_nota) > soma_parcial:
                return max(0.0, float(reg_rf.valor_nota) - t1 - t2)
        return soma_reg

def calcular_total_trimestral_aluno(db, aluno_id, disciplina, trimestre_nome):
    return sum_trim_simples(db, aluno_id, disciplina, trimestre_nome)

garantir_usuario_especifico("secretaria@escola.gov.br", "Secretaria Escolar", "secretaria")
garantir_usuario_especifico("pedagogico@escola.gov.br", "Coordenação Pedagógica", "pedagogico")
garantir_usuario_especifico("professor@escola.gov.br", "Prof. Wyller", "professor")
inicializar_calendario_padrao()

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if "estado_pauta" not in st.session_state:
    st.session_state.estado_pauta = {}

if "msg_sucesso_freq" not in st.session_state:
    st.session_state.msg_sucesso_freq = False

if "msg_sucesso_notas" not in st.session_state:
    st.session_state.msg_sucesso_notas = False

if "msg_sucesso_hist_sec" not in st.session_state:
    st.session_state.msg_sucesso_hist_sec = False

if "msg_sucesso_freq_sec" not in st.session_state:
    st.session_state.msg_sucesso_freq_sec = False

if "msg_sucesso_usuario" not in st.session_state:
    st.session_state.msg_sucesso_usuario = ""

if "msg_sucesso_novo_usuario" not in st.session_state:
    st.session_state.msg_sucesso_novo_usuario = ""

# ==========================================
# TELA DE LOGIN DINÂMICA
# ==========================================
if st.session_state.usuario_logado is None:
    st.markdown("<h2 style='text-align: center; margin:0px; padding-top:0px;'>📚 SIGES - SISTEMA INTEGRADO DE GESTÃO ESCOLAR</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin: 0px; font-weight: bold; color: #555;'>CEAPA - CENTRO EDUCACIONAL APRENDER, PENSAR E AGIR</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Selecione o seu perfil para acessar.</p>", unsafe_allow_html=True)

    db = next(get_db())
    usuarios_cadastrados = db.query(Usuario).order_by(Usuario.nome).all()
    db.close()
    mapa_usuarios = {f"{u.nome} ({u.email})": u for u in usuarios_cadastrados}
    opcoes_perfis = list(mapa_usuarios.keys()) + ["Outro Usuário (Digitar e-mail)"]

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        perfil_login_sel = st.selectbox("👤 Selecione o Perfil/Usuário para Entrar:", opcoes_perfis)

        if perfil_login_sel != "Outro Usuário (Digitar e-mail)":
            usr_obj = mapa_usuarios[perfil_login_sel]
            email_padrao = usr_obj.email
            senha_padrao = "123"
        else:
            email_padrao = ""
            senha_padrao = ""

        with st.form("form_login"):
            st.subheader("🔑 Autenticação")
            email_input = st.text_input("E-mail do Usuário", value=email_padrao)
            senha_input = st.text_input("Senha", type="password", value=senha_padrao)
            btn_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)

            if btn_entrar:
                db = SessionLocal()
                usuario = db.query(Usuario).filter(Usuario.email == email_input.strip().lower()).first()
                db.close()

                if usuario and verificar_senha(senha_input.strip(), usuario.senha_hash):
                    st.session_state.usuario_logado = {
                        "id": usuario.id,
                        "nome": usuario.nome,
                        "email": usuario.email,
                        "perfil": usuario.perfil
                    }
                    st.success(f"Bem-vindo(a), {usuario.nome}!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas. Verifique o e-mail e a senha.")

# ==========================================
# SISTEMA PRINCIPAL (AUTENTICADO)
# ==========================================
else:
    user = st.session_state.usuario_logado

    # BARRA LATERAL
    st.sidebar.markdown(f"### 👤 {user['nome']}")
    st.sidebar.caption(f"Perfil: **{user['perfil'].upper()}**")
    
    if st.sidebar.button("🚪 Sair / Trocar Perfil", use_container_width=True):
        st.session_state.usuario_logado = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### 🧭 Navegação")
    
    if user["perfil"] == "secretaria":
        menu = st.sidebar.selectbox(
            "Selecione o Módulo",
            [
                "📌 Painel Principal", 
                "Gestão de Turmas", 
                "Alunos e Matrículas", 
                "🗓️ Grade de Horários da Escola",
                "Calendário Escolar / Trimestres", 
                "🗓️ Calendário e Bloqueios", 
                "Lançamento/Auditoria de Notas", 
                "Gestão de Usuários e Senhas", 
                "📄 Relatórios e Documentos Emitidos", 
                "🔑 Alterar Minha Senha"
            ]
        )
    elif user["perfil"] == "pedagogico":
        menu = st.sidebar.selectbox(
            "Selecione o Módulo",
            [
                "📌 Painel Principal", 
                "Acompanhamento Pedagógico", 
                "Auditoria de Notas e Frequência", 
                "📄 Relatórios e Documentos Emitidos", 
                "🔑 Alterar Minha Senha"
            ]
        )
    elif user["perfil"] == "professor":
        menu = st.sidebar.selectbox(
            "Selecione o Módulo",
            [
                "📌 Painel Principal", 
                "Pauta de Frequência Diária", 
                "Registro de Conteúdo / Aulas", 
                "Lançamento de Notas", 
                "📄 Relatórios e Documentos Emitidos", 
                "🔑 Alterar Minha Senha"
            ]
        )
    else:
        menu = st.sidebar.selectbox("Selecione o Módulo", ["📌 Painel Principal", "🔑 Alterar Minha Senha"])

    # Cabeçalho limpo na tela principal
    st.markdown("<h3 style='margin:0px; padding-top:0px;'>📚 SIGES - Sistema Integrado de Gestão Escolar</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 3px 0px;'>", unsafe_allow_html=True)

    def obter_turmas_e_disciplinas_professor(db_sessao, turma_id_alvo=None):
        todas_t = db_sessao.query(Turma).all()
        disciplinas_atuais = obter_lista_disciplinas()
        if user["perfil"] in ["secretaria", "pedagogico"]:
            return todas_t, disciplinas_atuais

        usr_obj = db_sessao.query(Usuario).filter(Usuario.id == user["id"]).first()
        
        mapa_disc = {}
        if usr_obj and usr_obj.disciplinas_turmas:
            try:
                mapa_disc = json.loads(usr_obj.disciplinas_turmas)
            except:
                mapa_disc = {}

        if usr_obj and usr_obj.turmas_permitidas:
            ids_permitidos = [int(i) for i in usr_obj.turmas_permitidas.split(",") if i.strip().isdigit()]
            t_filtradas = [t for t in todas_t if t.id in ids_permitidos]
            turmas_finais = t_filtradas if t_filtradas else todas_t
        else:
            turmas_finais = todas_t

        if turma_id_alvo:
            disc_permitidas = mapa_disc.get(str(turma_id_alvo), [])
            if not disc_permitidas:
                disc_permitidas = disciplinas_atuais
            return turmas_finais, disc_permitidas

        return turmas_finais, disciplinas_atuais

    # ==========================================
    # TELA DE ENTRADA LIMPA (PAINEL PRINCIPAL)
    # ==========================================
    if menu == "📌 Painel Principal":
        st.markdown(f"""
            <div class="welcome-card">
                <h3 style="margin: 0px; color: #0d6efd;">Olá, {user['nome']}!</h3>
                <p style="margin-top: 10px; color: #495057; font-size: 1.05rem; line-height: 1.5;">
                    Bem-vindo ao <b>SIGES 2027</b> — Sistema Integrado de Gestão Escolar.<br>
                    Utilize o menu lateral em <b>Navegação</b> para selecionar o módulo desejado.
                </p>
            </div>
        """, unsafe_allow_html=True)

        db_est = next(get_db())
        t_turmas = db_est.query(Turma).count()
        t_usuarios = db_est.query(Usuario).count()

        st.markdown("##### 📊 Indicadores do Sistema")
        
        if user["perfil"] == "professor":
            turmas_prof, _ = obter_turmas_e_disciplinas_professor(db_est)
            qtd_turmas_prof = len(turmas_prof)
            
            ids_turmas_prof = [t.id for t in turmas_prof]
            total_alunos_prof = db_est.query(Aluno).filter(
                Aluno.turma_id.in_(ids_turmas_prof),
                Aluno.status == "Ativo",
                Aluno.nome != "", 
                Aluno.nome != None
            ).count() if ids_turmas_prof else 0

            col_m1, col_m2 = st.columns(2)
            col_m1.metric("🏫 Suas Turmas", qtd_turmas_prof)
            col_m2.metric("👨‍🎓 Total de Alunos", total_alunos_prof)

        elif user["perfil"] == "secretaria":
            turmas_todas = db_est.query(Turma).all()
            total_geral_turmas = len(turmas_todas)
            turnos_lista = ["Matutino", "Vespertino", "Noturno", "Integral"]
            
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("🏫 Total Geral de Turmas", total_geral_turmas)
            col_s2.metric("👥 Total de Usuários", t_usuarios)
            
            total_alunos_ativos_geral = db_est.query(Aluno).filter(Aluno.status == "Ativo", Aluno.nome != "", Aluno.nome != None).count()
            col_s3.metric("👨‍🎓 Total Geral de Alunos Ativos", total_alunos_ativos_geral)

            st.markdown("---")
            st.markdown("###### 🕒 Detalhamento por Turno")
            
            cols_turno = st.columns(len(turnos_lista))
            for idx, turno in enumerate(turnos_lista):
                t_turno_count = sum(1 for t in turmas_todas if t.turno == turno)
                ids_t_turno = [t.id for t in turmas_todas if t.turno == turno]
                a_turno_count = db_est.query(Aluno).filter(
                    Aluno.turma_id.in_(ids_t_turno), 
                    Aluno.status == "Ativo",
                    Aluno.nome != "", Aluno.nome != None
                ).count() if ids_t_turno else 0

                with cols_turno[idx]:
                    st.metric(f"Turno: {turno}", f"{t_turno_count} turmas", f"{a_turno_count} alunos ativos")

        elif user["perfil"] == "pedagogico":
            t_alunos_geral = db_est.query(Aluno).filter(Aluno.status == "Ativo", Aluno.nome != "", Aluno.nome != None).count()
            qtd_risco_nota = 0
            qtd_risco_falta = 0
            
            perc_risco_nota = (qtd_risco_nota / t_alunos_geral * 100) if t_alunos_geral > 0 else 0.0
            perc_risco_falta = (qtd_risco_falta / t_alunos_geral * 100) if t_alunos_geral > 0 else 0.0

            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            col_p1.metric("🏫 Total de Turmas", t_turmas)
            col_p2.metric("👨‍🎓 Alunos Matriculados", t_alunos_geral)
            col_p3.metric("⚠️ Risco de Rendimento", f"{qtd_risco_nota} alunos", delta=f"{perc_risco_nota:.1f}% do total", delta_color="inverse")
            col_p4.metric("🚨 Risco de Frequência", f"{qtd_risco_falta} alunos", delta=f"{perc_risco_falta:.1f}% do total", delta_color="inverse")

        else:
            t_alunos_geral = db_est.query(Aluno).filter(Aluno.status == "Ativo", Aluno.nome != "", Aluno.nome != None).count()
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("🏫 Total de Turmas", t_turmas)
            col_m2.metric("👨‍🎓 Total de Alunos", t_alunos_geral)
            col_m3.metric("👤 Usuários Cadastrados", t_usuarios)
            
        db_est.close()

        # Rodapé com Manual de Uso segmentado estritamente por perfil
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📖 Manual de Uso do Sistema (Clique para abrir)"):
            if user["perfil"] == "secretaria":
                st.markdown("""
                ### 🏛️ Manual Operacional — Perfil Secretaria
                * **Gestão de Turmas:** Cadastre novas turmas informando nome, turno e ano letivo. Também é possível editar ou excluir turmas existentes.
                * **Alunos e Matrículas:** Realize novas matrículas preenchendo os dados do aluno, responsável, raça/cor e Bolsa Família (NIS). Utilize a aba de remanejamento para transferir alunos entre turmas preservando histórico.
                * **Grade de Horários da Escola:** Configure a matriz semanal de aulas por turma selecionando o dia da semana, disciplina, professor e as aulas correspondentes de forma rápida.
                * **Calendário Escolar / Trimestres:** Defina as datas de início e término do 1º, 2º e 3º Trimestres letivos.
                * **Calendário e Bloqueios:** Cadastre feriados, recessos, JPP ou conselhos de classe. Dias marcados com bloqueio impedem lançamentos indevidos na pauta.
                * **Lançamento/Auditoria de Notas:** Audite notas gerais, lance históricos de alunos transferidos ou realize abonos e ajustes de frequência.
                * **Gestão de Usuários e Senhas:** Cadastre professores, configure as turmas e disciplinas permitidas para cada docente, ou gerencie as disciplinas oficiais da escola.
                * **Relatórios:** Emite atas de conselho, boletins escolares completos, busca ativa de faltas e lista nominal.
                """)
            elif user["perfil"] == "professor":
                st.markdown("""
                ### 👨‍🏫 Manual Operacional — Perfil Professor(a)
                * **Pauta de Frequência Diária:** Selecione sua turma, disciplina, trimestre e mês. A pauta exibirá **apenas os dias da semana em que possui aulas**, conforme a grade cadastrada. Clique nos botões de presença (`.`) para alternar faltas (`F`).
                * **Registro de Conteúdo / Aulas (Diário de Classe):** Informe a data, quantidade de aulas, objeto de conhecimento e o conteúdo detalhado trabalhado.
                * **Lançamento de Notas:** Insira as notas parciais (N1 a N4), recuperações paralelas (RP1 a RP4) e recuperação trimestral/final de forma rápida e segura.
                * **Relatórios Emitidos:** Visualize e imprima o **Relatório de Conteúdo Ministrado (Diário de Classe)** segmentado por trimestre.
                """)
            elif user["perfil"] == "pedagogico":
                st.markdown("""
                ### 📊 Manual Operacional — Perfil Coordenação Pedagógica
                * **Acompanhamento Pedagógico:** Monitore o desempenho geral das turmas e o andamento dos diários de classe.
                * **Auditoria:** Verifique índices de rendimento e alinhamento das frequências e conteúdos lançados pelos docentes.
                * **Relatórios:** Emita boletins, relatórios de busca ativa e atas para apoiar intervenções pedagógicas e reuniões de conselho de classe.
                """)
            else:
                st.markdown("""
                ### 📋 Manual Operacional Geral
                * Utilize o menu lateral para navegar entre os módulos liberados para o seu perfil de acesso.
                """)

        st.markdown("""
            <div class="footer-manual">
                SIGES 2027 — Centro Educacional Aprender, Pensar e Agir (CEAPA) &bull; Desenvolvido para Gestão Escolar Integrada
            </div>
        """, unsafe_allow_html=True)

    elif menu == "🔑 Alterar Minha Senha":
        st.subheader("🔑 Alterar Minha Senha Pessoal")
        st.caption(f"Usuário: **{user['nome']}** (`{user['email']}`)")

        with st.form("form_troca_senha_pessoal", clear_on_submit=True):
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha", type="password")
            confirma_senha = st.text_input("Confirme a Nova Senha", type="password")

            btn_salvar_minha_senha = st.form_submit_button("🔒 Atualizar Senha", use_container_width=True)

            if btn_salvar_minha_senha:
                if not senha_atual or not nova_senha or not confirma_senha:
                    st.warning("Preencha todos os campos do formulário.")
                elif nova_senha != confirma_senha:
                    st.error("A nova senha e a confirmação não coincidem.")
                else:
                    db = next(get_db())
                    usr_db = db.query(Usuario).filter(Usuario.id == user["id"]).first()
                    
                    if not verificar_senha(senha_atual, usr_db.senha_hash):
                        st.error("A senha atual informada está incorreta.")
                    else:
                        usr_db.senha_hash = gerar_hash_senha(nova_senha)
                        db.commit()
                        st.success("Sua senha foi alterada com sucesso!")
                    db.close()

    # ==========================================
    # MÓDULOS DA SECRETARIA ESCOLAR
    # ==========================================
    elif menu == "Gestão de Turmas":
        st.subheader("🏫 Gestão de Turmas Escolares")
        
        db = next(get_db())
        aba_cad_t, aba_edit_t = st.tabs(["➕ Nova Turma", "✏️ Editar / Excluir"])

        with aba_cad_t:
            col_t1, col_t2 = st.columns([1, 2])
            with col_t1:
                with st.form("form_nova_turma", clear_on_submit=True):
                    nome_turma = st.text_input("Nome da Turma (Ex: 1ª M01)")
                    turno_turma = st.selectbox("Turno", ["Matutino", "Vespertino", "Noturno", "Integral"])
                    ano_letivo = st.number_input("Ano Letivo", min_value=2024, max_value=2030, value=2027)
                    btn_cad_turma = st.form_submit_button("Cadastrar Turma", use_container_width=True)
                    
                    if btn_cad_turma:
                        if not nome_turma.strip():
                            st.warning("Informe o nome da turma.")
                        else:
                            nova_t = Turma(nome=nome_turma.strip().upper(), turno=turno_turma, ano_letivo=ano_letivo)
                            db.add(nova_t)
                            db.commit()
                            st.success(f"Turma '{nome_turma.upper()}' cadastrada com sucesso!")
                            st.rerun()

            with col_t2:
                st.markdown("##### 📋 Turmas Cadastradas")
                turmas_list = db.query(Turma).all()
                if not turmas_list:
                    st.info("Nenhuma turma cadastrada até o momento.")
                else:
                    dados_t = []
                    for t in turmas_list:
                        total_alunos = db.query(Aluno).filter(Aluno.turma_id == t.id, Aluno.status == "Ativo", Aluno.nome != "", Aluno.nome != None).count()
                        dados_t.append({
                            "ID": t.id,
                            "Nome da Turma": t.nome,
                            "Turno": t.turno,
                            "Ano Letivo": t.ano_letivo,
                            "Alunos Ativos": total_alunos
                        })
                    st.dataframe(pd.DataFrame(dados_t), use_container_width=True, hide_index=True)

        with aba_edit_t:
            turmas_list_edit = db.query(Turma).all()
            if not turmas_list_edit:
                st.info("Nenhuma turma disponível para edição.")
            else:
                mapa_t_edit = {f"{t.nome} ({t.turno}) - {t.ano_letivo}": t for t in turmas_list_edit}
                turma_sel_edit_nome = st.selectbox("🔍 Selecione a Turma para Editar ou Excluir:", list(mapa_t_edit.keys()))
                turma_edit_obj = mapa_t_edit[turma_sel_edit_nome]

                col_e_form, col_del_t = st.columns([2.5, 1])

                with col_e_form:
                    with st.form("form_editar_turma"):
                        col_e1, col_e2, col_e3 = st.columns(3)
                        with col_e1:
                            novo_nome_t = st.text_input("Nome da Turma", value=turma_edit_obj.nome)
                        with col_e2:
                            turnos_ops = ["Matutino", "Vespertino", "Noturno", "Integral"]
                            idx_turno = turnos_ops.index(turma_edit_obj.turno) if turma_edit_obj.turno in turnos_ops else 0
                            novo_turno_t = st.selectbox("Turno", turnos_ops, index=idx_turno)
                        with col_e3:
                            novo_ano_t = st.number_input("Ano Letivo", min_value=2024, max_value=2030, value=turma_edit_obj.ano_letivo)

                        btn_salvar_t = st.form_submit_button("✏️ Salvar Alterações da Turma", use_container_width=True)

                        if btn_salvar_t:
                            try:
                                turma_edit_obj.nome = novo_nome_t.strip().upper()
                                turma_edit_obj.turno = novo_turno_t
                                turma_edit_obj.ano_letivo = novo_ano_t
                                db.commit()
                                st.success("Turma atualizada com sucesso!")
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao atualizar turma: {e}")

                with col_del_t:
                    st.markdown("##### 🗑️ Excluir Turma")
                    st.warning(f"Atenção: A exclusão removerá **{turma_edit_obj.nome}**.")
                    if st.button("🗑️ Confirmar Exclusão de Turma", use_container_width=True, key=f"btn_del_turma_{turma_edit_obj.id}"):
                        try:
                            db.delete(turma_edit_obj)
                            db.commit()
                            st.success("Turma excluída com sucesso!")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Erro ao excluir turma: {e}")

        db.close()

    elif menu == "Alunos e Matrículas":
        st.subheader("👨‍🎓 Gestão, Matrícula, Edição, Remanejamento e Transferência de Alunos")
        
        db = next(get_db())
        
        try:
            db.query(Aluno).filter((Aluno.nome == None) | (Aluno.nome == "")).delete(synchronize_session=False)
            db.commit()
        except:
            db.rollback()

        turmas = db.query(Turma).all()
        
        if not turmas:
            st.warning("Cadastre primeiro ao menos uma turma para matricular alunos.")
            db.close()
        else:
            mapa_turmas = {f"{t.nome} ({t.turno})": t.id for t in turmas}
            
            aba_cad, aba_edit, aba_reman = st.tabs(["➕ Cadastrar Novo Aluno", "✏️ Editar / Excluir", "🔄 Remanejamento / Transferência"])
            
            with aba_cad:
                col_b1, _, _ = st.columns(3)
                with col_b1:
                    bolsa_familia_op = st.radio("Beneficiário do Bolsa Família?", ["Não", "Sim"], horizontal=True, key="bolsa_familia_radio")

                with st.form("form_novo_aluno_completo", clear_on_submit=True):
                    col_c1, col_c2, col_c3 = st.columns(3)
                    with col_c1:
                        nome_aluno = st.text_input("Nome Completo do Aluno *")
                        data_nasc = st.date_input("Data de Nascimento", value=date(2010, 1, 1), format="DD/MM/YYYY")
                        turma_alvo = st.selectbox("Turma para Matrícula *", list(mapa_turmas.keys()))
                    with col_c2:
                        matricula_aluno = st.text_input("Número de Matrícula (Ex: 20270101)")
                        cpf_aluno = st.text_input("CPF do Aluno")
                        raca_cor = st.selectbox("Raça / Cor", ["Branca", "Parda", "Preta", "Amarela", "Indígena", "Não Declarada"])
                    with col_c3:
                        nis_aluno = st.text_input(
                            "Número do NIS", 
                            placeholder="Digite o NIS..." if bolsa_familia_op == "Sim" else "Apenas Bolsa Família",
                            disabled=(bolsa_familia_op == "Não")
                        )
                        nome_mae = st.text_input("Nome da Mãe / Responsável Legal")

                    btn_cad_aluno = st.form_submit_button("💾 Realizar Matrícula do Aluno", use_container_width=True)
                    
                    if btn_cad_aluno:
                        if not nome_aluno.strip():
                            st.warning("Informe o nome completo do aluno.")
                        else:
                            try:
                                novo_a = Aluno(
                                    nome=nome_aluno.strip().upper(),
                                    matricula=matricula_aluno.strip() if matricula_aluno else None,
                                    nome_mae=nome_mae.strip() if nome_mae else None,
                                    cpf=cpf_aluno.strip() if cpf_aluno else None,
                                    raca_cor=raca_cor,
                                    nis=nis_aluno.strip() if nis_aluno and bolsa_familia_op == "Sim" else None,
                                    status="Ativo",
                                    turma_id=mapa_turmas[turma_alvo]
                                )
                                db.add(novo_a)
                                db.commit()
                                st.success(f"Aluno(a) '{nome_aluno.upper()}' matriculado(a) com sucesso!")
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao cadastrar aluno: {e}")

            with aba_edit:
                todos_alunos = db.query(Aluno).filter(Aluno.nome != "", Aluno.nome != None).order_by(Aluno.nome).all()
                if not todos_alunos:
                    st.info("Nenhum aluno disponível para edição.")
                else:
                    mapa_alunos_edit = {f"{a.nome} (Mat: {a.matricula or 'S/N'} - Status: {a.status})": a for a in todos_alunos}
                    aluno_sel_nome = st.selectbox("🔍 Selecione o Aluno para Editar ou Excluir:", list(mapa_alunos_edit.keys()))
                    aluno_obj = mapa_alunos_edit[aluno_sel_nome]

                    idx_turma_atual = list(mapa_turmas.values()).index(aluno_obj.turma_id) if aluno_obj.turma_id in mapa_turmas.values() else 0

                    col_edit_form, col_del_form = st.columns([2.5, 1])

                    with col_edit_form:
                        with st.form("form_editar_aluno"):
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                novo_nome_e = st.text_input("Nome Completo do Aluno", value=aluno_obj.nome)
                                nova_mat_e = st.text_input("Número de Matrícula", value=aluno_obj.matricula or "")
                                novo_resp_e = st.text_input("Nome da Mãe / Responsável Legal", value=getattr(aluno_obj, 'nome_mae', '') or "")
                                novo_cpf_e = st.text_input("CPF do Aluno", value=getattr(aluno_obj, 'cpf', '') or "")
                            with col_e2:
                                nova_turma_e = st.selectbox("Turma", list(mapa_turmas.keys()), index=idx_turma_atual)
                                status_ops = ["Ativo", "Inativo (Remanejado)", "Inativo (Transferido)"]
                                idx_st = status_ops.index(aluno_obj.status) if aluno_obj.status in status_ops else 0
                                novo_status_e = st.selectbox("Status do Aluno", status_ops, index=idx_st)
                                novo_nis_e = st.text_input("Número do NIS", value=getattr(aluno_obj, 'nis', '') or "")

                            btn_salvar_edit = st.form_submit_button("✏️ Salvar Alterações do Aluno", use_container_width=True)

                            if btn_salvar_edit:
                                if not novo_nome_e.strip():
                                    st.error("⚠️ O nome do aluno não pode ficar em branco!")
                                else:
                                    try:
                                        aluno_obj.nome = novo_nome_e.strip().upper()
                                        aluno_obj.matricula = nova_mat_e.strip() if nova_mat_e.strip() else None
                                        aluno_obj.nome_mae = novo_resp_e.strip() if novo_resp_e.strip() else None
                                        aluno_obj.cpf = novo_cpf_e.strip() if novo_cpf_e.strip() else None
                                        aluno_obj.nis = novo_nis_e.strip() if novo_nis_e.strip() else None
                                        aluno_obj.turma_id = mapa_turmas[nova_turma_e]
                                        aluno_obj.status = novo_status_e
                                        db.commit()
                                        st.success(f"Cadastro do aluno '{aluno_obj.nome}' atualizado com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        db.rollback()
                                        st.error(f"Erro ao atualizar: {e}")

                    with col_del_form:
                        st.markdown("##### 🗑️ Excluir Aluno")
                        st.warning(f"Atenção: A exclusão removerá **{aluno_obj.nome}** permanentemente.")
                        if st.button("🗑️ Confirmar Exclusão", use_container_width=True, key=f"btn_del_aluno_{aluno_obj.id}"):
                            try:
                                db.delete(aluno_obj)
                                db.commit()
                                st.success("Aluno excluído com sucesso!")
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao excluir aluno: {e}")

            with aba_reman:
                st.markdown("##### 🔄 Remanejamento ou Transferência com Histórico na Turma de Origem")
                st.caption("Ao remanejar, o registro original na turma de origem é marcado automaticamente como **Inativo (Remanejado)** e um novo registro ativo é gerado na turma de destino.")

                alunos_ativos_reman = db.query(Aluno).filter(Aluno.status == "Ativo", Aluno.nome != "", Aluno.nome != None).order_by(Aluno.nome).all()
                if not alunos_ativos_reman:
                    st.info("Nenhum aluno ativo disponível para remanejamento.")
                else:
                    mapa_ativos_reman = {f"{a.nome} (Mat: {a.matricula or 'S/N'})": a for a in alunos_ativos_reman}
                    aluno_reman_sel = st.selectbox("🔍 Selecione o Aluno Ativo:", list(mapa_ativos_reman.keys()), key="sel_aluno_reman")
                    aluno_para_reman = mapa_ativos_reman[aluno_reman_sel]

                    turma_origem_obj = db.query(Turma).filter(Turma.id == aluno_para_reman.turma_id).first()
                    st.info(f"Turma atual de origem: **{turma_origem_obj.nome if turma_origem_obj else 'Desconhecida'}**")

                    tipo_movimento = st.radio("Tipo de Movimentação:", ["Remanejamento para outra Turma / Turno", "Transferência da Escola (Saída)"], horizontal=True)
                    
                    turma_destino_sel = st.selectbox("Turma de Destino (para Remanejamento):", list(mapa_turmas.keys()), disabled=(tipo_movimento.startswith("Transferência")))

                    if st.button("🚀 Processar Movimentação do Aluno", use_container_width=True):
                        try:
                            if tipo_movimento.startswith("Remanejamento"):
                                nova_turma_id = mapa_turmas[turma_destino_sel]
                                if nova_turma_id == aluno_para_reman.turma_id:
                                    st.warning("A turma de destino é a mesma turma de origem.")
                                else:
                                    aluno_para_reman.status = "Inativo (Remanejado)"
                                    
                                    novo_aluno_turma = Aluno(
                                        nome=aluno_para_reman.nome,
                                        matricula=aluno_para_reman.matricula,
                                        nome_mae=aluno_para_reman.nome_mae,
                                        cpf=aluno_para_reman.cpf,
                                        raca_cor=aluno_para_reman.raca_cor,
                                        nis=aluno_para_reman.nis,
                                        status="Ativo",
                                        turma_id=nova_turma_id
                                    )
                                    db.add(novo_aluno_turma)
                                    db.commit()
                                    st.success(f"Aluno remanejado com sucesso! O histórico foi preservado na turma de origem e o aluno ativado na nova turma.")
                                    st.rerun()
                            else:
                                aluno_para_reman.status = "Inativo (Transferido)"
                                db.commit()
                                st.success(f"Aluno marcado como Transferido/Inativo com sucesso!")
                                st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Erro na movimentação: {e}")

            st.markdown("---")
            st.markdown("##### 👥 Alunos Matriculados (Geral)")
            turma_filtro_nome = st.selectbox("Filtrar Exibição por Turma:", ["Todas as Turmas"] + list(mapa_turmas.keys()))
            
            query_alunos = db.query(Aluno).filter(Aluno.nome != "", Aluno.nome != None)
            if turma_filtro_nome != "Todas as Turmas":
                query_alunos = query_alunos.filter(Aluno.turma_id == mapa_turmas[turma_filtro_nome])
            
            alunos_list = query_alunos.order_by(Aluno.nome).all()
            
            if not alunos_list:
                st.info("Nenhum aluno encontrado.")
            else:
                dados_a = []
                for idx, a in enumerate(alunos_list):
                    t_obj = db.query(Turma).filter(Turma.id == a.turma_id).first()
                    dados_a.append({
                        "Nº": idx + 1,
                        "Nome do Aluno": a.nome,
                        "Matrícula": a.matricula or "S/N",
                        "Responsável": getattr(a, 'nome_mae', None) or "-",
                        "Turma": t_obj.nome if t_obj else "Sem Turma",
                        "Status": a.status
                    })
                st.dataframe(pd.DataFrame(dados_a), use_container_width=True, hide_index=True)
            db.close()

    elif menu == "🗓️ Grade de Horários da Escola":
        st.subheader("🗓️ Cadastrar / Atualizar Grade de Horários da Escola")
        st.caption("Selecione a turma, o dia da semana, a disciplina, o professor e marque de uma só vez as aulas correspondentes.")

        db = next(get_db())
        turmas_list = db.query(Turma).order_by(Turma.nome).all()

        if not turmas_list:
            st.warning("Cadastre primeiro ao menos uma turma para definir a grade de horários.")
            db.close()
        else:
            mapa_t_gh = {f"{t.nome} ({t.turno})": t for t in turmas_list}
            turma_gh_sel = st.selectbox("🏫 Selecione a Turma:", list(mapa_t_gh.keys()))
            turma_gh_obj = mapa_t_gh[turma_gh_sel]

            professores_db = db.query(Usuario).filter(Usuario.perfil == "professor").order_by(Usuario.nome).all()
            mapa_profs = {f"{p.nome} ({p.email})": p.id for p in professores_db}
            mapa_profs_op = {"Sem Professor Definido": None}
            mapa_profs_op.update(mapa_profs)

            mapa_dias_semana = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira"}

            st.markdown("---")
            aba_cad_gh, aba_ver_gh = st.tabs(["➕ Adicionar por Bloco Semanal", "📋 Visualizar Grade Atual"])

            with aba_cad_gh:
                with st.form("form_cad_horario_turma", clear_on_submit=True):
                    col_gh1, col_gh2, col_gh3 = st.columns(3)
                    with col_gh1:
                        dia_sem_sel = st.selectbox("🗓️ Dia da Semana:", list(mapa_dias_semana.values()))
                        dia_num = [k for k, v in mapa_dias_semana.items() if v == dia_sem_sel][0]
                    with col_gh2:
                        disc_gh_sel = st.selectbox("📖 Disciplina:", TODAS_DISCIPLINAS)
                    with col_gh3:
                        prof_gh_sel = st.selectbox("👨‍🏫 Professor Responsável:", list(mapa_profs_op.keys()))
                        prof_id_valor = mapa_profs_op[prof_gh_sel]

                    st.markdown("##### 🔢 Marque quais aulas deste dia pertencem a esta disciplina/professor:")
                    col_a1, col_a2, col_a3, col_a4, col_a5, col_a6 = st.columns(6)
                    with col_a1: aula_1 = st.checkbox("1ª Aula", value=True)
                    with col_a2: aula_2 = st.checkbox("2ª Aula", value=True)
                    with col_a3: aula_3 = st.checkbox("3ª Aula", value=False)
                    with col_a4: aula_4 = st.checkbox("4ª Aula", value=False)
                    with col_a5: aula_5 = st.checkbox("5ª Aula", value=False)
                    with col_a6: aula_6 = st.checkbox("6ª Aula", value=False)

                    aulas_marcadas = []
                    if aula_1: aulas_marcadas.append(1)
                    if aula_2: aulas_marcadas.append(2)
                    if aula_3: aulas_marcadas.append(3)
                    if aula_4: aulas_marcadas.append(4)
                    if aula_5: aulas_marcadas.append(5)
                    if aula_6: aulas_marcadas.append(6)

                    dt_vigencia_sel = st.date_input("📅 Data de Início da Vigência:", value=date(2027, 2, 1), format="DD/MM/YYYY")

                    btn_salvar_gh = st.form_submit_button("💾 Salvar Bloco na Grade Semanal", use_container_width=True)

                    if btn_salvar_gh:
                        if not aulas_marcadas:
                            st.warning("Selecione pelo menos uma aula.")
                        else:
                            try:
                                # Remove os horários anteriores dessa mesma turma, dia e aulas marcadas para sobrescrever de forma limpa
                                for a_num in aulas_marcadas:
                                    db.query(GradeHorario).filter(
                                        GradeHorario.turma_id == turma_gh_obj.id,
                                        GradeHorario.dia_semana == dia_num,
                                        GradeHorario.numero_aula == a_num
                                    ).delete()

                                    nova_aula = GradeHorario(
                                        turma_id=turma_gh_obj.id,
                                        dia_semana=dia_num,
                                        numero_aula=a_num,
                                        disciplina=disc_gh_sel,
                                        professor_id=prof_id_valor,
                                        data_inicio_vigencia=dt_vigencia_sel
                                    )
                                    db.add(nova_aula)

                                db.commit()
                                st.success(f"Grade atualizada com sucesso para {turma_gh_obj.nome} na {dia_sem_sel}!")
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao salvar horário: {e}")

            with aba_ver_gh:
                aulas_grade = db.query(GradeHorario).filter(GradeHorario.turma_id == turma_gh_obj.id).order_by(GradeHorario.dia_semana, GradeHorario.numero_aula).all()
                if not aulas_grade:
                    st.info(f"Nenhum horário cadastrado para a turma **{turma_gh_obj.nome}**.")
                else:
                    dados_gh = []
                    for g in aulas_grade:
                        prof_obj = db.query(Usuario).filter(Usuario.id == g.professor_id).first() if g.professor_id else None
                        dados_gh.append({
                            "ID": g.id,
                            "Dia da Semana": mapa_dias_semana.get(g.dia_semana, "-"),
                            "Aula": f"{g.numero_aula}ª Aula",
                            "Disciplina": g.disciplina,
                            "Professor": prof_obj.nome if prof_obj else "Não Vinculado",
                            "Início da Vigência": g.data_inicio_vigencia.strftime("%d/%m/%Y")
                        })
                    
                    df_gh = pd.DataFrame(dados_gh)
                    st.dataframe(df_gh, use_container_width=True, hide_index=True)

                    st.markdown("---")
                    col_del_gh1, _ = st.columns([1.5, 2])
                    with col_del_gh1:
                        id_del_gh = st.selectbox("🗑️ Selecione um horário pelo ID para remover:", [d["ID"] for d in dados_gh])
                        if st.button("❌ Apagar Horário Selecionado", use_container_width=True):
                            db.query(GradeHorario).filter(GradeHorario.id == id_del_gh).delete()
                            db.commit()
                            st.success("Horário removido com sucesso!")
                            st.rerun()

        db.close()

    elif menu == "Calendário Escolar / Trimestres":
        st.subheader("📅 Gestão do Calendário Escolar e Períodos Trimestrais")
        st.caption("Ajuste as datas de início e término dos trimestres conforme o calendário anual.")

        db = next(get_db())
        ano_cal = st.number_input("Ano Letivo:", min_value=2024, max_value=2030, value=2027)

        trimestres_db = db.query(CalendarioEscolar).filter(CalendarioEscolar.ano_letivo == ano_cal).order_by(CalendarioEscolar.trimestre).all()

        with st.form("form_calendario_trimestres"):
            col_c1, col_c2, col_c3 = st.columns(3)

            datas_trim = {}
            for idx, trim_nome in enumerate(["1º Trimestre", "2º Trimestre", "3º Trimestre"]):
                reg_trim = next((t for t in trimestres_db if t.trimestre == trim_nome), None)
                dt_ini_default = reg_trim.data_inicio if reg_trim else date(ano_cal, 2 + (idx*3), 1)
                dt_fim_default = reg_trim.data_fim if reg_trim else date(ano_cal, 5 + (idx*3), 30)

                if idx == 0: target_col = col_c1
                elif idx == 1: target_col = col_c2
                else: target_col = col_c3

                with target_col:
                    st.markdown(f"##### {trim_nome}")
                    d_ini = st.date_input(f"Início ({trim_nome})", value=dt_ini_default, format="DD/MM/YYYY")
                    d_fim = st.date_input(f"Término ({trim_nome})", value=dt_fim_default, format="DD/MM/YYYY")
                    datas_trim[trim_nome] = (d_ini, d_fim)

            btn_salvar_cal = st.form_submit_button("💾 Salvar Calendário Escolar", use_container_width=True)

            if btn_salvar_cal:
                try:
                    for t_nome, (d_i, d_f) in datas_trim.items():
                        c_obj = db.query(CalendarioEscolar).filter(
                            CalendarioEscolar.ano_letivo == ano_cal,
                            CalendarioEscolar.trimestre == t_nome
                        ).first()

                        if c_obj:
                            c_obj.data_inicio = d_i
                            c_obj.data_fim = d_f
                        else:
                            novo_c = CalendarioEscolar(ano_letivo=ano_cal, trimestre=t_nome, data_inicio=d_i, data_fim=d_f)
                            db.add(novo_c)

                    db.commit()
                    st.success(f"Calendário escolar de {ano_cal} atualizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(f"Erro ao salvar calendário: {e}")

        db.close()

    elif menu == "Lançamento/Auditoria de Notas":
        st.subheader("📊 Auditoria, Lançamento Direto de Histórico e Abono de Frequência")
        
        db = next(get_db())
        turmas = db.query(Turma).all()
        
        if not turmas:
            st.warning("Nenhuma turma cadastrada.")
            db.close()
        else:
            mapa_turmas = {f"{t.nome} ({t.turno})": t for t in turmas}
            
            aba_auditoria, aba_lanc_notas, aba_ajuste_freq = st.tabs([
                "📊 Auditoria Visual",
                "📝 Lançamento/Correção de Notas",
                "🗓️ Ajuste/Abono de Frequência"
            ])

            # -------------------------------------------------------------
            # ABA 1: AUDITORIA VISUAL RÁPIDA
            # -------------------------------------------------------------
            with aba_auditoria:
                col_au1, col_au2, col_au3 = st.columns(3)
                with col_au1:
                    turma_sel_nome = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()), key="aud_turma_sel")
                    turma_obj = mapa_turmas[turma_sel_nome]
                with col_au2:
                    disciplina_sel = st.selectbox("📖 Disciplina:", TODAS_DISCIPLINAS, key="aud_disc_sel")
                with col_au3:
                    trimestre_sel = st.selectbox("📅 Trimestre:", ["1º Trimestre", "2º Trimestre", "3º Trimestre"], key="aud_trim_sel")

                alunos_turma = db.query(Aluno).filter(
                    Aluno.turma_id == turma_obj.id,
                    Aluno.nome != "",
                    Aluno.nome != None
                ).order_by(Aluno.nome).all()
                
                if not alunos_turma:
                    st.info("Nenhum aluno cadastrado nesta turma.")
                else:
                    dados_notas = []
                    for idx, a in enumerate(alunos_turma):
                        total_trim = calcular_total_trimestral_aluno(db, a.id, disciplina_sel, trimestre_sel)
                        
                        t1 = sum_trim_simples(db, a.id, disciplina_sel, "1º Trimestre")
                        t2 = sum_trim_simples(db, a.id, disciplina_sel, "2º Trimestre")
                        t3 = sum_trim_simples(db, a.id, disciplina_sel, "3º Trimestre")
                        soma_anual_reg = t1 + t2 + t3

                        rec_final_obj = db.query(Nota).filter(
                            Nota.aluno_id == a.id,
                            Nota.disciplina == disciplina_sel,
                            Nota.trimestre == "Rec_Final"
                        ).first()
                        val_rf = float(rec_final_obj.valor_nota) if rec_final_obj and rec_final_obj.valor_nota is not None else 0.0

                        total_anual_final = max(soma_anual_reg, val_rf)
                        status_aluno = "Aprovado" if total_anual_final >= 60.0 else "-"

                        dados_notas.append({
                            "Nº": idx + 1,
                            "Aluno": f"{a.nome} ({a.status})" if a.status != "Ativo" else a.nome,
                            "Matrícula": a.matricula or "S/N",
                            f"Total ({trimestre_sel})": f"{total_trim:.1f}",
                            "Total Anual Final": f"{total_anual_final:.1f}",
                            "Situação": status_aluno
                        })
                    
                    st.dataframe(pd.DataFrame(dados_notas), use_container_width=True, hide_index=True)

            # -------------------------------------------------------------
            # ABA 2: LANÇAMENTO / CORREÇÃO DE NOTAS
            # -------------------------------------------------------------
            with aba_lanc_notas:
                st.markdown("##### ✏️ Lançamento e Correção Direta de Notas (Histórico / Transferidos)")
                st.caption("Ideal para alunos que ingressaram por transferência e já possuem notas trimestrales consolidadas no histórico escolar.")

                col_ln1, col_ln2 = st.columns(2)
                with col_ln1:
                    turma_sel_hist = st.selectbox("🏫 Turma do Aluno:", list(mapa_turmas.keys()), key="hist_turma_sel")
                    turma_hist_obj = mapa_turmas[turma_sel_hist]

                    alunos_hist_list = db.query(Aluno).filter(
                        Aluno.turma_id == turma_hist_obj.id,
                        Aluno.status == "Ativo",
                        Aluno.nome != "", Aluno.nome != None
                    ).order_by(Aluno.nome).all()

                    if not alunos_hist_list:
                        st.warning("Nenhum aluno ativo nesta turma.")
                        aluno_hist_obj = None
                    else:
                        mapa_a_hist = {f"{a.nome} (Mat: {a.matricula or 'S/N'})": a for a in alunos_hist_list}
                        aluno_hist_nome = st.selectbox("👨‍🎓 Aluno:", list(mapa_a_hist.keys()), key="hist_aluno_sel")
                        aluno_hist_obj = mapa_a_hist[aluno_hist_nome]

                with col_ln2:
                    disc_hist_sel = st.selectbox("📖 Disciplina para Lançamento:", TODAS_DISCIPLINAS, key="hist_disc_sel")

                if aluno_hist_obj:
                    t1_atual = sum_trim_simples_isolado(db, aluno_hist_obj.id, disc_hist_sel, "1º Trimestre")
                    t2_atual = sum_trim_simples_isolado(db, aluno_hist_obj.id, disc_hist_sel, "2º Trimestre")
                    t3_atual = sum_trim_simples_isolado(db, aluno_hist_obj.id, disc_hist_sel, "3º Trimestre")
                    
                    rec_f_obj = db.query(Nota).filter(
                        Nota.aluno_id == aluno_hist_obj.id,
                        Nota.disciplina == disc_hist_sel,
                        Nota.trimestre == "Rec_Final"
                    ).first()
                    rf_atual = float(rec_f_obj.valor_nota) if rec_f_obj and rec_f_obj.valor_nota is not None else 0.0

                    with st.form("form_hist_notas_secretaria"):
                        st.markdown(f"###### Lançamento de Histórico para: **{aluno_hist_obj.nome}** (`{disc_hist_sel}`)")
                        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
                        
                        with col_h1:
                            nota_t1 = st.number_input("1º Trimestre (Máx: 30)", min_value=0.0, max_value=30.0, value=t1_atual, step=0.5)
                        with col_h2:
                            nota_t2 = st.number_input("2º Trimestre (Máx: 30)", min_value=0.0, max_value=30.0, value=t2_atual, step=0.5)
                        with col_h3:
                            nota_t3 = st.number_input("3º Trimestre (Máx: 40)", min_value=0.0, max_value=40.0, value=t3_atual, step=0.5)
                        with col_h4:
                            nota_rf = st.number_input("Rec. Final (Máx: 100)", min_value=0.0, max_value=100.0, value=rf_atual, step=1.0)

                        btn_salvar_hist = st.form_submit_button("💾 Salvar Histórico do Aluno", use_container_width=True)

                        if st.session_state.msg_sucesso_hist_sec:
                            st.markdown("<div class='msg-sucesso-block'>✅ Alterações salvas com sucesso!</div>", unsafe_allow_html=True)
                            st.session_state.msg_sucesso_hist_sec = False

                        if btn_salvar_hist:
                            try:
                                db.query(Nota).filter(
                                    Nota.aluno_id == aluno_hist_obj.id,
                                    Nota.disciplina == disc_hist_sel
                                ).delete(synchronize_session=False)

                                db.add(Nota(disciplina=disc_hist_sel, trimestre="1º Trimestre_N1", valor_nota=nota_t1, aluno_id=aluno_hist_obj.id))
                                db.add(Nota(disciplina=disc_hist_sel, trimestre="2º Trimestre_N1", valor_nota=nota_t2, aluno_id=aluno_hist_obj.id))
                                db.add(Nota(disciplina=disc_hist_sel, trimestre="3º Trimestre_N1", valor_nota=nota_t3, aluno_id=aluno_hist_obj.id))
                                db.add(Nota(disciplina=disc_hist_sel, trimestre="Rec_Final", valor_nota=nota_rf, aluno_id=aluno_hist_obj.id))

                                db.commit()
                                st.session_state.msg_sucesso_hist_sec = True
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao salvar histórico: {e}")

            # -------------------------------------------------------------
            # ABA 3: AJUSTE / ABONO DE FREQUÊNCIA
            # -------------------------------------------------------------
            with aba_ajuste_freq:
                st.markdown("##### 🗓️ Ajuste e Abono Administrativo de Frequência")
                st.caption("Insira abonos por atestado médico ou ajuste o número de faltas do aluno de forma rápida.")

                col_fa1, col_fa2, col_fa3 = st.columns(3)
                with col_fa1:
                    turma_sel_freq_adm = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()), key="freq_adm_turma_sel")
                    turma_freq_obj = mapa_turmas[turma_sel_freq_adm]

                    alunos_freq_list = db.query(Aluno).filter(
                        Aluno.turma_id == turma_freq_obj.id,
                        Aluno.status == "Ativo",
                        Aluno.nome != "", Aluno.nome != None
                    ).order_by(Aluno.nome).all()

                    if not alunos_freq_list:
                        st.warning("Nenhum aluno ativo nesta turma.")
                        aluno_freq_obj = None
                    else:
                        mapa_a_freq = {f"{a.nome} (Mat: {a.matricula or 'S/N'})": a for a in alunos_freq_list}
                        aluno_freq_nome = st.selectbox("👨‍🎓 Aluno:", list(mapa_a_freq.keys()), key="freq_adm_aluno_sel")
                        aluno_freq_obj = mapa_a_freq[aluno_freq_nome]

                with col_fa2:
                    disc_freq_sel = st.selectbox("📖 Disciplina:", TODAS_DISCIPLINAS, key="freq_adm_disc_sel")
                with col_fa3:
                    data_ajuste_freq = st.date_input("🗓️ Data Específica da Aula:", value=date(2027, 2, 1), format="DD/MM/YYYY")

                if aluno_freq_obj:
                    with st.form("form_ajuste_frequencia_adm"):
                        st.markdown(f"###### Lançamento Administrativo para: **{aluno_freq_obj.nome}** na data `{data_ajuste_freq.strftime('%d/%m/%Y')}`")
                        
                        freq_existente = db.query(FrequenciaDiaria).filter(
                            FrequenciaDiaria.aluno_id == aluno_freq_obj.id,
                            FrequenciaDiaria.disciplina == disc_freq_sel,
                            FrequenciaDiaria.data_aula == data_ajuste_freq
                        ).first()

                        status_atual_adm = freq_existente.status if freq_existente else "."
                        
                        mapa_status_label = {".": "Presença (.)", "F": "Falta Não Justificada (F)", "FJ": "Falta Justificada / Abono (FJ)"}
                        ops_status = [".", "F", "FJ"]
                        idx_st_adm = ops_status.index(status_atual_adm) if status_atual_adm in ops_status else 0

                        novo_status_adm = st.radio("Selecione o Status da Frequência:", ops_status, format_func=lambda x: mapa_status_label[x], index=idx_st_adm, horizontal=True)

                        btn_salvar_freq_adm = st.form_submit_button("💾 Salvar Ajuste de Frequência", use_container_width=True)

                        if st.session_state.msg_sucesso_freq_sec:
                            st.markdown("<div class='msg-sucesso-block'>✅ Alterações salvas com sucesso!</div>", unsafe_allow_html=True)
                            st.session_state.msg_sucesso_freq_sec = False

                        if btn_salvar_freq_adm:
                            try:
                                if freq_existente:
                                    freq_existente.status = novo_status_adm
                                else:
                                    novo_f_adm = FrequenciaDiaria(
                                        data_aula=data_ajuste_freq,
                                        disciplina=disc_freq_sel,
                                        status=novo_status_adm,
                                        aluno_id=aluno_freq_obj.id
                                    )
                                    db.add(novo_f_adm)

                                db.commit()
                                st.session_state.msg_sucesso_freq_sec = True
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao atualizar frequência: {e}")

        db.close()

    elif menu == "Gestão de Usuários e Senhas":
        st.subheader("🔐 Gestão de Usuários, Senhas e Disciplinas Oficiais")
        
        db = next(get_db())
        todas_turmas_geral = db.query(Turma).all()
        
        aba_cad_u, aba_edit_u, aba_cad_disc = st.tabs([
            "➕ Cadastrar Novo Usuário", 
            "✏️ Editar / Excluir Usuário", 
            "📚 Gerenciar Disciplinas"
        ])

        with aba_cad_disc:
            st.markdown("##### 📚 Cadastro e Gestão de Disciplinas Oficiais da Escola")
            st.caption("Adicione novas disciplinas ou remova as que não são utilizadas. As alterações refletem-se imediatamente nas pautas e boletins.")

            col_disc1, col_disc2 = st.columns([1, 1.5])
            with col_disc1:
                with st.form("form_nova_disciplina", clear_on_submit=True):
                    nova_disc_nome = st.text_input("Nome da Nova Disciplina")
                    btn_add_disc = st.form_submit_button("💾 Adicionar Disciplina", use_container_width=True)

                    if btn_add_disc:
                        if not nova_disc_nome.strip():
                            st.warning("Informe o nome da disciplina.")
                        else:
                            try:
                                nome_limpo = nova_disc_nome.strip().title()
                                existente = db.query(DisciplinaEscola).filter(DisciplinaEscola.nome == nome_limpo).first()
                                if existente:
                                    st.error("Esta disciplina já está cadastrada.")
                                else:
                                    db.add(DisciplinaEscola(nome=nome_limpo))
                                    db.commit()
                                    st.success(f"Disciplina '{nome_limpo}' cadastrada com sucesso!")
                                    st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao cadastrar disciplina: {e}")

            with col_disc2:
                st.markdown("##### 📋 Disciplinas Atuais no Sistema")
                lista_disc_db = db.query(DisciplinaEscola).order_by(DisciplinaEscola.nome).all()
                if not lista_disc_db:
                    st.info("Nenhuma disciplina cadastrada.")
                else:
                    for d in lista_disc_db:
                        c_d1, c_d2 = st.columns([3, 1])
                        c_d1.write(f"• **{d.nome}**")
                        if c_d2.button("🗑️ Excluir", key=f"del_disc_{d.id}"):
                            try:
                                db.delete(d)
                                db.commit()
                                st.success(f"Disciplina '{d.nome}' removida!")
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao excluir: {e}")

        with aba_cad_u:
            col_u1, col_u2 = st.columns([1, 2])
            with col_u1:
                nome_u = st.text_input("Nome do Usuário *", key="cad_nome_usr")
                email_u = st.text_input("E-mail do Usuário *", key="cad_email_usr")
                telefone_u = st.text_input("Telefone / WhatsApp (Ex: 27 99999-8888)", key="cad_tel_usr")
                senha_u = st.text_input("Senha Inicial (Padrão: 123)", type="password", value="123", key="cad_senha_usr")
                perfil_u = st.selectbox("Perfil de Acesso", ["professor", "pedagogico", "secretaria"], key="cad_perfil_usr")
                
                mapa_disc_salvar_novo = {}
                turmas_sel_novo = []

                if perfil_u == "professor":
                    st.markdown("##### 🏫 Marque a Turma e escolha a(s) Disciplina(s) logo abaixo:")
                    for t in todas_turmas_geral:
                        chk_t = st.checkbox(f"Turma {t.nome} ({t.turno})", key=f"novo_t_{t.id}")
                        if chk_t:
                            turmas_sel_novo.append(str(t.id))
                            discs_sel = st.multiselect(
                                f"Disciplinas na turma {t.nome}:",
                                obter_lista_disciplinas(),
                                default=[],
                                key=f"novo_disc_{t.id}"
                            )
                            mapa_disc_salvar_novo[str(t.id)] = discs_sel

                st.write("")
                btn_cad_user = st.button("Cadastrar Usuário", use_container_width=True, key="btn_exec_cad_user")

                if st.session_state.msg_sucesso_novo_usuario:
                    st.markdown(f"<div class='msg-sucesso-block'>✅ {st.session_state.msg_sucesso_novo_usuario}</div>", unsafe_allow_html=True)
                    st.session_state.msg_sucesso_novo_usuario = ""

                if btn_cad_user:
                    nome_clean = nome_u.strip()
                    email_clean = email_u.strip().lower()

                    if not nome_clean or not email_clean:
                        st.error("⚠️ Preencha o nome e o e-mail do usuário.")
                    elif perfil_u == "professor" and len(turmas_sel_novo) == 0:
                        st.error("⚠️ Para cadastrar um professor, selecione ao menos uma turma.")
                    elif perfil_u == "professor" and any(len(discs) == 0 for discs in mapa_disc_salvar_novo.values()):
                        st.error("⚠️ Selecione ao menos uma disciplina para cada turma marcada.")
                    else:
                        try:
                            existente = db.query(Usuario).filter(Usuario.email == email_clean).first()
                            if existente:
                                st.error("⚠️ Este e-mail já está cadastrado no sistema.")
                            else:
                                novo_usr = Usuario(
                                    nome=nome_clean,
                                    email=email_clean,
                                    telefone=telefone_u.strip() if telefone_u.strip() else None,
                                    senha_hash=gerar_hash_senha(senha_u.strip() if senha_u.strip() else "123"),
                                    perfil=perfil_u,
                                    turmas_permitidas=",".join(turmas_sel_novo) if perfil_u == "professor" else "",
                                    disciplinas_turmas=json.dumps(mapa_disc_salvar_novo) if perfil_u == "professor" else "{}"
                                )
                                db.add(novo_usr)
                                db.commit()
                                
                                st.session_state.msg_sucesso_novo_usuario = "Cadastro efetivado. Você já pode sair dessa página."
                                st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Erro ao salvar no banco de dados: {e}")

            with col_u2:
                st.markdown("##### 👥 Usuários Cadastrados")
                usuarios_list = db.query(Usuario).all()
                dados_u = []
                for u in usuarios_list:
                    dados_u.append({
                        "ID": u.id,
                        "Nome": u.nome,
                        "E-mail": u.email,
                        "Telefone": u.telefone or "Não informado",
                        "Perfil": u.perfil.upper()
                    })
                st.dataframe(pd.DataFrame(dados_u), use_container_width=True, hide_index=True)

        with aba_edit_u:
            usuarios_list_edit = db.query(Usuario).order_by(Usuario.nome).all()
            if not usuarios_list_edit:
                st.info("Nenhum usuário disponível para edição.")
            else:
                mapa_usuarios_edit = {f"{u.nome} ({u.email})": u for u in usuarios_list_edit}
                usr_sel_nome = st.selectbox("🔍 Selecione o Usuário para Gerenciar e Editar:", list(mapa_usuarios_edit.keys()))
                usr_edit_obj = mapa_usuarios_edit[usr_sel_nome]

                st.markdown(f"<div style='background-color: #e2f0cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>✏️ <b>Modo de Edição Ativo para:</b> {usr_edit_obj.nome} ({usr_edit_obj.perfil.upper()})</div>", unsafe_allow_html=True)

                col_form_e, col_form_del = st.columns([2.5, 1])

                with col_form_e:
                    with st.form("form_editar_usuario"):
                        st.markdown("##### Atualizar Dados Cadastrais e Alocações")
                        novo_nome_usr = st.text_input("Nome do Usuário", value=usr_edit_obj.nome)
                        novo_email_usr = st.text_input("E-mail do Usuário", value=usr_edit_obj.email)
                        novo_tel_usr = st.text_input("Telefone / WhatsApp", value=usr_edit_obj.telefone or "")
                        
                        perfis_op = ["professor", "pedagogico", "secretaria"]
                        idx_perfil = perfis_op.index(usr_edit_obj.perfil) if usr_edit_obj.perfil in perfis_op else 0
                        novo_perfil_usr = st.selectbox("Perfil de Acesso", perfis_op, index=idx_perfil)

                        st.caption("Redefinir Senha (Opcional - deixe em branco para manter a atual):")
                        nova_senha_usr = st.text_input("Redefinir Senha", type="password")

                        st.markdown("##### 🏫 Turmas e Disciplinas Atribuídas:")
                        ids_atuais = [i.strip() for i in (usr_edit_obj.turmas_permitidas or "").split(",") if i.strip()]
                        
                        mapa_disc_existente = {}
                        if usr_edit_obj.disciplinas_turmas:
                            try:
                                mapa_disc_existente = json.loads(usr_edit_obj.disciplinas_turmas)
                            except:
                                mapa_disc_existente = {}

                        mapa_disc_salvar_edit = {}
                        turmas_sel_edit = []

                        lista_disc_atual = obter_lista_disciplinas()
                        for t in todas_turmas_geral:
                            checked_default = str(t.id) in ids_atuais
                            chk_t_edit = st.checkbox(f"Turma {t.nome} ({t.turno})", value=checked_default, key=f"edit_t_{usr_edit_obj.id}_{t.id}")
                            if chk_t_edit:
                                turmas_sel_edit.append(str(t.id))
                                disc_default = mapa_disc_existente.get(str(t.id), [])
                                discs_sel_e = st.multiselect(
                                    f"Disciplinas na turma {t.nome}:",
                                    lista_disc_atual,
                                    default=[d for d in disc_default if d in lista_disc_atual],
                                    key=f"edit_disc_{usr_edit_obj.id}_{t.id}"
                                )
                                mapa_disc_salvar_edit[str(t.id)] = discs_sel_e

                        btn_salvar_usr = st.form_submit_button("💾 Salvar Alterações do Usuário", use_container_width=True)
                        
                        if st.session_state.msg_sucesso_usuario:
                            st.markdown(f"<div class='msg-sucesso-block'>✅ {st.session_state.msg_sucesso_usuario}</div>", unsafe_allow_html=True)
                            st.session_state.msg_sucesso_usuario = ""

                        if btn_salvar_usr:
                            if not novo_nome_usr.strip() or not novo_email_usr.strip():
                                st.warning("Preencha o nome e o e-mail do usuário.")
                            elif novo_perfil_usr == "professor" and len(turmas_sel_edit) == 0:
                                st.error("⚠️ Para salvar um professor, selecione ao menos uma turma.")
                            elif novo_perfil_usr == "professor" and any(len(discs) == 0 for discs in mapa_disc_salvar_edit.values()):
                                st.error("⚠️ Selecione ao menos uma disciplina para cada turma alocada ao professor.")
                            else:
                                try:
                                    usr_edit_obj.nome = novo_nome_usr.strip()
                                    usr_edit_obj.email = novo_email_usr.strip().lower()
                                    usr_edit_obj.telefone = novo_tel_usr.strip() if novo_tel_usr.strip() else None
                                    usr_edit_obj.perfil = novo_perfil_usr
                                    usr_edit_obj.turmas_permitidas = ",".join(turmas_sel_edit) if novo_perfil_usr == "professor" else ""
                                    usr_edit_obj.disciplinas_turmas = json.dumps(mapa_disc_salvar_edit) if novo_perfil_usr == "professor" else "{}"
                                    if nova_senha_usr.strip():
                                        usr_edit_obj.senha_hash = gerar_hash_senha(nova_senha_usr.strip())
                                    db.commit()
                                    
                                    st.session_state.msg_sucesso_usuario = "Alterações salvas. Você já pode sair dessa página."
                                    st.rerun()
                                except Exception as e:
                                    db.rollback()
                                    st.error(f"Erro ao atualizar usuário: {e}")

                with col_form_del:
                    st.markdown("##### 🗑️ Excluir Usuário")
                    st.warning(f"Atenção: Você está prestes a excluir **{usr_edit_obj.nome}**.")
                    if st.button("🗑️ Confirmar Exclusão de Usuário", use_container_width=True):
                        try:
                            db.delete(usr_edit_obj)
                            db.commit()
                            st.success("Usuário excluído com sucesso!")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Erro ao excluir usuário: {e}")

        db.close()

    elif user["perfil"] == "secretaria" and menu == "🗓️ Calendário e Bloqueios":
        st.subheader("🗓️ Gestão de Eventos e Bloqueios de Pauta")
        st.caption("Cadastre os dias em que não haverá aula regular (Feriados, JPP, Recessos, Conselho de Classe) para bloquear chamadas indevidas.")

        db = next(get_db())

        col_c1, col_c2 = st.columns([1, 2])

        with col_c1:
            st.markdown("##### ➕ Cadastrar Novo Evento / Bloqueio")
            data_evento = st.date_input("📅 Data do Evento:", value=datetime.now(), format="DD/MM/YYYY")
            
            tipo_ev = st.selectbox(
                "🏷️ Tipo de Evento:",
                ["Feriado Nacional", "Feriado Estadual", "Feriado Municipal", "Recesso Escolar", "JPP", "Conselho de Classe", "Outro"]
            )
            desc_ev = st.text_input("📝 Descrição / Motivo:", placeholder="Ex: Dia do Professor, Feriado de Cariacica...")
            bloquear = st.checkbox("🚫 Bloquear Pauta de Frequência para este dia?", value=True)

            if st.button("💾 Salvar no Calendário", use_container_width=True):
                data_str = data_evento.strftime("%Y-%m-%d")
                
                existente = db.query(EventoCalendario).filter(EventoCalendario.data == data_str).first()
                if existente:
                    existente.tipo_evento = tipo_ev
                    existente.descricao = desc_ev
                    existente.bloqueia_pauta = bloquear
                    st.success(f"Evento do dia {data_evento.strftime('%d/%m/%Y')} atualizado!")
                else:
                    novo_evento = EventoCalendario(
                        data=data_str,
                        tipo_evento=tipo_ev,
                        descricao=desc_ev,
                        bloqueia_pauta=bloquear
                    )
                    db.add(novo_evento)
                    st.success(f"Evento do dia {data_evento.strftime('%d/%m/%Y')} cadastrado!")
                
                db.commit()
                st.rerun()

        with col_c2:
            st.markdown("##### 📋 Eventos e Bloqueios Cadastrados")
            eventos = db.query(EventoCalendario).order_by(EventoCalendario.data).all()
            
            if not eventos:
                st.info("Nenhum evento ou bloqueio cadastrado até o momento.")
            else:
                dados_eventos = []
                for ev in eventos:
                    d_obj = datetime.strptime(ev.data, "%Y-%m-%d")
                    dados_eventos.append({
                        "ID": ev.id,
                        "Data": d_obj.strftime("%d/%m/%Y"),
                        "Tipo de Evento": ev.tipo_evento,
                        "Descrição": ev.descricao or "-",
                        "Bloqueia Chamada?": "🚫 Sim" if ev.bloqueia_pauta else "✅ Não"
                    })
                
                df_eventos = pd.DataFrame(dados_eventos)
                st.dataframe(df_eventos, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                ev_apagar_id = st.selectbox("🗑️ Selecione um evento pelo ID para remover:", [e["ID"] for e in dados_eventos], key="del_ev")
                if st.button("❌ Apagar Evento Selecionado"):
                    db.query(EventoCalendario).filter(EventoCalendario.id == ev_apagar_id).delete()
                    db.commit()
                    st.warning("Evento removido!")
                    st.rerun()

        db.close()

    # ==========================================
    # MÓDULOS DE RELATÓRIOS
    # ==========================================
    elif menu == "📄 Relatórios e Documentos Emitidos":
        st.subheader("📄 Módulo de Relatórios e Documentos Escolares")
        
        db = next(get_db())
        turmas, _ = obter_turmas_e_disciplinas_professor(db)
        
        if not turmas:
            st.warning("Nenhuma turma disponível.")
            db.close()
        else:
            mapa_turmas = {f"{t.nome} ({t.turno})": t for t in turmas}
            
            tipo_relatorio = st.selectbox(
                "📋 Selecione o Tipo de Relatório:",
                [
                    "📖 Registro de Conteúdo Ministrado (Diário de Classe)",
                    "📊 Ata de Rendimento Trimestral (Conselho de Classe)",
                    "👨‍🎓 Boletim Individual do Aluno",
                    "🚨 Relatório de Busca Ativa (Alunos em Risco por Frequência)",
                    "📋 Lista Nominal de Alunos por Turma"
                ]
            )

            st.markdown("---")

            # -------------------------------------------------------------
            # RELATÓRIO: REGISTRO DE CONTEÚDO TRIMESTRAL
            # -------------------------------------------------------------
            if tipo_relatorio.startswith("📖 Registro"):
                col_rc1, col_rc2, col_rc3 = st.columns(3)
                with col_rc1:
                    turma_sel_nome = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()), key="rel_cont_turma")
                    turma_obj = mapa_turmas[turma_sel_nome]

                _, disciplinas_permitidas = obter_turmas_e_disciplinas_professor(db, turma_obj.id)

                with col_rc2:
                    disc_sel_rel = st.selectbox("📖 Disciplina:", disciplinas_permitidas, key="rel_cont_disc")
                with col_rc3:
                    trimestre_sel_rel = st.selectbox("📅 Trimestre:", ["1º Trimestre", "2º Trimestre", "3º Trimestre"], key="rel_cont_trim")

                todos_professores = db.query(Usuario).filter(Usuario.perfil == "professor").all()
                professor_responsavel = "Não informado"
                for prof in todos_professores:
                    try:
                        turmas_p = [int(i.strip()) for i in (prof.turmas_permitidas or "").split(",") if i.strip().isdigit()]
                        if turma_obj.id in turmas_p:
                            mapa_d_prof = json.loads(prof.disciplinas_turmas or "{}")
                            discs_t_prof = mapa_d_prof.get(str(turma_obj.id), [])
                            if disc_sel_rel in discs_t_prof:
                                professor_responsavel = prof.nome
                                break
                    except:
                        pass

                registros_conteudo = db.query(RegistroConteudo).filter(
                    RegistroConteudo.turma_id == turma_obj.id,
                    RegistroConteudo.disciplina == disc_sel_rel,
                    RegistroConteudo.trimestre == trimestre_sel_rel
                ).order_by(RegistroConteudo.data_aula).all()

                if not registros_conteudo:
                    st.info(f"Nenhum registro de conteúdo cadastrado para **{turma_obj.nome}** em **{disc_sel_rel}** no **{trimestre_sel_rel}**.")
                else:
                    dados_cont = []
                    for rc in registros_conteudo:
                        prof_reg = rc.professor_nome if (rc.professor_nome and rc.professor_nome != "Não informado") else professor_responsavel
                        if prof_reg != "Não informado":
                            professor_responsavel = prof_reg

                        dados_cont.append({
                            "Data da Aula": rc.data_aula.strftime("%d/%m/%Y"),
                            "Aulas": rc.qtd_aulas,
                            "Objeto de Conhecimento / Título": rc.objeto_conhecimento,
                            "Conteúdo Trabalhado / Atividades": rc.conteudo_detalhado,
                            "Observações / Metodologia": rc.metodologia_obs or "-"
                        })

                    df_cont = pd.DataFrame(dados_cont)
                    
                    col_pr_c1, col_dl_c2 = st.columns(2)

                    cabecalho_conteudo_csv = (
                        f"TURMA;{turma_obj.nome} ({turma_obj.turno})\n"
                        f"DISCIPLINA;{disc_sel_rel}\n"
                        f"TRIMESTRE;{trimestre_sel_rel}\n"
                        f"PROFESSOR;{professor_responsavel}\n\n"
                    )
                    conteudo_tabela_cont = df_cont.to_csv(index=False, sep=';')
                    csv_cont_completo = (cabecalho_conteudo_csv + conteudo_tabela_cont).encode('utf-8-sig')

                    with col_dl_c2:
                        st.download_button(
                            label="📥 Baixar Relatório em Excel (.csv)",
                            data=csv_cont_completo,
                            file_name=f"Relatorio_Conteudo_{turma_obj.nome}_{disc_sel_rel}_{trimestre_sel_rel.replace(' ', '_')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    linhas_cont_html = ""
                    for row in dados_cont:
                        linhas_cont_html += f"""
                            <tr>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center; white-space: nowrap;">{row['Data da Aula']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center;">{row['Aulas']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: left; font-weight: bold;">{row['Objeto de Conhecimento / Título']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: left;">{row['Conteúdo Trabalhado / Atividades']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: left;">{row['Observações / Metodologia']}</td>
                            </tr>
                        """

                    html_impressao_conteudo = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Relatório de Conteúdo Ministrado</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; padding: 20px; }}
                            .box {{ border: 1px solid #000; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                            h1 {{ text-align: center; margin: 0 0 5px 0; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; color: #333; }}
                            h2 {{ text-align: center; margin: 5px 0 10px 0; font-size: 18px; color: #0d6efd; }}
                            table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
                            th {{ border: 1px solid #000; padding: 8px; background-color: #f2f2f2; }}
                            .rodape {{ margin-top: 30px; text-align: center; font-weight: bold; font-size: 13px; }}
                        </style>
                    </head>
                    <body>
                        <div class="box">
                            <h1>CEAPA - CENTRO EDUCACIONAL APRENDER, PENSAR E AGIR</h1>
                            <h2>📖 RELATÓRIO DE CONTEÚDO MINISTRADO - 2027</h2>
                            <hr style="border: none; border-top: 1px solid #ccc; margin: 10px 0;">
                            <p><b>Turma:</b> {turma_obj.nome} ({turma_obj.turno}) | <b>Disciplina:</b> {disc_sel_rel} | <b>Período:</b> {trimestre_sel_rel}</p>
                            <p><b>Professor(a):</b> {professor_responsavel}</p>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 12%;">Data</th>
                                    <th style="width: 8%;">Aulas</th>
                                    <th style="width: 30%;">Objeto de Conhecimento / Título</th>
                                    <th style="width: 35%;">Conteúdo Trabalhado</th>
                                    <th style="width: 15%;">Observações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {linhas_cont_html}
                            </tbody>
                        </table>
                        <div class="rodape">
                            Cariacica - ES, {datetime.now().strftime("%d/%m/%Y às %H:%M")}.
                        </div>
                    </body>
                    </html>
                    """

                    with col_pr_c1:
                        import streamlit.components.v1 as components
                        js_code_c = f"""
                            <button onclick="imprimir()" style="width: 100%; background-color: #0d6efd; color: white; padding: 9px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
                                🖨️ IMPRIMIR / SALVAR EM PDF
                            </button>
                            <script>
                                function imprimir() {{
                                    var win = window.open('', '_blank');
                                    win.document.write({json.dumps(html_impressao_conteudo)});
                                    win.document.close();
                                    win.focus();
                                    setTimeout(function() {{ win.print(); }}, 500);
                                }}
                            </script>
                        """
                        components.html(js_code_c, height=45)

                    st.markdown("---")
                    st.dataframe(df_cont, use_container_width=True, hide_index=True)

            # -------------------------------------------------------------
            # RELATÓRIO 1: ATA DE CONSELHO DE CLASSE
            # -------------------------------------------------------------
            elif tipo_relatorio.startswith("📊 Ata"):
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    turma_sel_nome = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()), key="rel_ata_turma")
                    turma_obj = mapa_turmas[turma_sel_nome]
                with col_r2:
                    trimestre_sel = st.selectbox("📅 Trimestre:", ["1º Trimestre", "2º Trimestre", "3º Trimestre"], key="rel_ata_trim")

                alunos_turma = db.query(Aluno).filter(
                    Aluno.turma_id == turma_obj.id,
                    Aluno.nome != "", Aluno.nome != None
                ).order_by(Aluno.nome).all()

                if not alunos_turma:
                    st.info("Nenhum aluno encontrado para esta turma.")
                else:
                    dados_ata = []
                    for idx, a in enumerate(alunos_turma):
                        linha = {
                            "Nº": idx + 1,
                            "Aluno": f"{a.nome} [{a.status}]" if a.status != "Ativo" else a.nome,
                            "Matrícula": a.matricula or "S/N"
                        }
                        
                        soma_geral = 0.0
                        disciplinas_com_nota = 0

                        for disc in obter_lista_disciplinas():
                            tot_disc = calcular_total_trimestral_aluno(db, a.id, disc, trimestre_sel)
                            linha[disc] = f"{tot_disc:.1f}"
                            soma_geral += tot_disc
                            disciplinas_com_nota += 1

                        media_geral = (soma_geral / disciplinas_com_nota) if disciplinas_com_nota > 0 else 0.0
                        linha["Média Geral"] = f"{media_geral:.1f}"
                        dados_ata.append(linha)

                    df_ata = pd.DataFrame(dados_ata)
                    st.dataframe(df_ata, use_container_width=True, hide_index=True)

                    cabecalho_ata_csv = (
                        f"TURMA;{turma_obj.nome} ({turma_obj.turno})\n"
                        f"PERIODO;{trimestre_sel}\n\n"
                    )
                    conteudo_tabela_ata_csv = df_ata.to_csv(index=False, sep=';')
                    csv_data_completo = (cabecalho_ata_csv + conteudo_tabela_ata_csv).encode('utf-8-sig')

                    col_btn_print, col_btn_dl = st.columns(2)
                    with col_btn_print:
                        st.info("💡 Para salvar em PDF ou Imprimir, pressione **Ctrl + P** no seu teclado a qualquer momento.")
                    with col_btn_dl:
                        st.download_button(
                            label="📥 Baixar Excel Separado por Colunas (.csv)",
                            data=csv_data_completo,
                            file_name=f"Ata_Rendimento_{turma_obj.nome}_{trimestre_sel.replace(' ', '_')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

            # -------------------------------------------------------------
            # RELATÓRIO 2: BOLETIM INDIVIDUAL DO ALUNO
            # -------------------------------------------------------------
            elif tipo_relatorio.startswith("👨‍🎓 Boletim"):
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    turma_sel_nome = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()), key="rel_bol_turma")
                    turma_obj = mapa_turmas[turma_sel_nome]

                    alunos_turma = db.query(Aluno).filter(
                        Aluno.turma_id == turma_obj.id,
                        Aluno.nome != "", Aluno.nome != None
                    ).order_by(Aluno.nome).all()

                with col_b2:
                    if alunos_turma:
                        mapa_a_bol = {f"{a.nome} (Status: {a.status})": a for a in alunos_turma}
                        aluno_sel_nome = st.selectbox("👨‍🎓 Aluno:", list(mapa_a_bol.keys()), key="rel_bol_aluno")
                        aluno_obj = mapa_a_bol[aluno_sel_nome]
                    else:
                        aluno_obj = None

                if aluno_obj:
                    data_hora_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")
                    
                    raw_resp = getattr(aluno_obj, 'nome_mae', None)
                    nome_responsavel = raw_resp.strip() if raw_resp and raw_resp.strip() else "-"
                    
                    dados_boletim = []

                    for disc in obter_lista_disciplinas():
                        t1 = sum_trim_simples(db, aluno_obj.id, disc, "1º Trimestre")
                        t2 = sum_trim_simples(db, aluno_obj.id, disc, "2º Trimestre")
                        t3 = sum_trim_simples(db, aluno_obj.id, disc, "3º Trimestre")
                        
                        rec_final_obj = db.query(Nota).filter(
                            Nota.aluno_id == aluno_obj.id,
                            Nota.disciplina == disc,
                            Nota.trimestre == "Rec_Final"
                        ).first()
                        val_rf = float(rec_final_obj.valor_nota) if rec_final_obj and rec_final_obj.valor_nota is not None else 0.0

                        soma_anual = t1 + t2 + t3
                        total_final = max(soma_anual, val_rf)
                        
                        total_faltas_disc = db.query(FrequenciaDiaria).filter(
                            FrequenciaDiaria.aluno_id == aluno_obj.id,
                            FrequenciaDiaria.disciplina == disc,
                            FrequenciaDiaria.status.in_(["F", "FJ"])
                        ).count()

                        situacao = "Aprovado" if total_final >= 60.0 else "-"

                        dados_boletim.append({
                            "Disciplina": disc,
                            "1º Trim. (30)": f"{t1:.1f}",
                            "2º Trim. (30)": f"{t2:.1f}",
                            "3º Trim. (40)": f"{t3:.1f}",
                            "Rec. Final": f"{val_rf:.1f}" if val_rf > 0 else "-",
                            "Total Anual": f"{total_final:.1f}",
                            "Faltas": total_faltas_disc,
                            "Situação": situacao
                        })

                    df_boletim = pd.DataFrame(dados_boletim)

                    col_print_b1, col_dl_b2 = st.columns(2)

                    cabecalho_csv = (
                        f"TURMA;{turma_obj.nome} ({turma_obj.turno})\n"
                        f"ALUNO;{aluno_obj.nome}\n"
                        f"RESPONSAVEL;{nome_responsavel}\n\n"
                    )
                    conteudo_tabela_csv = df_boletim.to_csv(index=False, sep=';')
                    csv_completo = (cabecalho_csv + conteudo_tabela_csv).encode('utf-8-sig')

                    with col_dl_b2:
                        st.download_button(
                            label="📥 Baixar Excel Separado por Colunas (.csv)",
                            data=csv_completo,
                            file_name=f"Boletim_{aluno_obj.nome.replace(' ', '_')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    linhas_html = ""
                    for row in dados_boletim:
                        cor_sit = "black" if row['Situação'] == "Aprovado" else "#555"
                        linhas_html += f"""
                            <tr>
                                <td style="border: 1px solid #000; padding: 6px; text-align: left;">{row['Disciplina']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center;">{row['1º Trim. (30)']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center;">{row['2º Trim. (30)']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center;">{row['3º Trim. (40)']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center;">{row['Rec. Final']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center; font-weight: bold;">{row['Total Anual']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center;">{row['Faltas']}</td>
                                <td style="border: 1px solid #000; padding: 6px; text-align: center; color: {cor_sit}; font-weight: bold;">{row['Situação']}</td>
                            </tr>
                        """

                    html_pagina_impressao = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Boletim Escolar - {aluno_obj.nome}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; padding: 20px; }}
                            .box {{ border: 1px solid #000; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                            h1 {{ text-align: center; margin: 0 0 5px 0; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; color: #333; }}
                            h2 {{ text-align: center; margin: 5px 0 10px 0; font-size: 18px; color: #0d6efd; }}
                            table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
                            th {{ border: 1px solid #000; padding: 8px; background-color: #f2f2f2; }}
                            .rodape {{ margin-top: 30px; text-align: center; font-weight: bold; font-size: 13px; }}
                        </style>
                    </head>
                    <body>
                        <div class="box">
                            <h1>CEAPA - CENTRO EDUCACIONAL APRENDER, PENSAR E AGIR</h1>
                            <h2>🏫 SIGES - BOLETIM ESCOLAR 2027</h2>
                            <hr style="border: none; border-top: 1px solid #ccc; margin: 10px 0;">
                            <p><b>Turma:</b> {turma_obj.nome} ({turma_obj.turno})</p>
                            <p><b>Aluno(a):</b> {aluno_obj.nome}</p>
                            <p><b>Responsável:</b> {nome_responsavel}</p>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="text-align: left;">Disciplina</th>
                                    <th>1º Trim. (30)</th>
                                    <th>2º Trim. (30)</th>
                                    <th>3º Trim. (40)</th>
                                    <th>Rec. Final</th>
                                    <th>Total Anual</th>
                                    <th>Faltas</th>
                                    <th>Situação</th>
                                </tr>
                            </thead>
                            <tbody>
                                {linhas_html}
                            </tbody>
                        </table>
                        <div class="rodape">
                            Cariacica - ES, {data_hora_emissao}.
                        </div>
                    </body>
                    </html>
                    """

                    with col_print_b1:
                        import streamlit.components.v1 as components
                        js_code = f"""
                            <button onclick="imprimir()" style="width: 100%; background-color: #0d6efd; color: white; padding: 9px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
                                🖨️ IMPRIMIR / SALVAR EM PDF
                            </button>
                            <script>
                                function imprimir() {{
                                    var win = window.open('', '_blank');
                                    win.document.write({json.dumps(html_pagina_impressao)});
                                    win.document.close();
                                    win.focus();
                                    setTimeout(function() {{ win.print(); }}, 500);
                                }}
                            </script>
                        """
                        components.html(js_code, height=45)

                    st.markdown("---")
                    st.subheader(f"📋 Boletim Escolar 2027")
                    st.caption(f"**Turma:** {turma_obj.nome} ({turma_obj.turno}) | **Aluno(a):** {aluno_obj.nome} | **Responsável:** {nome_responsavel}")
                    
                    st.dataframe(df_boletim, use_container_width=True, hide_index=True)

            # -------------------------------------------------------------
            # RELATÓRIO 3: BUSCA ATIVA / FREQUÊNCIA
            # -------------------------------------------------------------
            elif tipo_relatorio.startswith("🚨 Relatório"):
                st.markdown("##### 🚨 Alunos Ativos com Maior Índice de Faltas")
                turma_sel_nome = st.selectbox("🏫 Turma (ou Geral):", ["Todas as Turmas"] + list(mapa_turmas.keys()), key="rel_ba_turma")

                if turma_sel_nome == "Todas as Turmas":
                    alunos_query = db.query(Aluno).filter(Aluno.status == "Ativo", Aluno.nome != "", Aluno.nome != None).order_by(Aluno.nome).all()
                else:
                    t_obj = mapa_turmas[turma_sel_nome]
                    alunos_query = db.query(Aluno).filter(Aluno.turma_id == t_obj.id, Aluno.status == "Ativo", Aluno.nome != "", Aluno.nome != None).order_by(Aluno.nome).all()

                dados_ba = []
                for a in alunos_query:
                    t_aluno = db.query(Turma).filter(Turma.id == a.turma_id).first()
                    total_faltas = db.query(FrequenciaDiaria).filter(FrequenciaDiaria.aluno_id == a.id, FrequenciaDiaria.status == "F").count()
                    total_justificadas = db.query(FrequenciaDiaria).filter(FrequenciaDiaria.aluno_id == a.id, FrequenciaDiaria.status == "FJ").count()

                    if total_faltas > 0:
                        dados_ba.append({
                            "Aluno": a.nome,
                            "Matrícula": a.matricula or "S/N",
                            "Turma": t_aluno.nome if t_aluno else "Sem Turma",
                            "Faltas Não Justificadas (F)": total_faltas,
                            "Faltas Justificadas (FJ)": total_justificadas,
                            "Status de Risco": "🚨 Risco Elevado" if total_faltas >= 10 else "⚠️ Alerta de Frequência"
                        })

                if not dados_ba:
                    st.success("Nenhum aluno com histórico de faltas não justificadas registrado.")
                else:
                    df_ba = pd.DataFrame(dados_ba).sort_values(by="Faltas Não Justificadas (F)", ascending=False)
                    st.dataframe(df_ba, use_container_width=True, hide_index=True)

                    csv_data_ba = df_ba.to_csv(index=False, sep=';').encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Excel Separado por Colunas (.csv)",
                        data=csv_data_ba,
                        file_name="Relatorio_Busca_Ativa.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            # -------------------------------------------------------------
            # RELATÓRIO 4: LISTA NOMINAL DE ALUNOS POR TURMA
            # -------------------------------------------------------------
            elif tipo_relatorio.startswith("📋 Lista Nominal"):
                st.markdown("##### 📋 Listagem Nominal de Alunos por Turma")
                st.caption("Gera a relação limpa de nomes e matrículas para uso em simulados, listas de chamada e planilhas internas.")

                col_ln1, col_ln2 = st.columns(2)
                with col_ln1:
                    turma_sel_nome = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()), key="rel_lista_turma")
                    turma_obj = mapa_turmas[turma_sel_nome]
                with col_ln2:
                    ordenacao_lista = st.selectbox("🔤 Ordenação:", ["Alfabética (A-Z)", "Por Número de Matrícula"], key="rel_lista_ordem")

                query_alunos_lista = db.query(Aluno).filter(
                    Aluno.turma_id == turma_obj.id,
                    Aluno.status == "Ativo",
                    Aluno.nome != "", Aluno.nome != None
                )

                if ordenacao_lista == "Alfabética (A-Z)":
                    alunos_turma_lista = query_alunos_lista.order_by(Aluno.nome).all()
                else:
                    alunos_turma_lista = query_alunos_lista.order_by(Aluno.matricula).all() if hasattr(Aluno, 'matricula') else query_alunos_lista.order_by(Aluno.nome).all()

                if not alunos_turma_lista:
                    st.info("Nenhum aluno ativo encontrado nesta turma.")
                else:
                    dados_lista_nomes = []
                    for idx, a in enumerate(alunos_turma_lista):
                        dados_lista_nomes.append({
                            "Nº": idx + 1,
                            "ALUNO(A)": a.nome,
                        })

                    df_lista_nomes = pd.DataFrame(dados_lista_nomes)
                    st.dataframe(df_lista_nomes, use_container_width=True, hide_index=True)

                    cabecalho_lista_csv = (
                        f"TURMA;{turma_obj.nome} ({turma_obj.turno})\n"
                    )
                    conteudo_tabela_lista = df_lista_nomes.to_csv(index=False, sep=';')
                    csv_lista_completo = (cabecalho_lista_csv + conteudo_tabela_lista).encode('utf-8-sig')

                    col_pr_l1, col_dl_l2 = st.columns(2)
                    with col_dl_l2:
                        st.download_button(
                            label="📥 Baixar Lista em Excel (.csv)",
                            data=csv_lista_completo,
                            file_name=f"Lista_Alunos_{turma_obj.nome.replace(' ', '_')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

            db.close()

    # ==========================================
    # MÓDULOS DO PROFESSOR
    # ==========================================
    elif menu == "Pauta de Frequência Diária":
        st.caption("Legenda: **.** = Presença (Clique para alternar) | **F** = Falta (Professor) | **FJ** = Falta Justificada (Secretaria)")

        db = next(get_db())
        turmas, _ = obter_turmas_e_disciplinas_professor(db)

        if not turmas:
            st.warning("Nenhuma turma cadastrada ou alocada para o seu perfil.")
            db.close()
        else:
            mapa_turmas = {f"{t.nome} ({t.turno})": t for t in turmas}
            
            col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2.2, 2.0, 1.8, 1.8, 1.2])
            
            with col_f1:
                turma_sel_nome = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()))
                turma_obj = mapa_turmas[turma_sel_nome]

            _, disciplinas_permitidas = obter_turmas_e_disciplinas_professor(db, turma_obj.id)

            with col_f2:
                disciplina_sel = st.selectbox("📖 Disciplina:", disciplinas_permitidas)
            with col_f3:
                trimestre_sel = st.selectbox("📅 Trimestre:", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            with col_f5:
                ano_sel = st.number_input("Ano Letivo", min_value=2024, max_value=2030, value=2027)

            cal_reg = db.query(CalendarioEscolar).filter(
                CalendarioEscolar.ano_letivo == ano_sel,
                CalendarioEscolar.trimestre == trimestre_sel
            ).first()

            if not cal_reg:
                dt_inicio_trim = date(ano_sel, 2, 1)
                dt_fim_trim = date(ano_sel, 5, 30)
            else:
                dt_inicio_trim = cal_reg.data_inicio
                dt_fim_trim = cal_reg.data_fim

            meses_map = {1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho", 7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"}
            meses_do_trimestre = [m for m in range(dt_inicio_trim.month, dt_fim_trim.month + 1)]
            nomes_meses_trim = [meses_map[m] for m in meses_do_trimestre if m in meses_map]

            with col_f4:
                mes_sel_nome = st.selectbox("🗓️ Mês de Exibição:", nomes_meses_trim)
                mes_num = [k for k, v in meses_map.items() if v == mes_sel_nome][0]

            eventos_bloqueio = db.query(EventoCalendario).filter(EventoCalendario.bloqueia_pauta == True).all()
            dias_bloqueados_strs = {ev.data for ev in eventos_bloqueio}

            eventos_mes = db.query(EventoCalendario).all()
            avisos_mes = []
            for ev in eventos_mes:
                try:
                    d_ev = datetime.strptime(ev.data, "%Y-%m-%d").date()
                    if d_ev.year == ano_sel and d_ev.month == mes_num:
                        status_blq = "🚫 **Sem Aula / Pauta Bloqueada**" if ev.bloqueia_pauta else "✅ **Aula Mantida**"
                        desc_str = f" ({ev.descricao})" if ev.descricao else ""
                        avisos_mes.append(f"• **{d_ev.strftime('%d/%m/%Y')}** — {ev.tipo_evento}{desc_str} | {status_blq}")
                except:
                    pass

            if avisos_mes:
                st.info("📅 **Calendário & Eventos Deste Mês:**\n\n" + "\n".join(avisos_mes))

            alunos_turma = db.query(Aluno).filter(
                Aluno.turma_id == turma_obj.id,
                Aluno.nome != "",
                Aluno.nome != None
            ).order_by(Aluno.nome).all()

            if not alunos_turma:
                st.info(f"Nenhum aluno cadastrado na turma '{turma_obj.nome}'.")
                db.close()
            else:
                num_dias = calendar.monthrange(ano_sel, mes_num)[1]
                
                # Busca os dias da semana em que o professor leciona esta disciplina na turma
                grade_aulas = db.query(GradeHorario).filter(
                    GradeHorario.turma_id == turma_obj.id,
                    GradeHorario.disciplina == disciplina_sel
                ).all()

                dias_semana_permitidos = {g.dia_semana for g in grade_aulas} if grade_aulas else set(range(5))

                dias_uteis_mes = []
                for dia in range(1, num_dias + 1):
                    d_atual = date(ano_sel, mes_num, dia)
                    d_str = d_atual.strftime("%Y-%m-%d")
                    
                    # Filtra: dia da semana útil + dentro do trimestre + sem bloqueio + cadastrado na grade
                    if d_atual.weekday() < 5 and (dt_inicio_trim <= d_atual <= dt_fim_trim) and (d_str not in dias_bloqueados_strs) and (d_atual.weekday() in dias_semana_permitidos):
                        dias_uteis_mes.append(d_atual)

                total_dias_uteis = len(dias_uteis_mes)

                st.markdown(f"##### Pauta de Frequência: **{turma_obj.nome}** | **{disciplina_sel}** (`{total_dias_uteis} Dias de Aula no Mês`) *[{dt_inicio_trim.strftime('%d/%m')} a {dt_fim_trim.strftime('%d/%m')}]*")

                for aluno in alunos_turma:
                    for dt in dias_uteis_mes:
                        chave = f"freq_{aluno.id}_{dt.strftime('%Y%m%d')}_{disciplina_sel}"
                        if chave not in st.session_state.estado_pauta:
                            freq_bd = db.query(FrequenciaDiaria).filter(
                                FrequenciaDiaria.aluno_id == aluno.id,
                                FrequenciaDiaria.disciplina == disciplina_sel,
                                FrequenciaDiaria.data_aula == dt
                            ).first()
                            st.session_state.estado_pauta[chave] = freq_bd.status if freq_bd else "."

                larguras = [0.45, 4.2] + [0.48] * max(total_dias_uteis, 1) + [0.4, 0.4, 0.9]

                cols_head = st.columns(larguras)
                with cols_head[0]:
                    st.markdown("**Nº**")
                with cols_head[1]:
                    st.markdown("**Aluno**")

                for idx_d, dt in enumerate(dias_uteis_mes):
                    with cols_head[idx_d + 2]:
                        st.markdown(f"**{dt.day:02d}**")

                with cols_head[total_dias_uteis + 2]:
                    st.markdown("**F**")
                with cols_head[total_dias_uteis + 3]:
                    st.markdown("**FJ**")
                with cols_head[total_dias_uteis + 4]:
                    st.markdown("**% Pres**")

                st.markdown("<hr style='margin: 2px 0px;'>", unsafe_allow_html=True)

                for idx_a, aluno in enumerate(alunos_turma):
                    cols_aluno = st.columns(larguras)

                    tot_p = 0
                    tot_f = 0
                    tot_fj = 0
                    
                    eh_inativo = (aluno.status != "Ativo")

                    with cols_aluno[0]:
                        st.caption(f"**{idx_a + 1}**")
                    with cols_aluno[1]:
                        if eh_inativo:
                            st.markdown(f"<div class='nome-aluno-inativo'>{aluno.nome.upper()}<br><small>[{aluno.status.upper()}]</small></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='nome-aluno-box'>{aluno.nome.upper()}</div>", unsafe_allow_html=True)

                    for idx_d, dt in enumerate(dias_uteis_mes):
                        chave = f"freq_{aluno.id}_{dt.strftime('%Y%m%d')}_{disciplina_sel}"
                        val_atual = st.session_state.estado_pauta.get(chave, ".")

                        if val_atual == ".":
                            tot_p += 1
                        elif val_atual == "F":
                            tot_f += 1
                        elif val_atual == "FJ":
                            tot_fj += 1

                        with cols_aluno[idx_d + 2]:
                            if st.button(val_atual, key=f"btn_{chave}", disabled=eh_inativo):
                                if val_atual == ".":
                                    st.session_state.estado_pauta[chave] = "F"
                                elif val_atual == "F":
                                    st.session_state.estado_pauta[chave] = "."
                                st.rerun()

                    perc_p = (tot_p / total_dias_uteis * 100) if total_dias_uteis > 0 else 0.0

                    with cols_aluno[total_dias_uteis + 2]:
                        st.caption(f"**{tot_f}**")
                    with cols_aluno[total_dias_uteis + 3]:
                        st.caption(f"**{tot_fj}**")
                    with cols_aluno[total_dias_uteis + 4]:
                        st.caption(f"**% {perc_p:.1f}**")

                    st.markdown("<hr style='margin: 1px 0px;'>", unsafe_allow_html=True)

                st.write("")
                
                col_btn, col_msg, _ = st.columns([1.5, 2.5, 3])
                with col_btn:
                    btn_salvar_bd = st.button("💾 Salvar Pauta no Banco", use_container_width=True)
                
                with col_msg:
                    if st.session_state.msg_sucesso_freq:
                        st.markdown("<div class='msg-sucesso-block'>✅ Alterações salvas com sucesso!</div>", unsafe_allow_html=True)
                        st.session_state.msg_sucesso_freq = False

                if btn_salvar_bd:
                    try:
                        for aluno in alunos_turma:
                            if aluno.status == "Ativo":
                                for dt in dias_uteis_mes:
                                    chave = f"freq_{aluno.id}_{dt.strftime('%Y%m%d')}_{disciplina_sel}"
                                    st_val = st.session_state.estado_pauta.get(chave, ".")

                                    freq_reg = db.query(FrequenciaDiaria).filter(
                                        FrequenciaDiaria.aluno_id == aluno.id,
                                        FrequenciaDiaria.disciplina == disciplina_sel,
                                        FrequenciaDiaria.data_aula == dt
                                    ).first()

                                    if freq_reg:
                                        freq_reg.status = st_val
                                    else:
                                        novo_freq = FrequenciaDiaria(
                                            data_aula=dt,
                                            disciplina=disciplina_sel,
                                            status=st_val,
                                            aluno_id=aluno.id
                                        )
                                        db.add(novo_freq)

                        db.commit()
                        st.session_state.msg_sucesso_freq = True
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Erro ao salvar no banco: {e}")
                    finally:
                        db.close()
                else:
                    db.close()

    elif menu == "Registro de Conteúdo / Aulas":
        st.subheader("📖 Diário de Classe - Registro de Conteúdo e Aulas")

        db = next(get_db())
        turmas, _ = obter_turmas_e_disciplinas_professor(db)

        if not turmas:
            st.warning("Nenhuma turma alocada.")
            db.close()
        else:
            mapa_turmas = {f"{t.nome} ({t.turno})": t for t in turmas}
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                turma_sel_nome = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()))
                turma_obj = mapa_turmas[turma_sel_nome]

            _, disciplinas_permitidas = obter_turmas_e_disciplinas_professor(db, turma_obj.id)

            with col_c2:
                disciplina_sel = st.selectbox("📖 Disciplina:", disciplinas_permitidas)
            with col_c3:
                trimestre_sel = st.selectbox("📅 Trimestre:", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])

            cal_reg = db.query(CalendarioEscolar).filter(
                CalendarioEscolar.ano_letivo == 2027,
                CalendarioEscolar.trimestre == trimestre_sel
            ).first()

            d_i_tr = cal_reg.data_inicio if cal_reg else date(2027, 2, 1)
            d_f_tr = cal_reg.data_fim if cal_reg else date(2027, 5, 30)

            st.caption(f"📌 Período Letivo do {trimestre_sel}: **{d_i_tr.strftime('%d/%m/%Y')}** até **{d_f_tr.strftime('%d/%m/%Y')}**")
            st.markdown("---")

            eventos_bloqueados_db = db.query(EventoCalendario).filter(EventoCalendario.bloqueia_pauta == True).all()
            mapa_bloqueios = {ev.data: ev for ev in eventos_bloqueados_db}

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                data_aula_reg = st.date_input("🗓️ Data da Aula", value=d_i_tr, min_value=d_i_tr, max_value=d_f_tr, format="DD/MM/YYYY")
            with col_r2:
                qtd_aulas = st.number_input("🔢 Quantidade de Aulas", min_value=1, max_value=5, value=2, step=1)

            data_aula_str = data_aula_reg.strftime("%Y-%m-%d")
            eh_data_bloqueada = data_aula_str in mapa_bloqueios

            if eh_data_bloqueada:
                ev_bloq = mapa_bloqueios[data_aula_str]
                desc_ev = f" ({ev_bloq.descricao})" if ev_bloq.descricao else ""
                st.error(f"🚫 **Data Bloqueada pela Secretaria:** Não é possível registrar conteúdo no dia **{data_aula_reg.strftime('%d/%m/%Y')}** devido ao evento **{ev_bloq.tipo_evento}{desc_ev}**.")

            with st.form("form_registro_conteudo", clear_on_submit=True):
                st.markdown("##### ✏️ Detalhes da Aula")
                objeto_conhecimento = st.text_input("Objeto de Conhecimento / Título da Aula (Ex: Introdução à Ética Aristotélica)")
                conteudo_detalhado = st.text_area("Conteúdo Trabalhado / Atividades Realizadas", height=80)
                metodologia_obs = st.text_input("Metodologia / Recursos / Observações (Opcional)")

                btn_salvar_conteudo = st.form_submit_button("💾 Salvar Registro de Conteúdo", use_container_width=True)

                if btn_salvar_conteudo:
                    if eh_data_bloqueada:
                        st.error("🚫 A gravação foi cancelada pois a data selecionada está bloqueada no calendário escolar.")
                        st.stop()
                    elif not objeto_conhecimento.strip() or not conteudo_detalhado.strip():
                        st.warning("Preencha o Objeto de Conhecimento e o Conteúdo Trabalhado.")
                    else:
                        try:
                            novo_reg_cont = RegistroConteudo(
                                data_aula=data_aula_reg,
                                qtd_aulas=qtd_aulas,
                                disciplina=disciplina_sel,
                                trimestre=trimestre_sel,
                                turma_id=turma_obj.id,
                                objeto_conhecimento=objeto_conhecimento.strip(),
                                conteudo_detalhado=conteudo_detalhado.strip(),
                                metodologia_obs=metodologia_obs.strip() if metodologia_obs.strip() else None,
                                professor_nome=user["nome"]
                            )
                            db.add(novo_reg_cont)
                            db.commit()
                            st.success(f"Conteúdo do dia {data_aula_reg.strftime('%d/%m/%Y')} registrado com sucesso!")
                        except Exception as e:
                            db.rollback()
                            st.error(f"Erro ao salvar registro de conteúdo: {e}")

            db.close()

    elif menu == "Lançamento de Notas":
        st.subheader("📝 Lançamento de Notas e Recuperações")

        db = next(get_db())
        turmas, _ = obter_turmas_e_disciplinas_professor(db)

        if not turmas:
            st.warning("Nenhuma turma alocada.")
            db.close()
        else:
            mapa_turmas = {f"{t.nome} ({t.turno})": t for t in turmas}
            col_p1, col_p2, col_p3, col_p4 = st.columns([2.2, 2.0, 1.8, 1.2])
            with col_p1:
                turma_sel_nome = st.selectbox("🏫 Turma:", list(mapa_turmas.keys()))
                turma_obj = mapa_turmas[turma_sel_nome]

            _, disciplinas_permitidas = obter_turmas_e_disciplinas_professor(db, turma_obj.id)

            with col_p2:
                disciplina_sel = st.selectbox("📖 Disciplina:", disciplinas_permitidas)
            with col_p3:
                trimestre_sel = st.selectbox("📅 Trimestre:", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            with col_p4:
                ano_sel = st.number_input("Ano Letivo", min_value=2024, max_value=2030, value=2027)

            cal_reg_n = db.query(CalendarioEscolar).filter(
                CalendarioEscolar.ano_letivo == ano_sel,
                CalendarioEscolar.trimestre == trimestre_sel
            ).first()

            dt_i_n = cal_reg_n.data_inicio if cal_reg_n else date(ano_sel, 2, 1)
            dt_f_n = cal_reg_n.data_fim if cal_reg_n else date(ano_sel, 5, 30)

            alunos_turma = db.query(Aluno).filter(
                Aluno.turma_id == turma_obj.id,
                Aluno.nome != "",
                Aluno.nome != None
            ).order_by(Aluno.nome).all()

            if not alunos_turma:
                st.info(f"Nenhum aluno cadastrado na turma '{turma_obj.nome}'.")
                db.close()
            else:
                max_trim = 30.0 if trimestre_sel in ["1º Trimestre", "2º Trimestre"] else 40.0
                eh_terceiro = (trimestre_sel == "3º Trimestre")

                cols_largura = [2.2, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 1.0, 1.0, 1.0]

                st.markdown(f"##### Pauta de Notas: **{turma_obj.nome}** | **{disciplina_sel}** - **{trimestre_sel}** `(Máx: {max_trim:.0f} pts)` *[Período: {dt_i_n.strftime('%d/%m/%Y')} a {dt_f_n.strftime('%d/%m/%Y')}]*")

                with st.form("form_diario_notas_duplas", clear_on_submit=False):
                    dados_inputs_notas = {}

                    cols_head = st.columns(cols_largura)
                    with cols_head[0]: st.markdown("**Aluno**")
                    with cols_head[1]: st.markdown("**N1**")
                    with cols_head[2]: st.markdown("**RP1**")
                    with cols_head[3]: st.markdown("**N2**")
                    with cols_head[4]: st.markdown("**RP2**")
                    with cols_head[5]: st.markdown("**N3**")
                    with cols_head[6]: st.markdown("**RP3**")
                    with cols_head[7]: st.markdown("**N4**")
                    with cols_head[8]: st.markdown("**RP4**")
                    
                    if eh_terceiro:
                        with cols_head[9]: st.markdown("**Total Trim.**")
                        with cols_head[10]: st.markdown("**Rec. Final**")
                    else:
                        with cols_head[9]: st.markdown("**Rec. Trim.**")
                        with cols_head[10]: st.markdown("**Total Trim.**")

                    with cols_head[11]: st.markdown("**Total Anual**")

                    st.markdown("<hr style='margin: 2px 0px;'>", unsafe_allow_html=True)

                    for idx, aluno in enumerate(alunos_turma):
                        eh_inativo = (aluno.status != "Ativo")

                        notas_aluno_db = db.query(Nota).filter(
                            Nota.aluno_id == aluno.id,
                            Nota.disciplina == disciplina_sel
                        ).all()

                        val_n = [0.0]*4
                        val_rp = [0.0]*4
                        for i in range(1, 5):
                            reg_n = next((n for n in notas_aluno_db if n.trimestre == f"{trimestre_sel}_N{i}"), None)
                            reg_rp = next((n for n in notas_aluno_db if n.trimestre == f"{trimestre_sel}_RP{i}"), None)
                            if reg_n and reg_n.valor_nota is not None: val_n[i-1] = float(reg_n.valor_nota)
                            if reg_rp and reg_rp.valor_nota is not None: val_rp[i-1] = float(reg_rp.valor_nota)

                        if eh_terceiro:
                            reg_rf = next((n for n in notas_aluno_db if n.trimestre == "Rec_Final"), None)
                            val_rec_extra = float(reg_rf.valor_nota) if reg_rf and reg_rf.valor_nota is not None else 0.0
                        else:
                            reg_rt = next((n for n in notas_aluno_db if n.trimestre == f"{trimestre_sel}_RecTrim"), None)
                            val_rec_extra = float(reg_rt.valor_nota) if reg_rt and reg_rt.valor_nota is not None else 0.0

                        t1 = sum_trim_simples_isolado(db, aluno.id, disciplina_sel, "1º Trimestre")
                        t2 = sum_trim_simples_isolado(db, aluno.id, disciplina_sel, "2º Trimestre")

                        cols_linha = st.columns(cols_largura)
                        with cols_linha[0]:
                            if eh_inativo:
                                st.markdown(f"<div class='nome-aluno-inativo'><b>{idx + 1}.</b> {aluno.nome.upper()}<br><small>[{aluno.status.upper()}]</small></div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='nome-aluno-box'><b>{idx + 1}.</b> {aluno.nome.upper()}</div>", unsafe_allow_html=True)

                        dados_inputs_notas[aluno.id] = {"notas": [], "rps": [], "ativo": not eh_inativo}
                        t_tag = trimestre_sel.replace(" ", "_")

                        soma_efetiva = 0.0
                        for i in range(4):
                            with cols_linha[1 + (i*2)]:
                                n_val = st.number_input(f"N{i+1}_{aluno.id}_{t_tag}", min_value=0.0, max_value=max_trim, value=val_n[i], step=0.5, label_visibility="collapsed", disabled=eh_inativo)
                            with cols_linha[2 + (i*2)]:
                                rp_val = st.number_input(f"RP{i+1}_{aluno.id}_{t_tag}", min_value=0.0, max_value=max_trim, value=val_rp[i], step=0.5, label_visibility="collapsed", disabled=eh_inativo)
                            
                            dados_inputs_notas[aluno.id]["notas"].append(n_val)
                            dados_inputs_notas[aluno.id]["rps"].append(rp_val)
                            soma_efetiva += max(n_val, rp_val)

                        if eh_terceiro:
                            total_trimestral = soma_efetiva
                            with cols_linha[9]:
                                st.caption(f"**{total_trimestral:.1f}**")
                            with cols_linha[10]:
                                rec_f_val = st.number_input(f"RecF_{aluno.id}", min_value=0.0, max_value=100.0, value=val_rec_extra, step=1.0, label_visibility="collapsed", disabled=eh_inativo)
                                dados_inputs_notas[aluno.id]["rec_final"] = rec_f_val
                            
                            soma_anual_parcial = t1 + t2 + total_trimestral
                            total_anual = max(soma_anual_parcial, dados_inputs_notas[aluno.id]["rec_final"])
                        else:
                            with cols_linha[9]:
                                rec_trim_val = st.number_input(f"RT_{aluno.id}_{t_tag}", min_value=0.0, max_value=max_trim, value=val_rec_extra, step=0.5, label_visibility="collapsed", disabled=eh_inativo)
                                dados_inputs_notas[aluno.id]["rec_trim"] = rec_trim_val
                            
                            total_trimestral = max(soma_efetiva, dados_inputs_notas[aluno.id]["rec_trim"])
                            outros_t = [t for t in ["1º Trimestre", "2º Trimestre", "3º Trimestre"] if t != trimestre_sel]
                            soma_outros = sum([sum_trim_simples_isolado(db, aluno.id, disciplina_sel, t) for t in outros_t])
                            total_anual = soma_outros + total_trimestral

                            with cols_linha[10]:
                                st.caption(f"**{total_trimestral:.1f}**")

                        with cols_linha[11]:
                            badge_s = "✅" if total_anual >= 60.0 else "⚠️"
                            st.caption(f"{badge_s} **{total_anual:.1f}**")

                        st.markdown("<hr style='margin: 1px 0px;'>", unsafe_allow_html=True)

                    col_btn_n, col_msg_n, _ = st.columns([1.5, 2.5, 3])
                    with col_btn_n:
                        btn_salvar_notas = st.form_submit_button(f"💾 Salvar Notas", use_container_width=True)
                    
                    with col_msg_n:
                        if st.session_state.msg_sucesso_notas:
                            st.markdown("<div class='msg-sucesso-block'>✅ Alterações salvas com sucesso!</div>", unsafe_allow_html=True)
                            st.session_state.msg_sucesso_notas = False

                    if btn_salvar_notas:
                        try:
                            for aluno_id, dic_v in dados_inputs_notas.items():
                                if dic_v.get("ativo", True):
                                    db.query(Nota).filter(
                                        Nota.aluno_id == aluno_id,
                                        Nota.disciplina == disciplina_sel,
                                        Nota.trimestre.like(f"{trimestre_sel}%")
                                    ).delete(synchronize_session=False)

                                    if eh_terceiro:
                                        db.query(Nota).filter(
                                            Nota.aluno_id == aluno_id,
                                            Nota.disciplina == disciplina_sel,
                                            Nota.trimestre == "Rec_Final"
                                        ).delete(synchronize_session=False)

                                    for i in range(4):
                                        db.add(Nota(disciplina=disciplina_sel, trimestre=f"{trimestre_sel}_N{i+1}", valor_nota=dic_v["notas"][i], aluno_id=aluno_id))
                                        db.add(Nota(disciplina=disciplina_sel, trimestre=f"{trimestre_sel}_RP{i+1}", valor_nota=dic_v["rps"][i], aluno_id=aluno_id))

                                    if eh_terceiro:
                                        db.add(Nota(disciplina=disciplina_sel, trimestre="Rec_Final", valor_nota=dic_v.get("rec_final", 0.0), aluno_id=aluno_id))
                                    else:
                                        db.add(Nota(disciplina=disciplina_sel, trimestre=f"{trimestre_sel}_RecTrim", valor_nota=dic_v.get("rec_trim", 0.0), aluno_id=aluno_id))

                            db.commit()
                            st.session_state.msg_sucesso_notas = True
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Erro ao salvar notas: {e}")
                        finally:
                            db.close()
