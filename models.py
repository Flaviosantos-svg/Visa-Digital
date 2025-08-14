from extensions import db # <-- Essa é a importação CORRETA para o 'db'
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


notificacao_fiscais = db.Table('notificacao_fiscais',
    db.Column('notificacao_id', db.Integer, db.ForeignKey('notificacoes.id'), primary_key=True),
    db.Column('funcionario_id', db.Integer, db.ForeignKey('funcionarios.id'), primary_key=True)
)

# ==============================================================================
# 1. MODELOS DE BASE
# ==============================================================================
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Empresas(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(200), nullable=False)
    protocolo = db.Column(db.String(50), unique=False, nullable=True) 
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    nome_fantasia = db.Column(db.String(200))
    porte = db.Column(db.String(50))
    data_abertura = db.Column(db.String(20))
    situacao_cadastral = db.Column(db.String(50))
    cnae_principal = db.Column(db.String(255))
    cnae_secundario = db.Column(db.Text)
    licencas_publicas = db.relationship('LicencasPublicas', back_populates='empresa', lazy=True)
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(255)) # Campo consolidado
    
    # Contato
    telefone_empresa = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Responsáveis
    responsavel_juridico_nome = db.Column(db.String(150))
    responsavel_juridico_cpf = db.Column(db.String(14))
    responsavel_juridico_tel = db.Column(db.String(20))
    
    contador_presente = db.Column(db.Boolean, default=False, nullable=False)
    contador_nome = db.Column(db.String(150), nullable=True) 
    contador_cpf = db.Column(db.String(14), nullable=True)   
    contador_tel = db.Column(db.String(20), nullable=True)   
    
    # Horários de Funcionamento (Garantindo que todos existem)
    horario_segunda_feira = db.Column(db.String(50), nullable=True)
    horario_terca_feira = db.Column(db.String(50), nullable=True)
    horario_quarta_feira = db.Column(db.String(50), nullable=True)
    horario_quinta_feira = db.Column(db.String(50), nullable=True)
    horario_sexta_feira = db.Column(db.String(50), nullable=True)
    horario_sabado = db.Column(db.String(50), nullable=True)
    horario_domingo = db.Column(db.String(50), nullable=True)
    funciona_feriado = db.Column(db.String(10), nullable=True)
    horario_feriado = db.Column(db.String(50), nullable=True)
    
    # Status e Datas
    status = db.Column(db.String(50), default='Em análise') 
    justificativa_status = db.Column(db.Text, nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com Licenças
    licencas = db.relationship('LicencaEmpresa', back_populates='empresa', lazy=True, cascade="all, delete-orphan")
    denuncias = db.relationship('Denuncias', backref='empresa', lazy=True)
    def __repr__(self):
        return f'<Empresas {self.id}: {self.nome_fantasia or self.razao_social}>'

# A classe ProtocoloSequencial já está correta com 'categoria'
class ProtocoloSequencial(db.Model):
    __tablename__ = 'protocolo_sequencial'
    
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    ultimo_numero = db.Column(db.Integer, nullable=False, default=0)
    
    # Garante que a combinação de ano e categoria seja sempre única
    __table_args__ = (db.UniqueConstraint('ano', 'categoria', name='_ano_categoria_uc'),)

    def __repr__(self):
        return f'<ProtocoloSequencial {self.categoria}-{self.ano}/{self.ultimo_numero}>'

class Checklist(db.Model):
    __tablename__ = 'checklists'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    # Armazena a estrutura de seções e perguntas como JSON
    itens = db.Column(db.JSON, nullable=True) 
    # CAMPO ATUALIZADO: Adicionado server_default='1' para a migração funcionar
    ativo = db.Column(db.Boolean, default=True, nullable=False, server_default='1')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Checklist {self.titulo}>'



# ==============================================================================
# 2. MODELOS DEPENDENTES
# ==============================================================================
class LicencaEmpresa(db.Model):
    __tablename__ = 'licencas_empresa'
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(20), unique=True, nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    status = db.Column(db.String(50), default='Pendente')
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_validade = db.Column(db.Date, nullable=True)
    ano_exercicio = db.Column(db.Integer)
    observacoes = db.Column(db.Text, nullable=True)
    alvara_pdf_path = db.Column(db.String(255), nullable=True)
    e_mei = db.Column(db.String(10), nullable=True)
    comprovante_taxa_path = db.Column(db.String(255), nullable=True)

    # --- CAMPOS DO FORMULÁRIO ---
    
    # Informações Gerais
    tipo_atividade = db.Column(db.String(100))
    descricao_atividade = db.Column(db.Text)

    # Local Físico
    possui_local_fisico = db.Column(db.String(10))
    endereco_completo = db.Column(db.String(300), nullable=True)

    # Responsável Técnico (RT)
    necessita_rt = db.Column(db.String(10))
    rt_nome = db.Column(db.String(150), nullable=True)
    rt_cpf = db.Column(db.String(20), nullable=True)
    rt_conselho = db.Column(db.String(50), nullable=True)
    rt_numero_conselho = db.Column(db.String(50), nullable=True)
    rt_declaracao_path = db.Column(db.String(255), nullable=True)

    # Medicamentos Controlados (AFE)
    vende_controlados = db.Column(db.String(10))
    afe_numero = db.Column(db.String(100), nullable=True)
    afe_anexo_path = db.Column(db.String(255), nullable=True)

    # Retinóicos
    vende_retinoicos = db.Column(db.String(10))
    retinoicos_numero_autorizacao = db.Column(db.String(100), nullable=True)
    retinoicos_data_autorizacao = db.Column(db.Date, nullable=True)
    retinoicos_validade = db.Column(db.Date, nullable=True)
    retinoicos_anexo_path = db.Column(db.String(255), nullable=True)
    
    realiza_manipulacao = db.Column(db.String(10), nullable=True)

    # Animais Vivos
    vende_animais = db.Column(db.String(10))
    rt_vet_nome = db.Column(db.String(150), nullable=True)
    rt_vet_cpf = db.Column(db.String(20), nullable=True)
    rt_vet_crmv = db.Column(db.String(50), nullable=True)
    rt_vet_declaracao_path = db.Column(db.String(255), nullable=True)

    # Dedetização
    realizou_dedetizacao = db.Column(db.String(10))
    dedetizacao_data = db.Column(db.Date, nullable=True)
    dedetizacao_anexo_path = db.Column(db.String(255), nullable=True)
    anexos_pendencia = db.Column(db.JSON, nullable=True)
    # --- RELACIONAMENTO CORRIGIDO ---
    # Esta é a principal alteração. Removemos o 'backref' que causava o conflito.
    # Assumimos que o modelo 'Empresas' tem um relacionamento chamado 'licencas'.
    empresa = db.relationship('Empresas', back_populates='licencas')


class LicencaAutonomo(db.Model):
    __tablename__ = 'licencas_autonomos'
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(50), unique=True, nullable=False)
    autonomo_id = db.Column(db.Integer, db.ForeignKey('autonomos.id'), nullable=False)
    status = db.Column(db.String(50), default='Pendente')
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos do formulário
    nacionalidade = db.Column(db.String(50))
    estado_civil = db.Column(db.String(50))
    local_atuacao_endereco = db.Column(db.String(255))
    local_atuacao_tipo = db.Column(db.String(100))
    local_atuacao_referencia = db.Column(db.String(255))
    descricao_atividade = db.Column(db.Text)
    possui_rt = db.Column(db.String(10))
    rt_nome = db.Column(db.String(150), nullable=True)
    rt_cpf = db.Column(db.String(20), nullable=True)
    rt_conselho = db.Column(db.String(50), nullable=True)
    usa_quimicos = db.Column(db.String(10))
    usa_perfuro = db.Column(db.String(10))
    faz_invasivo = db.Column(db.String(10))
    invasivo_descricao = db.Column(db.Text, nullable=True)
    ano_exercicio = db.Column(db.Integer, nullable=True)
   
    # Caminhos dos documentos
    rt_declaracao_path = db.Column(db.String(255), nullable=True)
    doc_identidade_path = db.Column(db.String(255), nullable=True)
    doc_cpf_path = db.Column(db.String(255), nullable=True)
    doc_residencia_path = db.Column(db.String(255), nullable=True)
    doc_formacao_path = db.Column(db.String(255), nullable=True)
    doc_dedetizacao_path = db.Column(db.String(255), nullable=True)
    doc_alvara_funcionamento_path = db.Column(db.String(255), nullable=True)
    alvara_pdf_path = db.Column(db.String(255), nullable=True)
    autonomo = db.relationship('Autonomo', back_populates='licencas')
    observacoes = db.Column(db.Text, nullable=True)



    def __repr__(self):
        return f'<LicencaAutonomo {self.protocolo}>'

class LicencaEvento(db.Model):
    __tablename__ = 'licencas_eventos'
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(50), unique=True, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    anexos_pendencia = db.Column(db.JSON, nullable=True)
    # Dados do Solicitante
    solicitante_nome = db.Column(db.String(150), nullable=False)
    solicitante_cpf_cnpj = db.Column(db.String(18), nullable=False)
    solicitante_rg = db.Column(db.String(20))
    solicitante_telefone = db.Column(db.String(20))
    solicitante_email = db.Column(db.String(120))
    solicitante_endereco = db.Column(db.String(250))

    # Dados do Evento
    nome_evento = db.Column(db.String(150), nullable=False)
    tipos_evento = db.Column(db.String(255)) # Guarda os tipos de evento selecionados
    local_evento = db.Column(db.String(250))
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    horario = db.Column(db.String(50))

    # Estrutura do Evento
    vende_bebidas = db.Column(db.String(10))
    tipo_casco = db.Column(db.String(20))
    usa_estrutura_montavel = db.Column(db.String(10))
    usa_churrasqueira = db.Column(db.String(10))
    churrasqueira_tipo = db.Column(db.String(20))
    churrasqueira_gas_validade = db.Column(db.String(10))
    usa_fritadeira = db.Column(db.String(10))
    fritadeira_gas_validade = db.Column(db.String(10))
    manipula_alimentos = db.Column(db.String(10))
    tem_pia = db.Column(db.String(10))

    # Liberação dos Bombeiros
    bombeiros_liberacao = db.Column(db.String(10))
    bombeiros_numero = db.Column(db.String(50))
    bombeiros_data = db.Column(db.Date)
    
    # Caminhos dos Documentos Anexados
    doc_bombeiros_path = db.Column(db.String(255))
    doc_cpf_cnpj_path = db.Column(db.String(255))
    doc_alvara_local_path = db.Column(db.String(255))
    doc_autorizacao_rua_path = db.Column(db.String(255))

    # Status e Metadados
    status = db.Column(db.String(50), default='Pendente')
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_validade = db.Column(db.Date, nullable=True)
    alvara_pdf_path = db.Column(db.String(300), nullable=True)

    def __repr__(self):
        return f'<LicencaEvento {self.nome_evento}>'


class LicencasPublicas(db.Model):
    __tablename__ = 'licencas_publicas'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    protocolo_licencas_publicas = db.Column(db.String, unique=True, nullable=False)
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String, default='Pendente')
    observacoes = db.Column(db.Text, nullable=True) 
    data_validade = db.Column(db.Date, nullable=True)

    # --- INÍCIO DA ALTERAÇÃO ---
    # Adicionados os campos para armazenar a resposta do cidadão a uma pendência
    resposta_pendencia_texto = db.Column(db.Text, nullable=True)
    anexo_pendencia_path = db.Column(db.String, nullable=True)
    # --- FIM DA ALTERAÇÃO ---

    unidade_nome = db.Column(db.String)
    unidade_cnes_inep = db.Column(db.String)
    unidade_endereco = db.Column(db.String)
    unidade_ponto_ref = db.Column(db.String)
    unidade_tipo = db.Column(db.String)
    unidade_tipo_outro = db.Column(db.String)
    responsavel_unidade_nome = db.Column(db.String)
    responsavel_unidade_cpf = db.Column(db.String)
    responsavel_unidade_cargo = db.Column(db.String)
    responsavel_unidade_conselho = db.Column(db.String)
    responsavel_unidade_contato = db.Column(db.String)
    responsavel_unidade_declaracao_rt_path = db.Column(db.String)
    atividades_desenvolvidas = db.Column(db.Text)
    servicos_prestados = db.Column(db.Text)
    possui_cozinha = db.Column(db.Boolean)
    possui_farmacia = db.Column(db.Boolean)
    anexo_declaracao_responsavel_path = db.Column(db.String)
    anexo_declaracao_rt_geral_path = db.Column(db.String)
    observacoes_adicionais = db.Column(db.Text)
    ciencia_solicitante_nome = db.Column(db.String)
    ciencia_solicitante_cargo = db.Column(db.String)
    
    empresa = db.relationship('Empresas', back_populates='licencas_publicas')


class Denuncias(db.Model):
    __tablename__ = 'denuncias'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    protocolo_denuncia = db.Column(db.String, unique=True, nullable=False)
    data_denuncia = db.Column(db.DateTime, default=datetime.utcnow)
    anonimato = db.Column(db.Boolean)
    denunciante_nome = db.Column(db.String)
    denunciante_telefone = db.Column(db.String)
    denunciante_email = db.Column(db.String)
    denunciado_nome = db.Column(db.String)
    denunciado_rua = db.Column(db.String)
    denunciado_numero = db.Column(db.String)
    denunciado_bairro = db.Column(db.String)
    denunciado_municipio = db.Column(db.String)
    denunciado_ponto_ref = db.Column(db.String)
    denunciado_tipo_local = db.Column(db.String)
    motivo_classificacao = db.Column(db.String)
    motivo_descricao = db.Column(db.Text)
    anexos_path = db.Column(db.String)
    status = db.Column(db.String, default='Recebida')
    despacho_fiscal = db.Column(db.Text)
    fiscal_anexos_path = db.Column(db.String)
    cpf_vinculado = db.Column(db.String, nullable=True)
    denunciado_cpf_cnpj = db.Column(db.String(18), nullable=True, index=True)
    acao_gerada = db.Column(db.String, nullable=True)

class Notificacoes(db.Model):
    __tablename__ = 'notificacoes'
    id = db.Column(db.Integer, primary_key=True)
    
    # --- Colunas Mantidas e Adaptadas ---
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    protocolo_notificacao = db.Column(db.String, unique=True, nullable=False)
    data_notificacao = db.Column(db.Date, default=datetime.utcnow)
    ciencia_nome = db.Column(db.String)
    ciencia_documento = db.Column(db.String)
    anexos_path = db.Column(db.String)
    parecer_final = db.Column(db.String, default='Pendente')

    # --- Novos Campos para o Formulário ---
    motivo_notificacao = db.Column(db.Text, nullable=True)
    descricao_irregularidade = db.Column(db.Text, nullable=True)
    prazo_regularizacao = db.Column(db.String(50), nullable=True)

    # --- RELACIONAMENTO MUITOS-PARA-MUITOS (ADICIONADO) ---
    # Este é o campo que cria a ligação com os funcionários através da tabela de associação.
    # O nome 'fiscais_responsaveis' vem do seu erro original.
    fiscais_responsaveis = db.relationship(
        'Funcionario',
        secondary=notificacao_fiscais,
        back_populates='notificacoes_associadas',
        lazy='dynamic' # Opcional: útil para consultas mais eficientes
    )

class AutosInfracao(db.Model):
    __tablename__ = 'autos_infracao'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    protocolo_auto = db.Column(db.String, unique=True, nullable=False)
    data_auto = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    descricao_infracao = db.Column(db.Text, nullable=False)
    artigos_infringidos = db.Column(db.Text)
    penalidades_sugeridas = db.Column(db.Text)
    prazo_defesa_dias = db.Column(db.Integer)
    fiscal_nome = db.Column(db.String)
    anexos_path = db.Column(db.String)
    status = db.Column(db.String, default='Emitido')
    cpf_vinculado = db.Column(db.String(14))


class Vistoria(db.Model):
    __tablename__ = 'vistoria'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    protocolo_vistoria = db.Column(db.String(50), unique=True, nullable=True)
    status_analise = db.Column(db.String(50), nullable=False, server_default='Pendente')
    fotos = db.Column(db.JSON, nullable=True) # Armazenará uma lista de nomes de arquivos
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklists.id'), nullable=True)
    data_vistoria = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(100))
    documentacao_verificada = db.Column(db.JSON)
    checklist_respostas = db.Column(db.JSON)
    # ATUALIZADO: Armazena múltiplas observações e fiscais como JSON
    observacoes = db.Column(db.JSON)
    fiscais = db.Column(db.JSON)
    prazo_adequacao = db.Column(db.Date, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    cpf_cnpj_vinculado = db.Column(db.String(18), nullable=True, index=True)
    # Relacionamentos
    empresa = db.relationship('Empresas')
    checklist = db.relationship('Checklist')

class Irregularidade(db.Model):
    __tablename__ = 'irregularidades'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    infracao = db.Column(db.String(200), nullable=True)
    inciso = db.Column(db.Text, nullable=True)
    explicacao = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Irregularidade {self.nome}>'

class ChecklistPerguntas(db.Model):
    __tablename__ = 'checklist_perguntas'
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklists.id'), nullable=False)
    categoria = db.Column(db.String, default='Geral', nullable=False)
    texto_pergunta = db.Column(db.String, nullable=False)
    ordem = db.Column(db.Integer, default=0)
    tipo_resposta = db.Column(db.String, default='multipla_escolha', nullable=False)

class VistoriaRespostas(db.Model):
    __tablename__ = 'vistoria_respostas'
    id = db.Column(db.Integer, primary_key=True)
    vistoria_id = db.Column(db.Integer, db.ForeignKey('vistoria.id'), nullable=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('checklist_perguntas.id'), nullable=False)
    resposta = db.Column(db.String)
    pergunta = db.relationship('ChecklistPerguntas', lazy='joined')


class SolicitacaoReceituario(db.Model):
    __tablename__ = 'solicitacoes_receituario'
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(50), unique=True, nullable=False) # Protocolo gerado automaticamente
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Dados do Local Solicitante
    cnpj_local = db.Column(db.String(18), nullable=False)
    nome_local = db.Column(db.String(200), nullable=False)
    endereco_local = db.Column(db.String(255), nullable=False)
    numero_local = db.Column(db.String(20)) # Número do endereço
    contato_local = db.Column(db.String(20), nullable=False)

    # Dados do Profissional Solicitante
    nome_profissional = db.Column(db.String(150), nullable=False)
    cpf_profissional = db.Column(db.String(14), nullable=False)
    conselho_profissional = db.Column(db.String(50), nullable=False) # Ex: CRM, CRO, CRMV + número
    telefone_contato = db.Column(db.String(20), nullable=False)
    email_contato = db.Column(db.String(120), nullable=False)

    # Detalhes da Solicitação (que tipos e quantidades foram solicitadas)
    # Vamos armazenar como JSON ou string, pois são dinâmicos.
    # No SQL, isso é um TEXT. No Python, Flask/SQLAlchemy converterá (se usar JSON type)
    # ou você precisará parsear/serializar manualmente. Por simplicidade inicial, String.
    receituarios_solicitados_json = db.Column(db.Text, nullable=False) # JSON: {'A_amarela': '5', 'C_branca': '10'}

    status = db.Column(db.String(50), default='Pendente', nullable=False) # Pendente, Em Análise, Atendida, Recusada
    justificativa_recusa = db.Column(db.Text)
    data_atendimento = db.Column(db.DateTime) # Data em que a solicitação foi atendida

    # Relacionamento com os atendimentos/dispensas (um para muitos)
    atendimentos = db.relationship('AtendimentoReceituario', backref='solicitacao', lazy=True)

    def __repr__(self):
        return f'<SolicitacaoReceituario {self.protocolo} - {self.nome_local}>'

class TipoReceituario(db.Model):
    __tablename__ = 'tipos_receituario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False) # Ex: "Notificação A (Amarela)"
    sigla = db.Column(db.String(10), unique=True, nullable=False) # Ex: "A", "B1", "B2", "C"
    cor_folha = db.Column(db.String(50)) # Ex: "Amarela", "Azul", "Branca"
    folhas_por_bloco = db.Column(db.Integer, nullable=False, default=50) # Padrão, pode variar

    # Relacionamento com EstoqueReceituario e BlocoReceituario
    estoques = db.relationship('EstoqueReceituario', backref='tipo', lazy=True)
    blocos = db.relationship('BlocoReceituario', backref='tipo', lazy=True)

    def __repr__(self):
        return f'<TipoReceituario {self.sigla} - {self.nome}>'

class EstoqueReceituario(db.Model):
    __tablename__ = 'estoque_receituario'
    id = db.Column(db.Integer, primary_key=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipos_receituario.id'), nullable=False, unique=True)
    
    quantidade_blocos_disponivel = db.Column(db.Integer, default=0, nullable=False)
    quantidade_folhas_disponivel = db.Column(db.Integer, default=0, nullable=False) # Total de folhas disponíveis
    
    # Campo para registrar o último número disponível para dispensa. Isso é importante para a sequencia.
    # Ex: Para Receituário A, o ultimo_numero_disponivel pode ser 123456 (referente à folha)
    # Isso seria a folha FINAL do último bloco inserido no estoque.
    # Este campo é mais complexo e pode ser gerenciado por blocos individuais.
    # Por ora, vamos deixar mais simples e focar no BlocoReceituario.
    
    data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Estoque {self.tipo.sigla}: {self.quantidade_blocos_disponivel} blocos>'


# Modelo para gerenciar CADA BLOCO DE RECEITUÁRIO INDIVIDUALMENTE
# Isso é CRÍTICO para controlar a numeração e dispensa sequencial
class BlocoReceituario(db.Model):
    __tablename__ = 'blocos_receituario'
    id = db.Column(db.Integer, primary_key=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipos_receituario.id'), nullable=False)
    
    numero_bloco = db.Column(db.String(50), nullable=False) # Ex: "001", "123A", conforme o controle
    
    numero_inicial = db.Column(db.Integer, nullable=False) # Número da primeira folha do bloco
    numero_final = db.Column(db.Integer, nullable=False)   # Número da última folha do bloco
    
    data_entrada_estoque = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    status = db.Column(db.String(20), default='Disponível', nullable=False) # Disponível, Dispensado, Em Uso, Descartado
    
    # Relacionamento com AtendimentoReceituario: um bloco pode ser dispensado em um atendimento
    # Uma relação muitos-para-muitos ou uma referência ao atendimento que o dispensou.
    # Por simplicidade, vamos adicionar um campo que referencia o atendimento.
    atendimento_id = db.Column(db.Integer, db.ForeignKey('atendimentos_receituario.id'), nullable=True)

    def __repr__(self):
        return f'<Bloco {self.numero_bloco} ({self.tipo.sigla}): {self.numero_inicial}-{self.numero_final} Status: {self.status}>'


# Modelo para registrar CADA ATENDIMENTO/DISPENSA de receituário a um profissional
class AtendimentoReceituario(db.Model):
    __tablename__ = 'atendimentos_receituario'
    id = db.Column(db.Integer, primary_key=True)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey('solicitacoes_receituario.id'), nullable=False)
    data_atendimento = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Informações de quem recebeu
    nome_recebedor = db.Column(db.String(150), nullable=False)
    cpf_recebedor = db.Column(db.String(14), nullable=False)
    telefone_recebedor = db.Column(db.String(20))

    # Detalhes do que foi dispensado neste atendimento (quantos blocos de cada tipo)
    # Por simplicidade, vamos armazenar quais blocos_ids foram dispensados neste atendimento
    # e quais numerações foram atribuídas a ele, se necessário.
    # Ou podemos ter uma relação one-to-many com BlocoReceituario
    blocos_dispensados = db.relationship('BlocoReceituario', backref='atendimento', lazy=True)

    def __repr__(self):
        return f'<Atendimento {self.id} para Sol: {self.solicitacao.protocolo} em {self.data_atendimento.strftime("%Y-%m-%d")}>'

class SolicitacaoCalazar(db.Model):
    __tablename__ = 'solicitacoes_calazar'
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(50), unique=True, nullable=False)
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Dados do Proprietário (do formulário inicial)
    proprietario_nome = db.Column(db.String(150), nullable=False)
    proprietario_cpf = db.Column(db.String(14))
    proprietario_endereco = db.Column(db.String(255), nullable=False)
    proprietario_telefone = db.Column(db.String(20), nullable=False)

    # Dados do Animal (do formulário inicial)
    animal_nome = db.Column(db.String(100), nullable=False)
    animal_especie = db.Column(db.String(50), default="Canina", nullable=False)
    animal_raca = db.Column(db.String(100), nullable=False)
    animal_sexo = db.Column(db.String(10))
    animal_idade = db.Column(db.String(50))
    animal_cor = db.Column(db.String(50))
    animal_foto_path = db.Column(db.String(255))

    # Informações Clínicas e Coleta (do formulário inicial)
    sinais_clinicos = db.Column(db.Text)
    data_coleta_sugerida = db.Column(db.Date)
    horario_coleta_sugerido = db.Column(db.Time)

    # Status da solicitação no processo de análise
    status = db.Column(db.String(50), default='Em Análise', nullable=False)
    data_atendimento = db.Column(db.DateTime) 

    # --- CAMPOS PARA RESULTADOS DO TESTE (ADMINISTRADOR PREENCHE) ---
    data_realizacao_teste = db.Column(db.Date)
    kit_utilizado = db.Column(db.String(100))
    lote_kit = db.Column(db.String(50))
    validade_kit = db.Column(db.Date)
    resultado_teste_rapido = db.Column(db.String(50))
    tipo_teste_realizado = db.Column(db.String(50))
    foto_focinho_path = db.Column(db.String(300), nullable=True)
    foto_patas_path = db.Column(db.String(300), nullable=True)
    foto_corpo_inteiro_path = db.Column(db.String(300), nullable=True)
    foto_teste_rapido_path = db.Column(db.String(300), nullable=True)
    enviado_lacen = db.Column(db.Boolean, default=False, nullable=False) # Garanta que este seja False por padrão

    observacoes_resultado = db.Column(db.Text)
    anamnese_veterinario = db.Column(db.Text)

    veterinario_responsavel_nome = db.Column(db.String(150))
    veterinario_crmv = db.Column(db.String(50))

    # Flag para liberação do resultado para consulta pública
    resultado_liberado = db.Column(db.Boolean, default=False, nullable=False)
    data_liberacao_resultado = db.Column(db.DateTime)

    justificativa_recusa = db.Column(db.Text)

    def __repr__(self):
        return f'<SolicitacaoCalazar {self.protocolo} - Animal: {self.animal_nome}>'

class Funcionario(db.Model):
    __tablename__ = 'funcionarios'  # Nome da tabela no banco de dados

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    cargo = db.Column(db.String(50), nullable=False) # Ex: 'Coordenador', 'Fiscal', 'Administrativo'
    caminho_assinatura = db.Column(db.String(255), nullable=True)

    # --- RELACIONAMENTO DE VOLTA (ADICIONADO) ---
    # Permite acessar facilmente todas as notificações de um funcionário.
    notificacoes_associadas = db.relationship(
        'Notificacoes',
        secondary=notificacao_fiscais,
        back_populates='fiscais_responsaveis',
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<Funcionario {self.nome} - {self.cargo}>'

class Autonomo(db.Model):
    __tablename__ = 'autonomos'
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default='Pendente')
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # 1. Dados Pessoais
    nome_completo = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20))
    orgao_expedidor = db.Column(db.String(20))
    uf_rg = db.Column(db.String(2))
    data_nascimento = db.Column(db.Date)
    sexo = db.Column(db.String(20))

    # 2. Contato
    telefone_celular = db.Column(db.String(20))
    email = db.Column(db.String(120))

    # 3. Endereço
    endereco_atendimento = db.Column(db.String(255))
    tipo_local = db.Column(db.String(50))

    # 4. Dados Profissionais
    profissao = db.Column(db.String(100))
    conselho_classe = db.Column(db.String(50))
    numero_registro_profissional = db.Column(db.String(50))
    inscricao_municipal = db.Column(db.String(50))
    atividades_exercidas = db.Column(db.Text)
    modalidade_atendimento = db.Column(db.String(50))
    horario_funcionamento = db.Column(db.Text)
    licencas = db.relationship('LicencaAutonomo', back_populates='autonomo', lazy=True, cascade="all, delete-orphan")
    # 5. Documentos Anexados (Caminhos dos ficheiros)
    doc_alvara_funcionamento_path = db.Column(db.String(255), nullable=True)
    doc_cpf_rg_path = db.Column(db.String(255), nullable=True)
    doc_comprovante_endereco_path = db.Column(db.String(255), nullable=True)
    doc_registro_conselho_path = db.Column(db.String(255), nullable=True)
    doc_declaracao_rt_path = db.Column(db.String(255), nullable=True)
    doc_declaracao_atividades_path = db.Column(db.String(255), nullable=True)
    doc_termo_compromisso_path = db.Column(db.String(255), nullable=True)

class PessoaFisica(db.Model):
    __tablename__ = 'pessoas_fisicas'
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(50), unique=True, nullable=True)
    
    # 1. Identificação
    nome_completo = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20))
    orgao_expedidor = db.Column(db.String(20))
    uf_rg = db.Column(db.String(2))
    data_nascimento = db.Column(db.Date)
    telefone_contato = db.Column(db.String(20))
    email = db.Column(db.String(120))

    # 2. Endereço do Local
    endereco_local = db.Column(db.String(250))
    tipo_local = db.Column(db.String(100))

    # 3. Situação do Local
    recebeu_notificacao = db.Column(db.Boolean, default=False)
    foi_objeto_denuncia = db.Column(db.Boolean, default=False)
    recebeu_visita = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)

    # 4. Finalidade do Cadastro
    finalidade_cadastro = db.Column(db.String(100))

    # Metadados
    status = db.Column(db.String(50), nullable=False, default='Pendente')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PessoaFisica {self.nome_completo}>'