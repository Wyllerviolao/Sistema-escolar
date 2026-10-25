from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Turma(Base):
    __tablename__ = "turmas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    turno = Column(String)
    ano_letivo = Column(Integer, default=2027)

    alunos = relationship("Aluno", back_populates="turma", cascade="all, delete-orphan")

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    matricula = Column(String, nullable=True)
    nome_mae = Column(String, nullable=True)
    cpf = Column(String, nullable=True)
    raca_cor = Column(String, nullable=True)
    nis = Column(String, nullable=True)
    status = Column(String, default="Ativo")
    turma_id = Column(Integer, ForeignKey("turmas.id"))

    turma = relationship("Turma", back_populates="alunos")
    notas = relationship("Nota", back_populates="aluno", cascade="all, delete-orphan")
    frequencias = relationship("FrequenciaDiaria", back_populates="aluno", cascade="all, delete-orphan")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String, unique=True, index=True)
    telefone = Column(String, nullable=True)
    senha_hash = Column(String)
    perfil = Column(String)  # "secretaria", "pedagogico", "professor"
    turmas_permitidas = Column(String, default="")
    disciplinas_turmas = Column(String, default="{}")

class Nota(Base):
    __tablename__ = "notas"

    id = Column(Integer, primary_key=True, index=True)
    disciplina = Column(String)
    trimestre = Column(String)
    valor_nota = Column(Float, default=0.0)
    aluno_id = Column(Integer, ForeignKey("alunos.id"))

    aluno = relationship("Aluno", back_populates="notas")

class FrequenciaDiaria(Base):
    __tablename__ = "frequencia_diaria"

    id = Column(Integer, primary_key=True, index=True)
    data_aula = Column(Date)
    disciplina = Column(String)
    status = Column(String, default=".")  # ".", "F", "FJ"
    aluno_id = Column(Integer, ForeignKey("alunos.id"))

    aluno = relationship("Aluno", back_populates="frequencias")

class CalendarioEscolar(Base):
    __tablename__ = "calendario_escolar"

    id = Column(Integer, primary_key=True, index=True)
    ano_letivo = Column(Integer)
    trimestre = Column(String)
    data_inicio = Column(Date)
    data_fim = Column(Date)

class DisciplinaEscola(Base):
    __tablename__ = "disciplinas_escola"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)

class EventoCalendario(Base):
    __tablename__ = "eventos_calendario"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(String, unique=True, index=True)
    tipo_evento = Column(String)
    descricao = Column(String, nullable=True)
    bloqueia_pauta = Column(Boolean, default=True)

class RegistroConteudo(Base):
    __tablename__ = "registros_conteudo"

    id = Column(Integer, primary_key=True, index=True)
    data_aula = Column(Date)
    qtd_aulas = Column(Integer, default=1)
    disciplina = Column(String)
    trimestre = Column(String)
    turma_id = Column(Integer, ForeignKey("turmas.id"))
    objeto_conhecimento = Column(String)
    conteudo_detalhado = Column(String)
    metodologia_obs = Column(String, nullable=True)
    professor_nome = Column(String, nullable=True)

class GradeHorario(Base):
    __tablename__ = "grade_horario"

    id = Column(Integer, primary_key=True, index=True)
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=False)
    dia_semana = Column(Integer, nullable=False)  # 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta
    numero_aula = Column(Integer, nullable=False) # 1, 2, 3, 4, 5, 6...
    disciplina = Column(String, nullable=False)
    professor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    data_inicio_vigencia = Column(Date, nullable=False)

    turma = relationship("Turma")
    professor = relationship("Usuario")