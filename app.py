import os
import json
import re
from datetime import datetime, date, timedelta
from models import Autonomo
from models import PessoaFisica, db
from models import (
    db, Empresas, Autonomo, PessoaFisica, Funcionario,
    LicencaEmpresa, LicencaAutonomo, LicencaEvento, LicencasPublicas,
    Denuncias, Vistoria, Notificacoes, AutosInfracao,
    ProtocoloSequencial
)
from sqlalchemy import func
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, text, union_all
from fpdf import FPDF
from flask import render_template
from flask import request, redirect, url_for, flash, render_template
from models import db, Empresas, ProtocoloSequencial
from models import Autonomo, PessoaFisica,  db, ProtocoloSequencial
from models import Autonomo, Denuncias, Vistoria, Notificacoes
from models import Empresas, Autonomo
from sqlalchemy import or_ 
from flask import request, render_template, flash, redirect, url_for, jsonify
from sqlalchemy import or_, func 
from flask import request, flash, redirect, url_for
from flask import render_template, flash, json
from models import db, Empresas, LicencaEmpresa, LicencaAutonomo, LicencasPublicas, Denuncias
from sqlalchemy import text, or_
from models import db, LicencaEmpresa, LicencaAutonomo, LicencaEvento, Empresas, Autonomo
from models import db, Empresas, Autonomo, PessoaFisica, LicencaEmpresa, LicencaAutonomo, LicencaEvento, Vistoria, Denuncias, Notificacoes, AutosInfracao
from flask import send_from_directory, flash, redirect, url_for, request, send_file, render_template
from flask import request, render_template
from models import db, Autonomo, ProtocoloSequencial
from datetime import datetime
from flask import request, flash, redirect, url_for, current_app
from fpdf import FPDF, XPos, YPos
from flask import send_from_directory, flash, redirect, url_for, request, send_file, render_template
import uuid 
from fpdf.enums import XPos, YPos
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import traceback
from models import db, LicencaEmpresa, Funcionario
from datetime import datetime, timezone
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
from flask import current_app
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from flask import Flask, render_template, request, flash, redirect, url_for
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.utils import secure_filename
from models import Denuncias, Empresas
from weasyprint import HTML
from flask_login import login_required, current_user
import locale
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime
from models import db, Empresas, Autonomo, Notificacoes, Irregularidade, Funcionario
from sqlalchemy.orm import joinedload
from flask import make_response








app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'your_super_secret_key_change_this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'visa_digital.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Configuração de Pastas ---
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['RELATORIOS_FOLDER'] = os.path.join(basedir, 'relatorios')
app.config['ALVARAS_FOLDER'] = os.path.join(app.instance_path, 'alvaras') 

# :: INÍCIO DA CORREÇÃO ::
# Adicionando a pasta para os laudos, que estava em falta
app.config['LAUDOS_FOLDER'] = os.path.join(app.instance_path, 'laudos')
# :: FIM DA CORREÇÃO ::

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Cria as pastas se não existirem
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'fotos_vistorias'), exist_ok=True)
os.makedirs(app.config['ALVARAS_FOLDER'], exist_ok=True)
os.makedirs(app.config['RELATORIOS_FOLDER'], exist_ok=True)

# :: INÍCIO DA CORREÇÃO ::
# Criando a pasta de laudos, se não existir
os.makedirs(app.config['LAUDOS_FOLDER'], exist_ok=True)
# :: FIM DA CORREÇÃO ::


# --- Inicialização das Extensões ---
from extensions import db, migrate

db.init_app(app)
migrate.init_app(app, db)

# --- Importação dos Modelos ---
# Importe os modelos DEPOIS da inicialização do 'db'
from models import (
    User, Empresas, ProtocoloSequencial, SolicitacaoReceituario, 
    TipoReceituario, EstoqueReceituario, BlocoReceituario, 
    AtendimentoReceituario, SolicitacaoCalazar, Vistoria, 
    Checklist, Irregularidade, LicencasPublicas,
    Denuncias, Notificacoes, AutosInfracao, Funcionario
)

# --- Context Processor ---
@app.context_processor
def inject_global_vars():
    return dict(ano_atual=datetime.now().year)

# --- Classes e Funções Auxiliares ---
class PDF(FPDF):
    def header(self):
        if os.path.exists('static/logo.png'): self.image('static/logo.png', 10, 8, 25)
        self.set_font('Arial', 'B', 14)
        self.cell(80)
        self.cell(30, 10, 'Prefeitura Municipal - Vigilância Sanitária', 0, 0, 'C')
        self.ln(25)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        endereco_visa = "Rua Exemplo, 123 - Centro - Cidade/UF - CEP 00000-000"
        self.cell(0, 5, endereco_visa, 0, 1, 'C')
        self.cell(0, 5, f'Página {self.page_no()}', 0, 0, 'C')

def handle_licenca_upload(file_key, tipo_documento):
    """Salva um ficheiro de anexo da licença e retorna o nome do ficheiro."""
    file = request.files.get(file_key)
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        # Cria um nome de ficheiro único para evitar sobreposições
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{tipo_documento}_{filename}"
        
        # Define o caminho para salvar
        upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        licencas_docs_folder = os.path.join(upload_folder, 'licencas_docs')
        os.makedirs(licencas_docs_folder, exist_ok=True)
        
        save_path = os.path.join(licencas_docs_folder, unique_filename)
        file.save(save_path)
        return unique_filename
    return None



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------------------------------------GUARDAR FOTO ANIMAL------------------------------------------------------------------------------------------
def salvar_foto_animal(file, protocolo):
    """Salva uma foto de animal e retorna o caminho relativo."""
    if file and file.filename != '':
        # Garante que o nome do arquivo é seguro
        filename = secure_filename(file.filename)
        # Cria um nome único para evitar sobreposição de arquivos
        unique_filename = f"{protocolo}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        
        # Cria a subpasta para fotos de calazar se não existir
        subpasta_fotos = os.path.join(app.config['UPLOAD_FOLDER'], 'fotos_calazar')
        os.makedirs(subpasta_fotos, exist_ok=True)
        
        # Salva o arquivo
        caminho_completo = os.path.join(subpasta_fotos, unique_filename)
        file.save(caminho_completo)
        
        # Retorna o caminho relativo para salvar no banco de dados
        return os.path.join('fotos_calazar', unique_filename)
    return None
           
# -----------------------------------------------------------GERAR ALVARÁ EMPRESA ------------------------------------------------------------------------------------------
def gerar_alvara_pdf(licenca, dados_editados, responsavel_assinatura):
    """
    Gera um PDF de Alvará Sanitário com layout profissional e organizado,
    incluindo a assinatura dinâmica do responsável.
    """
    # --- 1. PREPARAÇÃO ---
    protocolo_sanitizado = licenca.protocolo.replace('/', '-')
    filename = f"alvara_{protocolo_sanitizado}_{licenca.ano_exercicio}.pdf"
    filepath = os.path.join(current_app.config['ALVARAS_FOLDER'], filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    margin = 0.8 * inch # Aumentado a margem para mais respiro

    # --- 2. CABEÇALHO ---
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        # O brasão foi aproximado do cabeçalho
        c.drawImage(logo_path, x=margin, y=height - margin - 90, width=100, height=100, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2.0, height - margin - 15, "ESTADO DO PIAUÍ")
    c.drawCentredString(width / 2.0, height - margin - 30, "PREFEITURA MUNICIPAL DE ESPERANTINA")
    
    # :: INÍCIO DA ALTERAÇÃO ::
    # Adicionada a Secretaria Municipal de Saúde
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, height - margin - 45, "SECRETARIA MUNICIPAL DE SAÚDE")
    c.drawCentredString(width / 2.0, height - margin - 60, "COORDENAÇÃO DE VIGILÂNCIA SANITÁRIA")
    # :: FIM DA ALTERAÇÃO ::
    
    c.setFont("Helvetica-Bold", 20) # Tamanho do título aumentado
    c.drawCentredString(width / 2.0, height - margin - 95, "ALVARÁ SANITÁRIO") # Posição ajustada
    
    # --- 3. DADOS DO ESTABELECIMENTO ---
    y = height - margin - 120
    c.line(margin, y, width - margin, y)
    y -= 25

    x_label = margin
    x_value = margin + 160
    line_height = 22 # Espaçamento entre linhas aumentado

    # Estilos para parágrafos com quebra de linha automática
    styles = getSampleStyleSheet()
    style_value = styles['Normal']
    style_value.fontName = 'Helvetica'
    style_value.fontSize = 9
    style_value.leading = 12
    style_value.alignment = TA_LEFT

    def draw_field(y_pos, label, value):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_label, y_pos, label.upper() + ":")
        
        # Usa Paragraph para quebrar linhas longas automaticamente
        p = Paragraph(str(value or ""), style_value)
        p_width = width - x_value - margin
        p_height = p.wrap(p_width, 1000)[1] # Calcula a altura necessária
        
        p.drawOn(c, x_value, y_pos - (p_height - style_value.fontSize) / 2)
        
        # Retorna a nova posição Y, considerando a altura do parágrafo
        return y_pos - max(line_height, p_height + 8)

    y = draw_field(y, "Protocolo", licenca.protocolo)
    y = draw_field(y, "Razão Social", licenca.empresa.razao_social)
    y = draw_field(y, "Nome Fantasia", licenca.empresa.nome_fantasia)
    y = draw_field(y, "CNPJ", licenca.empresa.cnpj)
    
    endereco_final = licenca.empresa.endereco
    if str(getattr(licenca, 'possui_local_fisico', 'nao')).strip().lower() == 'sim':
        endereco_local = getattr(licenca, 'endereco_completo', '').strip()
        if endereco_local:
            endereco_final = endereco_local
    y = draw_field(y, "Endereço", endereco_final)
    
    y = draw_field(y, "Município", "Esperantina - PI")
    y = draw_field(y, "CEP", "64.180-000")
    y = draw_field(y, "Atividade Principal", getattr(licenca.empresa, 'cnae_principal', '') or '')
    y = draw_field(y, "Atividade(s) Secundária(s)", getattr(licenca.empresa, 'cnae_secundario', 'Não informado') or 'Não informado')
    y = draw_field(y, "Horário de Funcionamento", getattr(licenca.empresa, 'horario_segunda_feira', 'Não informado'))

    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_label, y, "RESPONSABILIDADE TÉCNICA:")
    if str(getattr(licenca, 'necessita_rt', 'nao')).strip().lower() in ('sim', 'true', '1'):
        rt_nome = (getattr(licenca, 'rt_nome', '') or '').strip()
        if rt_nome:
            rt_conselho = (getattr(licenca, 'rt_conselho', '') or '').strip()
            rt_numero = (getattr(licenca, 'rt_numero_conselho', '') or '').strip()
            conselho_str = f"{rt_conselho}: {rt_numero}" if rt_conselho and rt_numero else rt_conselho
            
            p_rt = Paragraph(f"{rt_nome}<br/>{conselho_str}", style_value)
            p_rt.wrapOn(c, width - x_value - margin, 50)
            p_rt.drawOn(c, x_value, y - 5)
            y -= line_height * 1
        else:
            c.drawString(x_value, y, "Dados do RT não informados")
            y -= line_height
    else:
        c.drawString(x_value, y, "Não se aplica")
        y -= line_height
    
    # --- 4. OBSERVAÇÕES ---
    y += 5 
    c.line(margin, y, width - margin, y)
    y -= 25
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_label, y, "OBSERVAÇÕES:")
    y -= 15
    
    all_obs_lines = []
    if licenca.observacoes and licenca.observacoes.strip():
        all_obs_lines.extend(licenca.observacoes.strip().split('\n'))
    if str(getattr(licenca, 'vende_controlados', 'Não')).strip().lower() == 'sim':
        all_obs_lines.append(f"Venda de medicamentos Inclusos na Portaria 344/98 sob AFE de numero: {getattr(licenca, 'afe_numero', 'N/A')}.")
    if str(getattr(licenca, 'vende_retinoicos', 'Não')).strip().lower() == 'sim':
        validade_obj = getattr(licenca, 'retinoicos_validade', None)
        validade_str = validade_obj.strftime('%d/%m/%Y') if validade_obj else 'N/A'
        all_obs_lines.append(f"Venda de Medicamentos Retinoicos sob aut. de numero: {getattr(licenca, 'retinoicos_numero_autorizacao', 'N/A')}, com validade até: {validade_str}.")
    if str(getattr(licenca, 'vende_animais', 'Não')).strip().lower() == 'sim':
        all_obs_lines.append(f"Venda de Animais Vivos sob responsabilidade de: {getattr(licenca, 'rt_vet_nome', 'N/A')}, CRMV: {getattr(licenca, 'rt_vet_crmv', 'N/A')}.")
    if str(getattr(licenca, 'realiza_manipulacao', 'Não')).strip().lower() == 'sim':
        all_obs_lines.append("Realiza a manipulação de medicamentos.")

    if all_obs_lines:
        obs_text = "<br/>".join([f"- {line}" for line in all_obs_lines])
        p_obs = Paragraph(obs_text, style_value)
        p_obs_height = p_obs.wrap(width - margin - (x_label + 5), 1000)[1]
        p_obs.drawOn(c, x_label + 5, y - p_obs_height)
        y -= p_obs_height + 15
    else:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(x_label + 5, y, "Nada consta.")
        y -= line_height

    # --- 5. VALIDADE E DATA ---
    y -= 30 
    c.line(margin, y, width - margin, y)
    y -= 20

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 4, y, "LOCAL E DATA")
    c.drawCentredString(width / 2, y, "VALIDADE")
    c.drawCentredString(width * 0.75, y, "EXERCÍCIO")
    
    c.setFont("Helvetica", 10)
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    data_validade_str = licenca.data_validade.strftime("%d/%m/%Y") if licenca.data_validade else "N/A"
    c.drawCentredString(width / 4, y - 18, f"Esperantina-PI, {data_emissao}")
    c.drawCentredString(width / 2, y - 18, data_validade_str)
    c.drawCentredString(width * 0.75, y - 18, str(licenca.ano_exercicio))

    # --- 6. ASSINATURA ---
    y_assinatura = y - 70
    
    caminho_img = responsavel_assinatura.get('caminho_imagem')
    if caminho_img and os.path.exists(caminho_img):
        c.drawImage(caminho_img, x=width/2 - 75, y=y_assinatura, width=150, height=45, preserveAspectRatio=True, mask='auto')
        y_assinatura -= 5 

    c.line(width/2 - 130, y_assinatura, width/2 + 130, y_assinatura)
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, y_assinatura - 15, responsavel_assinatura.get('nome', '').upper())
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2.0, y_assinatura - 30, responsavel_assinatura.get('cargo', 'Cargo não informado').title())

    # --- 7. RODAPÉ ---
    codigo_autenticidade = str(uuid.uuid4()).split('-')[0].upper()
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2.0, margin / 2 + 15, f"Código de Autenticidade: {codigo_autenticidade}")
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width / 2.0, margin / 2, "Este documento deverá permanecer exposto em local visível no estabelecimento empresarial.")

    c.save()
    return filename

# -----------------------------------------------------------ALVARÁ LICENÇA AUTONOMO ----------------------------------------------------------------------------------------------------------------------------------
def gerar_alvara_pdf_autonomo(licenca, responsavel_assinatura):
    """Gera um PDF de Alvará Sanitário para um profissional autônomo com o layout especificado."""
    
    autonomo = licenca.autonomo # Acede ao objeto do autônomo através da licença
    protocolo_sanitizado = licenca.protocolo.replace('/', '-')
    ano_atual = datetime.now().year
    filename = f"alvara_autonomo_{protocolo_sanitizado}_{ano_atual}.pdf"
    filepath = os.path.join(current_app.config['ALVARAS_FOLDER'], filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    margin = 0.8 * inch

    # --- CABEÇALHO ---
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, x=margin, y=height - margin - 65, width=75, height=75, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2.0, height - margin - 15, "ESTADO DO PIAUÍ")
    c.drawCentredString(width / 2.0, height - margin - 30, "PREFEITURA MUNICIPAL DE ESPERANTINA")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, height - margin - 45, "SECRETARIA MUNICIPAL DE SAÚDE")
    c.drawCentredString(width / 2.0, height - margin - 60, "COORDENAÇÃO DE VIGILÂNCIA SANITÁRIA")
    
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2.0, height - margin - 95, "ALVARÁ SANITÁRIO PARA AUTÔNOMO")

    # --- PROTOCOLO ---
    y = height - margin - 130
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "PROTOCOLO:")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 80, y, autonomo.protocolo)
    
    # --- DADOS DO AUTÔNOMO ---
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "DADOS DO AUTÔNOMO")
    c.line(margin, y - 5, width - margin, y - 5)
    y -= 25

    x_label = margin
    x_value = margin + 100
    line_height = 20

    def draw_field(y_pos, label, value):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_label, y_pos, label + ":")
        c.setFont("Helvetica", 10)
        c.drawString(x_value, y_pos, str(value or "Não informado"))
        return y_pos - line_height

    y = draw_field(y, "Nome", autonomo.nome_completo)
    y = draw_field(y, "CPF", autonomo.cpf)
    y = draw_field(y, "CNAE/Atividade", autonomo.atividades_exercidas)
    y = draw_field(y, "Endereço", autonomo.endereco_atendimento)
    y = draw_field(y, "Telefone", autonomo.telefone_celular)
    y = draw_field(y, "E-mail", autonomo.email)

    # --- TEXTO LEGAL ---
    y -= 30
    styles = getSampleStyleSheet()
    style_justify = ParagraphStyle(name='Justify', parent=styles['Normal'], alignment=TA_JUSTIFY, fontSize=10, leading=14)
    
    legal_text = """
    A VIGILÂNCIA SANITÁRIA MUNICIPAL, no uso de suas atribuições legais, e considerando a
    legislação sanitária vigente, CONCEDE o presente Alvará Sanitário, autorizando o exercício da
    atividade acima mencionada, atendendo às condições sanitárias exigidas.
    """
    p = Paragraph(legal_text, style_justify)
    p_height = p.wrap(width - 2 * margin, 1000)[1]
    p.drawOn(c, margin, y - p_height)
    y -= p_height + 30

    # --- VALIDADE, DATA E EXERCÍCIO (SECÇÃO CORRIGIDA) ---
    c.line(margin, y, width - margin, y)
    y -= 20

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 4, y, "LOCAL E DATA")
    c.drawCentredString(width / 2, y, "VALIDADE")
    c.drawCentredString(width * 0.75, y, "EXERCÍCIO")
    
    c.setFont("Helvetica", 10)
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    
    # Usa a data de validade da licença, se existir. Caso contrário, usa o padrão.
    data_validade_str = licenca.data_validade.strftime("%d/%m/%Y") if licenca.data_validade else f"31/12/{ano_atual}"
    
    c.drawCentredString(width / 4, y - 18, f"Esperantina-PI, {data_emissao}")
    c.drawCentredString(width / 2, y - 18, data_validade_str)
    c.drawCentredString(width * 0.75, y - 18, str(licenca.ano_exercicio or ano_atual))

    # --- ASSINATURA ---
    y_assinatura = y - 80
    
    caminho_img = responsavel_assinatura.get('caminho_imagem')
    if caminho_img and os.path.exists(caminho_img):
        c.drawImage(caminho_img, x=width/2 - 75, y=y_assinatura, width=150, height=45, preserveAspectRatio=True, mask='auto')
        y_assinatura -= 5 

    c.line(width/2 - 130, y_assinatura, width/2 + 130, y_assinatura)
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, y_assinatura - 15, responsavel_assinatura.get('nome', '').upper())
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2.0, y_assinatura - 30, responsavel_assinatura.get('cargo', 'Cargo não informado').title())

    # --- RODAPÉ ---
    codigo_autenticidade = str(uuid.uuid4()).split('-')[0].upper()
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2.0, margin / 2 + 15, f"Código de Autenticidade: {codigo_autenticidade}")
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width / 2.0, margin / 2, "Este documento deverá permanecer exposto em local visível.")

    c.save()
    return filename




# -----------------------------------------------------------ALVARÁ LICENÇA EVENTOS ----------------------------------------------------------------------------------------------------------------------------------

def gerar_alvara_pdf_evento(licenca, responsavel_assinatura):
    """Gera um PDF de Alvará Sanitário para um Evento com o layout especificado."""
    
    protocolo_sanitizado = licenca.protocolo.replace('/', '-')
    ano_atual = datetime.now().year
    filename = f"alvara_evento_{protocolo_sanitizado}_{ano_atual}.pdf"
    filepath = os.path.join(current_app.config['ALVARAS_FOLDER'], filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    margin = 0.8 * inch

    # --- CABEÇALHO ---
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, x=margin, y=height - margin - 65, width=75, height=75, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2.0, height - margin - 15, "ESTADO DO PIAUÍ")
    c.drawCentredString(width / 2.0, height - margin - 30, "PREFEITURA MUNICIPAL DE ESPERANTINA")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, height - margin - 45, "SECRETARIA MUNICIPAL DE SAÚDE")
    c.drawCentredString(width / 2.0, height - margin - 60, "COORDENAÇÃO DE VIGILÂNCIA SANITÁRIA")
    
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2.0, height - margin - 95, "ALVARÁ SANITÁRIO PARA EVENTO TEMPORÁRIO")

    # --- PROTOCOLO ---
    y = height - margin - 130
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "PROTOCOLO:")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 80, y, licenca.protocolo)
    
    def draw_field(y_pos, label, value, x_offset=150):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y_pos, label + ":")
        c.setFont("Helvetica", 10)
        c.drawString(margin + x_offset, y_pos, str(value or "Não informado"))
        return y_pos - 20

    # --- DADOS DO RESPONSÁVEL PELO EVENTO ---
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "DADOS DO RESPONSÁVEL PELO EVENTO")
    c.line(margin, y - 5, width - margin, y - 5)
    y -= 25
    
    y = draw_field(y, "Nome completo", licenca.solicitante_nome)
    y = draw_field(y, "CPF/CNPJ", licenca.solicitante_cpf_cnpj)
    y = draw_field(y, "Endereço", licenca.solicitante_endereco)
    y = draw_field(y, "Telefone", licenca.solicitante_telefone)
    y = draw_field(y, "E-mail", licenca.solicitante_email)

    # --- DADOS DO EVENTO ---
    y -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "DADOS DO EVENTO")
    c.line(margin, y - 5, width - margin, y - 5)
    y -= 25

    y = draw_field(y, "Nome do evento", licenca.nome_evento)
    y = draw_field(y, "Tipo de evento", licenca.tipos_evento)
    
    periodo = f"{licenca.data_inicio.strftime('%d/%m/%Y')} a {licenca.data_fim.strftime('%d/%m/%Y')}" if licenca.data_inicio and licenca.data_fim else "N/A"
    y = draw_field(y, "Data(s) de realização", periodo)
    
    y = draw_field(y, "Horário", licenca.horario)
    y = draw_field(y, "Local do evento", licenca.local_evento)

    # --- TEXTO LEGAL ---
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "LICENÇA SANITÁRIA TEMPORÁRIA CONCEDIDA")
    c.line(margin, y - 5, width - margin, y - 5)
    y -= 15
    
    styles = getSampleStyleSheet()
    style_justify = ParagraphStyle(name='Justify', parent=styles['Normal'], alignment=TA_JUSTIFY, fontSize=9, leading=12)
    legal_text = """
    A Vigilância Sanitária Municipal concede o Alvará de Licença Sanitária para a realização do 
    evento acima descrito, limitado ao período de validade informado, e condicionado ao cumprimento das 
    normas sanitárias vigentes, podendo ser cancelado a qualquer momento em caso de descumprimento.
    """
    p = Paragraph(legal_text, style_justify)
    p_height = p.wrap(width - 2 * margin, 1000)[1]
    p.drawOn(c, margin, y - p_height)
    y -= p_height + 30

    # --- VALIDADE, DATA E EXERCÍCIO ---
    c.line(margin, y, width - margin, y)
    y -= 20

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 4, y, "LOCAL E DATA")
    c.drawCentredString(width / 2, y, "VALIDADE")
    c.drawCentredString(width * 0.75, y, "EXERCÍCIO")
    
    c.setFont("Helvetica", 10)
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    data_validade_str = licenca.data_validade.strftime("%d/%m/%Y") if licenca.data_validade else "N/A"
    c.drawCentredString(width / 4, y - 18, f"Esperantina-PI, {data_emissao}")
    c.drawCentredString(width / 2, y - 18, data_validade_str)
    c.drawCentredString(width * 0.75, y - 18, str(ano_atual))

    # --- ASSINATURA ---
    y_assinatura = y - 80
    
    caminho_img = responsavel_assinatura.get('caminho_imagem')
    if caminho_img and os.path.exists(caminho_img):
        c.drawImage(caminho_img, x=width/2 - 75, y=y_assinatura, width=150, height=45, preserveAspectRatio=True, mask='auto')
        y_assinatura -= 5 

    c.line(width/2 - 130, y_assinatura, width/2 + 130, y_assinatura)
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, y_assinatura - 15, responsavel_assinatura.get('nome', '').upper())
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2.0, y_assinatura - 30, responsavel_assinatura.get('cargo', 'Cargo não informado').title())

    # --- RODAPÉ ---
    codigo_autenticidade = str(uuid.uuid4()).split('-')[0].upper()
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2.0, margin / 2 + 15, f"Código de Autenticidade: {codigo_autenticidade}")
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width / 2.0, margin / 2, "Este documento deverá permanecer exposto em local visível.")

    c.save()
    return filename

# -----------------------------------------------------------LAUDO TESTE CALAZAR ---------------------------------------------------------------------------------------------------------------------------------

def gerar_laudo_calazar_pdf(solicitacao, veterinario_assinatura):
    """
    Gera um PDF do Laudo de Teste de Calazar com layout profissional,
    recriando fielmente o modelo fornecido.

    :param solicitacao: O objeto da classe SolicitacaoCalazar com todos os dados.
    :param veterinario_assinatura: Um dicionário com os dados do veterinário.
    :return: O nome do ficheiro PDF gerado.
    """
    # --- 1. PREPARAÇÃO DO DOCUMENTO ---
    protocolo_sanitizado = solicitacao.protocolo.replace('/', '-')
    filename = f"laudo_calazar_{protocolo_sanitizado}.pdf"
    filepath = os.path.join(current_app.config['LAUDOS_FOLDER'], filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    margin = 0.75 * inch
    
    # --- 2. CABEÇALHO ---
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, x=margin, y=height - margin - 85, width=90, height=90, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2.0, height - margin - 20, "ESTADO DO PIAUÍ")
    c.drawCentredString(width / 2.0, height - margin - 35, "PREFEITURA MUNICIPAL DE ESPERANTINA")
    
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2.0, height - margin - 50, "SECRETARIA MUNICIPAL DE SAÚDE")
    c.drawCentredString(width / 2.0, height - margin - 65, "COORDENAÇÃO DE VIGILÂNCIA SANITÁRIA")
    
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2.0, height - margin - 100, "LAUDO TESTE DE CALAZAR")
    
    # --- 3. PROTOCOLO ---
    y = height - margin - 130
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "PROTOCOLO:")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 80, y, solicitacao.protocolo)
    y -= 25

    # --- 4. DADOS EM SECÇÕES ---
    # Função auxiliar para desenhar os campos
    def draw_field(y_pos, label, value):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin + 10, y_pos, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(margin + 150, y_pos, str(value or 'Não informado'))
        return y_pos - 20

    # Secção 1: Dados do Proprietário
    c.roundRect(margin, y - 90, width - 2 * margin, 90, 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 10, y - 15, "1. Dados do Proprietário")
    y_field = y - 30
    y_field = draw_field(y_field, "Nome Completo", solicitacao.proprietario_nome)
    y_field = draw_field(y_field, "CPF", solicitacao.proprietario_cpf)
    y_field = draw_field(y_field, "Endereço", solicitacao.proprietario_endereco)
    y_field = draw_field(y_field, "Telefone", solicitacao.proprietario_telefone)
    y -= 105

    # Secção 2: Dados do Animal
    c.roundRect(margin, y - 70, width - 2 * margin, 70, 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 10, y - 15, "2. Dados do Animal")
    y_field = y - 30
    y_field = draw_field(y_field, "Nome do Animal", solicitacao.animal_nome)
    y_field = draw_field(y_field, "Espécie / Raça", f"{solicitacao.animal_especie} / {solicitacao.animal_raca}")
    y_field = draw_field(y_field, "Sexo / Idade / Cor", f"{solicitacao.animal_sexo} / {solicitacao.animal_idade} / {solicitacao.animal_cor}")
    y -= 85
    
    # Secção 3: Resultado do Teste
    c.roundRect(margin, y - 170, width - 2 * margin, 170, 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 10, y - 15, "3. Resultado do Teste de Leishmaniose Visceral")
    y_field = y - 30
    y_field = draw_field(y_field, "Data da Realização do Teste", solicitacao.data_realizacao_teste.strftime('%d/%m/%Y') if solicitacao.data_realizacao_teste else "N/A")
    y_field = draw_field(y_field, "Tipo de Teste Realizado", "Teste Rápido Imunocromatográfico")
    y_field = draw_field(y_field, "Kit Utilizado", solicitacao.kit_utilizado)
    y_field = draw_field(y_field, "Lote do Kit", solicitacao.lote_kit)
    y_field = draw_field(y_field, "Validade do Kit", solicitacao.validade_kit)
    y_field = draw_field(y_field, "Resultado do Teste Rápido", solicitacao.resultado_teste_rapido)
    y_field = draw_field(y_field, "Amostra Enviada ao LACEN", "Não")
    y_field = draw_field(y_field, "Anamnese do Veterinário", solicitacao.observacoes_resultado)
    y -= 185

    # --- 5. RESULTADO FINAL E OBSERVAÇÕES ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, f"Resultado: {solicitacao.resultado_teste_rapido.upper() if solicitacao.resultado_teste_rapido else 'INDETERMINADO'}")
    y -= 25

    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Observação/Interpretação:")
    y -= 15
    
    styles = getSampleStyleSheet()
    style_obs = ParagraphStyle(name='Observacao', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
    obs_text = """
    Observou-se o surgimento de apenas uma linha, a linha controle (C), no dispositivo de teste. A ausência
    da linha teste (T) indica que não foram detectados anticorpos anti-Leishmania spp. em níveis detectáveis
    pelo método na amostra analisada. Um resultado negativo não exclui a possibilidade de infecção em casos de exposição muito recente
    (janela imunológica) ou em pacientes/animais com comprometimento do sistema imune.
    """
    p_obs = Paragraph(obs_text.strip().replace("\n", " "), style_obs)
    p_obs.wrapOn(c, width - 2 * margin, 100)
    p_obs.drawOn(c, margin, y - p_obs.height)
    y -= (p_obs.height + 25)

    # --- 6. ASSINATURA E DATA ---
    y_assinatura = y
    data_emissao_str = datetime.now().strftime("%d de %B de %Y")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, y_assinatura, f"Esperantina-PI, {data_emissao_str}")
    y_assinatura -= 20

    caminho_img = veterinario_assinatura.get('caminho_imagem')
    if caminho_img and os.path.exists(caminho_img):
        c.drawImage(caminho_img, x=width/2 - 75, y=y_assinatura, width=150, height=45, preserveAspectRatio=True, mask='auto')
        y_assinatura -= 5
    else:
        y_assinatura -= 30
    
    c.line(width/2 - 130, y_assinatura, width/2 + 130, y_assinatura)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2.0, y_assinatura - 12, veterinario_assinatura.get('nome', '').upper())
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2.0, y_assinatura - 24, veterinario_assinatura.get('cargo', 'CRMV não informado'))
    
    # --- 7. RODAPÉ ---
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2.0, margin, f"Código de Autenticidade: {solicitacao.protocolo}")
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2.0, margin - 12, "Este documento deverá permanecer exposto em local visível no estabelecimento empresarial.")

    c.save()
    return filename

@app.route('/imprimir/laudo-calazar/<int:solicitacao_id>')
def admin_imprimir_resultado_calazar(solicitacao_id):
    """
    Rota para gerar e servir o PDF de um laudo de teste de Calazar.
    """
    # --- INÍCIO DA CORREÇÃO ---
    # Verifica se as pastas de destino estão configuradas para evitar erros.
    # Estas variáveis devem ser definidas no seu ficheiro principal app.py.
    # Ex: app.config['LAUDOS_FOLDER'] = os.path.join(basedir, 'laudos')
    if 'LAUDOS_FOLDER' not in current_app.config:
        current_app.logger.error("A variável de configuração 'LAUDOS_FOLDER' não foi definida no app.py.")
        return "Erro de configuração do servidor: O diretório para guardar laudos não foi especificado.", 500
    if 'UPLOAD_FOLDER' not in current_app.config:
        current_app.logger.error("A variável de configuração 'UPLOAD_FOLDER' não foi definida no app.py.")
        return "Erro de configuração do servidor: O diretório de uploads não foi especificado.", 500
    # --- FIM DA CORREÇÃO ---

    try:
        # 1. Busca a solicitação no banco de dados
        solicitacao = SolicitacaoCalazar.query.get_or_404(solicitacao_id)

        # 2. Prepara os dados da assinatura do veterinário
        veterinario_assinatura = {
            'nome': 'NOME NÃO ENCONTRADO',
            'cargo': 'CRMV não informado',
            'caminho_imagem': None
        }

        # Busca o funcionário (veterinário) responsável para obter a assinatura
        if solicitacao.veterinario_responsavel_nome:
            # Assumindo que você tem um modelo 'Funcionario' para os veterinários
            veterinario = Funcionario.query.filter_by(nome=solicitacao.veterinario_responsavel_nome).first()
            if veterinario:
                # Constrói o caminho completo para a imagem da assinatura
                if veterinario.caminho_assinatura: # Garante que o caminho não está vazio
                    caminho_completo_assinatura = os.path.join(current_app.config['UPLOAD_FOLDER'], veterinario.caminho_assinatura)
                    veterinario_assinatura['caminho_imagem'] = caminho_completo_assinatura
                
                veterinario_assinatura['nome'] = veterinario.nome
                veterinario_assinatura['cargo'] = f"CRMV: {solicitacao.veterinario_crmv or 'N/A'}"
            else:
                # Se não encontrar o veterinário, usa os dados da própria solicitação
                veterinario_assinatura['nome'] = solicitacao.veterinario_responsavel_nome
                veterinario_assinatura['cargo'] = f"CRMV: {solicitacao.veterinario_crmv or 'N/A'}"

        # 3. Chama a função que gera o PDF
        # Esta é a função que está no outro Canvas
        nome_ficheiro_pdf = gerar_laudo_calazar_pdf(solicitacao, veterinario_assinatura)

        # 4. Envia o ficheiro PDF gerado para o utilizador
        # 'LAUDOS_FOLDER' deve ser o nome da pasta onde os laudos são guardados
        return send_from_directory(
            directory=current_app.config['LAUDOS_FOLDER'],
            path=nome_ficheiro_pdf,
            as_attachment=False  # False para abrir no navegador, True para forçar o download
        )

    except Exception as e:
        # Em caso de erro, regista o erro e retorna uma mensagem amigável
        current_app.logger.error(f"Erro ao gerar laudo PDF para solicitação {solicitacao_id}: {e}")
        return "Ocorreu um erro ao gerar o laudo. Por favor, tente novamente.", 500




# -----------------------------------------------------------LIMPAR CNPJ----------------------------------------------------------------------------------------------------------------------------------
def limpar_cnpj(cnpj_bruto):
    if not cnpj_bruto: return ""
    return "".join(filter(str.isdigit, cnpj_bruto))
# ----------------------------------------------------------- FILE -------------------------------------------------------------------------------------------------------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------------------------------------SALVAR FOTO VISTORIA----------------------------------------------------------------------------------------------------------------------------------

def salvar_fotos_vistoria(files):
    nomes_fotos = []
    # Busca a configuração da pasta de uploads. O padrão é 'static/uploads'.
    upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    # Define a subpasta específica para as fotos de vistorias.
    fotos_vistoria_folder = os.path.join(upload_folder, 'fotos_vistorias')
    
    # Cria a pasta se ela não existir.
    os.makedirs(fotos_vistoria_folder, exist_ok=True)

    for i in range(1, 11): # Loop de foto_1 a foto_10
        file_key = f'foto_{i}'
        if file_key in files:
            file = files[file_key]
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # Cria um nome de arquivo único para evitar sobreposições
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
                save_path = os.path.join(fotos_vistoria_folder, unique_filename)
                
                file.save(save_path)
                nomes_fotos.append(unique_filename)
    return nomes_fotos
# -----------------------------------------------------------UPLOAD DE ARQUIVOS ------------------------------------------------------------------------------------------

# --- Funções Auxiliares ---

def handle_upload(file_key, subfolder, multiple=False):
    """
    Processa o upload de um ou múltiplos arquivos, salvando em uma subpasta específica.
    Retorna apenas o nome do(s) arquivo(s) para ser salvo no banco de dados.
    """
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_path, exist_ok=True)
    
    saved_filenames = []

    if multiple:
        uploaded_files = request.files.getlist(file_key)
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
                full_path = os.path.join(upload_path, filename)
                file.save(full_path)
                # CORREÇÃO: Guarda apenas o nome do arquivo, sem a subpasta.
                saved_filenames.append(filename) 
        
        return ", ".join(saved_filenames) if saved_filenames else None
    
    else:
        uploaded_file = request.files.get(file_key)
        if uploaded_file and uploaded_file.filename:
            filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{uploaded_file.filename}")
            full_path = os.path.join(upload_path, filename)
            uploaded_file.save(full_path)
            # CORREÇÃO: Retorna apenas o nome do arquivo, sem a subpasta.
            return filename
            
    return None



# -----------------------------------------------------------GERAR PROTOCOLO SEQUENCIAL ------------------------------------------------------------------------------------------
def gerar_protocolo(categoria, prefixo):
    """
    Gera um número de protocolo sequencial para uma determinada categoria e ano.
    Ex: gerar_protocolo('EMPRESA', 'VISA-CE') -> 'VISA-CE-2025/0001'
    """
    ano_atual = datetime.now().year
    
    # Busca o registro do ano e categoria, bloqueando a linha para atualização.
    # O .with_for_update() é a chave para evitar números duplicados.
    protocolo_seq = ProtocoloSequencial.query.filter_by(
        ano=ano_atual,
        categoria=categoria
    ).with_for_update().first()

    if not protocolo_seq:
        protocolo_seq = ProtocoloSequencial(
            ano=ano_atual,
            categoria=categoria,
            ultimo_numero=0
        )
        db.session.add(protocolo_seq)
        db.session.flush() # Garante que o objeto seja persistido na sessão

    # Incrementa o número e formata o protocolo
    protocolo_seq.ultimo_numero += 1
    numero_formatado = f"{protocolo_seq.ultimo_numero:04d}"
    protocolo_gerado = f"{prefixo}-{ano_atual}/{numero_formatado}"
    
    return protocolo_gerado

# -----------------------------------------------------------UPLOAD DE ARQUIVOS EVENTOS ------------------------------------------------------------------------------------------
def handle_evento_upload(file_key, tipo_documento):
    """Salva um ficheiro de anexo da licença de evento e retorna o nome do ficheiro."""
    file = request.files.get(file_key)
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{tipo_documento}_{filename}"
        
        upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        eventos_docs_folder = os.path.join(upload_folder, 'eventos_docs')
        os.makedirs(eventos_docs_folder, exist_ok=True)
        
        save_path = os.path.join(eventos_docs_folder, unique_filename)
        file.save(save_path)
        return unique_filename
    return None

# ---------------------------------------------------------- FUNÇÃO PARA LIMPAR DOC. ---------------------------------------------------------------------------------------------------------------
def limpar_documento(doc):
    """Função auxiliar para remover caracteres não numéricos de um documento."""
    if not doc:
        return ""
    return re.sub(r'\D', '', doc)

# -----------------------------------------------------------SALVAR DOC AUTONOMO------------------------------------------------------------------------------------------------------------
def salvar_documento_autonomo(file, tipo_documento):
    """Salva um ficheiro de documento para um autônomo e retorna o nome do ficheiro."""
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{tipo_documento}_{filename}"
        
        upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        autonomos_docs_folder = os.path.join(upload_folder, 'autonomos_docs')
        os.makedirs(autonomos_docs_folder, exist_ok=True)
        
        save_path = os.path.join(autonomos_docs_folder, unique_filename)
        file.save(save_path)
        return unique_filename
    return None
# ---------------------------------------------------------------------------GERAR ALVARÁ SANITARIO INST. PUBLICAS------------------------------------------------------------------------------------------
def gerar_alvara_instituicao_publica_pdf(licenca, responsavel_assinatura):
    """
    Gera um PDF de Alvará Sanitário para Instituições Públicas,
    seguindo o modelo fornecido.

    :param licenca: O objeto da classe LicencasPublicas.
    :param responsavel_assinatura: Dicionário com dados do responsável pela assinatura.
    :return: O nome do ficheiro PDF gerado.
    """
    # --- 1. PREPARAÇÃO ---
    protocolo_sanitizado = licenca.protocolo_licencas_publicas.replace('/', '-')
    filename = f"alvara_publica_{protocolo_sanitizado}.pdf"
    # Certifique-se de que a pasta 'ALVARAS_FOLDER' está configurada
    filepath = os.path.join(current_app.config['ALVARAS_FOLDER'], filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    margin = 0.75 * inch

    # --- 2. CABEÇALHO ---
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, x=margin, y=height - margin - 85, width=90, height=90, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2.0, height - margin - 20, "ESTADO DO PIAUÍ")
    c.drawCentredString(width / 2.0, height - margin - 35, "PREFEITURA MUNICIPAL DE ESPERANTINA")
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2.0, height - margin - 50, "COORDENAÇÃO DE VIGILÂNCIA SANITÁRIA")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - margin - 80, "ALVARÁ SANITÁRIO")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2.0, height - margin - 100, "INSTITUIÇÕES PÚBLICAS")

    # --- 3. DADOS DA INSTITUIÇÃO E UNIDADE ---
    y = height - margin - 130
    
    def draw_field(y_pos, label, value, font_size=9):
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(margin, y_pos, f"{label.upper()}:")
        c.setFont("Helvetica", font_size)
        c.drawString(margin + 140, y_pos, str(value or 'Não informado'))
        return y_pos - (font_size + 8)

    y = draw_field(y, "Protocolo", licenca.protocolo_licencas_publicas)
    if licenca.empresa:
        y = draw_field(y, "Razão Social", licenca.empresa.razao_social)
        y = draw_field(y, "Nome Fantasia", licenca.empresa.nome_fantasia)
        y = draw_field(y, "CNPJ", licenca.empresa.cnpj)
    y = draw_field(y, "Nome da Unidade", licenca.unidade_nome)
    y = draw_field(y, "CNES/INEP", licenca.unidade_cnes_inep)
    y = draw_field(y, "Endereço", licenca.unidade_endereco)
    y = draw_field(y, "Ponto de Referência", licenca.unidade_ponto_ref)
    y = draw_field(y, "Tipo de Unidade", licenca.unidade_tipo_outro or licenca.unidade_tipo)
    y -= 10

    # --- 4. DADOS DO RESPONSÁVEL ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "DADOS DO RESPONSÁVEL OU DO R. TÉCNICO.")
    y -= 20
    y = draw_field(y, "Nome", licenca.responsavel_unidade_nome)
    y = draw_field(y, "Cargo/Função", licenca.responsavel_unidade_cargo)
    y = draw_field(y, "Conselho Profissional", licenca.responsavel_unidade_conselho)
    y -= 10
    
    # Horário de Funcionamento (Exemplo, este dado não está no seu modelo de licença pública)
    y = draw_field(y, "Horário de Funcionamento", "Não informado no cadastro")
    y -= 20

    # --- 5. TEXTO LEGAL ---
    styles = getSampleStyleSheet()
    style_text = ParagraphStyle(name='LegalText', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, alignment=TA_LEFT)
    legal_text = """
    A Vigilância Sanitária de Esperantina/PI, no uso de suas atribuições legais, conforme
    legislação sanitária vigente (Lei Federal nº 6.437/77, Lei nº 8.080/90, RDC/ANVISA aplicáveis, e
    legislação municipal pertinente), <b>CONCEDE</b> o presente Alvará Sanitário, autorizando o
    funcionamento da instituição acima identificada nas condições estabelecidas, após inspeção e
    comprovação de que atende aos requisitos mínimos de saúde pública e segurança sanitária.
    """
    p = Paragraph(legal_text.strip().replace("\n", " "), style_text)
    p.wrapOn(c, width - 2 * margin, 200)
    p.drawOn(c, margin, y - p.height)
    y -= (p.height + 30)

    # --- 6. VALIDADE E DATA ---
    c.line(margin, y, width - margin, y)
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 4, y, "LOCAL E DATA")
    c.drawCentredString(width / 2, y, "VALIDADE")
    c.drawCentredString(width * 0.75, y, "EXERCÍCIO")
    y -= 18
    c.setFont("Helvetica", 10)
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    data_validade_str = licenca.data_validade.strftime("%d/%m/%Y") if licenca.data_validade else "N/A"
    c.drawCentredString(width / 4, y, f"Esperantina-PI, {data_emissao}")
    c.drawCentredString(width / 2, y, data_validade_str)
    c.drawCentredString(width * 0.75, y, str(datetime.now().year))
    y -= 40

    # --- 7. ASSINATURA ---
    caminho_img = responsavel_assinatura.get('caminho_imagem')
    if caminho_img and os.path.exists(caminho_img):
        c.drawImage(caminho_img, x=width/2 - 75, y=y, width=150, height=45, preserveAspectRatio=True, mask='auto')
    
    c.line(width/2 - 130, y - 5, width/2 + 130, y - 5)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2.0, y - 17, responsavel_assinatura.get('nome', '').upper())
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2.0, y - 29, responsavel_assinatura.get('cargo', 'Cargo não informado'))

    # --- 8. RODAPÉ ---
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2.0, margin, f"Código de Autenticidade: {licenca.protocolo_licencas_publicas}")
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2.0, margin - 12, "Este documento deverá permanecer exposto em local visível no estabelecimento empresarial.")

    c.save()
    return filename

# ---------------------------------------------------------------------------------GERAR RELATÓRIO DENUNCIAS------------------------------------------------------------------------------------------
def gerar_relatorio_denuncia_pdf(denuncia):
    pdf = PDF() # Usa nossa classe com cabeçalho/rodapé
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatório de Atendimento de Denúncia", 0, 1, "C")
    pdf.ln(10)

    # Função auxiliar interna para adicionar linhas ao relatório de texto
    def add_row(title, content):
        pdf.set_font("Arial", "B", 11)
        pdf.multi_cell(50, 8, title, 0, "L")
        pdf.set_xy(pdf.get_x() + 50, pdf.get_y() - 8)
        pdf.set_font("Arial", "", 11)
        content_str = str(content) if content is not None else "Não informado"
        pdf.multi_cell(0, 8, content_str, 0, "L")
        pdf.ln(4)

    # --- Seção de Texto do Relatório ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "1. Dados da Denúncia", 0, 1, "L")
    add_row("Protocolo:", denuncia.protocolo_denuncia)
    add_row("Data:", denuncia.data_denuncia.strftime('%d/%m/%Y %H:%M') if denuncia.data_denuncia else 'N/A')
    add_row("Status Atual:", denuncia.status)
    add_row("Denunciante:", "(Anônimo)" if denuncia.anonimato else denuncia.denunciante_nome)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "2. Local Denunciado", 0, 1, "L")
    add_row("Estabelecimento:", denuncia.denunciado_nome)
    add_row("Endereço:", f"{denuncia.denunciado_rua}, {denuncia.denunciado_numero} - {denuncia.denunciado_bairro}")
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "3. Motivo e Descrição", 0, 1, "L")
    add_row("Classificação:", denuncia.motivo_classificacao)
    add_row("Descrição:", denuncia.motivo_descricao)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "4. Despacho do Fiscal", 0, 1, "L")
    add_row("Observações:", denuncia.despacho_fiscal)


    def adicionar_paginas_de_fotos(titulo_pagina, caminhos_dos_anexos):
        if not caminhos_dos_anexos: return
        imagens = [p for p in caminhos_dos_anexos.split(';') if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not imagens: return

        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, titulo_pagina, 0, 1, "C")
        pdf.ln(10)

        x_start, y_start = 15, pdf.get_y()
        img_width, img_height = 70, 100
        x_margin, y_margin = 10, 10
        x, y = x_start, y_start
        fotos_na_pagina = 0

        for img_path in imagens:
            if fotos_na_pagina == 4:
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, titulo_pagina, 0, 1, "C")
                pdf.ln(10)
                x, y = x_start, y_start
                fotos_na_pagina = 0
            
            if fotos_na_pagina == 0: x, y = x_start, y_start
            elif fotos_na_pagina == 1: x = x_start + img_width + x_margin
            elif fotos_na_pagina == 2: x, y = x_start, y_start + img_height + y_margin
            elif fotos_na_pagina == 3: x = x_start + img_width + x_margin
            
            try:
                if os.path.exists(img_path):
                    pdf.image(img_path, x, y, img_width, img_height)
            except Exception as e:
                print(f"Erro ao adicionar imagem {img_path} ao PDF: {e}")
            fotos_na_pagina += 1

    adicionar_paginas_de_fotos("ANEXOS FOTOS DENUNCIANTE", denuncia.anexos_path)
    adicionar_paginas_de_fotos("ANEXOS FOTOS FISCAL", denuncia.fiscal_anexos_path)

    # --- Finalização ---
    filename = f"relatorio_denuncia_{denuncia.protocolo_denuncia.replace('/', '_')}.pdf"
    filepath = os.path.join(app.config['RELATORIOS_FOLDER'], filename)
    pdf.output(filepath)
    return filepath



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin/registrar_processo')
def registrar_processo_hub():
    return render_template('registrar_processo_hub.html')

#---------------------------------------------------------------------------------------CADASTRO DE EMPRESA------------------------------------------------------------------------------------------------------#

@app.route('/cadastro-empresa', methods=['GET', 'POST'])
def cadastro_empresa():
    if request.method == 'POST':
        # --- Coleta e Validação do CNPJ ---
        cnpj_com_mascara = request.form.get('cnpj')
        
        if not cnpj_com_mascara:
            flash('Erro: O campo CNPJ é obrigatório.', 'danger')
            return redirect(url_for('cadastro_empresa'))

        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj_com_mascara)
        empresa_existente = Empresas.query.filter_by(cnpj=cnpj_limpo).first()

        if empresa_existente:
            flash(f'Erro: O CNPJ {cnpj_com_mascara} já está cadastrado no sistema.', 'danger')
            return redirect(url_for('cadastro_empresa'))

        try:
            # --- LÓGICA DE GERAÇÃO DE PROTOCOLO ---
            protocolo_gerado = gerar_protocolo('EMPRESA', 'VISA-CE')

            nova_empresa = Empresas(
                protocolo=protocolo_gerado,
                status='em_analise', 
                cnpj=cnpj_limpo,
                razao_social=request.form.get('razao_social'),
                nome_fantasia=request.form.get('nome_fantasia'),
                porte=request.form.get('porte'),
                data_abertura=request.form.get('data_abertura'),
                situacao_cadastral=request.form.get('situacao_cadastral'),
                cnae_principal=request.form.get('cnae_principal'),
                cnae_secundario=request.form.get('cnae_secundario'),
                endereco=request.form.get('endereco'),
                bairro=request.form.get('bairro'),
                cidade=request.form.get('cidade'),
                email=request.form.get('email'),
                telefone_empresa=request.form.get('telefone_empresa'),
                responsavel_juridico_nome=request.form.get('responsavel_juridico_nome'),
                responsavel_juridico_cpf=request.form.get('responsavel_juridico_cpf'),
                responsavel_juridico_tel=request.form.get('responsavel_juridico_tel'),
                contador_nome=request.form.get('contador_nome'),
                contador_cpf=request.form.get('contador_cpf'),
                contador_tel=request.form.get('contador_tel'),
                
                # --- CORREÇÃO DOS HORÁRIOS ---
                # Garante que todos os horários são lidos e guardados
                horario_segunda_feira=request.form.get('horario_segunda_feira'),
                horario_terca_feira=request.form.get('horario_terca_feira'),
                horario_quarta_feira=request.form.get('horario_quarta_feira'),
                horario_quinta_feira=request.form.get('horario_quinta_feira'),
                horario_sexta_feira=request.form.get('horario_sexta_feira'),
                horario_sabado=request.form.get('horario_sabado'),
                horario_domingo=request.form.get('horario_domingo'),
                funciona_feriado=request.form.get('funciona_feriado'),
                horario_feriado=request.form.get('horario_feriado') if request.form.get('funciona_feriado') == 'sim' else None
            )
            
            db.session.add(nova_empresa)
            db.session.commit()
            
            flash(f"Solicitação de cadastro recebida! Protocolo: {protocolo_gerado}. Sua solicitação está em análise.", 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            print(f"ERRO DETALHADO AO CADASTRAR: {e}") 
            flash('Ocorreu um erro inesperado ao processar o cadastro. Por favor, tente novamente.', 'danger')
            return redirect(url_for('cadastro_empresa'))

    return render_template('cadastro_empresa.html')


@app.route('/licenca/empresa/salvar', methods=['POST'])
def salvar_licenca_empresa():
    empresa_id = request.form.get('empresa_id')
    try:
        if not empresa_id:
            flash('ID da empresa não encontrado.', 'danger')
            return redirect(url_for('solicitar_licenca_cnpj'))

        def safe_parse_date(date_string):
            if date_string:
                try:
                    return datetime.strptime(date_string, '%Y-%m-%d').date()
                except ValueError:
                    return None
            return None

        protocolo_gerado = gerar_protocolo('EMPRESA', 'LSAE')

        nova_licenca = LicencaEmpresa(
            protocolo=protocolo_gerado,
            empresa_id=empresa_id,
            status='Pendente',
            data_solicitacao=datetime.now(timezone.utc),
            
            ano_exercicio=request.form.get('ano_exercicio'),
            tipo_atividade=request.form.get('tipo_atividade'),
            descricao_atividade=request.form.get('descricao_atividade'),
            
            possui_local_fisico=request.form.get('possui_local_fisico'),
            endereco_completo=request.form.get('endereco_completo'),
            
            necessita_rt=request.form.get('necessita_rt'),
            rt_nome=request.form.get('rt_nome'),
            rt_cpf=request.form.get('rt_cpf'),
            rt_conselho=request.form.get('rt_conselho'),
            rt_numero_conselho=request.form.get('rt_numero_conselho'),
            
            vende_controlados=request.form.get('vende_controlados'),
            afe_numero=request.form.get('afe_numero'),
            
            vende_retinoicos=request.form.get('vende_retinoicos'),
            retinoicos_numero_autorizacao=request.form.get('retinoicos_numero_autorizacao'),
            retinoicos_data_autorizacao=safe_parse_date(request.form.get('retinoicos_data_autorizacao')),
            retinoicos_validade=safe_parse_date(request.form.get('retinoicos_validade')),
            
            vende_animais=request.form.get('vende_animais'),
            rt_vet_nome=request.form.get('rt_vet_nome'),
            rt_vet_cpf=request.form.get('rt_vet_cpf'),
            rt_vet_crmv=request.form.get('rt_vet_crmv'),

            realizou_dedetizacao=request.form.get('realizou_dedetizacao'),
            dedetizacao_data=safe_parse_date(request.form.get('dedetizacao_data')),
            realiza_manipulacao=request.form.get('realiza_manipulacao'),

            # Campo MEI adicionado
            e_mei=request.form.get('e_mei')
        )

        # Processamento dos anexos
        nova_licenca.rt_declaracao_path = salvar_arquivo_upload(request.files.get('rt_declaracao'), 'rt')
        nova_licenca.afe_anexo_path = salvar_arquivo_upload(request.files.get('afe_anexo'), 'afe')
        nova_licenca.retinoicos_anexo_path = salvar_arquivo_upload(request.files.get('retinoicos_anexo'), 'retinoicos')
        nova_licenca.rt_vet_declaracao_path = salvar_arquivo_upload(request.files.get('rt_vet_declaracao'), 'rt_vet')
        nova_licenca.dedetizacao_anexo_path = salvar_arquivo_upload(request.files.get('dedetizacao_anexo'), 'dedetizacao')
        # Anexo da taxa adicionado
        nova_licenca.comprovante_taxa_path = salvar_arquivo_upload(request.files.get('comprovante_taxa'), 'taxas')

        db.session.add(nova_licenca)
        db.session.commit()
        
        flash(f'Sua solicitação de licença foi enviada com sucesso! Protocolo: {protocolo_gerado}', 'success')
        return redirect(url_for('admin_dashboard')) # Redirecionamento para um dashboard, ajuste se necessário

    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao processar sua solicitação: {e}', 'danger')
        
        cnpj = ''
        if empresa_id:
            empresa = db.session.get(Empresas, int(empresa_id))
            if empresa:
                cnpj = empresa.cnpj
        
        return redirect(url_for('solicitar_licenca_cnpj', cnpj=cnpj))


@app.route('/admin/empresas')
def admin_empresas_cadastradas():
    query_q = request.args.get('q', '')
    
    # Inicia a consulta base no modelo Empresas
    query = Empresas.query.filter_by(status='Aprovado')

    # Adiciona o filtro de busca textual, se existir
    if query_q:
        search = f"%{query_q}%"
        query = query.filter(or_(
            Empresas.razao_social.like(search),
            Empresas.cnpj.like(search)
        ))

    # Ordena e executa a consulta
    empresas = query.order_by(Empresas.razao_social).all()
    
    return render_template('admin_empresas_cadastradas.html', 
                           empresas=empresas, 
                           query_q=query_q)


@app.route('/admin/empresa/<int:empresa_id>')
def admin_ficha_empresa(empresa_id):
    # 1. Busca a empresa pelo ID. Se não encontrar, retorna um erro 404 automaticamente.
    empresa = Empresas.query.get_or_404(empresa_id)
    
    # 2. Busca todos os históricos vinculados, já ordenados.
    # O SQLAlchemy já converte as datas para objetos datetime, então não precisamos da função 'processar_datas'.
    licencas = LicencaEmpresa.query.filter_by(empresa_id=empresa_id).order_by(LicencaEmpresa.data_solicitacao.desc()).all()
    vistorias = Vistoria.query.filter_by(empresa_id=empresa_id).order_by(Vistoria.data_vistoria.desc()).all()
    denuncias = Denuncias.query.filter_by(empresa_id=empresa_id).order_by(Denuncias.data_denuncia.desc()).all()
    notificacoes = Notificacoes.query.filter_by(empresa_id=empresa_id).order_by(Notificacoes.data_notificacao.desc()).all()
    
    # 3. Renderiza o template, passando os objetos diretamente.
    return render_template('admin_ficha_empresa.html', 
                           empresa=empresa, 
                           licencas=licencas, 
                           vistorias=vistorias, 
                           denuncias=denuncias, 
                           notificacoes=notificacoes)

@app.route('/admin/imprimir_ficha/empresa/<int:empresa_id>')
def admin_imprimir_ficha_empresa(empresa_id):
    # ... (seu código para buscar a empresa) ...
    empresa = ...
    data_geracao = ...

    return render_template(
        'admin_imprimir_ficha_empresa.html', 
        processo=empresa, # <--- Corrigido para 'processo'
        data_geracao=data_geracao
    )

@app.route('/admin/solicitacoes')
def admin_analisar_solicitacoes():
    query_search = request.args.get('q', '')
    query_status = request.args.get('status', '')

    # 1. Inicia a consulta base, filtrando por status diferente de 'Aprovado'
    query = Empresas.query.filter(Empresas.status != 'Aprovado')
    # 2. Adiciona o filtro de busca textual, se existir
    if query_search:
        search_term = f"%{query_search}%"
        query = query.filter(or_(
            Empresas.razao_social.like(search_term),
            Empresas.cnpj.like(search_term)
        ))

    # 3. Adiciona o filtro de status, se existir
    if query_status:
        query = query.filter_by(status=query_status)

    # 4. Ordena e executa a consulta
    solicitacoes = query.order_by(Empresas.data_cadastro.desc()).all()
    
    # 5. Renderiza o template.
    return render_template('admin_analisar_solicitacoes.html', 
                           solicitacoes=solicitacoes,
                           query_search=query_search,
                           query_status=query_status)

@app.route('/admin/detalhe_cadastro/<int:empresa_id>')
def admin_detalhe_cadastro(empresa_id):
    empresa = Empresas.query.get_or_404(empresa_id)
    return render_template('admin_detalhe_cadastro.html', empresa=empresa)

@app.route('/admin/atualizar_status/<int:empresa_id>', methods=['POST'])
def admin_atualizar_status(empresa_id):
    novo_status = request.form.get('novo_status')
    justificativa = request.form.get('justificativa', '').strip()

    if novo_status in ['Pendente de Correção', 'Reprovado'] and not justificativa:
        flash('A justificativa é obrigatória para os status "Pendente de Correção" e "Reprovado".', 'danger')
        if 'detalhe_cadastro' in request.referrer:
            return redirect(url_for('admin_detalhe_cadastro', empresa_id=empresa_id))
        else:
            return redirect(url_for('admin_ficha_empresa', empresa_id=empresa_id))

    try:
        empresa_para_atualizar = Empresas.query.get_or_404(empresa_id)
        empresa_para_atualizar.status = novo_status
        empresa_para_atualizar.justificativa_status = justificativa if justificativa else None
        db.session.commit()
        flash(f'Status do cadastro atualizado para "{novo_status}" com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao atualizar o status: {e}', 'danger')
    
    if 'detalhe_cadastro' in request.referrer:
        return redirect(url_for('admin_detalhe_cadastro', empresa_id=empresa_id))
    else:
        return redirect(url_for('admin_ficha_empresa', empresa_id=empresa_id))



#------------------------------------------------------------------------------------SOLICITAÇÃO, DE LICENÇA SANIT. ---------------------------------------------------------------------------------------------------------------#


@app.route('/api/buscar_cadastro_completo/<string:documento>')
def api_buscar_cadastro_completo(documento):
    """API para buscar os dados completos de um cadastro por CNPJ/CPF."""
    documento_limpo = re.sub(r'[^0-9]', '', documento)

    if len(documento_limpo) == 14: # CNPJ
        empresa = Empresas.query.filter(or_(Empresas.cnpj == documento_limpo, Empresas.cnpj == documento), Empresas.status == 'Aprovado').first()
        if empresa:
            return jsonify({
                'encontrado': True, 'tipo': 'empresa', 'id': empresa.id,
                'dados': {
                    'CNPJ': empresa.cnpj,
                    'Razão Social': empresa.razao_social,
                    'Nome Fantasia': empresa.nome_fantasia,
                    'CNAE Primário': empresa.cnae_principal,
                    'CNAE Secundário': empresa.cnae_secundario,
                    'Situação Cadastral': empresa.situacao_cadastral,
                    'Ano de Abertura': empresa.data_abertura,
                    'Endereço': empresa.endereco,
                    'Horário de Funcionamento': empresa.horario_segunda_feira, # Exemplo
                    'Responsável Jurídico': empresa.responsavel_juridico_nome
                }
            })
    
    return jsonify({'encontrado': False})

 
@app.route('/admin/licencas/historico')
def admin_historico_licencas():
    # Pega todos os parâmetros de filtro da URL
    query_busca = request.args.get('q', '')
    data_inicio_str = request.args.get('data_inicio', '')
    data_fim_str = request.args.get('data_fim', '')
    
    # Inicia a consulta base para TODAS as licenças
    query = Licencas.query
    query = query.filter(Licencas.status.in_(['Aprovado', 'Reprovado', 'Cancelado']))

    # Filtro por texto (Protocolo ou CNPJ)
    if query_busca:
        search_term = f"%{query_busca}%"
        # O join é necessário para buscar na tabela de Empresas
        query = query.join(Empresas).filter(
            db.or_(
                Licencas.protocolo_licencas.like(search_term),
                Empresas.cnpj.like(search_term)
            )
        )

    # Filtro por data de início
    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            # Filtra pela data de emissão do alvará
            query = query.filter(Licencas.data_emissao >= data_inicio)
        except (ValueError, TypeError):
            flash('Formato de data inicial inválido. Use AAAA-MM-DD.', 'warning')
    
    # Filtro por data de fim
    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
            query = query.filter(Licencas.data_emissao <= data_fim.replace(hour=23, minute=59, second=59))
        except (ValueError, TypeError):
            flash('Formato de data final inválido. Use AAAA-MM-DD.', 'warning')

    # Ordena as licenças pela mais recente e executa a consulta
    todas_as_licencas = query.order_by(Licencas.id.desc()).all()
    
    return render_template(
        'admin_historico_licencas.html', 
        licencas=todas_as_licencas,
        query_busca=query_busca,
        data_inicio=data_inicio_str,
        data_fim=data_fim_str
    )

@app.route('/admin/atualizar_status_licenca/<int:licenca_id>', methods=['POST'])
def admin_atualizar_status_licenca(licenca_id):
    novo_status = request.form.get('novo_status')
    justificativa = request.form.get('justificativa', '').strip()

    # Validação da justificativa (seu código aqui já estava correto)
    if novo_status in ['Pendente de Correção', 'Reprovado', 'Cancelado'] and not justificativa:
        flash('A justificativa é obrigatória para este status.', 'danger')
        return redirect(url_for('admin_detalhe_licenca', licenca_id=licenca_id))

    # Busca a licença que queremos atualizar
    licenca_para_atualizar = Licencas.query.get_or_404(licenca_id)

    try:
        # Se o status for 'Aprovado', aciona a lógica para gerar o PDF
        if novo_status == 'Aprovado':
            # A função 'gerar_e_salvar_alvara_pdf' já está corrigida no Canvas 'pdf_download_fix'
            # para retornar APENAS o nome do arquivo.
            # Ela precisa do objeto 'licenca' completo para acessar os dados da empresa relacionada.
            nome_do_arquivo = gerar_e_salvar_alvara_pdf(licenca_para_atualizar)
            
            # ATUALIZAÇÃO CORRETA: Salva apenas o nome do arquivo no banco de dados
            licenca_para_atualizar.alvara_pdf_path = nome_do_arquivo
            
            # Define as datas de emissão e vencimento
            licenca_para_atualizar.data_emissao = date.today()
            # Define o vencimento para 31 de Dezembro do ano corrente
            licenca_para_atualizar.data_vencimento = date(date.today().year, 12, 31)

        # Atualiza os campos comuns para qualquer mudança de status
        licenca_para_atualizar.status = novo_status
        licenca_para_atualizar.justificativa_status = justificativa or None
        
        # Salva todas as mudanças no banco de uma só vez
        db.session.commit()
        flash(f'Status da licença atualizado para "{novo_status}" com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        # É muito útil imprimir o erro no console para debug
        print(f"--- ERRO AO ATUALIZAR LICENÇA: {e} ---")
        flash(f'Ocorreu um erro ao atualizar a licença: {e}', 'danger')

    return redirect(url_for('admin_detalhe_licenca', licenca_id=licenca_id))


#-------------------------------------------------------CADASTRO, ANALISE, DETALHES DA EMPRESA-------------------------------------------------------------------------------#


@app.route('/consultar_solicitacao', methods=['GET', 'POST'])
def consultar_solicitacao():
    resultado_protocolo = None
    historico_entidade = None
    entidade = None

    if request.method == 'POST':
        tipo_consulta = request.form.get('tipo_consulta')
        valor_consulta = request.form.get('valor_consulta', '').strip()

        if not valor_consulta:
            flash('Por favor, digite um valor para a consulta.', 'warning')
            return render_template('consultar_solicitacao.html')

        if tipo_consulta == 'protocolo':
            # --- INÍCIO DA CORREÇÃO ---
            # Adicionado 'LicencasPublicas' à lista de modelos para a busca
            modelos_com_protocolo = [
                LicencaEmpresa, LicencaAutonomo, LicencaEvento, 
                Empresas, Autonomo, PessoaFisica, 
                SolicitacaoCalazar, LicencasPublicas
            ]
            
            for model in modelos_com_protocolo:
                resultado = None
                # Verifica qual campo de protocolo o modelo usa e constrói a query corretamente
                if hasattr(model, 'protocolo_licencas_publicas'):
                    resultado = model.query.filter(func.upper(model.protocolo_licencas_publicas) == valor_consulta.upper()).first()
                elif hasattr(model, 'protocolo'):
                    resultado = model.query.filter(func.upper(model.protocolo) == valor_consulta.upper()).first()

                if resultado:
                    # Constrói um dicionário unificado com os dados do resultado
                    resultado_protocolo = {
                        'protocolo': getattr(resultado, 'protocolo_licencas_publicas', getattr(resultado, 'protocolo', 'N/A')),
                        'status': getattr(resultado, 'status', 'N/A'),
                        'data': getattr(resultado, 'data_solicitacao', getattr(resultado, 'data_cadastro', None)),
                        'tipo': model.__name__.replace('Licenca', 'Licença '),
                        'observacoes': getattr(resultado, 'observacoes', getattr(resultado, 'observacoes_resultado', None)),
                        'record_id': resultado.id,
                        'model_name': model.__name__,
                        'resultado_liberado': getattr(resultado, 'resultado_liberado', False) # Específico para Calazar
                    }
                    break 
            # --- FIM DA CORREÇÃO ---
        
        elif tipo_consulta == 'cnpj':
            valor_limpo = re.sub(r'[^0-9]', '', valor_consulta)
            entidade = Empresas.query.filter_by(cnpj=valor_limpo).first()
            if entidade:
                historico_entidade = []
                # Adiciona o cadastro da empresa
                historico_entidade.append({'protocolo': entidade.protocolo, 'tipo': 'Cadastro de Empresa', 'data': entidade.data_cadastro, 'status': entidade.status, 'record_id': entidade.id, 'model_name': 'Empresas'})
                # Adiciona as licenças privadas
                for licenca in entidade.licencas:
                    historico_entidade.append({'protocolo': licenca.protocolo, 'tipo': 'Licença de Empresa', 'data': licenca.data_solicitacao, 'status': licenca.status, 'record_id': licenca.id, 'model_name': 'LicencaEmpresa'})
                # --- INÍCIO DA CORREÇÃO ---
                # Adiciona as licenças públicas ao histórico do CNPJ
                for licenca_pub in entidade.licencas_publicas:
                    historico_entidade.append({'protocolo': licenca_pub.protocolo_licencas_publicas, 'tipo': 'Licença Pública', 'data': licenca_pub.data_solicitacao, 'status': licenca_pub.status, 'record_id': licenca_pub.id, 'model_name': 'LicencasPublicas'})
                # --- FIM DA CORREÇÃO ---

        elif tipo_consulta == 'cpf':
            # (A sua lógica de busca por CPF continua aqui, sem alterações)
            valor_limpo = re.sub(r'[^0-9]', '', valor_consulta)
            historico_entidade = []
            
            entidade = Autonomo.query.filter_by(cpf=valor_limpo).first() or \
                       PessoaFisica.query.filter_by(cpf=valor_limpo).first()
            
            if entidade:
                historico_entidade.append({
                    'protocolo': entidade.protocolo, 
                    'tipo': 'Cadastro de ' + type(entidade).__name__, 
                    'data': getattr(entidade, 'data_cadastro', None), 'status': entidade.status,
                    'record_id': entidade.id, 'model_name': type(entidade).__name__,
                    'observacoes': getattr(entidade, 'observacoes', None)
                })
                if hasattr(entidade, 'licencas'):
                    for licenca in entidade.licencas:
                        historico_entidade.append({
                            'protocolo': licenca.protocolo, 'tipo': 'Licença de Autônomo', 
                            'data': licenca.data_solicitacao, 'status': licenca.status,
                            'record_id': licenca.id, 'model_name': 'LicencaAutonomo',
                            'observacoes': getattr(licenca, 'observacoes', None)
                        })

            solicitacoes_calazar = SolicitacaoCalazar.query.filter_by(proprietario_cpf=valor_limpo).all()
            if solicitacoes_calazar and not entidade:
                entidade = {'nome_completo': solicitacoes_calazar[0].proprietario_nome}

            for solicitacao in solicitacoes_calazar:
                historico_entidade.append({
                    'protocolo': solicitacao.protocolo,
                    'tipo': 'Solicitação de Teste de Calazar',
                    'data': solicitacao.data_solicitacao,
                    'status': solicitacao.status,
                    'record_id': solicitacao.id,
                    'model_name': 'SolicitacaoCalazar',
                    'observacoes': solicitacao.observacoes_resultado,
                    'resultado_liberado': solicitacao.resultado_liberado
                })

    return render_template(
        'consultar_solicitacao.html', 
        resultado_protocolo=resultado_protocolo,
        historico_entidade=historico_entidade,
        entidade=entidade
    )


#-----------------------------------------------------------------RESPONDER PENDENCIA ------------------------------------------------------------------------------------------------

@app.route('/cidadao/responder_pendencia/<string:tipo_processo>/<int:processo_id>', methods=['POST'])
def cidadao_responder_pendencia(tipo_processo, processo_id):
    """
    Processa o envio de documentos e respostas pelo cidadão para resolver uma pendência.
    """
    model_map = {
        'LicencaEmpresa': LicencaEmpresa,
        'LicencaAutonomo': LicencaAutonomo,
        'LicencaEvento': LicencaEvento,
        # Adicione outros modelos conforme necessário
    }
    
    model_class = model_map.get(tipo_processo)
    if not model_class:
        flash('Tipo de processo inválido.', 'danger')
        return redirect(url_for('consultar_solicitacao'))

    processo = model_class.query.get_or_404(processo_id)
    
    # Pega os dados do formulário
    anexo = request.files.get('anexo_pendencia')
    resposta_texto = request.form.get('resposta_texto', '').strip()

    # Validação: Exige que o cidadão envie um anexo ou uma resposta em texto.
    if (not anexo or not anexo.filename) and not resposta_texto:
        flash('É necessário anexar um ficheiro ou escrever uma resposta para resolver a pendência.', 'warning')
        return redirect(request.referrer or url_for('consultar_solicitacao'))

    data_hora_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Cria uma entrada de log para o histórico de observações
    historico_observacao = f"\n\n--- RESPOSTA DO CIDADÃO EM {data_hora_atual} ---"
    
    # Processa o anexo, se houver
    if anexo and anexo.filename:
        # Supondo que a sua função 'salvar_arquivo_upload' já existe e funciona
        caminho_anexo = salvar_arquivo_upload(anexo, f"pendencia_{tipo_processo}_{processo_id}")

        if not caminho_anexo:
             flash('Ocorreu um erro ao salvar o anexo. Tente novamente.', 'danger')
             return redirect(request.referrer)

        # Adiciona o anexo à lista de anexos de pendência (campo JSON)
        if not hasattr(processo, 'anexos_pendencia') or not processo.anexos_pendencia:
            processo.anexos_pendencia = []
        
        processo.anexos_pendencia.append({
            'nome_original': anexo.filename,
            'caminho_salvo': caminho_anexo,
            'data_envio': data_hora_atual
        })
        flag_modified(processo, "anexos_pendencia")
        
        historico_observacao += f"\nAnexo enviado: {anexo.filename}"

    # Adiciona a resposta em texto ao log, se houver
    if resposta_texto:
        historico_observacao += f"\nResposta do cidadão: {resposta_texto}"

    # Adiciona o log ao campo de observações principal do processo
    if hasattr(processo, 'observacoes'):
        processo.observacoes = (processo.observacoes or '') + historico_observacao
    
    # Muda o status para que o admin possa reanalisar
    processo.status = 'Em Análise'  # Status mais claro que 'Pendente'
    
    db.session.commit()

    flash('Resposta enviada com sucesso! A sua solicitação será reanalisada em breve.', 'success')
    return redirect(url_for('consultar_solicitacao'))


@app.route('/download/file/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download/relatorio/<filename>')
def download_relatorio(filename):
    return send_from_directory(app.config['RELATORIOS_FOLDER'], filename)

# --- Rotas de Denúncias ---


@app.route('/denuncias/detalhe/<int:denuncia_id>')
def detalhe_denuncia(denuncia_id):
    denuncia = Denuncias.query.get_or_404(denuncia_id)
    return render_template('detalhe_denuncia.html', denuncia=denuncia)

@app.route('/denuncias/gerar_relatorio/<int:denuncia_id>')
def gerar_relatorio_denuncia(denuncia_id):
    denuncia = Denuncias.query.get_or_404(denuncia_id)
    try:
        filepath = gerar_relatorio_denuncia_pdf(denuncia)
        flash('Relatório gerado com sucesso!', 'success')
        return redirect(url_for('download_relatorio', filename=os.path.basename(filepath)))
    except Exception as e:
        flash(f'Erro ao gerar relatório: {e}', 'danger')
        return redirect(url_for('detalhe_denuncia', denuncia_id=denuncia_id))

# Exemplo de rota para criar denúncia (necessita de formulário no HTML)
@app.route('/denuncias/nova', methods=['GET', 'POST'])
def nova_denuncia():
    if request.method == 'POST':
        try:
            # --- 1. Geração do Protocolo ---
            ano_atual = datetime.now().year
            prefixo_denuncia = f"DEN-{ano_atual}/"
            ultimo_denuncia_protocolo = db.session.query(db.func.max(Denuncias.protocolo_denuncia)).filter(
                Denuncias.protocolo_denuncia.like(f"{prefixo_denuncia}%")
            ).scalar()
            
            if ultimo_denuncia_protocolo:
                ultimo_num = int(ultimo_denuncia_protocolo.split('/')[-1])
                proximo_num_denuncia = ultimo_num + 1
            else:
                proximo_num_denuncia = 1
            
            protocolo_denuncia = f"{prefixo_denuncia}{proximo_num_denuncia:05d}"

            # --- 2. Processamento dos Anexos ---
            anexos_salvos = handle_upload('anexos', subfolder='denuncias', multiple=True)

            # --- 3. Criação do Objeto Denúncia ---
            nova_denuncia_obj = Denuncias(
                protocolo_denuncia=protocolo_denuncia,
                data_denuncia=datetime.utcnow(),
                anonimato='anonimato' in request.form,
                denunciante_nome=request.form.get('denunciante_nome'),
                denunciante_telefone=request.form.get('denunciante_telefone'),
                denunciante_email=request.form.get('denunciante_email'),
                denunciado_nome=request.form.get('denunciado_nome'),
                denunciado_rua=request.form.get('denunciado_rua'),
                denunciado_numero=request.form.get('denunciado_numero'),
                denunciado_bairro=request.form.get('denunciado_bairro'),
                denunciado_municipio=request.form.get('denunciado_municipio'),
                denunciado_ponto_ref=request.form.get('denunciado_ponto_ref'),
                denunciado_tipo_local=request.form.get('denunciado_tipo_local'),
                motivo_classificacao=", ".join(request.form.getlist('motivo_classificacao')),
                motivo_descricao=request.form.get('motivo_descricao'),
                anexos_path=anexos_salvos
            )
            
            # --- 4. Salva no Banco de Dados ---
            db.session.add(nova_denuncia_obj)
            db.session.commit()
            
            # --- 5. Feedback e Redirecionamento ---
            flash(f'Denúncia registrada com sucesso! Protocolo: {protocolo_denuncia}', 'success')
            return redirect(url_for('index')) # <-- Redireciona para a página inicial

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao registrar a denúncia: {e}', 'danger')
            return redirect(url_for('nova_denuncia'))

    # Se for GET, apenas exibe a página com o formulário.
    return render_template('registrar_denuncia.html')

@app.route('/admin/denuncia/<int:denuncia_id>/despachar', methods=['POST'])
def admin_despachar_denuncia(denuncia_id):
    denuncia = Denuncias.query.get_or_404(denuncia_id)
    
    try:
        # 1. Atualizar campos simples
        denuncia.status = request.form.get('novo_status')
        denuncia.despacho_fiscal = request.form.get('despacho_fiscal')
        denuncia.acao_gerada = request.form.get('acao_futura')

        # 2. Lidar com o vínculo (CPF/CNPJ)
        tipo_vinculo = request.form.get('tipo_vinculo')
        if tipo_vinculo == 'empresa':
            cnpj_informado = request.form.get('denunciado_cnpj')
            empresa = Empresas.query.filter_by(cnpj=cnpj_informado).first()
            if empresa:
                denuncia.empresa_id = empresa.id
                denuncia.denunciado_cpf_cnpj = cnpj_informado
                denuncia.cpf_vinculado = None # Limpa o vínculo de CPF
            else:
                flash(f'Empresa com CNPJ {cnpj_informado} não encontrada.', 'warning')
        
        elif tipo_vinculo == 'cpf':
            cpf_informado = request.form.get('denunciado_cpf')
            denuncia.cpf_vinculado = cpf_informado
            denuncia.empresa_id = None # Limpa o vínculo de empresa
        
        else: # 'nao'
            denuncia.empresa_id = None
            denuncia.cpf_vinculado = None

        # 3. Lidar com novos anexos do fiscal
        novos_anexos = handle_upload('fiscal_anexos', subfolder='fiscais', multiple=True)
        if novos_anexos:
            if denuncia.fiscal_anexos_path: # Se já existem anexos, adiciona os novos
                denuncia.fiscal_anexos_path += f", {novos_anexos}"
            else: # Se não, cria a lista
                denuncia.fiscal_anexos_path = novos_anexos

        # 4. Salvar tudo no banco de dados
        db.session.commit()
        flash('Denúncia atualizada com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar a denúncia: {e}', 'danger')

    return redirect(url_for('admin_detalhe_denuncia', denuncia_id=denuncia.id))


# --- ROTAS DE ADMINISTRAÇÃO ---
@app.route('/admin')
def admin_dashboard():
    try:
        # Contadores para os cards usando os novos modelos
        cadastros_pendentes = Empresas.query.filter(Empresas.status != 'Aprovado').count()
        
        # CORREÇÃO: Soma as licenças pendentes das novas tabelas
        licencas_empresa_pendentes = LicencaEmpresa.query.filter_by(status='Pendente').count()
        licencas_autonomo_pendentes = LicencaAutonomo.query.filter_by(status='Pendente').count()
        licencas_pendentes = licencas_empresa_pendentes + licencas_autonomo_pendentes

        licencas_publicas_pendentes = LicencasPublicas.query.filter_by(status='Pendente').count()
        denuncias_abertas = Denuncias.query.filter(or_(Denuncias.status == 'Recebida', Denuncias.status == 'Em Análise')).count()

        stats = {
            'cadastros_pendentes': cadastros_pendentes,
            'licencas_pendentes': licencas_pendentes,
            'licencas_publicas_pendentes': licencas_publicas_pendentes,
            'denuncias_abertas': denuncias_abertas
        }

        # Lógica para o gráfico (mantida como está)
        ano_atual = datetime.now().year
        sql_grafico = text("""
            SELECT strftime('%m', data_denuncia) as mes, COUNT(id) as total
            FROM denuncias
            WHERE strftime('%Y', data_denuncia) = :ano
            GROUP BY mes
            ORDER BY mes
        """)
        denuncias_por_mes_db = db.session.execute(sql_grafico, {'ano': str(ano_atual)}).mappings().all()

        meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        # Garante que todos os meses estejam presentes no gráfico
        dados_meses = {str(i).zfill(2): 0 for i in range(1, 13)}
        for row in denuncias_por_mes_db:
            dados_meses[row['mes']] = row['total']
        
        chart_labels = meses_nomes
        chart_data = [dados_meses[str(i).zfill(2)] for i in range(1, 13)]

        return render_template('admin_dashboard.html', 
                               stats=stats, 
                               chart_labels=json.dumps(chart_labels), 
                               chart_data=json.dumps(chart_data))

    except Exception as e:
        flash(f"Ocorreu um erro ao carregar o dashboard: {e}", "danger")
        print(f"ERRO NO DASHBOARD: {e}")
        # Retorna um template com dados vazios para evitar que a página quebre
        return render_template('admin_dashboard.html', stats={}, chart_labels='[]', chart_data='[]')

# --- Novas Rotas Adicionadas ---

@app.route('/admin/denuncias')
# @login_required  # <-- Se você usa sistema de login, descomente esta linha
def admin_listar_denuncias():
    """Exibe todas as denúncias registradas para o administrador."""
    # Busca todas as denúncias, ordenando pelas mais recentes primeiro
    denuncias = Denuncias.query.order_by(Denuncias.data_denuncia.desc()).all()
    
    # Renderiza um novo template que vamos criar, passando a lista de denúncias
    return render_template('admin_listar_denuncias.html', denuncias=denuncias)



@app.route('/admin/denuncias')
def admin_atender_denuncias():
    query_q = request.args.get('q', '')
    query_status = request.args.get('status', '')
    query_data_inicio = request.args.get('data_inicio', '')
    query_data_fim = request.args.get('data_fim', '')

    # Inicia a consulta base no modelo Denuncias
    query = Denuncias.query

    # Aplica os filtros dinamicamente
    if query_q:
        search_term = f"%{query_q}%"
        query = query.filter(or_(
            Denuncias.protocolo_denuncia.like(search_term),
            Denuncias.denunciado_nome.like(search_term)
        ))
    if query_status:
        query = query.filter_by(status=query_status)
    if query_data_inicio:
        # Converte a string de data para objeto date para comparação
        try:
            data_inicio_obj = datetime.strptime(query_data_inicio, '%Y-%m-%d').date()
            query = query.filter(Denuncias.data_denuncia >= data_inicio_obj)
        except ValueError:
            flash('Formato de data de início inválido. Use AAAA-MM-DD.', 'warning')
            # Você pode optar por retornar aqui ou continuar sem o filtro de data
    if query_data_fim:
        # Adiciona um dia para incluir o dia final na busca
        try:
            fim_date_obj = datetime.strptime(query_data_fim, '%Y-%m-%d').date()
            query = query.filter(Denuncias.data_denuncia < fim_date_obj + timedelta(days=1))
        except ValueError:
            flash('Formato de data final inválido. Use AAAA-MM-DD.', 'warning')
            # Você pode optar por retornar aqui ou continuar sem o filtro de data

    # Ordena e executa a consulta
    denuncias = query.order_by(Denuncias.data_denuncia.desc()).all()
    
    return render_template('admin_atender_denuncias.html', 
                           denuncias=denuncias,
                           query_q=query_q,
                           query_status=query_status,
                           query_data_inicio=query_data_inicio,
                           query_data_fim=query_data_fim)


@app.route('/admin/denuncia/<int:denuncia_id>')
# @login_required # Se você usa sistema de login, descomente
def admin_detalhe_denuncia(denuncia_id):
    """Exibe os detalhes completos de uma denúncia específica."""
    # O get_or_404 busca a denúncia pelo ID. Se não encontrar, exibe um erro 404 (Página não encontrada).
    denuncia = Denuncias.query.get_or_404(denuncia_id)
    return render_template('admin_detalhe_denuncia.html', denuncia=denuncia)


@app.route('/uploads/<path:subfolder>/<path:filename>')
def uploaded_file(subfolder, filename):
    """Serve os arquivos que foram enviados para uma subpasta específica."""
    # Constrói o caminho completo para a pasta de uploads
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    # Retorna o arquivo de forma segura
    return send_from_directory(upload_dir, filename)

            
    # Prepara a lista de anexos do fiscal para o template
    anexos_fiscal_preparados = []
    if denuncia.fiscal_anexos_path:
        for path_completo in denuncia.fiscal_anexos_path.split(';'):
            if path_completo: # Garante que o caminho não é uma string vazia
                anexos_fiscal_preparados.append({
                    'filename_completo': os.path.basename(path_completo),
                    'nome_exibicao': path_completo.split('_', 1)[-1]
                })

    return render_template('admin_detalhe_denuncia.html', 
                           denuncia=denuncia, 
                           anexos_denunciante=anexos_denunciante_preparados,
                           anexos_fiscal=anexos_fiscal_preparados)
                           
@app.route('/admin/denuncia/<int:denuncia_id>/gerar_relatorio') # ou /relatorio-pdf, conforme sua escolha
# @login_required
def admin_gerar_relatorio_denuncia(denuncia_id):
    try:
        denuncia = Denuncias.query.get_or_404(denuncia_id)
        
        fiscal_anexos_paths = []
        if denuncia.fiscal_anexos_path:
            filenames = denuncia.fiscal_anexos_path.split(',')
            for filename in filenames:
                filename = filename.strip()
                if filename:
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fiscais', filename)
                    fiscal_anexos_paths.append(full_path)
        
        # Garanta que 'now=datetime.now' está aqui
        rendered_html = render_template(
            'relatorio_denuncia_pdf.html', 
            denuncia=denuncia, 
            fiscal_anexos=fiscal_anexos_paths,
            now=datetime.now
        )
        
        pdf = HTML(string=rendered_html, base_url=request.base_url).write_pdf()
        pdf_filename = f"Relatorio_Denuncia_{denuncia.protocolo_denuncia.replace('/', '-')}.pdf"
        
        response = Response(pdf, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'inline; filename={pdf_filename}'
        return response
        
    except Exception as e:
        # Esta parte é a que gera a mensagem de erro
        flash(f"Erro ao gerar o PDF: {e}", "danger")
        return redirect(url_for('admin_detalhe_denuncia', denuncia_id=denuncia_id))



#----------------------------ROTA VISTORIAS ---------------------------------------------------------------------------------------

@app.route('/registrar_nova_vistoria', methods=['GET', 'POST'])
def registrar_nova_vistoria():
    checklists = Checklist.query.order_by(Checklist.titulo).all()
    
    # --- MUDANÇA 2: Corrigir a consulta para usar o modelo 'Funcionario' ---
    try:
        # Buscamos na tabela 'Funcionario' e filtramos pelo 'cargo'
        fiscais_db = Funcionario.query.filter(Funcionario.cargo.ilike('%fiscal%')).all()
        
        # --- MUDANÇA 3: Usar 'f.nome' em vez de 'f.nome_completo' ---
        # O template espera uma chave 'nome_completo', então mantemos a chave e ajustamos o valor.
        funcionarios_list = [
            {'id': f.id, 'nome_completo': f.nome, 'matricula': f.matricula}
            for f in fiscais_db
        ]
    except Exception as e:
        flash(f'Erro ao carregar a lista de fiscais: {e}', 'danger')
        funcionarios_list = []

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'buscar_empresa':
            cnpj_pesquisado = request.form.get('cnpj_cpf')
            empresa = Empresas.query.filter_by(cnpj=limpar_cnpj(cnpj_pesquisado)).first() if cnpj_pesquisado else None
            
            return render_template('registrar_vistoria.html', 
                                   checklists=checklists, 
                                   funcionarios=funcionarios_list,
                                   empresa=empresa, 
                                   cnpj_pesquisado=cnpj_pesquisado)

        elif action == 'salvar_vistoria':
            try:
                # Lógica de protocolo (sem alteração)
                ano_atual = datetime.now().year
                categoria_protocolo = 'VISTORIA'
                protocolo_seq = ProtocoloSequencial.query.filter_by(ano=ano_atual, categoria=categoria_protocolo).with_for_update().first()
                if not protocolo_seq:
                    protocolo_seq = ProtocoloSequencial(ano=ano_atual, categoria=categoria_protocolo, ultimo_numero=0)
                    db.session.add(protocolo_seq)
                    db.session.flush()
                protocolo_seq.ultimo_numero += 1
                protocolo_gerado = f"VIS-{ano_atual}/{protocolo_seq.ultimo_numero:04d}"
                
                # --- MUDANÇA 4: Corrigir o salvamento para usar 'Funcionario' e 'f.nome' ---
                inspetores_ids = request.form.getlist('inspetores[]')
                fiscais_selecionados = Funcionario.query.filter(Funcionario.id.in_(inspetores_ids)).all()
                fiscais_json = [
                    {'nome': f.nome, 'matricula': f.matricula} 
                    for f in fiscais_selecionados
                ]

                # Coleta do restante dos dados (sem alteração)
                empresa_id = request.form.get('empresa_id')
                data_inspecao_str = request.form.get('data_inspecao')
                data_inspecao = datetime.strptime(data_inspecao_str, '%Y-%m-%d').date() if data_inspecao_str else datetime.now().date()
                objetivos = request.form.getlist('objetivo_inspecao')
                if request.form.get('objetivo_inspecao_outro') and request.form.get('objetivo_outro_texto'):
                    objetivos.append(f"Outro: {request.form.get('objetivo_outro_texto')}")

                documentos_str = ['Alvará de Funcionamento', 'Alvará Sanitário', 'Certificado de Dedetização', 'Manual de Boas Práticas', 'Procedimentos Operacionais Padronizados (POPs)', 'Comprovante de Limpeza de Caixa d\'Água', 'Comprovante de Controle de Pragas', 'Atestados de Saúde Ocupacional (ASO)']
                documentacao_verificada = {
                doc: ('Apresentado' if f"doc_{doc.lower().replace(' ', '_').replace('\'', '')}" in request.form else 'Não Apresentado')
                for doc in documentos_str}
                checklist_respostas = {key: val for key, val in request.form.items() if key.startswith('pergunta_')}
                nao_conformidades = request.form.getlist('nao_conformidades[]')
                recomendacoes = request.form.getlist('recomendacoes[]')
                prazos = request.form.getlist('prazos[]')
                recomendacoes_com_prazo = [{'recomendacao': r, 'prazo': p} for r, p in zip(recomendacoes, prazos)]
                observacoes_compiladas = {"nao_conformidades": nao_conformidades, "recomendacoes": recomendacoes_com_prazo}
                nomes_fotos = salvar_fotos_vistoria(request.files)

                nova_vistoria = Vistoria(
                    protocolo_vistoria=protocolo_gerado,
                    empresa_id=empresa_id if empresa_id else None,
                    data_vistoria=data_inspecao,
                    motivo=', '.join(objetivos),
                    fiscais=json.dumps(fiscais_json),
                    documentacao_verificada=json.dumps(documentacao_verificada),
                    checklist_id=request.form.get('checklist_id'),
                    checklist_respostas=json.dumps(checklist_respostas),
                    observacoes=json.dumps(observacoes_compiladas),
                    fotos=json.dumps(nomes_fotos),
                    status_analise='Pendente'
                )

                db.session.add(nova_vistoria)
                db.session.commit()
                flash(f'Vistoria registrada com sucesso! Protocolo: {protocolo_gerado}', 'success')
                return redirect(url_for('admin_analisar_processos'))

            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao registrar vistoria: {e}', 'danger')
                return render_template('registrar_vistoria.html',
                                       checklists=checklists,
                                       funcionarios=funcionarios_list)

    # Requisição GET
    return render_template('registrar_vistoria.html', 
                           checklists=checklists,
                           funcionarios=funcionarios_list,
                           empresa=None, 
                           cnpj_pesquisado=None)


@app.route('/admin/vistorias')
def admin_listar_vistorias():
    """Exibe uma lista de todas as vistorias realizadas."""
    # Busca todas as vistorias, ordenando pelas mais recentes primeiro
    vistorias = Vistoria.query.order_by(Vistoria.data_vistoria.desc()).all()
    return render_template('admin_listar_vistorias.html', vistorias=vistorias)

@app.route('/admin/vistorias/salvar', methods=['POST'])
def salvar_vistoria():
    try:
        empresa_id = request.form.get('empresa_id')
        if not empresa_id:
            flash('Busque e selecione uma empresa antes de salvar.', 'danger')
            return redirect(url_for('registrar_vistoria'))

        # Coleta das respostas do checklist (sem alterações)
        checklist_id = request.form.get('checklist_id')
        respostas_json = None
        if checklist_id:
            perguntas = request.form.getlist('pergunta_texto[]')
            respostas_coletadas = []
            for i in range(len(perguntas)):
                resposta = request.form.get(f'resposta_{i}')
                respostas_coletadas.append(resposta)
            observacoes = request.form.getlist('observacao[]')
            
            checklist_obj = Checklist.query.get(checklist_id)
            if checklist_obj:
                respostas_data = {"sections": []}
                question_counter = 0
                for section in checklist_obj.itens.get('sections', []):
                    new_section = {"title": section['title'], "questions": []}
                    for question in section.get('questions', []):
                        if question_counter < len(perguntas):
                            new_section["questions"].append({
                                "text": perguntas[question_counter],
                                "answer": respostas_coletadas[question_counter],
                                "observation": observacoes[question_counter]
                            })
                            question_counter += 1
                    respostas_data["sections"].append(new_section)
                respostas_json = respostas_data

        # Coleta das observações e fiscais
        observacoes_list = request.form.getlist('observacoes[]')
        fiscais_nomes = request.form.getlist('fiscais_nomes[]')
        fiscais_matriculas = request.form.getlist('fiscais_matriculas[]')
        
        fiscais_data = [
            {"nome": nome, "matricula": matricula} 
            for nome, matricula in zip(fiscais_nomes, fiscais_matriculas) if nome
        ]

        nova_vistoria = Vistoria(
            empresa_id=empresa_id,
            data_vistoria=datetime.strptime(request.form.get('data_vistoria'), '%Y-%m-%d').date(),
            checklist_id=checklist_id or None,
            motivo=request.form.get('motivo_vistoria'),
            documentacao_verificada={"documentos": request.form.getlist('documentacao[]')},
            checklist_respostas=respostas_json,
            observacoes={"observacoes": observacoes_list},
            fiscais={"fiscais": fiscais_data},
            prazo_adequacao=datetime.strptime(request.form.get('prazo_adequacao'), '%Y-%m-%d').date() if request.form.get('prazo_adequacao') else None
        )
        
        db.session.add(nova_vistoria)
        db.session.commit()
        
        flash('Vistoria registrada com sucesso!', 'success')
        return redirect(url_for('admin_ficha_empresa', empresa_id=empresa_id))

    except Exception as e:
        db.session.rollback()
        print(f"--- ERRO AO SALVAR VISTORIA: {e} ---")
        flash(f'Ocorreu um erro ao salvar a vistoria: {e}', 'danger')
        return redirect(url_for('registrar_vistoria'))

@app.route('/admin/vistoria/<int:vistoria_id>/relatorio_pdf')
def gerar_relatorio_vistoria_pdf(vistoria_id):
    vistoria = Vistoria.query.get_or_404(vistoria_id)

    # Processa todas as strings JSON (código existente, sem alterações)
    fotos = json.loads(vistoria.fotos) if vistoria.fotos else []
    checklist_respostas = json.loads(vistoria.checklist_respostas) if vistoria.checklist_respostas else {}
    observacoes_data = json.loads(vistoria.observacoes) if vistoria.observacoes else {}
    fiscais = json.loads(vistoria.fiscais) if vistoria.fiscais else []
    documentacao_verificada = json.loads(vistoria.documentacao_verificada) if vistoria.documentacao_verificada else {}

    # Lógica para combinar perguntas e respostas (código existente, com uma pequena melhoria)
    perguntas_com_respostas = []
    checklist_obj = None # Inicializa a variável
    if vistoria.checklist_id:
        checklist_obj = Checklist.query.get(vistoria.checklist_id) # Atribui o objeto do checklist
        if checklist_obj and checklist_obj.itens:
            # Garante que 'itens' seja um dicionário
            itens_data = json.loads(checklist_obj.itens) if isinstance(checklist_obj.itens, str) else checklist_obj.itens
            
            if itens_data and 'sections' in itens_data:
                for i, section in enumerate(itens_data.get('sections', [])):
                    for j, question in enumerate(section.get('questions', [])):
                        # A lógica do ID sintético foi mantida
                        synthetic_id = f"{checklist_obj.id}_{i}_{j}"
                        resposta_key = f"pergunta_{synthetic_id}"
                        if resposta_key in checklist_respostas:
                            perguntas_com_respostas.append({
                                'texto': question.get('text'),
                                'resposta': checklist_respostas[resposta_key]
                            })

    # ADICIONADO: Cria a string da data de emissão já formatada
    data_de_emissao = datetime.now().strftime('%d de %B de %Y')

    # Envia todas as variáveis já processadas para o novo template do relatório
    return render_template(
        'relatorio_vistoria_pdf.html',
        vistoria=vistoria,
        fotos=fotos,
        observacoes_data=observacoes_data,
        fiscais=fiscais,
        documentacao_verificada=documentacao_verificada,
        perguntas_com_respostas=perguntas_com_respostas,
        checklist=checklist_obj, # ADICIONADO: Passa o objeto do checklist para o template
        data_emissao=data_de_emissao # ADICIONADO: Passa a data formatada para o template
    )
@app.route('/admin/vistorias')
def admin_analisar_vistorias():
    # --- Pega os parâmetros da URL ---
    query_q = request.args.get('q', '')
    # Renomeado para 'situacao' para corresponder ao novo modelo
    query_situacao = request.args.get('situacao', '') 
    query_data_inicio = request.args.get('data_inicio', '')
    query_data_fim = request.args.get('data_fim', '')

    # --- Inicia a consulta base com os NOVOS modelos ---
    # Vistorias e Empresas
    query = db.session.query(Vistoria, Empresas).outerjoin( # <-- CORRIGIDO AQUI: Vistorias
        Empresas, Vistoria.empresa_id == Empresas.id # <-- CORRIGIDO AQUI: empresa_id
    )

    # --- Aplica os filtros ---
    if query_q:
        search = f"%{query_q}%"
        # Filtra pelos NOVOS campos. Removi 'protocolo' e 'cpf'. Adicionei 'nome_fantasia' e 'vistoriadores'.
        query = query.filter(or_(
            Empresas.razao_social.like(search),
            Empresas.cnpj.like(search),
            Empresas.nome_fantasia.like(search),
            Vistoria.fiscais.like(search) # <-- CORRIGIDO AQUI: Vistorias
        ))

    if query_situacao:
        # Filtra pelo NOVO campo 'situacao'
        query = query.filter(Vistoria.situacao == query_situacao) # <-- CORRIGIDO AQUI: Vistorias

    if query_data_inicio:
        try:
            data_inicio_obj = datetime.strptime(query_data_inicio, '%Y-%m-%d').date()
            query = query.filter(Vistoria.data_vistoria >= data_inicio_obj) # <-- CORRIGIDO AQUI: Vistorias
        except ValueError:
            flash('Formato de data de início inválido. Use AAAA-MM-DD.', 'warning')

    if query_data_fim:
        try:
            fim_date = datetime.strptime(query_data_fim, '%Y-%m-%d').date()
            query = query.filter(Vistoria.data_vistoria < fim_date + timedelta(days=1)) # <-- CORRIGIDO AQUI: Vistorias
        except ValueError:
            flash('Formato de data final inválido. Use AAAA-MM-DD.', 'warning')

    # --- Ordena e executa a consulta ---
    # A query agora retorna uma lista de tuplas: (objeto_vistoria, objeto_estabelecimento)
    vistorias_com_estabelecimentos = query.order_by(Vistoria.data_vistoria.desc()).all() # <-- CORRIGIDO AQUI: Vistorias
    
    # --- Renderiza o template com os dados atualizados ---
    return render_template('admin_analisar_vistorias.html', 
                           vistorias=vistorias_com_estabelecimentos,
                           query_q=query_q,
                           query_situacao=query_situacao, # Passa a variável com o novo nome
                           query_data_inicio=query_data_inicio,
                           query_data_fim=query_data_fim)

@app.route('/admin/vistoria/<int:vistoria_id>')
def admin_detalhe_vistoria(vistoria_id):
    vistoria = Vistoria.query.get_or_404(vistoria_id)

    # Processa as strings JSON e as transforma em listas/dicionários Python
    fotos = json.loads(vistoria.fotos) if vistoria.fotos else []
    checklist_respostas = json.loads(vistoria.checklist_respostas) if vistoria.checklist_respostas else {}
    observacoes_data = json.loads(vistoria.observacoes) if vistoria.observacoes else {}
    fiscais = json.loads(vistoria.fiscais) if vistoria.fiscais else []
    documentacao_verificada = json.loads(vistoria.documentacao_verificada) if vistoria.documentacao_verificada else {}

    perguntas_com_respostas = []
    if vistoria.checklist_id and checklist_respostas:
        # Esta linha agora funcionará, pois 'Checklist' foi importado
        checklist_obj = Checklist.query.get(vistoria.checklist_id)
        
        if checklist_obj and checklist_obj.itens:
            itens_data = {}
            try:
                itens_data = json.loads(checklist_obj.itens) if isinstance(checklist_obj.itens, str) else checklist_obj.itens
            except (json.JSONDecodeError, TypeError):
                itens_data = {}

            if itens_data and 'sections' in itens_data:
                for i, section in enumerate(itens_data.get('sections', [])):
                    for j, question in enumerate(section.get('questions', [])):
                        synthetic_id = f"{checklist_obj.id}_{i}_{j}"
                        resposta_key = f"pergunta_{synthetic_id}"
                        
                        if resposta_key in checklist_respostas:
                            perguntas_com_respostas.append({
                                'texto': question.get('text'),
                                'resposta': checklist_respostas[resposta_key]
                            })

    return render_template(
        'admin_detalhe_vistoria.html',
        vistoria=vistoria,
        fotos=fotos,
        checklist_respostas=checklist_respostas,
        observacoes_data=observacoes_data,
        fiscais=fiscais,
        documentacao_verificada=documentacao_verificada,
        perguntas_com_respostas=perguntas_com_respostas
    )

@app.route('/admin/vistoria/<int:vistoria_id>/salvar_parecer', methods=['POST'], endpoint='admin_salvar_parecer_vistoria')
def admin_salvar_parecer_vistoria(vistoria_id):
    # O nome do campo no formulário HTML é 'novo_status', e não 'parecer_final'.
    # A linha abaixo foi ajustada para ler o nome correto.
    parecer = request.form.get('novo_status')
    
    # Busca a vistoria que será atualizada
    vistoria_para_atualizar = Vistoria.query.get_or_404(vistoria_id)
    
    try:
        # Adiciona uma verificação para garantir que um valor foi selecionado
        if parecer:
            vistoria_para_atualizar.status_analise = parecer
            db.session.commit()
            flash(f'Parecer "{parecer}" salvo com sucesso para a vistoria!', 'success')
        else:
            flash('Nenhum parecer foi selecionado. Nenhuma alteração foi feita.', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar o parecer: {e}', 'danger')
        print(f"Erro detalhado ao salvar parecer: {e}") # Adicionado para depuração
        
    return redirect(url_for('admin_detalhe_vistoria', vistoria_id=vistoria_id))

from flask import render_template, request, flash, redirect, url_for
from datetime import datetime, timezone # Importa timezone para datas UTC
from sqlalchemy import func
import re # Importa o módulo de expressões regulares para limpeza

# Certifique-se de importar todos os modelos necessários, incluindo Autonomo
from models import db, Empresas, Autonomo, Notificacoes, Irregularidade, Funcionario

def limpar_documento(doc):
    """Função auxiliar para remover caracteres não numéricos de um documento."""
    if not doc:
        return ""
    return re.sub(r'\D', '', doc)

@app.route('/admin/registrar_notificacao', methods=['GET', 'POST'])
def registrar_notificacao():
    # Variáveis de controle do formulário
    entidade = None
    cnpj_pesquisado = ""
    show_unidentified_option = False
    search_performed = False

    # Busca as listas para os dropdowns
    irregularidades_lista = Irregularidade.query.order_by(Irregularidade.nome).all()
    fiscais_lista = Funcionario.query.filter(func.lower(Funcionario.cargo) == 'fiscal').order_by(Funcionario.nome).all()
    
    if request.method == 'POST':
        form_data = request.form
        action = form_data.get('action')
        cnpj_pesquisado = form_data.get('cnpj_cpf', '')
        search_performed = True

        if action == 'buscar_empresa':
            cnpj_cpf_limpo = limpar_documento(cnpj_pesquisado)
            empresa_encontrada = Empresas.query.filter_by(cnpj=cnpj_cpf_limpo).first()
            if empresa_encontrada:
                entidade = {"id": empresa_encontrada.id, "nome_principal": empresa_encontrada.razao_social, "tipo": "empresa"}
            else:
                autonomo_encontrado = Autonomo.query.filter_by(cpf=cnpj_cpf_limpo).first()
                if autonomo_encontrado:
                    entidade = {"id": autonomo_encontrado.id, "nome_principal": autonomo_encontrado.nome, "tipo": "autonomo"}
            
            if not entidade:
                show_unidentified_option = True
        
        elif action == 'salvar_notificacao':
            try:
                # Gera o protocolo
                ano_atual = datetime.now().year
                prefixo = f"NOT-{ano_atual}/"
                ultimo = db.session.query(db.func.max(Notificacoes.protocolo_notificacao)).filter(Notificacoes.protocolo_notificacao.like(f"{prefixo}%")).scalar()
                proximo_num = int(ultimo.split('/')[1]) + 1 if ultimo else 1
                protocolo = f"{prefixo}{proximo_num:05d}"

                # Formata as irregularidades
                lista_irregularidades = request.form.getlist('irregularidade_id')
                lista_prazos = request.form.getlist('prazo_irregularidade')
                irregularidades_formatadas = []
                for i, irreg_id in enumerate(lista_irregularidades):
                    irregularidade_obj = db.session.get(Irregularidade, irreg_id)
                    if irregularidade_obj:
                        prazo = lista_prazos[i] if i < len(lista_prazos) and lista_prazos[i] else "Não definido"
                        irregularidades_formatadas.append(f"- {irregularidade_obj.nome} (Prazo: {prazo})")

                # Cria o objeto base da notificação com os nomes de campo CORRETOS
                nova_notificacao = Notificacoes(
                    protocolo_notificacao=protocolo,
                    data_notificacao=datetime.now(timezone.utc),
                    # Usando o nome correto do campo do modelo
                    descricao_irregularidade="\n".join(irregularidades_formatadas),
                    # Mapeando os campos do formulário para os campos do modelo
                    ciencia_nome=form_data.get('responsavel_info_nome'),
                    ciencia_documento=form_data.get('responsavel_info_cpf'),
                    # O campo 'motivo_notificacao' pode ser usado para as observações
                    motivo_notificacao=form_data.get('observacoes_adicionais'),
                    parecer_final='Pendente'
                )

                # Adiciona os fiscais à relação many-to-many
                fiscal_id_1 = form_data.get('fiscal_id_1')
                fiscal_id_2 = form_data.get('fiscal_id_2')
                if fiscal_id_1:
                    fiscal1 = db.session.get(Funcionario, fiscal_id_1)
                    if fiscal1: nova_notificacao.fiscais_responsaveis.append(fiscal1)
                if fiscal_id_2:
                    fiscal2 = db.session.get(Funcionario, fiscal_id_2)
                    if fiscal2: nova_notificacao.fiscais_responsaveis.append(fiscal2)

                # Define o tipo de notificação (Regular ou Avulsa)
                if form_data.get('unidentified_notification_choice') == 'on':
                    # ATENÇÃO: Adicione os campos abaixo ao seu modelo Notificacoes para que a notificação avulsa funcione
                    # notificado_avulso_nome = db.Column(db.String)
                    # notificado_avulso_documento = db.Column(db.String)
                    # notificado_avulso_telefone = db.Column(db.String)
                    # notificado_avulso_endereco = db.Column(db.String)
                    nova_notificacao.notificado_avulso_nome = form_data.get('unidentified_nome')
                    nova_notificacao.notificado_avulso_documento = form_data.get('unidentified_cpf_cnpj')
                    nova_notificacao.notificado_avulso_telefone = form_data.get('unidentified_telefone')
                    nova_notificacao.notificado_avulso_endereco = form_data.get('unidentified_endereco')
                else:
                    entidade_id = form_data.get('entidade_id')
                    entidade_tipo = form_data.get('entidade_tipo')
                    if entidade_tipo == 'empresa':
                        nova_notificacao.empresa_id = entidade_id
                    elif entidade_tipo == 'autonomo':
                        nova_notificacao.autonomo_id = entidade_id

                db.session.add(nova_notificacao)
                db.session.commit()
                flash(f'Notificação registrada com sucesso! Protocolo: {protocolo}', 'success')
                return redirect(url_for('admin.listar_notificacoes')) 

            except Exception as e:
                db.session.rollback()
                flash(f'Ocorreu um erro ao salvar a notificação: {e}', 'danger')

    # Passa as variáveis para o template
    return render_template('registrar_notificacao.html', 
                           entidade=entidade, 
                           cnpj_pesquisado=cnpj_pesquisado,
                           irregularidades_lista=irregularidades_lista,
                           fiscais_lista=fiscais_lista,
                           show_unidentified_option=show_unidentified_option,
                           search_performed=search_performed)



@app.route('/admin/notificacoes')
# @login_required # Lembre-se de proteger suas rotas de admin
def admin_analisar_notificacoes():
    query_q = request.args.get('q', '')
    query_parecer = request.args.get('parecer', '')
    query_data_inicio = request.args.get('data_inicio', '')
    query_data_fim = request.args.get('data_fim', '')

    # --- CORREÇÃO NA CONSULTA BASE ---
    # A consulta agora seleciona o objeto Notificacoes completo e, separadamente,
    # o nome da empresa. Isso resolve o erro no template.
    query = db.session.query(
        Notificacoes,
        Empresas.razao_social  # Ou Empresas.nome_fantasia, o que preferir
    ).outerjoin(Empresas, Notificacoes.empresa_id == Empresas.id)

    # --- A SUA LÓGICA DE FILTROS FOI MANTIDA, POIS ESTÁ CORRETA ---
    if query_q:
        search = f"%{query_q}%"
        query = query.filter(or_(
            Notificacoes.protocolo_notificacao.like(search),
            Empresas.razao_social.like(search),
            Notificacoes.cpf_vinculado.like(search) # Adicionado para buscar por CPF
        ))

    if query_parecer:
        query = query.filter(Notificacoes.parecer_final == query_parecer)

    if query_data_inicio:
        try:
            dt_inicio = datetime.strptime(query_data_inicio, '%Y-%m-%d').date()
            query = query.filter(Notificacoes.data_notificacao >= dt_inicio)
        except ValueError:
            flash("Data de início inválida. Use AAAA-MM-DD.", "warning")

    if query_data_fim:
        try:
            dt_fim = datetime.strptime(query_data_fim, '%Y-%m-%d').date()
            # Adiciona 23:59:59 para incluir o dia inteiro na busca
            dt_fim_completa = datetime.combine(dt_fim, datetime.max.time())
            query = query.filter(Notificacoes.data_notificacao <= dt_fim_completa)
        except ValueError:
            flash("Data fim inválida. Use AAAA-MM-DD.", "warning")

    notificacoes = query.order_by(Notificacoes.data_notificacao.desc()).all()
    
    return render_template('analisar_processos.html', 
                           query_q=query_q, 
                           query_parecer=query_parecer, 
                           query_data_inicio=query_data_inicio,
                           query_data_fim=query_data_fim)

@app.route('/admin/notificacao/<int:notificacao_id>')
def admin_detalhe_notificacao(notificacao_id):
    """
    Busca uma notificação pelo ID.
    
    IMPORTANTE: Para que os detalhes da empresa e do autônomo apareçam,
    seu modelo 'Notificacoes' em models.py precisa ter os relacionamentos definidos.
    Adicione as seguintes linhas dentro da sua classe 'Notificacoes':

    empresa = db.relationship('Empresas', backref='notificacoes')
    autonomo = db.relationship('Autonomo', backref='notificacoes')
    """
    # Simplificando a busca.
    notificacao = Notificacoes.query.get(notificacao_id)

    # Se a notificação não for encontrada, retorna um erro 404.
    if not notificacao:
        abort(404)

    # CORREÇÃO: O caminho do template foi restaurado para 'admin/detalhe_notificacao.html'
    # conforme sua confirmação.
    return render_template('admin_detalhe_notificacao.html', notificacao=notificacao)



@app.route('/admin/notificacao/<int:notificacao_id>/salvar_parecer', methods=['POST'])
def admin_salvar_parecer_notificacao(notificacao_id):
    parecer = request.form.get('parecer_final')
    justificativa = request.form.get('justificativa_parecer')
    
    # Busca a notificação que será atualizada
    notificacao_para_atualizar = Notificacoes.query.get_or_404(notificacao_id)
    
    try:
        notificacao_para_atualizar.parecer_final = parecer
        notificacao_para_atualizar.justificativa_parecer = justificativa
        db.session.commit()
        flash(f'Parecer final "{parecer}" salvo com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar o parecer da notificação: {e}', 'danger')
        
    return redirect(url_for('admin_detalhe_notificacao', notificacao_id=notificacao_id))


#-------------------------------------------------------------TUDO SOBRE NOTIFICAÇÃO---------------------------------------------------------------------------------------------------------

@app.route('/admin/notificacao/<int:notificacao_id>/gerar-pdf')
def admin_gerar_pdf_notificacao(notificacao_id):
    """
    Gera um arquivo PDF para uma notificação específica.
    """
    # Busca a notificação pelo ID ou retorna um erro 404 se não encontrar.
    notificacao = Notificacoes.query.get_or_404(notificacao_id)

    # Inicializa o objeto PDF
    pdf = FPDF()
    pdf.add_page()
    # Define a fonte que suporta caracteres latinos
    pdf.set_font("Arial", size=12)

    # --- Cabeçalho do Documento ---
    # CORREÇÃO: Removemos o .encode(). A biblioteca FPDF lida com a codificação.
    pdf.cell(200, 10, txt=f"Notificação - Protocolo: {notificacao.protocolo_notificacao}", ln=True, align='C')
    pdf.ln(10)

    # --- Seção 1: Identificação do Notificado ---
    pdf.set_font("Arial", 'B', size=11)
    pdf.cell(200, 10, txt="1. Identificação do Notificado", ln=True)
    pdf.set_font("Arial", size=11)

    if notificacao.empresa_id:
        empresa = Empresas.query.get(notificacao.empresa_id)
        if empresa:
            pdf.cell(200, 7, txt=f"Razão Social: {empresa.razao_social}", ln=True)
            pdf.cell(200, 7, txt=f"CNPJ: {empresa.cnpj}", ln=True)
        else:
            pdf.cell(200, 7, txt="Empresa não encontrada.", ln=True)
    else:
        pdf.cell(200, 7, txt=f"Nome: {notificacao.ciencia_nome or 'Não informado'}", ln=True)
        pdf.cell(200, 7, txt=f"Documento: {notificacao.ciencia_documento or 'Não informado'}", ln=True)
    
    pdf.ln(5)

    # --- Seção 2: Detalhes da Notificação ---
    pdf.set_font("Arial", 'B', size=11)
    pdf.cell(200, 10, txt="2. Detalhes da Notificação", ln=True)
    pdf.set_font("Arial", size=11)
    
    data_formatada = notificacao.data_notificacao.strftime('%d/%m/%Y') if notificacao.data_notificacao else 'Não informada'
    pdf.cell(200, 7, txt=f"Data da Vistoria: {data_formatada}", ln=True)
    pdf.multi_cell(0, 7, txt=f"Irregularidades: {notificacao.descricao_irregularidade or 'Nenhuma irregularidade descrita.'}")

    pdf.ln(5)

    # --- Seção 3: Fiscais Responsáveis ---
    pdf.set_font("Arial", 'B', size=11)
    pdf.cell(200, 10, txt="3. Fiscais Responsáveis", ln=True)
    pdf.set_font("Arial", size=11)

    nomes_fiscais = [fiscal.nome for fiscal in notificacao.fiscais_responsaveis]
    texto_equipe = ", ".join(nomes_fiscais) if nomes_fiscais else 'Não informado'
    
    pdf.cell(200, 7, txt=f"Equipe: {texto_equipe}", ln=True)

    # --- Seção de Assinatura ---
    pdf.ln(10)
    pdf.set_font("Arial", 'I', size=10)
    pdf.cell(200, 10, txt="________________________________", ln=True, align='C')
    pdf.cell(200, 7, txt=f"{notificacao.ciencia_nome or 'Responsável não informado'}", ln=True, align='C')
    pdf.cell(200, 7, txt="Ciente", ln=True, align='C')

    # --- Geração da Resposta HTTP ---
    # A saída já está em bytes, então não é necessário codificar novamente.
    response_data = pdf.output(dest='S')
    response = make_response(response_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=notificacao_{notificacao.protocolo_notificacao}.pdf'
    
    return response

@app.route('/admin/licenca_publica/<int:licenca_id>/salvar_parecer', methods=['POST'])
def admin_salvar_parecer_licenca_publica(licenca_id):
    novo_status = request.form.get('novo_status')
    justificativa = request.form.get('justificativa')
    
    # Busca a licença que será atualizada
    licenca_para_atualizar = LicencasPublicas.query.get_or_404(licenca_id)
    
    try:
        licenca_para_atualizar.status = novo_status
        licenca_para_atualizar.justificativa_status = justificativa
        db.session.commit()
        flash(f'Status da licença pública atualizado para "{novo_status}" com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar parecer: {e}', 'danger')
        print(f"ERRO AO SALVAR PARECER LICENÇA PÚBLICA: {e}")
        
    return redirect(url_for('admin_detalhe_licenca_publica', licenca_id=licenca_id))

@app.route('/admin/consultar_licencas_publicas')
def admin_consultar_licencas_publicas():
    # Busca todas as licenças públicas, fazendo um JOIN com a tabela de empresas
    licencas = db.session.query(LicencasPublicas, Empresas).join(
        Empresas, LicencasPublicas.empresa_id == Empresas.id # CORREÇÃO: instituicao_id para empresa_id
    ).order_by(LicencasPublicas.data_solicitacao.desc()).all()
    
    return render_template('admin_consultar_licencas_publicas.html', licencas=licencas)

# Em app.py
# Substitua sua função 'registrar_auto_infracao' por esta:

@app.route('/admin/registrar_auto_infracao', methods=['GET', 'POST'])
def registrar_auto_infracao():
    empresa = None
    cnpj_pesquisado = ""
    numero_proximo_auto = None

    # 🔹 Função para gerar próximo número
    def gerar_numero_auto():
        ano_atual = datetime.now().year
        prefixo = f"AUT-{ano_atual}/"

        ultimo = db.session.query(
            db.func.max(AutosInfracao.protocolo_auto)
        ).filter(AutosInfracao.protocolo_auto.like(f"{prefixo}%")).scalar()

        if ultimo:
            ultimo_numero = int(ultimo.split('/')[-1])
            proximo_num = ultimo_numero + 1
        else:
            proximo_num = 1

        return f"{prefixo}{proximo_num:05d}"

    # Sempre gera número ao abrir o formulário
    numero_proximo_auto = gerar_numero_auto()

    if request.method == 'GET':
        cnpj_preenchido_url = request.args.get('cnpj_vinculado')
        cpf_preenchido_url = request.args.get('cpf_vinculado')
        if cnpj_preenchido_url:
            cnpj_limpo = limpar_cnpj(cnpj_preenchido_url)
            empresa = Empresas.query.filter_by(cnpj=cnpj_limpo).first()
            cnpj_pesquisado = cnpj_preenchido_url
        elif cpf_preenchido_url:
            cpf_limpo = limpar_cnpj(cpf_preenchido_url)
            cnpj_pesquisado = cpf_limpo
            flash(f'CPF {cpf_preenchido_url} preenchido. Busque o estabelecimento ou prossiga.', 'info')

    if request.method == 'POST':
        try:
            empresa_id_auto = request.form.get('empresa_id')
            cpf_vinculado_auto = None
            if not empresa_id_auto:
                cpf_vinculado_auto = limpar_cnpj(request.form.get('cnpj_cpf_hidden'))

            # Garante que o número é válido no momento do salvamento
            numero_gerado = gerar_numero_auto()

            novo_auto = AutosInfracao(
                protocolo_auto=numero_gerado,
                empresa_id=empresa_id_auto if empresa_id_auto else None,
                cpf_vinculado=cpf_vinculado_auto,
                data_auto=datetime.utcnow(),
                irregularidades_constatadas=request.form.get('irregularidades_constatadas'),
                prazo_defesa_dias=request.form.get('prazo_defesa_dias'),
                fiscal_responsavel=request.form.get('fiscal_responsavel'),
                status='Pendente'
            )
            db.session.add(novo_auto)
            db.session.commit()

            flash(f'Auto de Infração registrado com sucesso! Protocolo: {numero_gerado}', 'success')
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao registrar o auto de infração: {e}', 'danger')
            print(f"ERRO AO REGISTRAR AUTO DE INFRAÇÃO: {e}")

    return render_template(
        'registrar_auto_infracao.html',
        empresa=empresa,
        cnpj_pesquisado=cnpj_pesquisado,
        numero_proximo_auto=numero_proximo_auto
    )

@app.route('/admin/analisar_processos')
def admin_analisar_processos():
    query_q = request.args.get('q', '')
    query_tipo = request.args.get('tipo', '')
    query_data_inicio = request.args.get('data_inicio', '')
    query_data_fim = request.args.get('data_fim', '')

    # --- CORREÇÃO APLICADA ---
    # Com base no seu py, o nome correto da coluna na tabela 'vistoria'
    # é 'protocolo_vistoria'. A consulta SQL foi ajustada para refletir isso.
    # Os nomes das colunas para 'notificacoes' e 'autos_infracao' foram mantidos
    # conforme o seu código original.
    sql_string = """
    SELECT uniao.*, e.razao_social FROM (
        SELECT id, protocolo_vistoria as protocolo, data_vistoria as data_processo, 'Vistoria' as tipo, empresa_id, status_analise as status FROM vistoria
        UNION ALL
        SELECT id, protocolo_notificacao as protocolo, data_notificacao as data_processo, 'Notificação' as tipo, empresa_id, parecer_final as status FROM notificacoes
        UNION ALL
        SELECT id, protocolo_auto as protocolo, data_auto as data_processo, 'Auto de Infração' as tipo, empresa_id, status FROM autos_infracao
    ) as uniao
    LEFT JOIN empresas e ON uniao.empresa_id = e.id
    """
    
    conditions = []
    params = {}

    if query_q:
        conditions.append("(uniao.protocolo LIKE :q OR e.razao_social LIKE :q)")
        params['q'] = f"%{query_q}%"
    if query_tipo:
        conditions.append("uniao.tipo = :tipo")
        params['tipo'] = query_tipo
    if query_data_inicio:
        conditions.append("date(uniao.data_processo) >= :data_inicio")
        params['data_inicio'] = query_data_inicio
    if query_data_fim:
        conditions.append("date(uniao.data_processo) <= :data_fim")
        params['data_fim'] = query_data_fim

    if conditions:
        sql_string += " WHERE " + " AND ".join(conditions)

    sql_string += " ORDER BY uniao.data_processo DESC"

    # Executa a busca e envia os resultados DIRETAMENTE para o template
    processos = db.session.execute(text(sql_string), params).mappings().all()
    
    return render_template('analisar_processos.html',
                           processos=processos,
                           query_q=query_q,
                           query_tipo=query_tipo,
                           query_data_inicio=query_data_inicio,
                           query_data_fim=query_data_fim)

@app.template_filter('format_date_string')
def format_date_string(value, format='%d/%m/%Y'):
    """Filtro customizado para formatar datas que podem vir como string."""
    if not value:
        return 'N/A'
    
    # Se já for um objeto de data, formata e retorna
    if isinstance(value, (datetime, date)):
        return value.strftime(format)

    # Se for uma string, tenta converter
    if isinstance(value, str):
        try:
            # Tenta o formato completo primeiro
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return dt.strftime(format)
        except ValueError:
            try:
                # Se falhar, tenta o formato só com data
                dt = datetime.strptime(value, '%Y-%m-%d')
                return dt.strftime(format)
            except ValueError:
                # Se tudo falhar, retorna a string original para não quebrar a página
                return value
    
    return value


# Em app.py

@app.route('/admin/checklists')
def listar_checklists():
    todos_checklists = Checklist.query.order_by(Checklist.data_criacao.desc()).all()
    return render_template('admin_listar_checklists.html', checklists=todos_checklists)


@app.route('/admin/checklists/novo', methods=['GET', 'POST'])
def novo_checklist():
    if request.method == 'POST':
        titulo = request.form.get('nome_checklist')
        # Pega o valor do checkbox 'ativo'. Se não for enviado, será 'None'.
        ativo = request.form.get('ativo') == 'on'
        
        # Coleta as listas de dados do formulário dinâmico
        categorias = request.form.getlist('categorias[]')
        perguntas = request.form.getlist('perguntas[]')
        tipos_resposta = request.form.getlist('tipos_resposta[]')
        pergunta_categoria_map = request.form.getlist('pergunta_categoria[]')

        if not titulo:
            flash('O nome do checklist é obrigatório.', 'danger')
            return redirect(url_for('novo_checklist'))

        # Monta a estrutura JSON para salvar no banco
        checklist_data = {"sections": []}
        sections_dict = {cat_name: [] for cat_name in categorias if cat_name}

        for i, pergunta_text in enumerate(perguntas):
            categoria_nome = pergunta_categoria_map[i]
            if categoria_nome in sections_dict:
                sections_dict[categoria_nome].append({
                    "text": pergunta_text,
                    "type": tipos_resposta[i]
                })
        
        for title, questions_list in sections_dict.items():
            checklist_data["sections"].append({
                "title": title,
                "questions": questions_list
            })

        novo_checklist = Checklist(titulo=titulo, itens=checklist_data, ativo=ativo)
        db.session.add(novo_checklist)
        db.session.commit()

        flash('Novo checklist criado com sucesso!', 'success')
        return redirect(url_for('listar_checklists'))

    return render_template('admin_novo_checklist.html')



@app.route('/admin/checklists/editar/<int:checklist_id>', methods=['GET', 'POST'])
def editar_checklist(checklist_id):
    checklist = Checklist.query.get_or_404(checklist_id) # CORRIGIDO AQUI: Checklists

    if request.method == 'POST':
        try:
            checklist.nome = request.form.get('nome_checklist')
            
            # Estratégia de Sincronização: Apagar as perguntas antigas e recriar
            ChecklistItem.query.filter_by(checklist_id=checklist.id).delete() # CORRIGIDO AQUI: ChecklistItem
            
            perguntas_textos = request.form.getlist('perguntas[]')
            tipos_resposta = request.form.getlist('tipos_resposta[]')
            perguntas_categorias = request.form.getlist('pergunta_categoria[]')
            
            for i, texto_pergunta in enumerate(perguntas_textos):
                if texto_pergunta.strip():
                    nova_pergunta = ChecklistItem( # CORRIGIDO AQUI: ChecklistItem
                        checklist_id=checklist.id,
                        categoria=perguntas_categorias[i].strip(),
                        texto_pergunta=texto_pergunta.strip(),
                        tipo_resposta=tipos_resposta[i],
                        ordem=i
                    )
                    db.session.add(nova_pergunta)

            db.session.commit()
            flash('Checklist atualizado com sucesso!', 'success')
            return redirect(url_for('listar_checklists'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar checklist: {e}', 'danger')
            print(f"ERRO AO EDITAR CHECKLIST: {e}")
            
    # Prepara os dados para pré-preencher o formulário
    perguntas_por_categoria = {}
    # CORRIGIDO AQUI: Acessar a relação 'itens' e o modelo 'ChecklistItem'
    for p in checklist.itens.order_by(ChecklistItem.ordem): 
        if p.categoria not in perguntas_por_categoria:
            perguntas_por_categoria[p.categoria] = []
        perguntas_por_categoria[p.categoria].append({
            'texto': p.texto_pergunta,
            'tipo_resposta': p.tipo_resposta
        })
    
    return render_template('admin_editar_checklist.html', checklist=checklist, perguntas_data=json.dumps(perguntas_por_categoria))


@app.route('/api/checklist/<int:checklist_id>')
def get_checklist_perguntas(checklist_id):
    checklist = Checklist.query.get_or_404(checklist_id)
    
    if not checklist.itens or 'sections' not in checklist.itens:
        return jsonify({})

    perguntas_por_categoria = {}
    
    for i, section in enumerate(checklist.itens['sections']):
        categoria = section.get('title')
        questions = section.get('questions', [])
        
        if categoria and questions:
            perguntas_por_categoria[categoria] = []
            for j, q in enumerate(questions):
                synthetic_id = f"{checklist.id}_{i}_{j}"
                texto_pergunta = q.get('text', '')
                tipo_resposta = q.get('type')

                # --- CORREÇÃO APLICADA AQUI ---
                # Força o tipo de resposta para 'multipla_escolha' se a pergunta
                # terminar com um ponto de interrogação, garantindo que o
                # formulário sempre mostre as opções "Sim/Não/N.A" para perguntas.
                if texto_pergunta.strip().endswith('?'):
                    tipo_resposta = 'multipla_escolha'

                perguntas_por_categoria[categoria].append({
                    'id': synthetic_id,
                    'texto': texto_pergunta,
                    'tipo_resposta': tipo_resposta
                })

    return jsonify(perguntas_por_categoria)

@app.route('/solicitar-teste-calazar', methods=['GET', 'POST'])
def solicitar_teste_calazar():
    if request.method == 'POST':
        data_coleta_str = request.form.get('data_coleta')
        declaracao = request.form.get('declaracao_autorizacao')

        if not data_coleta_str:
            flash('O campo "Data Sugerida para Coleta" é obrigatório.', 'warning')
            return redirect(url_for('solicitar_teste_calazar'))
        
        if not declaracao:
            flash('Você precisa marcar a caixa de "Declaração e Autorização" para continuar.', 'warning')
            return redirect(url_for('solicitar_teste_calazar'))

        try:
            # 1. Gerar Protocolo Único
            ano_atual = datetime.now().year
            
            ultimo_protocolo = ProtocoloSequencial.query.filter_by(categoria='CALAZAR', ano=ano_atual).first()
            if not ultimo_protocolo:
                ultimo_protocolo = ProtocoloSequencial(categoria='CALAZAR', ano=ano_atual, ultimo_numero=0)
                db.session.add(ultimo_protocolo)
            
            ultimo_protocolo.ultimo_numero += 1
            protocolo_str = f"STCAZ-{ano_atual}/{str(ultimo_protocolo.ultimo_numero).zfill(4)}"

            protocolo_filename_safe = protocolo_str.replace('/', '-')

            # 2. Salvar as fotos usando o nome seguro
            foto_focinho_path = salvar_foto_animal(request.files.get('foto_focinho'), protocolo_filename_safe)
            foto_patas_path = salvar_foto_animal(request.files.get('foto_patas'), protocolo_filename_safe)
            foto_corpo_inteiro_path = salvar_foto_animal(request.files.get('foto_corpo_inteiro'), protocolo_filename_safe)

            # --- INÍCIO DA CORREÇÃO ---
            # Converte a string do horário para um objeto time do Python
            horario_coleta_str = request.form.get('horario_coleta')
            horario_coleta_obj = None
            if horario_coleta_str:
                horario_coleta_obj = datetime.strptime(horario_coleta_str, '%H:%M').time()
            # --- FIM DA CORREÇÃO ---

            # 3. Criar a nova solicitação com os dados do formulário
            nova_solicitacao = SolicitacaoCalazar(
                protocolo=protocolo_str,
                status='Aguardando Agendamento',
                data_solicitacao=datetime.now(),
                
                # Dados do Proprietário
                proprietario_nome=request.form.get('proprietario_nome'),
                proprietario_cpf=request.form.get('proprietario_cpf'),
                proprietario_endereco=request.form.get('proprietario_endereco'),
                proprietario_telefone=request.form.get('proprietario_telefone'),
                
                # Dados do Animal
                animal_nome=request.form.get('animal_nome'),
                animal_especie=request.form.get('animal_especie'),
                animal_raca=request.form.get('animal_raca'),
                animal_sexo=request.form.get('animal_sexo'),
                animal_idade=request.form.get('animal_idade'),
                animal_cor=request.form.get('animal_cor'),
                
                # Caminhos das fotos salvas
                foto_focinho_path=foto_focinho_path,
                foto_patas_path=foto_patas_path,
                foto_corpo_inteiro_path=foto_corpo_inteiro_path,
                
                # Informações Clínicas
                sinais_clinicos=request.form.get('sinais_clinicos'),
                data_coleta_sugerida=datetime.strptime(data_coleta_str, '%Y-%m-%d').date(),
                horario_coleta_sugerido=horario_coleta_obj # Usa o objeto de tempo convertido
            )

            # 4. Salvar no Banco de Dados
            db.session.add(nova_solicitacao)
            db.session.commit()

            # 5. Mostrar mensagem de sucesso com o protocolo
            flash(f"Sua solicitação foi enviada com sucesso! O número do seu protocolo é: {protocolo_str}. Guarde este número para consultas futuras.", 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            print(f"ERRO NA ROTA solicitar_teste_calazar: {e}")
            flash(f"Ocorreu um erro interno ao processar sua solicitação. Por favor, tente novamente.", 'danger')
            return redirect(url_for('solicitar_teste_calazar'))

    return render_template('solicitar_teste_calazar.html')

# NOVO: Rota para Solicitação de Receituário
@app.route('/solicitar-receituario', methods=['GET', 'POST'])
def solicitar_receituario():
    if request.method == 'POST':
        # --- Coletar os dados do formulário ---
        # Dados do Local Solicitante
        cnpj_local = request.form.get('cnpj_local')
        nome_local = request.form.get('nome_local')
        endereco_local = request.form.get('endereco_local')
        numero_local = request.form.get('numero_local')
        contato_local = request.form.get('contato_local')

        # Dados do Profissional Solicitante
        nome_profissional = request.form.get('nome_profissional')
        cpf_profissional = request.form.get('cpf_profissional')
        conselho_profissional = request.form.get('conselho_profissional')
        telefone_contato = request.form.get('telefone_contato')
        email_contato = request.form.get('email_contato')

        # Detalhes da Solicitação (receituários e quantidades)
        receituarios_solicitados = {}
        
        if request.form.get('receituario_A_amarela') == 'sim':
            quantidade_a_str = request.form.get('quantidade_a')
            if quantidade_a_str and quantidade_a_str.isdigit():
                receituarios_solicitados['A_amarela'] = int(quantidade_a_str)
            else:
                flash('Quantidade inválida para Notificação A (Amarela).', 'danger')
                return redirect(url_for('solicitar_receituario'))

        if request.form.get('receituario_B1_azul') == 'sim':
            quantidade_b1_str = request.form.get('quantidade_b1')
            if quantidade_b1_str and quantidade_b1_str.isdigit():
                receituarios_solicitados['B1_azul'] = int(quantidade_b1_str)
            else:
                flash('Quantidade inválida para Notificação B (Azul).', 'danger')
                return redirect(url_for('solicitar_receituario'))

        if request.form.get('receituario_B2_sibutramina') == 'sim':
            quantidade_b2_str = request.form.get('quantidade_b2')
            if quantidade_b2_str and quantidade_b2_str.isdigit():
                receituarios_solicitados['B2_sibutramina'] = int(quantidade_b2_str)
            else:
                flash('Quantidade inválida para Notificação B2 (Sibutramina).', 'danger')
                return redirect(url_for('solicitar_receituario'))

        if request.form.get('receituario_C_branca') == 'sim':
            quantidade_c_str = request.form.get('quantidade_c')
            if quantidade_c_str and quantidade_c_str.isdigit():
                receituarios_solicitados['C_branca'] = int(quantidade_c_str)
            else:
                flash('Quantidade inválida para Receituário de Controle Especial.', 'danger')
                return redirect(url_for('solicitar_receituario'))

        # Converter o dicionário de solicitações para uma string JSON para salvar no DB
        receituarios_solicitados_json = json.dumps(receituarios_solicitados)

        # --- Validação básica se pelo menos um receituário foi solicitado ---
        if not receituarios_solicitados:
            flash('Nenhum tipo de receituário foi selecionado para solicitação.', 'danger')
            return redirect(url_for('solicitar_receituario'))

        # --- INÍCIO DO BLOCO TRY PRINCIPAL para toda a lógica de POST ---
        try:
            # --- Gerar o protocolo ---
            protocolo_gerado = f"VISA-REC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}" 
            
            # --- Criar e Salvar a Solicitação ---
            nova_solicitacao = SolicitacaoReceituario(
                protocolo=protocolo_gerado,
                cnpj_local=cnpj_local,
                nome_local=nome_local,
                endereco_local=endereco_local,
                numero_local=numero_local,
                contato_local=contato_local,
                nome_profissional=nome_profissional,
                cpf_profissional=cpf_profissional,
                conselho_profissional=conselho_profissional,
                telefone_contato=telefone_contato,
                email_contato=email_contato,
                receituarios_solicitados_json=receituarios_solicitados_json,
                status='Pendente' # Status inicial
            )
            
            db.session.add(nova_solicitacao)
            db.session.commit()

            flash(f"Solicitação de Receituários enviada com sucesso! Protocolo: {nova_solicitacao.protocolo}. Sua solicitação está em análise.", 'success')
            return redirect(url_for('index')) # Redireciona para a página inicial

        except Exception as e:
            db.session.rollback() # Desfaz qualquer mudança no DB em caso de erro
            print(f"ERRO AO SALVAR SOLICITAÇÃO DE RECEITUÁRIOS NO DB: {e}")
            import traceback
            traceback.print_exc() # Imprime a traceback completa no console do servidor
            flash('Ocorreu um erro inesperado ao enviar sua solicitação. Por favor, tente novamente.', 'danger')
            return redirect(url_for('solicitar_receituario'))
        # --- FIM DO BLOCO TRY PRINCIPAL ---

    # Método GET: Renderiza o formulário
    return render_template('solicitacao_receituario.html')

@app.route('/admin/solicitacoes-receituario')
# @login_required # Se você usa Flask-Login para proteger rotas de admin
def admin_solicitacoes_receituario():
    # Busca todas as solicitações de receituário do banco de dados, ordenadas pela data mais recente
    solicitacoes = SolicitacaoReceituario.query.order_by(SolicitacaoReceituario.data_solicitacao.desc()).all()
    
    # Renderiza o template que exibirá a tabela de solicitações, passando a lista de objetos
    return render_template('admin_solicitacoes_receituario.html', solicitacoes=solicitacoes)

@app.route('/admin/atender-receituario/<int:solicitacao_id>', methods=['GET', 'POST'])
# @login_required # Se você usa Flask-Login para proteger rotas de admin
def admin_atender_receituario(solicitacao_id):
    solicitacao = SolicitacaoReceituario.query.get_or_404(solicitacao_id)
    
    # Converte o JSON de receituários solicitados para exibir no template
    receituarios_solicitados_parsed = json.loads(solicitacao.receituarios_solicitados_json)
    
    # --- PREPARAÇÃO DE DADOS PARA O MÉTODO GET ---
    # Busca todos os tipos de receituário e cria um mapa (ID -> Objeto, Sigla -> Objeto)
    tipos_receituario_list = TipoReceituario.query.all()
    tipos_receituario_map_by_id = {tipo.id: tipo for tipo in tipos_receituario_list}
    tipos_receituario_map_by_sigla = {tipo.sigla: tipo for tipo in tipos_receituario_list} # Novo mapa por sigla

    # Busca blocos disponíveis e os agrupa por tipo de receituário
    blocos_disponiveis = BlocoReceituario.query.filter_by(status='Disponível')\
                                                .order_by(BlocoReceituario.tipo_id, BlocoReceituario.numero_inicial, BlocoReceituario.numero_bloco)\
                                                .all()
    
    blocos_disponiveis_agrupados = {}
    for bloco in blocos_disponiveis:
        sigla_do_tipo = tipos_receituario_map_by_id.get(bloco.tipo_id).sigla # Pega a sigla do tipo do bloco
        if sigla_do_tipo not in blocos_disponiveis_agrupados:
            blocos_disponiveis_agrupados[sigla_do_tipo] = []
        blocos_disponiveis_agrupados[sigla_do_tipo].append(bloco)
    # --- FIM PREPARAÇÃO DE DADOS GET ---

    if request.method == 'POST':
        nome_recebedor = request.form.get('nome_recebedor')
        cpf_recebedor = request.form.get('cpf_recebedor')
        telefone_recebedor = request.form.get('telefone_recebedor')
        blocos_dispensar_ids_str = request.form.getlist('blocos_dispensar_ids[]') # IDs dos blocos selecionados

        # Validações dos dados do recebedor
        if not all([nome_recebedor, cpf_recebedor]):
            flash('Nome e CPF do recebedor são obrigatórios para concluir o atendimento.', 'danger')
            return redirect(url_for('admin_atender_receituario', solicitacao_id=solicitacao.id))
        
        if not blocos_dispensar_ids_str: # Se nenhum bloco foi selecionado
            flash('Nenhum bloco de receituário foi selecionado para dispensar.', 'danger')
            return redirect(url_for('admin_atender_receituario', solicitacao_id=solicitacao.id))

        try:
            # Converte os IDs de string para inteiro
            blocos_dispensar_ids = [int(bloco_id) for bloco_id in blocos_dispensar_ids_str]

            # Inicia o registro do atendimento
            novo_atendimento = AtendimentoReceituario(
                solicitacao_id=solicitacao.id,
                nome_recebedor=nome_recebedor,
                cpf_recebedor=cpf_recebedor,
                telefone_recebedor=telefone_recebedor
                # data_atendimento é default=datetime.utcnow
            )
            db.session.add(novo_atendimento)
            db.session.flush() # Garante que o novo_atendimento.id esteja disponível

            blocos_dispensados_count = 0
            total_folhas_dispensadas = 0

            # Atualiza o status dos blocos selecionados e calcula totais
            for bloco_id in blocos_dispensar_ids:
                bloco = BlocoReceituario.query.get(bloco_id)
                if bloco and bloco.status == 'Disponível':
                    bloco.status = 'Dispensado'
                    bloco.atendimento_id = novo_atendimento.id # Associa o bloco ao atendimento
                    blocos_dispensados_count += 1
                    total_folhas_dispensadas += (bloco.numero_final - bloco.numero_inicial + 1)
                else:
                    flash(f'Erro: Bloco ID {bloco_id} não encontrado ou não disponível para dispensa.', 'warning')
                    db.session.rollback() # Desfaz tudo se houver problema com um bloco
                    return redirect(url_for('admin_atender_receituario', solicitacao_id=solicitacao.id))

            # Atualiza o status da solicitação
            solicitacao.status = 'Atendida'
            solicitacao.data_atendimento = datetime.utcnow() # Registra data de atendimento da solicitação

            # Atualiza o EstoqueReceituario geral
            # Para cada tipo de bloco dispensado, atualize o EstoqueReceituario correspondente
            blocos_por_tipo = {} # Dicionário para somar blocos/folhas por tipo
            for bloco_id in blocos_dispensar_ids:
                bloco = BlocoReceituario.query.get(bloco_id)
                if bloco:
                    if bloco.tipo_id not in blocos_por_tipo:
                        blocos_por_tipo[bloco.tipo_id] = {'blocos': 0, 'folhas': 0}
                    blocos_por_tipo[bloco.tipo_id]['blocos'] += 1
                    blocos_por_tipo[bloco.tipo_id]['folhas'] += (bloco.numero_final - bloco.numero_inicial + 1)

            for tipo_id, quantidades in blocos_por_tipo.items():
                estoque_geral = EstoqueReceituario.query.filter_by(tipo_id=tipo_id).first()
                if estoque_geral:
                    estoque_geral.quantidade_blocos_disponivel -= quantidades['blocos']
                    estoque_geral.quantidade_folhas_disponivel -= quantidades['folhas']
                    # Garante que não fiquem valores negativos
                    estoque_geral.quantidade_blocos_disponivel = max(0, estoque_geral.quantidade_blocos_disponivel)
                    estoque_geral.quantidade_folhas_disponivel = max(0, estoque_geral.quantidade_folhas_disponivel)
                else:
                    print(f"ATENÇÃO: Estoque geral para Tipo ID {tipo_id} não encontrado ao dispensar.") # Para debug

            db.session.commit()
            
            flash(f'Solicitação {solicitacao.protocolo} atendida com sucesso! {blocos_dispensados_count} bloco(s) ({total_folhas_dispensadas} folhas) dispensado(s).', 'success')
            # Redireciona para a página do comprovante
            return redirect(url_for('admin_comprovante_receituario', atendimento_id=novo_atendimento.id))

        except Exception as e:
            db.session.rollback()
            print(f"ERRO AO ATENDER SOLICITAÇÃO DE RECEITUÁRIOS: {e}")
            import traceback
            traceback.print_exc()
            flash('Ocorreu um erro inesperado ao atender a solicitação. Detalhes no console do servidor.', 'danger')
            return redirect(url_for('admin_atender_receituario', solicitacao_id=solicitacao.id))

    return render_template('admin_atender_receituario.html', 
                           solicitacao=solicitacao,
                           receituarios_solicitados_parsed=receituarios_solicitados_parsed,
                           tipos_receituario_map=tipos_receituario_map_by_sigla, # Passa o mapa por sigla para o template
                           blocos_disponiveis_agrupados=blocos_disponiveis_agrupados)


@app.route('/admin/solicitacoes-receituario/<int:solicitacao_id>')
# @login_required # Se você usa Flask-Login
def admin_detalhe_receituario(solicitacao_id):
    solicitacao = SolicitacaoReceituario.query.get_or_404(solicitacao_id)
    
    # Converte a string JSON de volta para um objeto Python
    receituarios_solicitados_parsed = json.loads(solicitacao.receituarios_solicitados_json)
    
    # Mapeia tipos de receituário (para exibir nomes completos)
    tipos_receituario_map = {tipo.sigla: tipo for tipo in TipoReceituario.query.all()}

    # --- NOVO: Buscar dados do atendimento e blocos dispensados, SE a solicitação foi atendida ---
    atendimento = None
    blocos_dispensados = None
    if solicitacao.status == 'Atendida' and solicitacao.data_atendimento:
        # Busca o atendimento associado a esta solicitação (pode haver mais de um, se for reatendida)
        # Vamos pegar o último atendimento, assumindo que uma solicitação é atendida uma vez
        atendimento = AtendimentoReceituario.query.filter_by(solicitacao_id=solicitacao.id)\
                                                .order_by(AtendimentoReceituario.data_atendimento.desc())\
                                                .first()
        if atendimento:
            # Busca todos os blocos associados a ESTE atendimento
            blocos_dispensados = BlocoReceituario.query.filter_by(atendimento_id=atendimento.id)\
                                                    .order_by(BlocoReceituario.tipo_id, BlocoReceituario.numero_inicial)\
                                                    .all()
            
            # Agrupa os blocos dispensados por tipo para exibição organizada
            blocos_dispensados_agrupados = {}
            for bloco in blocos_dispensados:
                sigla_do_tipo = tipos_receituario_map.get(bloco.tipo.sigla) # Pega o tipo_obj pela sigla
                if sigla_do_tipo.sigla not in blocos_dispensados_agrupados:
                    blocos_dispensados_agrupados[sigla_do_tipo.sigla] = []
                blocos_dispensados_agrupados[sigla_do_tipo.sigla].append(bloco)
        
        # Passa os dados para o template se forem encontrados
        if atendimento and blocos_dispensados:
            return render_template('admin_detalhe_receituario.html', 
                                   solicitacao=solicitacao, 
                                   receituarios_solicitados_parsed=receituarios_solicitados_parsed,
                                   tipos_receituario_map=tipos_receituario_map,
                                   atendimento=atendimento, # NOVO: Objeto do atendimento
                                   blocos_dispensados_agrupados=blocos_dispensados_agrupados) # NOVO: Blocos dispensados
    # --- FIM NOVO ---

    # Retorno padrão se a solicitação não foi atendida ou dados não encontrados
    return render_template('admin_detalhe_receituario.html', 
                           solicitacao=solicitacao, 
                           receituarios_solicitados_parsed=receituarios_solicitados_parsed,
                           tipos_receituario_map=tipos_receituario_map) # Passa para o template
# Rota para atualizar o status da solicitação (será criada logo após este detalhe)

@app.route('/admin/receituario/comprovante/<int:atendimento_id>')
# @login_required # Se você usa Flask-Login para proteger rotas de admin
def admin_comprovante_receituario(atendimento_id):
    atendimento = AtendimentoReceituario.query.get_or_404(atendimento_id)
    solicitacao = SolicitacaoReceituario.query.get_or_404(atendimento.solicitacao_id)
    
    # Blocos dispensados neste atendimento
    blocos_dispensados = BlocoReceituario.query.filter_by(atendimento_id=atendimento.id).all()
    
    # Converte o JSON de receituários solicitados para exibir no comprovante
    receituarios_solicitados_parsed = json.loads(solicitacao.receituarios_solicitados_json)
    
    # Mapeia tipos de receituário (para exibir nomes completos)
    tipos_receituario_map = {tipo.id: tipo for tipo in TipoReceituario.query.all()}
    tipos_receituario_map_by_sigla = {tipo.sigla: tipo for tipo in TipoReceituario.query.all()}

    return render_template('admin_comprovante_receituario.html', 
                           atendimento=atendimento,
                           solicitacao=solicitacao,
                           blocos_dispensados=blocos_dispensados,
                           receituarios_solicitados_parsed=receituarios_solicitados_parsed,
                           tipos_receituario_map=tipos_receituario_map, # Passa o mapa por ID para o template
                           tipos_receituario_map_by_sigla=tipos_receituario_map_by_sigla) # Passa o mapa por sigla



@app.route('/admin/solicitacoes-receituario/atualizar-status/<int:solicitacao_id>', methods=['POST'])
# @login_required
def admin_atualizar_status_receituario(solicitacao_id):
    novo_status = request.form.get('novo_status')
    justificativa = request.form.get('justificativa', '').strip() # Pode ser para recusa

    solicitacao = SolicitacaoReceituario.query.get_or_404(solicitacao_id)

    # Validação simples
    if novo_status in ['Recusada'] and not justificativa:
        flash('A justificativa é obrigatória para recusar uma solicitação.', 'danger')
        return redirect(url_for('admin_detalhe_receituario', solicitacao_id=solicitacao.id))

    try:
        solicitacao.status = novo_status
        solicitacao.justificativa_recusa = justificativa if justificativa else None
        if novo_status == 'Atendida':
            solicitacao.data_atendimento = datetime.utcnow() # Registra a data de atendimento
        else:
            solicitacao.data_atendimento = None # Limpa se o status mudar de atendida

        db.session.commit()
        flash(f'Status da solicitação atualizado para "{novo_status}" com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"ERRO AO ATUALIZAR STATUS DA SOLICITAÇÃO: {e}")
        flash(f'Ocorreu um erro ao atualizar o status: {e}', 'danger')

    return redirect(url_for('admin_detalhe_receituario', solicitacao_id=solicitacao.id))




@app.route('/admin/estoque-receituario')
# @login_required # Se você usa Flask-Login para proteger rotas de admin
def admin_estoque_receituario():
    # Buscar todos os tipos de receituário
    tipos_receituario = TipoReceituario.query.order_by(TipoReceituario.sigla).all()

    # Criar uma estrutura de dados para passar ao template
    # Ex: { TipoA: { estoque_geral: obj, blocos: [bloco1, bloco2] }, TipoB1: { ... } }
    estoque_por_tipo = {}

    for tipo in tipos_receituario:
        # Busca o registro de estoque geral para este tipo (se existir)
        estoque_geral_do_tipo = EstoqueReceituario.query.filter_by(tipo_id=tipo.id).first()
        
        # Busca todos os blocos individuais para este tipo, ordenados por número inicial ou número do bloco
        blocos_individuais_do_tipo = BlocoReceituario.query.filter_by(tipo_id=tipo.id)\
                                                          .order_by(BlocoReceituario.numero_inicial, BlocoReceituario.numero_bloco)\
                                                          .all()
        
        estoque_por_tipo[tipo.sigla] = {
            'tipo_obj': tipo, # Passa o objeto do tipo completo
            'estoque_geral': estoque_geral_do_tipo,
            'blocos_individuais': blocos_individuais_do_tipo
        }

    return render_template('admin_estoque_receituario.html', estoque_por_tipo=estoque_por_tipo)





@app.route('/admin/estoque/cadastrar-lote', methods=['GET', 'POST'])
# @login_required # Se você usa Flask-Login para proteger rotas de admin
def admin_cadastrar_lote_receituario():
    tipos_receituario = TipoReceituario.query.all() # Busca todos os tipos de receituário para preencher o select

    if request.method == 'POST':
        tipo_receituario_id = request.form.get('tipo_receituario')
        data_entrada_estoque_str = request.form.get('data_entrada_estoque')

        # --- Validações iniciais (tipo e data) ---
        if not all([tipo_receituario_id, data_entrada_estoque_str]):
            flash('O tipo de receituário e a data de entrada são obrigatórios.', 'danger')
            return redirect(url_for('admin_cadastrar_lote_receituario'))

        try: # <--- INÍCIO DO TRY PRINCIPAL
            # Converte a data de entrada para objeto date/datetime
            data_entrada_estoque = datetime.strptime(data_entrada_estoque_str, '%Y-%m-%d').date()

            # Busque o objeto TipoReceituario completo para acessar a sigla e folhas_por_bloco
            tipo_selecionado = TipoReceituario.query.get(tipo_receituario_id)
            if not tipo_selecionado:
                flash('Tipo de receituário inválido.', 'danger')
                return redirect(url_for('admin_cadastrar_lote_receituario'))

            blocos_cadastrados_count = 0
            total_folhas_adicionadas = 0
            
            # --- LÓGICA CONDICIONAL: SEPARANDO TIPOS COM NUMERAÇÃO DE PÁGINAS E SEM ---
            if tipo_selecionado.sigla == 'C': # Receituário de Controle Especial (Branco)
                quantidade_blocos_chegou_str = request.form.get('quantidade_blocos_chegou')
                folhas_por_bloco_c_str = request.form.get('folhas_por_bloco_c_hidden') # Pega o valor do campo oculto do HTML
                
                # --- NOVOS PRINTS PARA DEBUG (ADICIONE AQUI) ---
                print(f"DEBUG (TIPO C): quantidade_blocos_chegou_str = '{quantidade_blocos_chegou_str}' (Tipo: {type(quantidade_blocos_chegou_str)})")
                print(f"DEBUG (TIPO C): folhas_por_bloco_c_str = '{folhas_por_bloco_c_str}' (Tipo: {type(folhas_por_bloco_c_str)})")
                # --- FIM DOS PRINTS ---

                if not quantidade_blocos_chegou_str or not folhas_por_bloco_c_str:
                    flash('Para Receituário de Controle Especial, a quantidade de blocos e folhas por bloco são obrigatórias.', 'danger')
                    return redirect(url_for('admin_cadastrar_lote_receituario'))
                
                try:
                    quantidade_blocos_chegou = int(quantidade_blocos_chegou_str)
                    folhas_por_bloco_c = int(folhas_por_bloco_c_str)
                except ValueError:
                    flash('A quantidade de blocos e folhas por bloco devem ser números válidos.', 'danger')
                    db.session.rollback()
                    return redirect(url_for('admin_cadastrar_lote_receituario'))
                
                if quantidade_blocos_chegou <= 0 or folhas_por_bloco_c <= 0:
                    flash('A quantidade de blocos e folhas por bloco devem ser maiores que zero.', 'danger')
                    return redirect(url_for('admin_cadastrar_lote_receituario'))

                
                if quantidade_blocos_chegou <= 0 or folhas_por_bloco_c <= 0:
                    flash('A quantidade de blocos e folhas por bloco devem ser maiores que zero.', 'danger')
                    return redirect(url_for('admin_cadastrar_lote_receituario'))

                # Loop para gerar e salvar cada bloco "não numerado"
                for i in range(quantidade_blocos_chegou):
                    # O sistema gera o número do bloco sequencialmente
                    numero_bloco_gerado = f"{tipo_selecionado.sigla}-BLOCO-{i+1:04d}" 
                    
                    novo_bloco = BlocoReceituario(
                        tipo_id=tipo_selecionado.id,
                        numero_bloco=numero_bloco_gerado,
                        numero_inicial=1,
                        numero_final=folhas_por_bloco_c,
                        data_entrada_estoque=data_entrada_estoque
                    )
                    db.session.add(novo_bloco)
                    blocos_cadastrados_count += 1
                    total_folhas_adicionadas += folhas_por_bloco_c

            else: # Lógica para outros tipos de receituário (A, B1, B2) - COM numeração de páginas
                numeros_bloco = request.form.getlist('numero_bloco[]')
                numeros_inicial = request.form.getlist('numero_inicial[]')
                numeros_final = request.form.getlist('numero_final[]')

                if not numeros_bloco or len(numeros_bloco) == 0:
                    flash('Nenhum bloco de receituário informado para cadastro (use o botão "Adicionar Novo Bloco").', 'danger')
                    return redirect(url_for('admin_cadastrar_lote_receituario'))
                
                if len(numeros_bloco) != len(numeros_inicial) or len(numeros_bloco) != len(numeros_final):
                    flash('Dados de bloco incompletos: certifique-se de preencher Número do Bloco, Inicial e Final para cada entrada.', 'danger')
                    return redirect(url_for('admin_cadastrar_lote_receituario'))

                for i in range(len(numeros_bloco)):
                    bloco_num = numeros_bloco[i].strip()
                    ini_num_str = numeros_inicial[i].strip()
                    fim_num_str = numeros_final[i].strip()

                    if not bloco_num or not ini_num_str or not fim_num_str:
                        flash(f'Erro: Todos os campos do Bloco {i+1} (Número do Bloco, Inicial e Final) devem ser preenchidos.', 'danger')
                        db.session.rollback()
                        return redirect(url_for('admin_cadastrar_lote_receituario'))

                    try: # <--- TRY INTERNO para conversão de valores dos outros tipos
                        ini_num = int(ini_num_str)
                        fim_num = int(fim_num_str)
                    except ValueError: # <--- EXCEPT INTERNO para ValueError dos outros tipos
                        flash(f'Erro no Bloco {i+1}: Os números inicial e final devem ser números válidos.', 'danger')
                        db.session.rollback()
                        return redirect(url_for('admin_cadastrar_lote_receituario'))
                    
                    if fim_num <= ini_num:
                        flash(f'Erro no Bloco {bloco_num} (Bloco {i+1}): O número final ({fim_num}) deve ser maior que o número inicial ({ini_num}).', 'danger')
                        db.session.rollback()
                        return redirect(url_for('admin_cadastrar_lote_receituario'))

                    novo_bloco = BlocoReceituario(
                        tipo_id=tipo_selecionado.id,
                        numero_bloco=bloco_num,
                        numero_inicial=ini_num,
                        numero_final=fim_num,
                        data_entrada_estoque=data_entrada_estoque
                    )
                    db.session.add(novo_bloco)
                    blocos_cadastrados_count += 1
                    total_folhas_adicionadas += (fim_num - ini_num + 1)
            # --- FIM DA LÓGICA CONDICIONAL ---
            
            # --- Atualização do EstoqueReceituario geral (comum a ambos os tipos) ---
            estoque_geral = EstoqueReceituario.query.filter_by(tipo_id=tipo_selecionado.id).first()
            if not estoque_geral:
                estoque_geral = EstoqueReceituario(
                    tipo_id=tipo_selecionado.id,
                    quantidade_blocos_disponivel=0,
                    quantidade_folhas_disponivel=0
                )
                db.session.add(estoque_geral)
                db.session.flush() # CRÍTICO: Garante que o objeto existe na sessão antes da soma
                
            estoque_geral.quantidade_blocos_disponivel += blocos_cadastrados_count
            estoque_geral.quantidade_folhas_disponivel += total_folhas_adicionadas
            
            db.session.commit() # Comita todas as mudanças
            
            flash(f'{blocos_cadastrados_count} bloco(s) de receituário cadastrado(s) com sucesso! Total de folhas adicionadas: {total_folhas_adicionadas}.', 'success')
            return redirect(url_for('admin_estoque_receituario'))

        except ValueError: # <--- ESTE EXCEPT TRATA APENAS ERROS DE CONVERSÃO DE DATA INICIAL
            flash('Formato de data de entrada inválido. Verifique o campo Data de Entrada no Estoque.', 'danger')
            db.session.rollback()
            return redirect(url_for('admin_cadastrar_lote_receituario'))
        except Exception as e: # <--- ESTE EXCEPT GERAL PEGA QUALQUER OUTRO ERRO
            db.session.rollback()
            print(f"ERRO AO CADASTRAR LOTE DE RECEITUÁRIO: {e}")
            import traceback
            traceback.print_exc()
            flash('Ocorreu um erro inesperado ao cadastrar o lote. Detalhes no console do servidor.', 'danger')
            return redirect(url_for('admin_cadastrar_lote_receituario'))

    # Método GET: Renderiza o formulário
    return render_template('admin_cadastrar_lote_receituario.html', 
                           tipos_receituario=tipos_receituario, 
                           today_date=date.today().isoformat())


@app.route('/admin/analisar-testes-calazar')
# @login_required
def admin_analisar_testes_calazar():
    solicitacoes_calazar = SolicitacaoCalazar.query.order_by(SolicitacaoCalazar.data_solicitacao.desc()).all()
    return render_template('admin_analisar_testes_calazar.html', solicitacoes_calazar=solicitacoes_calazar)


@app.route('/admin/testes-calazar/listar')
def admin_listar_solicitacao_calazar():
    """Lista todas as solicitações de teste de calazar para análise."""
    solicitacoes = SolicitacaoCalazar.query.order_by(SolicitacaoCalazar.data_solicitacao.desc()).all()
    return render_template('admin_listar_solicitacao_calazar.html', solicitacoes_calazar=solicitacoes)



@app.route('/admin/testes-calazar/atualizar-status/<int:solicitacao_id>', methods=['POST'])
def admin_atualizar_status_calazar(solicitacao_id):
    """Atualiza o status e os dados de uma solicitação de teste de calazar."""
    solicitacao = SolicitacaoCalazar.query.get_or_404(solicitacao_id)
    
    # Atualiza o status
    solicitacao.status = request.form.get('status')
    
    # Pega e formata as datas e outros campos do formulário
    data_atendimento_str = request.form.get('data_atendimento')
    if data_atendimento_str:
        solicitacao.data_atendimento = datetime.strptime(data_atendimento_str, '%Y-%m-%d').date()

    data_realizacao_teste_str = request.form.get('data_realizacao_teste')
    if data_realizacao_teste_str:
        solicitacao.data_realizacao_teste = datetime.strptime(data_realizacao_teste_str, '%Y-%m-%d').date()

    solicitacao.kit_utilizado = request.form.get('kit_utilizado')
    solicitacao.lote_kit = request.form.get('lote_kit')
    
    # --- INÍCIO DA CORREÇÃO ---
    # Converte a string da validade do kit para um objeto de data, tentando múltiplos formatos
    validade_kit_str = request.form.get('validade_kit')
    if validade_kit_str:
        try:
            # Tenta primeiro o formato DD/MM/YYYY (comum em inputs de texto)
            solicitacao.validade_kit = datetime.strptime(validade_kit_str, '%d/%m/%Y').date()
        except ValueError:
            try:
                # Se falhar, tenta o formato YYYY-MM-DD (padrão de input date)
                solicitacao.validade_kit = datetime.strptime(validade_kit_str, '%Y-%m-%d').date()
            except ValueError:
                # Se ambos os formatos falharem, exibe um erro
                flash('Formato de data inválido para a validade do kit. Por favor, use o formato DD/MM/YYYY.', 'danger')
                return redirect(url_for('admin_detalhe_teste_calazar', solicitacao_id=solicitacao_id))
    else:
        solicitacao.validade_kit = None # Garante que o campo fique nulo se estiver vazio
    # --- FIM DA CORREÇÃO ---

    solicitacao.resultado_teste_rapido = request.form.get('resultado_teste_rapido')
    solicitacao.observacoes_resultado = request.form.get('observacoes_resultado')
    solicitacao.veterinario_responsavel_nome = request.form.get('veterinario_responsavel_nome')
    solicitacao.veterinario_crmv = request.form.get('veterinario_crmv')

    resultado_liberado_val = request.form.get('resultado_liberado')
    solicitacao.resultado_liberado = True if resultado_liberado_val == 'true' else False

    db.session.commit()
    
    flash('Status e informações da solicitação atualizados com sucesso!', 'success')
    return redirect(url_for('admin_detalhe_teste_calazar', solicitacao_id=solicitacao_id))





@app.route('/admin/testes-calazar/detalhe/<int:solicitacao_id>')
def admin_detalhe_teste_calazar(solicitacao_id):
    """Exibe os detalhes de uma solicitação de teste de calazar para análise."""
    solicitacao = SolicitacaoCalazar.query.get_or_404(solicitacao_id)
    return render_template('admin_detalhe_teste_calazar.html', solicitacao=solicitacao)


@app.route('/admin/imprimir-solicitacao-calazar/<int:solicitacao_id>')
def admin_imprimir_solicitacao_calazar(solicitacao_id):
    solicitacao = SolicitacaoCalazar.query.get_or_404(solicitacao_id)
    
    # Renderiza o template de impressão da solicitação
    return render_template('admin_imprimir_solicitacao_calazar.html', solicitacao=solicitacao)



#----------------------------------ROTAS DE IRREGURALIDADES ---------------------------------------------------------------------------------------------

@app.route('/admin/irregularidades')
def admin_listar_irregularidades():
    """Exibe a lista de todas as irregularidades cadastradas."""
    irregularidades = Irregularidade.query.order_by(Irregularidade.nome).all()
    return render_template('admin_listar_irregularidades.html', irregularidades=irregularidades)

@app.route('/admin/irregularidades/nova', methods=['GET', 'POST'])
def admin_nova_irregularidade():
    """Exibe o formulário para criar uma nova irregularidade e salva os dados."""
    if request.method == 'POST':
        try:
            nova_irregularidade = Irregularidade(
                nome=request.form.get('nome'),
                infracao=request.form.get('infracao'),
                inciso=request.form.get('inciso'),
                explicacao=request.form.get('explicacao')
            )
            db.session.add(nova_irregularidade)
            db.session.commit()
            flash('Irregularidade cadastrada com sucesso!', 'success')
            return redirect(url_for('admin_listar_irregularidades'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar irregularidade: {e}', 'danger')
    
    return render_template('admin_nova_irregularidade.html', irregularidade=None)

@app.route('/admin/irregularidades/editar/<int:irregularidade_id>', methods=['GET', 'POST'])
def admin_editar_irregularidade(irregularidade_id):
    """Exibe o formulário para editar uma irregularidade existente e salva as alterações."""
    irregularidade = Irregularidade.query.get_or_404(irregularidade_id)
    if request.method == 'POST':
        try:
            irregularidade.nome = request.form.get('nome')
            irregularidade.infracao = request.form.get('infracao')
            irregularidade.inciso = request.form.get('inciso')
            irregularidade.explicacao = request.form.get('explicacao')
            db.session.commit()
            flash('Irregularidade atualizada com sucesso!', 'success')
            return redirect(url_for('admin_listar_irregularidades'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar irregularidade: {e}', 'danger')

    return render_template('admin_nova_irregularidade.html', irregularidade=irregularidade)

@app.route('/admin/irregularidades/deletar/<int:irregularidade_id>', methods=['POST'])
def admin_deletar_irregularidade(irregularidade_id):
    """Deleta uma irregularidade do banco de dados."""
    irregularidade = Irregularidade.query.get_or_404(irregularidade_id)
    try:
        db.session.delete(irregularidade)
        db.session.commit()
        flash('Irregularidade deletada com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar irregularidade: {e}', 'danger')
    
    return redirect(url_for('admin_listar_irregularidades'))

#-------------------------------------CADASTRO DE FISCAIS SANITÁRIOS----------------------------------------------------------------------------------------------
# Em app.py
# Substitua as rotas antigas de 'fiscais' por estas:

@app.route('/admin/funcionarios')
def admin_gerenciar_funcionarios():
    funcionarios = Funcionario.query.order_by(Funcionario.nome).all()
    return render_template('admin_gerenciar_funcionarios.html', funcionarios=funcionarios)

@app.route('/admin/funcionarios/novo', methods=['GET', 'POST'])
def admin_adicionar_funcionario():
    if request.method == 'POST':
        nome = request.form.get('nome')
        matricula = request.form.get('matricula')
        cargo = request.form.get('cargo') # Campo novo
        assinatura_file = request.files.get('assinatura_imagem')

        if not nome or not matricula or not cargo:
            flash('Nome, matrícula e cargo são obrigatórios.', 'danger')
            return redirect(url_for('admin_adicionar_funcionario'))

        novo_funcionario = Funcionario(nome=nome, matricula=matricula, cargo=cargo)

        if assinatura_file and assinatura_file.filename:
            filename = secure_filename(f"func_{matricula}_{assinatura_file.filename}")
            assinaturas_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'assinaturas')
            os.makedirs(assinaturas_folder, exist_ok=True)
            caminho_arquivo = os.path.join(assinaturas_folder, filename)
            assinatura_file.save(caminho_arquivo)
            novo_funcionario.caminho_assinatura = os.path.join('assinaturas', filename)

        db.session.add(novo_funcionario)
        db.session.commit()
        flash('Funcionário adicionado com sucesso!', 'success')
        return redirect(url_for('admin_gerenciar_funcionarios'))

    return render_template('admin_form_funcionario.html', title="Adicionar Novo Funcionário")

@app.route('/admin/funcionarios/editar/<int:funcionario_id>', methods=['GET', 'POST'])
def admin_editar_funcionario(funcionario_id):
    funcionario = db.get_or_404(Funcionario, funcionario_id)
    if request.method == 'POST':
        funcionario.nome = request.form.get('nome')
        funcionario.matricula = request.form.get('matricula')
        funcionario.cargo = request.form.get('cargo') # Campo novo

        assinatura_file = request.files.get('assinatura_imagem')
        if assinatura_file and assinatura_file.filename:
            filename = secure_filename(f"func_{funcionario.matricula}_{assinatura_file.filename}")
            assinaturas_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'assinaturas')
            os.makedirs(assinaturas_folder, exist_ok=True)
            caminho_arquivo = os.path.join(assinaturas_folder, filename)
            assinatura_file.save(caminho_arquivo)
            funcionario.caminho_assinatura = os.path.join('assinaturas', filename)

        db.session.commit()
        flash('Funcionário atualizado com sucesso!', 'success')
        return redirect(url_for('admin_gerenciar_funcionarios'))

    return render_template('admin_form_funcionario.html', title="Editar Funcionário", funcionario=funcionario)

# ------------------------------------------------------------------------------- ROTAS CADASTRO DE  AUTÔNOMOS -------------------------------------------------------------------------------------------------------
# --- ROTA NOVA: Cadastra um novo autônomo no sistema ---
@app.route('/admin/autonomo/novo', methods=['GET', 'POST'])
def admin_novo_autonomo():
    if request.method == 'POST':
        try:
            # Lógica para gerar protocolo (adapte se necessário)
            protocolo = gerar_protocolo('AUTONOMO', 'LSAA')

            novo_autonomo = Autonomo(
                protocolo=protocolo,
                nome_completo=request.form.get('nome_completo'),
                cpf=request.form.get('cpf'),
                rg=request.form.get('rg'),
                orgao_expedidor=request.form.get('orgao_expedidor'),
                uf_rg=request.form.get('uf_rg'),
                data_nascimento=datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date() if request.form.get('data_nascimento') else None,
                sexo=request.form.get('sexo'),
                telefone_celular=request.form.get('telefone_celular'),
                email=request.form.get('email'),
                endereco_atendimento=request.form.get('endereco_atendimento'),
                tipo_local=request.form.get('tipo_local'),
                profissao=request.form.get('profissao'),
                conselho_classe=request.form.get('conselho_classe'),
                numero_registro_profissional=request.form.get('numero_registro_profissional'),
                inscricao_municipal=request.form.get('inscricao_municipal'),
                atividades_exercidas=request.form.get('atividades_exercidas'),
                modalidade_atendimento=request.form.get('modalidade_atendimento'),
                horario_funcionamento=request.form.get('horario_funcionamento')
            )

            # Salva cada um dos documentos
            # Garante que todos os ficheiros são lidos e os seus caminhos guardados
            subpasta_docs = f"autonomo_{novo_autonomo.cpf.replace('.', '').replace('-', '')}"
            novo_autonomo.doc_alvara_funcionamento_path = salvar_arquivo_upload(request.files.get('doc_alvara_funcionamento'), subpasta_docs)
            novo_autonomo.doc_cpf_rg_path = salvar_arquivo_upload(request.files.get('doc_cpf_rg'), subpasta_docs)
            novo_autonomo.doc_comprovante_endereco_path = salvar_arquivo_upload(request.files.get('doc_comprovante_endereco'), subpasta_docs)
            novo_autonomo.doc_registro_conselho_path = salvar_arquivo_upload(request.files.get('doc_registro_conselho'), subpasta_docs)
            novo_autonomo.doc_declaracao_rt_path = salvar_arquivo_upload(request.files.get('doc_declaracao_rt'), subpasta_docs)
            novo_autonomo.doc_declaracao_atividades_path = salvar_arquivo_upload(request.files.get('doc_declaracao_atividades'), subpasta_docs)
            novo_autonomo.doc_termo_compromisso_path = salvar_arquivo_upload(request.files.get('doc_termo_compromisso'), subpasta_docs)

            db.session.add(novo_autonomo)
            db.session.commit()
            flash(f'Cadastro de autônomo enviado com sucesso! Protocolo: {protocolo}', 'success')
            return redirect(url_for('admin_listar_autonomos'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao processar o cadastro: {e}', 'danger')
            return redirect(url_for('admin_novo_autonomo'))
            
    return render_template('admin_novo_autonomo.html')

@app.route('/admin/autonomos_aprovados')
def admin_autonomos_cadastrados():
    """Exibe a lista de todos os profissionais autônomos com cadastro aprovado."""
    query = request.args.get('q', '')
    
    # CORREÇÃO: Removido o prefixo 'models.'
    base_query = Autonomo.query.filter_by(status='Aprovado')

    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Autonomo.nome_completo.ilike(search_term),
                Autonomo.cpf.ilike(search_term)
            )
        )
    
    autonomos_aprovados = base_query.order_by(Autonomo.nome_completo).all()
    
    return render_template('admin_autonomos_cadastrados.html', 
                           autonomos=autonomos_aprovados, 
                           query_q=query)

@app.route('/admin/autonomo/imprimir_ficha/<int:autonomo_id>')
def admin_imprimir_ficha_autonomo(autonomo_id):
    """Gera uma página de impressão para a ficha cadastral de um autônomo."""
    autonomo = Autonomo.query.get_or_404(autonomo_id)
    
    # Gera a data e hora atuais para serem usadas no template
    data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    return render_template('admin_imprimir_ficha_autonomo.html', 
                           autonomo=autonomo, 
                           data_geracao=data_geracao)







# ----------------------------------- ROTAS CADASTRAR  PESSOA FÍSICA ---------------------------------------------------------------------------------------------------------------------

@app.route('/admin/pessoas_fisicas')
def admin_listar_pessoas_fisicas():
    """Exibe a lista de Pessoas Físicas com filtro de busca."""
    query_search = request.args.get('q', '')
    # CORREÇÃO: A consulta agora filtra para mostrar apenas os cadastros que NÃO estão 'Aprovado'.
    base_query = PessoaFisica.query.filter(PessoaFisica.status != 'Aprovado')

    if query_search:
        search_term = f"%{query_search}%"
        base_query = base_query.filter(
            or_(
                PessoaFisica.nome_completo.ilike(search_term),
                PessoaFisica.cpf.ilike(search_term)
            )
        )
    
    pessoas = base_query.order_by(PessoaFisica.data_criacao.desc()).all()
    return render_template('admin_listar_pessoas_fisicas.html', 
                           pessoas=pessoas,
                           query_q=query_search)


@app.route('/admin/pessoas_fisicas_aprovadas')
def admin_pessoas_fisicas_aprovadas():
    """Exibe a lista de Pessoas Físicas com cadastro aprovado."""
    query = request.args.get('q', '')
    base_query = PessoaFisica.query.filter_by(status='Aprovado')
    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(or_(PessoaFisica.nome_completo.ilike(search_term), PessoaFisica.cpf.ilike(search_term)))
    pessoas_aprovadas = base_query.order_by(PessoaFisica.nome_completo).all()
    return render_template('admin_pessoas_fisicas_aprovadas.html', pessoas=pessoas_aprovadas, query_q=query)

@app.route('/admin/pessoa_fisica/ficha/<int:pessoa_id>')
def admin_ficha_pessoa_fisica(pessoa_id):
    """Exibe a ficha completa de uma Pessoa Física, incluindo seu histórico de processos."""
    pessoa = PessoaFisica.query.get_or_404(pessoa_id)
    
    # Busca por processos vinculados ao CPF da pessoa física
    # Adapte os nomes das colunas se forem diferentes nos seus modelos
    denuncias = Denuncias.query.filter_by(denunciado_cpf_cnpj=pessoa.cpf).all()
    vistorias = Vistoria.query.filter_by(cpf_cnpj_vinculado=pessoa.cpf).all()
    notificacoes = Notificacoes.query.filter_by(notificado_cpf_cnpj=pessoa.cpf).all()

    return render_template('admin_ficha_pessoa_fisica.html', 
                           pessoa=pessoa,
                           denuncias=denuncias,
                           vistorias=vistorias,
                           notificacoes=notificacoes)


@app.route('/cadastro_pessoa_fisica', methods=['GET', 'POST'])
def cadastro_pessoa_fisica():
    if request.method == 'POST':
        try:
            protocolo_novo = gerar_protocolo('PESSOA_FISICA', 'PF')

            data_nasc_str = request.form.get('data_nascimento')
            data_nascimento = datetime.strptime(data_nasc_str, '%Y-%m-%d').date() if data_nasc_str else None
            situacao = request.form.getlist('situacao_local')
            finalidade = request.form.getlist('finalidade_cadastro')
            if 'Outro_finalidade' in finalidade:
                finalidade.remove('Outro_finalidade')
                outro_texto = request.form.get('finalidade_outro_texto')
                if outro_texto:
                    finalidade.append(f"Outro: {outro_texto}")

            nova_pessoa = PessoaFisica(
                protocolo=protocolo_novo,
                nome_completo=request.form.get('nome_completo'),
                cpf=request.form.get('cpf'),
                rg=request.form.get('rg'),
                orgao_expedidor=request.form.get('orgao_expedidor'),
                uf_rg=request.form.get('uf_rg'),
                data_nascimento=data_nascimento,
                telefone_contato=request.form.get('telefone_contato'),
                email=request.form.get('email'),
                endereco_local=request.form.get('endereco_local'),
                tipo_local=request.form.get('tipo_local'),
                situacao_local=json.dumps(situacao),
                finalidade_cadastro=json.dumps(finalidade),
                observacoes=request.form.get('observacoes')
            )
            db.session.add(nova_pessoa)
            db.session.commit()
            flash(f'Cadastro de Pessoa Física enviado com sucesso! Protocolo: {protocolo_novo}', 'success')
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro: CPF já cadastrado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao enviar o cadastro: {e}', 'danger')

    return render_template('cadastro_pessoa_fisica.html')

@app.route('/admin/pessoa_fisica/<int:pessoa_id>')
def admin_detalhe_pessoa_fisica(pessoa_id):
    """Exibe os detalhes de um cadastro de pessoa física para análise."""
    pessoa = PessoaFisica.query.get_or_404(pessoa_id)
    
    # Processa os campos JSON para facilitar a exibição no template
    situacao_local = json.loads(pessoa.situacao_local) if pessoa.situacao_local else []
    finalidade_cadastro = json.loads(pessoa.finalidade_cadastro) if pessoa.finalidade_cadastro else []
    
    return render_template('admin_detalhe_pessoa_fisica.html', 
                           pessoa=pessoa,
                           situacao_local=situacao_local,
                           finalidade_cadastro=finalidade_cadastro)

@app.route('/admin/pessoa_fisica/<int:pessoa_id>/atualizar_status', methods=['POST'])
def admin_atualizar_status_pessoa_fisica(pessoa_id):
    """Atualiza o status de um cadastro de pessoa física."""
    pessoa = PessoaFisica.query.get_or_404(pessoa_id)
    novo_status = request.form.get('novo_status')

    if novo_status:
        pessoa.status = novo_status
        db.session.commit()
        flash(f'Status do cadastro de {pessoa.nome_completo} foi atualizado para {novo_status}.', 'success')
    else:
        flash('Nenhum novo status foi selecionado.', 'warning')
        
    return redirect(url_for('admin_detalhe_pessoa_fisica', pessoa_id=pessoa.id))

@app.route('/admin/pessoa_fisica/imprimir_ficha/<int:pessoa_id>')
def admin_imprimir_ficha_pessoa_fisica(pessoa_id):
    """Gera uma página de impressão para a ficha cadastral de uma pessoa física."""
    pessoa = PessoaFisica.query.get_or_404(pessoa_id)
    data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template('admin_imprimir_ficha_pessoa_fisica.html', 
                           pessoa=pessoa, 
                           data_geracao=data_geracao)






#-----------------------------------------------------------------------------ROTA PARA SOLICITAR LICENÇA PARA EVENTOS ----------------------------------------------------------------------------------------------------------------------------

@app.route('/admin/licencas/empresas')
def admin_analisar_licencas():
    """Exibe a lista de solicitações de licença de empresas, com filtro de busca."""
    query_search = request.args.get('q', '') # Pega o termo de busca da URL

    # Inicia a consulta base
    base_query = db.session.query(LicencaEmpresa).join(Empresas)

    # Se houver um termo de busca, filtra por protocolo, razão social ou CNPJ
    if query_search:
        search_term = f"%{query_search}%"
        base_query = base_query.filter(
            or_(
                LicencaEmpresa.protocolo.ilike(search_term),
                Empresas.razao_social.ilike(search_term),
                Empresas.cnpj.ilike(search_term)
            )
        )
    
    licencas_empresas = base_query.order_by(LicencaEmpresa.data_solicitacao.desc()).all()
    
    return render_template('admin_listar_licencas.html', 
                           licencas=licencas_empresas,
                           query_q=query_search)

@app.route('/admin/licencas/autonomos')
def admin_analisar_licencas_autonomos():
    """Exibe a lista de solicitações de licença APENAS de autônomos."""
    # A consulta busca todas as licenças que estão associadas a um autônomo.
    licencas_autonomos = db.session.query(LicencaAutonomo).join(Autonomo).order_by(LicencaAutonomo.data_solicitacao.desc()).all()
    
    # Esta linha está correta e aponta para o ficheiro 'admin_listar_licencas_autonomos.html'
    return render_template('admin_listar_licencas_autonomos.html', licencas=licencas_autonomos)



@app.route('/admin/solicitacao/<int:solicitacao_id>')
def admin_detalhe_solicitacao(solicitacao_id):
    """Exibe os detalhes de uma solicitação de cadastro de empresa para análise."""
    # O nome do modelo aqui é 'Empresas', com 's' no final, como nos seus outros códigos.
    empresa = models.Empresas.query.get_or_404(solicitacao_id)
    return render_template('admin_detalhe_solicitacao.html', empresa=empresa)

# Você também precisará de uma rota para receber o POST do formulário de aprovação.
# Este é um exemplo de como ela poderia ser:
@app.route('/admin/solicitacao/<int:solicitacao_id>/atualizar', methods=['POST'])
def admin_aprovar_reprovar_solicitacao(solicitacao_id):
    empresa = models.Empresas.query.get_or_404(solicitacao_id)
    novo_status = request.form.get('novo_status')
    observacao = request.form.get('observacao')

    if novo_status:
        empresa.status = novo_status
        # Você pode querer salvar a observação em um campo específico, se ele existir
        # empresa.observacao = observacao
        db.session.commit()
        flash(f'O status da empresa {empresa.razao_social} foi atualizado para {novo_status}.', 'success')
    else:
        flash('Nenhum novo status foi selecionado.', 'warning')
        
    return redirect(url_for('admin_detalhe_solicitacao', solicitacao_id=solicitacao_id))

# ------------------------- ROTAS REESTRUTURADAS PARA SOLICITAÇÃO DE LICENÇA -------------------------------------------------------------------------------------

# --- ROTAS REESTRUTURADAS PARA SOLICITAÇÃO DE LICENÇA ---






# --- ROTA PARA ANÁLISE DE LICENÇA DE EMPRESA ---

@app.route('/admin/licenca/empresa/<int:licenca_id>')
def admin_detalhe_licenca_empresa(licenca_id):
    """
    Exibe os detalhes de uma licença de empresa para análise.
    """
    licenca = db.get_or_404(LicencaEmpresa, licenca_id)

    # A linha que causava o erro foi removida.
    # Não precisamos mais de 'rt_info' ou 'afe_info', pois o template
    # acede aos dados diretamente do objeto 'licenca'.
    
    return render_template('admin_detalhe_licenca_empresa.html', licenca=licenca)


@app.route('/admin/licenca/empresa/atualizar_status/<int:licenca_id>', methods=['POST'])
def admin_atualizar_status_licenca_empresa(licenca_id):
    licenca = LicencaEmpresa.query.get_or_404(licenca_id)
    novo_status = request.form.get('novo_status')
    data_validade_str = request.form.get('data_validade')
    observacoes = request.form.get('observacoes')

    if novo_status:
        licenca.status = novo_status
        licenca.observacoes = observacoes
        
        if data_validade_str:
            try:
                licenca.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de data inválido.', 'danger')
                return redirect(url_for('admin_detalhe_licenca_empresa', licenca_id=licenca.id))
        
        if novo_status == 'Aprovado':
            coordenador = Funcionario.query.filter_by(cargo='Coordenador').first()
            if not coordenador or not coordenador.caminho_assinatura:
                flash('Coordenador com assinatura não encontrado. Não foi possível gerar o alvará.', 'danger')
                db.session.commit()
                return redirect(url_for('admin_detalhe_licenca_empresa', licenca_id=licenca.id))

            caminho_completo_assinatura = os.path.join(current_app.root_path, 'static', coordenador.caminho_assinatura)
            responsavel_assinatura = {
                'nome': coordenador.nome,
                'cargo': coordenador.cargo,
                'caminho_imagem': caminho_completo_assinatura
            }

            # Gera o PDF e, crucialmente, guarda o nome do ficheiro na licença
            nome_alvara = gerar_alvara_pdf(licenca, {}, responsavel_assinatura)
            licenca.alvara_pdf_path = nome_alvara
            
            flash('Status atualizado e alvará gerado com sucesso!', 'success')
        else:
            licenca.alvara_pdf_path = None
            flash('Status da licença atualizado com sucesso!', 'success')
            
        db.session.add(licenca)
        db.session.commit()
    else:
        flash('Nenhum novo status foi selecionado.', 'warning')

    return redirect(url_for('admin_detalhe_licenca_empresa', licenca_id=licenca.id))


@app.route('/alvara/download/<path:protocolo_str>')
def download_alvara_publico(protocolo_str):
    """
    Rota pública e segura para download de alvarás aprovados.
    Usa o número de protocolo para buscar.
    """
    licenca = LicencaEmpresa.query.filter_by(protocolo=protocolo_str).first()
    if not licenca:
        licenca = LicencaAutonomo.query.filter_by(protocolo=protocolo_str).first()
    if not licenca:
        licenca = LicencaEvento.query.filter_by(protocolo=protocolo_str).first()

    if not licenca:
        abort(404)

    status_normalizado = licenca.status.lower().strip()
    if (status_normalizado != 'aprovado' and status_normalizado != 'aprovada') or not licenca.alvara_pdf_path:
        abort(403, description="Alvará não disponível para este protocolo.")

    try:
        # CORREÇÃO: Usando a chave 'ALVARAS_FOLDER' que você definiu
        return send_from_directory(
            app.config['ALVARAS_FOLDER'], 
            licenca.alvara_pdf_path, 
            as_attachment=False # 'False' para abrir no navegador, 'True' para forçar download
        )
    except FileNotFoundError:
        abort(404, description="Arquivo do alvará não encontrado no servidor.")

# Em app.py

@app.route('/admin/licenca/empresa/<int:licenca_id>/gerar_alvara_final')
def admin_gerar_alvara_final(licenca_id):
    licenca = db.get_or_404(LicencaEmpresa, licenca_id)

    if licenca.status != 'Aprovada':
        flash('Só é possível gerar alvará para licenças com status "Aprovada".', 'warning')
        return redirect(url_for('admin_detalhe_licenca_empresa', licenca_id=licenca.id))

    # Busca pelo funcionário com o cargo 'Coordenador' que tenha assinatura.
    coordenador = Funcionario.query.filter_by(cargo='Coordenador').filter(Funcionario.caminho_assinatura != None).first()

    if not coordenador:
        flash('Nenhum Coordenador com assinatura cadastrada foi encontrado para gerar o alvará.', 'danger')
        return redirect(url_for('admin_detalhe_licenca_empresa', licenca_id=licenca.id))
        
    caminho_completo_assinatura = os.path.join(app.root_path, 'static', coordenador.caminho_assinatura)
    
    responsavel_assinatura = {
        'nome': coordenador.nome,
        'cargo': coordenador.cargo,
        'matricula': coordenador.matricula,
        'caminho_imagem': caminho_completo_assinatura
    }
    
    # Esta chamada agora corresponde à função no Canvas
    nome_alvara = gerar_alvara_pdf(licenca, {}, responsavel_assinatura)

    if nome_alvara:
        licenca.alvara_pdf_path = nome_alvara
        db.session.commit()
        flash('Alvará definitivo gerado com sucesso!', 'success')
        # Retorna o PDF diretamente para o usuário
        return send_from_directory(os.path.join(current_app.config['ALVARAS_FOLDER']), nome_alvara, as_attachment=False)
    else:
        flash('Ocorreu um erro ao gerar o PDF do alvará.', 'danger')
        return redirect(url_for('admin_detalhe_licenca_empresa', licenca_id=licenca.id))

def salvar_arquivo_upload(arquivo, subpasta):
    if not arquivo or not arquivo.filename:
        return None
    
    filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{arquivo.filename}")
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'licencas_docs', subpasta)
    os.makedirs(upload_folder, exist_ok=True)
    caminho_completo = os.path.join(upload_folder, filename)
    arquivo.save(caminho_completo)
    return os.path.join('licencas_docs', subpasta, filename)




@app.route('/imprimir_ficha/licenca_empresa/<int:licenca_id>')
def imprimir_ficha_licenca_empresa(licenca_id):
    """Gera uma página de impressão dedicada para uma Licença de Empresa."""
    
    # Busca o processo de licença pelo ID fornecido.
    processo = LicencaEmpresa.query.get_or_404(licenca_id)
    
    # Pega a data e hora atuais para exibir no rodapé da ficha.
    agora = datetime.now()
    
    # Renderiza o template de impressão, passando os dados do processo.
    return render_template('imprimir_ficha.html', processo=processo, agora=agora)

@app.route('/admin/licenca/imprimir_ficha/<string:tipo>/<int:licenca_id>')
def admin_imprimir_ficha_licenca(tipo, licenca_id):
    """Gera uma página de impressão para uma solicitação de licença específica."""
    licenca = None
    if tipo == 'empresa':
        licenca = LicencaEmpresa.query.get_or_404(licenca_id)
    elif tipo == 'autonomo':
        licenca = LicencaAutonomo.query.get_or_404(licenca_id)
    else:
        abort(404)

    # Processa os campos JSON para facilitar a exibição no template
    rt_info = json.loads(licenca.rt_info) if licenca.rt_info else {}
    
    # ----> PASSO 1: A linha abaixo PRECISA estar aqui <----
    data_de_geracao = datetime.now()

    # ----> PASSO 2: O parâmetro 'data_geracao' PRECISA ser adicionado aqui <----
    return render_template('admin_imprimir_ficha_licenca.html', 
                           licenca=licenca,
                           tipo=tipo,
                           rt_info=rt_info,
                           data_geracao=data_de_geracao) # <--- O novo p





# --- ROTA NOVA: Atualiza o status de um cadastro de autônomo --

# --- ROTA ANTIGA (Ainda útil para licenças) ---
@app.route('/admin/detalhe_licenca/<int:licenca_id>')
def admin_detalhe_licenca(licenca_id):
    """Exibe os detalhes de uma licença (lógica genérica)."""
    tipo = request.args.get('tipo')
    if tipo == 'autonomo':
        # Redireciona para a nova rota específica
        return redirect(url_for('admin_detalhe_licenca', licenca_id=licenca_id))
    
    licenca = LicencaEmpresa.query.get_or_404(licenca_id)
    requerente = licenca.empresa
    origin = request.args.get('origin', 'analise') 
        
    return render_template('admin_detalhe_licenca.html', 
                           licenca=licenca, 
                           requerente=requerente, 
                           tipo='empresa',
                           origin=origin)




@app.route('/admin/autonomos')
def admin_listar_autonomos():
    """Exibe a lista de Autônomos com filtro de busca."""
    query_search = request.args.get('q', '')
    # CORREÇÃO: O filtro foi ajustado para ser mais robusto, mostrando tudo que não está 'Aprovado'.
    base_query = Autonomo.query.filter(Autonomo.status != 'Aprovado')

    if query_search:
        search_term = f"%{query_search}%"
        base_query = base_query.filter(
            or_(
                Autonomo.nome_completo.ilike(search_term),
                Autonomo.cpf.ilike(search_term)
            )
        )

    autonomos_pendentes = base_query.order_by(Autonomo.data_cadastro.desc()).all()
    return render_template('admin_listar_autonomos.html', 
                           autonomos=autonomos_pendentes,
                           query_q=query_search)


@app.route('/admin/autonomo/analisar/<int:autonomo_id>')
def admin_detalhe_autonomo(autonomo_id):
    autonomo = Autonomo.query.get_or_404(autonomo_id)

    # Cria um dicionário com os documentos que foram anexados
    documentos_anexados = {}
    doc_map = {
        "Alvará de Funcionamento": autonomo.doc_alvara_funcionamento_path,
        "Cópia do CPF e RG": autonomo.doc_cpf_rg_path,
        "Comprovante de Endereço": autonomo.doc_comprovante_endereco_path,
        "Registro no Conselho de Classe": autonomo.doc_registro_conselho_path,
        "Declaração de Responsabilidade Técnica": autonomo.doc_declaracao_rt_path,
        "Declaração de Atividades Exercidas": autonomo.doc_declaracao_atividades_path,
        "Termo de Compromisso Sanitário": autonomo.doc_termo_compromisso_path
    }

    for nome, caminho in doc_map.items():
        if caminho: # Adiciona ao dicionário apenas se o ficheiro foi enviado
            documentos_anexados[nome] = caminho

    return render_template('admin_analise_cadastro_autonomo.html', autonomo=autonomo, documentos_anexados=documentos_anexados)


@app.route('/admin/autonomo/atualizar_status/<int:autonomo_id>', methods=['POST'])
def admin_atualizar_status_autonomo(autonomo_id):
    autonomo = Autonomo.query.get_or_404(autonomo_id)
    novo_status = request.form.get('novo_status')

    if novo_status:
        autonomo.status = novo_status
        
        if novo_status == 'Aprovado':
            # =================================================================
            # == PONTO CRÍTICO DA CORREÇÃO ==
            # A linha abaixo é a que resolve o erro. A chamada à função 
            # DEVE incluir os dois argumentos: 'autonomo' e 'responsavel_assinatura'.
            # Se o erro persiste, é porque esta linha no seu ficheiro
            # ainda está com a versão antiga (apenas com 'autonomo').
            # =================================================================
            coordenador = Funcionario.query.filter_by(cargo='Coordenador').first()
            if not coordenador:
                flash('Nenhum funcionário com o cargo "Coordenador" foi encontrado no sistema.', 'danger')
                return redirect(url_for('admin_detalhe_autonomo', autonomo_id=autonomo_id))
            
            if not coordenador.caminho_assinatura:
                flash('O Coordenador cadastrado não possui uma assinatura associada.', 'danger')
                return redirect(url_for('admin_detalhe_autonomo', autonomo_id=autonomo_id))

            caminho_completo_assinatura = os.path.join(current_app.root_path, 'static', coordenador.caminho_assinatura)
            
            responsavel_assinatura = {
                'nome': coordenador.nome,
                'cargo': coordenador.cargo,
                'caminho_imagem': caminho_completo_assinatura
            }

            # A chamada à função DEVE incluir os dois argumentos.
            gerar_alvara_pdf_autonomo(autonomo, responsavel_assinatura)
            
            flash('Status atualizado e alvará gerado com sucesso!', 'success')
        else:
            flash('Status do autônomo atualizado com sucesso!', 'success')
            
        db.session.commit()
    else:
        flash('Nenhum novo status foi selecionado.', 'warning')

    return redirect(url_for('admin_detalhe_autonomo', autonomo_id=autonomo_id))

#------------------------------------------------------NOVA ROTA DE SOLICITAÇÃO----------------------------------------------------------------------------------------------------------------------
@app.route('/solicitar_licenca')
def solicitar_licenca():
    """Exibe a página de seleção (hub) para o tipo de licença."""
    return render_template('solicitar_licenca_hub.html')

@app.route('/solicitar_licenca/empresa', methods=['GET'])
def solicitar_licenca_cnpj():
    """Exibe o formulário de licença para empresas (busca por CNPJ)."""
    empresa = None
    query_cnpj = request.args.get('cnpj', '')
    if query_cnpj:
        cnpj_limpo = re.sub(r'[^0-9]', '', query_cnpj)
        empresa = Empresas.query.filter(or_(Empresas.cnpj == cnpj_limpo, Empresas.cnpj == query_cnpj), Empresas.status == 'Aprovado').first()
        if not empresa:
            flash('Nenhuma empresa aprovada encontrada com o CNPJ informado.', 'danger')
    ano_atual = datetime.now().year
    return render_template('solicitar_licenca_cnpj.html', empresa=empresa, query_cnpj=query_cnpj, ano_atual=ano_atual)

@app.route('/solicitar_licenca/autonomo', methods=['GET', 'POST'])
def solicitar_licenca_cpf():
    """
    Exibe o formulário de busca por CPF. Se um CPF for enviado via POST,
    busca o autônomo e re-renderiza a página com o formulário completo.
    """
    autonomo = None
    query_cpf = ''

    if request.method == 'POST':
        query_cpf = request.form.get('cpf_busca', '')
        if query_cpf:
            cpf_limpo = re.sub(r'[^0-9]', '', query_cpf)
            
            autonomo = Autonomo.query.filter(
                or_(Autonomo.cpf == cpf_limpo, Autonomo.cpf == query_cpf),
                Autonomo.status == 'Aprovado'
            ).first()

            if not autonomo:
                flash('Nenhum autônomo aprovado foi encontrado com o CPF informado.', 'danger')
    
    ano_atual = datetime.now().year
    return render_template('solicitar_licenca_cpf.html', 
                           autonomo=autonomo, 
                           query_cpf=query_cpf,
                           ano_atual=ano_atual)

# --- NOVAS ROTAS SEPARADAS PARA SALVAR CADA TIPO DE LICENÇA ---



@app.route('/admin/autonomo/ficha/<int:autonomo_id>')
def admin_ficha_autonomo(autonomo_id):
    """Exibe a ficha completa de um autônomo, incluindo seu histórico de processos."""
    autonomo = Autonomo.query.get_or_404(autonomo_id)
    
    # --- CORREÇÃO APLICADA ---
    # A busca agora é feita apenas nas tabelas que possuem um campo para o CPF.
    
    # Busca por denúncias usando a coluna correta
    denuncias = Denuncias.query.filter_by(denunciado_cpf_cnpj=autonomo.cpf).all()
    
    # Busca por licenças usando a relação direta
    licencas = LicencaAutonomo.query.filter_by(autonomo_id=autonomo.id).all()
    
    # As buscas abaixo foram comentadas porque, como você indicou,
    # estas tabelas ainda não possuem um campo para o CPF.
    # Para ativá-las no futuro, precisaríamos de adicionar um campo de CPF
    # aos modelos Vistoria e Notificacoes.
    vistorias = [] # Vistoria.query.filter_by(cpf_vinculado=autonomo.cpf).all()
    notificacoes = [] # Notificacoes.query.filter_by(notificado_cpf_cnpj=autonomo.cpf).all()

    return render_template('admin_ficha_autonomo.html', 
                           autonomo=autonomo,
                           denuncias=denuncias,
                           licencas=licencas,
                           vistorias=vistorias,
                           notificacoes=notificacoes)




@app.route('/salvar_licenca_autonomo', methods=['POST'])
def salvar_licenca_autonomo():
    """Salva a solicitação de licença para um Autônomo."""
    try:
        autonomo_id = request.form.get('autonomo_id')
        if not autonomo_id:
            flash('Erro: ID do autônomo não foi encontrado.', 'danger')
            return redirect(url_for('solicitar_licenca_cpf'))

        protocolo_gerado = gerar_protocolo('LICENCA_AUTONOMO', 'LSAA')

        nova_licenca = LicencaAutonomo(
            protocolo=protocolo_gerado,
            autonomo_id=autonomo_id,
            status='Pendente',
            data_solicitacao=datetime.now(),
            ano_exercicio=request.form.get('ano_exercicio'), # Campo adicionado aqui
            nacionalidade=request.form.get('nacionalidade'),
            estado_civil=request.form.get('estado_civil'),
            local_atuacao_endereco=request.form.get('local_atuacao_endereco'),
            local_atuacao_tipo=request.form.get('local_atuacao_tipo'),
            local_atuacao_referencia=request.form.get('local_atuacao_referencia'),
            descricao_atividade=request.form.get('descricao_atividade'),
            possui_rt=request.form.get('possui_rt'),
            rt_nome=request.form.get('rt_nome'),
            rt_cpf=request.form.get('rt_cpf'),
            rt_conselho=request.form.get('rt_conselho'),
            usa_quimicos=request.form.get('usa_quimicos'),
            usa_perfuro=request.form.get('usa_perfuro'),
            faz_invasivo=request.form.get('faz_invasivo'),
            invasivo_descricao=request.form.get('invasivo_descricao')
        )

        # Processa e associa os caminhos dos ficheiros
        subpasta_docs = f"licenca_autonomo_{autonomo_id}"
        nova_licenca.rt_declaracao_path = handle_upload('rt_declaracao', subpasta_docs)
        nova_licenca.doc_identidade_path = handle_upload('doc_identidade', subpasta_docs)
        nova_licenca.doc_cpf_path = handle_upload('doc_cpf', subpasta_docs)
        nova_licenca.doc_residencia_path = handle_upload('doc_residencia', subpasta_docs)
        nova_licenca.doc_formacao_path = handle_upload('doc_formacao', subpasta_docs)
        nova_licenca.doc_dedetizacao_path = handle_upload('doc_dedetizacao', subpasta_docs)
        nova_licenca.doc_alvara_funcionamento_path = handle_upload('doc_alvara_funcionamento', subpasta_docs)
        
        db.session.add(nova_licenca)
        db.session.commit()
        flash(f'Solicitação de licença (Autônomo) enviada com sucesso! Protocolo: {protocolo_gerado}', 'success')
        return redirect(url_for('admin_analisar_licencas_autonomos'))

    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao salvar a licença: {e}', 'danger')
        print(f"ERRO DETALHADO AO SALVAR LICENÇA AUTÔNOMO: {e}")
        return redirect(url_for('solicitar_licenca_cpf'))

@app.route('/solicitar-licenca-evento', methods=['GET', 'POST'])
def solicitar_licenca_evento():
    if request.method == 'POST':
        try:
            # Coleta os tipos de evento (checkboxes)
            tipos_selecionados = request.form.getlist('evento_tipo')
            if 'Outro' in tipos_selecionados:
                outro_tipo = request.form.get('evento_tipo_outro')
                if outro_tipo:
                    tipos_selecionados.remove('Outro')
                    tipos_selecionados.append(outro_tipo)
            
            protocolo = gerar_protocolo('EVENTO', 'LSAEV') # Adapte se necessário

            nova_licenca = LicencaEvento(
                protocolo=protocolo,
                # Dados do Solicitante
                solicitante_nome=request.form.get('solicitante_nome'),
                solicitante_cpf_cnpj=request.form.get('solicitante_cpf_cnpj'),
                solicitante_rg=request.form.get('solicitante_rg'),
                solicitante_telefone=request.form.get('solicitante_telefone'),
                solicitante_email=request.form.get('solicitante_email'),
                solicitante_endereco=request.form.get('solicitante_endereco'),
                # Dados do Evento
                nome_evento=request.form.get('evento_nome'),
                tipos_evento=", ".join(tipos_selecionados),
                local_evento=request.form.get('evento_local'),
                data_inicio=datetime.strptime(request.form.get('evento_data_inicio'), '%Y-%m-%d').date(),
                data_fim=datetime.strptime(request.form.get('evento_data_fim'), '%Y-%m-%d').date(),
                horario=request.form.get('evento_horario'),
                # Estrutura do Evento
                vende_bebidas=request.form.get('vende_bebidas'),
                tipo_casco=request.form.get('tipo_casco'),
                usa_estrutura_montavel=request.form.get('usa_estrutura_montavel'),
                usa_churrasqueira=request.form.get('usa_churrasqueira'),
                churrasqueira_tipo=request.form.get('churrasqueira_tipo'),
                churrasqueira_gas_validade=request.form.get('churrasqueira_gas_validade'),
                usa_fritadeira=request.form.get('usa_fritadeira'),
                fritadeira_gas_validade=request.form.get('fritadeira_gas_validade'),
                manipula_alimentos=request.form.get('manipula_alimentos'),
                tem_pia=request.form.get('tem_pia'),
                # Bombeiros
                bombeiros_liberacao=request.form.get('bombeiros_liberacao'),
                bombeiros_numero=request.form.get('bombeiros_numero'),
                bombeiros_data=datetime.strptime(request.form.get('bombeiros_data'), '%Y-%m-%d').date() if request.form.get('bombeiros_data') else None
            )
            
            # Processamento de Anexos
            subpasta_docs = f"evento_{protocolo.replace('/', '-')}"
            nova_licenca.doc_bombeiros_path = salvar_arquivo_upload(request.files.get('anexo_bombeiros'), subpasta_docs)
            nova_licenca.doc_cpf_cnpj_path = salvar_arquivo_upload(request.files.get('anexo_cpf_cnpj'), subpasta_docs)
            nova_licenca.doc_alvara_local_path = salvar_arquivo_upload(request.files.get('anexo_alvara_local'), subpasta_docs)
            nova_licenca.doc_autorizacao_rua_path = salvar_arquivo_upload(request.files.get('anexo_autorizacao_rua'), subpasta_docs)

            db.session.add(nova_licenca)
            db.session.commit()
            
            flash(f'Solicitação para o evento "{nova_licenca.nome_evento}" enviada com sucesso! Protocolo: {protocolo}', 'success')
            return redirect(url_for('index')) # Mude para a sua página de sucesso
        
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao processar a sua solicitação: {e}', 'danger')
            return redirect(url_for('solicitar_licenca_evento'))

    return render_template('solicitar_licenca_evento.html')


#----------------------------------------LICENÇA EVENTOS------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/admin/licencas/eventos')
def admin_listar_licencas_eventos():
    """Exibe a lista de solicitações de licença para eventos, com filtro de busca."""
    query_search = request.args.get('q', '') # Pega o termo de busca da URL

    # Inicia a consulta base
    base_query = LicencaEvento.query

    # Se houver um termo de busca, filtra pelos campos relevantes
    if query_search:
        search_term = f"%{query_search}%"
        base_query = base_query.filter(
            or_(
                LicencaEvento.protocolo.ilike(search_term),
                LicencaEvento.nome_evento.ilike(search_term),
                LicencaEvento.solicitante_nome.ilike(search_term)
            )
        )
    
    eventos = base_query.order_by(LicencaEvento.data_solicitacao.desc()).all()
    
    return render_template('admin_listar_licencas_eventos.html', 
                           eventos=eventos,
                           query_q=query_search)

@app.route('/admin/licenca_evento/<int:evento_id>')
def admin_detalhe_licenca_evento(evento_id):
    """Exibe os detalhes de uma solicitação de licença de evento para análise."""
    licenca = LicencaEvento.query.get_or_404(evento_id)
    
    # Em app.py, dentro de admin_detalhe_licenca_evento
    
    
    return render_template('admin_detalhe_licenca_evento.html', licenca=licenca)

# A sua rota para atualizar o status continua a mesma

@app.route('/admin/licenca/evento/atualizar_status/<int:evento_id>', methods=['POST'])
def admin_atualizar_status_licenca_evento(evento_id):
    licenca = LicencaEvento.query.get_or_404(evento_id)
    novo_status = request.form.get('novo_status')
    data_validade_str = request.form.get('data_validade')
    observacoes_texto = request.form.get('observacoes', '').strip()

    if novo_status:
        licenca.status = novo_status
        
        if data_validade_str:
            try:
                licenca.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de data inválido.', 'danger')
                # CORREÇÃO: O parâmetro foi alterado para 'evento_id'
                return redirect(url_for('admin_detalhe_licenca_evento', evento_id=evento_id))
        
        if observacoes_texto:
            data_hora_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
            nova_entrada_historico = f"\n\n--- OBSERVAÇÃO DO ADMIN EM {data_hora_atual} ---\n{observacoes_texto}"
            licenca.observacoes = (licenca.observacoes or '') + nova_entrada_historico

        if novo_status == 'Aprovado':
            # Assumindo que você tem uma função para gerar o alvará de evento
            # e um modelo Funcionario para o coordenador.
            coordenador = Funcionario.query.filter_by(cargo='Coordenador').first()
            if not coordenador or not coordenador.caminho_assinatura:
                flash('Coordenador com assinatura não encontrado. Não foi possível gerar o alvará.', 'danger')
                db.session.commit()
                # CORREÇÃO: O parâmetro foi alterado para 'evento_id'
                return redirect(url_for('admin_detalhe_licenca_evento', evento_id=evento_id))

            caminho_completo_assinatura = os.path.join(current_app.root_path, 'static', coordenador.caminho_assinatura)
            responsavel_assinatura = {
                'nome': coordenador.nome,
                'cargo': coordenador.cargo,
                'caminho_imagem': caminho_completo_assinatura
            }

            # Substitua 'gerar_alvara_pdf_evento' pela sua função real
            nome_alvara = gerar_alvara_pdf_evento(licenca, responsavel_assinatura)
            licenca.alvara_pdf_path = nome_alvara
            
            flash('Status atualizado e alvará gerado com sucesso!', 'success')
        else:
            licenca.alvara_pdf_path = None
            flash('Status da licença atualizado com sucesso!', 'success')
            
        db.session.commit()
    else:
        flash('Nenhum novo status foi selecionado.', 'warning')

    # CORREÇÃO: O parâmetro foi alterado para 'evento_id'
    return redirect(url_for('admin_detalhe_licenca_evento', evento_id=evento_id))


@app.route('/admin/licenca/evento/<int:licenca_id>/imprimir_ficha')
def admin_imprimir_ficha_licenca_evento(licenca_id):
    """Gera uma página de impressão para uma solicitação de licença de evento."""
    licenca = LicencaEvento.query.get_or_404(licenca_id)
    
    # Gera a data e hora atuais para serem usadas no template
    data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Processa os campos JSON para facilitar a exibição no template
    # Em app.py, dentro de admin_imprimir_ficha_licenca_evento
    
    
    return render_template(
    'admin_imprimir_ficha_licenca_evento.html', 
    licenca=licenca, 
    data_geracao=data_geracao
)


@app.route('/admin/licenca/autonomo/<int:licenca_id>')
def admin_detalhe_licenca_autonomo(licenca_id):
    """Exibe os detalhes de uma licença de autônomo para análise."""
    
    # Busca a licença específica pelo ID.
    licenca = LicencaAutonomo.query.get_or_404(licenca_id)
    
    # --- INÍCIO DA CORREÇÃO ---
    # Cria um dicionário com os documentos que foram anexados à licença.
    # Isto garante que a variável 'documentos_anexados' seja sempre enviada para o template.
    documentos_anexados = {}
    doc_map = {
        "Alvará de Funcionamento (Prefeitura)": licenca.doc_alvara_funcionamento_path,
        "Documento de Identidade": licenca.doc_identidade_path,
        "CPF": licenca.doc_cpf_path,
        "Comprovante de Residência": licenca.doc_residencia_path,
        "Certificado do Curso": licenca.doc_formacao_path,
        "Comprovante de Dedetização": licenca.doc_dedetizacao_path,
        "Declaração de RT": licenca.rt_declaracao_path
    }

    for nome, caminho in doc_map.items():
        if caminho: # Adiciona ao dicionário apenas se o ficheiro foi enviado
            documentos_anexados[nome] = caminho
    # --- FIM DA CORREÇÃO ---

    # Renderiza o template, passando tanto a licença como a lista de documentos.
    return render_template(
        'admin_detalhe_licenca_autonomo.html', 
        licenca=licenca, 
        documentos_anexados=documentos_anexados
    )

@app.route('/admin/licenca/autonomo/atualizar_status/<int:licenca_id>', methods=['POST'])
def admin_atualizar_status_licenca_autonomo(licenca_id):
    licenca = LicencaAutonomo.query.get_or_404(licenca_id)
    novo_status = request.form.get('novo_status')
    data_validade_str = request.form.get('data_validade')
    # Pega o texto do campo de observações do formulário
    observacoes_texto = request.form.get('observacoes', '').strip()

    if novo_status:
        licenca.status = novo_status
        
        # Guarda a data de validade se ela for enviada
        if data_validade_str:
            try:
                licenca.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de data inválido.', 'danger')
                return redirect(url_for('admin_detalhe_licenca_autonomo', licenca_id=licenca_id))
        
        # --- INÍCIO DA ALTERAÇÃO ---
        # Se o admin escreveu uma nova observação, adiciona ao histórico.
        if observacoes_texto:
            data_hora_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
            # Formata a nova entrada para criar um log claro
            nova_entrada_historico = f"\n\n--- OBSERVAÇÃO DO ADMIN EM {data_hora_atual} ---\n{observacoes_texto}"
            # Anexa a nova entrada ao histórico existente, ou cria um novo se estiver vazio
            licenca.observacoes = (licenca.observacoes or '') + nova_entrada_historico
        # --- FIM DA ALTERAÇÃO ---

        # Lógica para gerar o alvará quando o status é 'Aprovado'
        if novo_status == 'Aprovado':
            coordenador = Funcionario.query.filter_by(cargo='Coordenador').first()
            if not coordenador or not coordenador.caminho_assinatura:
                flash('Coordenador com assinatura não encontrado. Não foi possível gerar o alvará.', 'danger')
                db.session.commit() # Salva o status e a observação mesmo que o alvará falhe
                return redirect(url_for('admin_detalhe_licenca_autonomo', licenca_id=licenca_id))

            caminho_completo_assinatura = os.path.join(current_app.root_path, 'static', coordenador.caminho_assinatura)
            responsavel_assinatura = {
                'nome': coordenador.nome,
                'cargo': coordenador.cargo,
                'caminho_imagem': caminho_completo_assinatura
            }

            nome_alvara = gerar_alvara_pdf_autonomo(licenca, responsavel_assinatura)
            licenca.alvara_pdf_path = nome_alvara
            
            flash('Status atualizado e alvará gerado com sucesso!', 'success')
        else:
            # Se o status não for 'Aprovado', garante que não há um caminho de alvará antigo
            licenca.alvara_pdf_path = None
            flash('Status da licença atualizado com sucesso!', 'success')
            
        db.session.commit() # Salva todas as alterações na base de dados
    else:
        flash('Nenhum novo status foi selecionado.', 'warning')

    return redirect(url_for('admin_detalhe_licenca_autonomo', licenca_id=licenca_id))


@app.route('/admin/licenca/autonomo/alvara/<int:licenca_id>')
def admin_download_alvara_autonomo(licenca_id):
    licenca = LicencaAutonomo.query.get_or_404(licenca_id)
    if licenca.alvara_pdf_path:
        return send_from_directory(
            current_app.config['ALVARAS_FOLDER'], 
            licenca.alvara_pdf_path, 
            as_attachment=False
        )
    else:
        flash('Alvará não encontrado para esta licença.', 'danger')
        return redirect(url_for('admin_detalhe_licenca_autonomo', licenca_id=licenca_id))

        
   
# --- NOVA ROTA PARA IMPRIMIR A FICHA DE SOLICITAÇÃO ---
@app.route('/admin/licenca/autonomo/<int:licenca_id>/imprimir_ficha')
def admin_imprimir_ficha_licenca_autonomo(licenca_id):
    """Gera uma página de impressão para uma solicitação de licença de autônomo."""
    licenca = LicencaAutonomo.query.get_or_404(licenca_id)
    
    # Gera a data e hora atuais para serem usadas no template
    data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    return render_template('admin_imprimir_ficha_licenca_autonomo.html', 
                           licenca=licenca, 
                           data_geracao=data_geracao)



@app.route('/admin/download_alvara_evento/<path:filename>')
def download_alvara_evento(filename):
    """Permite o download de um alvará de evento gerado."""
    alvaras_folder = app.config.get('ALVARAS_FOLDER')
    filepath = os.path.join(alvaras_folder, filename)
    
    if not os.path.exists(filepath):
        flash('Erro: O ficheiro do alvará não foi encontrado no servidor.', 'danger')
        return redirect(url_for('admin_listar_licencas_eventos'))
        
    return send_file(filepath, as_attachment=True)

@app.route('/test_pdf')
def test_pdf_route():
    """Esta rota serve para testar a geração do PDF com dados de exemplo."""
    
    # Simulação de um objeto de licença e dados para o teste
    licenca_exemplo = {'protocolo': f"2025_{datetime.now().strftime('%H%M%S')}"}
    
    dados_exemplo = {
        'protocolo': licenca_exemplo['protocolo'],
        'data_validade': '2026-07-30',
        'razao_social': 'DROGARIA SAÚDE TOTAL LTDA',
        'nome_fantasia': 'Farma Saúde',
        'cnpj': '12.345.678/0001-99',
        'endereco': 'Rua das Flores, 123, Centro, Esperantina - PI',
        'responsavel_juridico': 'João da Silva',
        'horario_funcionamento': '08:00 às 18:00',
        'rt_nome': 'Maria Oliveira',
        'rt_conselho': 'CRF-PI',
        'rt_numero_conselho': '1234',
        'vende_controlados': 'sim',
        'afe_numero': '1234567',
        'vende_retinoicos': 'nao',
        'vende_animais': 'nao'
    }

    fiscal_exemplo = {
        'nome': 'Flávio Azevedo',
        'matricula': '98765',
        'caminho_imagem': 'assinatura.png' 
    }
    
    # Criando um arquivo de imagem de assinatura falso para o teste, se não existir
    if not os.path.exists(fiscal_exemplo['caminho_imagem']):
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (200, 60), color = 'white')
            d = ImageDraw.Draw(img)
            d.text((10,10), "Assinatura", fill=(0,0,0))
            img.save('assinatura.png')
            print("Arquivo 'assinatura.png' de teste criado.")
        except ImportError:
            print("AVISO: PIL/Pillow não instalado. Não foi possível criar a imagem de assinatura de teste.")
            fiscal_exemplo['caminho_imagem'] = None

    nome_arquivo = gerar_alvara_pdf(licenca_exemplo, dados_exemplo, fiscal_exemplo)

    if nome_arquivo:
        flash(f"PDF '{nome_arquivo}' gerado com sucesso!")
        return redirect(url_for('listar_alvaras'))
    else:
        flash("Ocorreu um erro ao gerar o PDF.", "error")
        return redirect(url_for('index'))

@app.route('/alvaras')
def listar_alvaras():
    """Lista todos os alvarás na pasta de alvarás."""
    try:
        # Garante que a pasta exista antes de listar
        os.makedirs(app.config['ALVARAS_FOLDER'], exist_ok=True)
        files = os.listdir(app.config['ALVARAS_FOLDER'])
        if not files:
            return '<h1>Alvarás Gerados</h1><p>Nenhum alvará foi gerado ainda.</p><a href="/">Voltar</a>'
        
        links = [f'<li><a href="/alvaras/{f}">{f}</a></li>' for f in sorted(files, reverse=True)]
        return f"<h1>Alvarás Gerados</h1><ul>{''.join(links)}</ul>"
    except FileNotFoundError:
        return "Pasta de alvarás não encontrada.", 404

@app.route('/download-alvara/<path:filename>')
def download_alvara(filename):
    """
    Serve o arquivo do alvará para download a partir da pasta de uploads.
    """
    # É uma boa prática usar uma configuração para o diretório de uploads
    alvara_folder = current_app.config['ALVARAS_FOLDER']
    return send_from_directory(alvara_folder, filename, as_attachment=True)

#----------------------------------------ROTA LICENÇA PUBLICA.------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/solicitar_licenca_publica', methods=['GET', 'POST'])
def solicitar_licenca_publica():
    instituicao = None
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'buscar_instituicao':
            cnpj_limpo = limpar_cnpj(request.form.get('cnpj'))
            instituicao = Empresas.query.filter_by(cnpj=cnpj_limpo).first()
            if not instituicao:
                flash('Nenhuma instituição encontrada com o CNPJ informado.', 'danger')

        elif action == 'enviar_solicitacao_publica':
            try:
                # Geração de Protocolo
                ano_atual = datetime.now().year
                prefixo = f"LPUB-{ano_atual}/"
                ultimo = db.session.query(db.func.max(LicencasPublicas.protocolo_licencas_publicas)).filter(LicencasPublicas.protocolo_licencas_publicas.like(f"{prefixo}%")).scalar()
                proximo_num = int(ultimo.split('/')[1]) + 1 if ultimo else 1
                protocolo = f"{prefixo}{proximo_num:05d}"
                
                # Tratamento de Uploads
                subpasta_anexos = 'licencas_publicas'
                declaracao_rt_path = handle_upload('responsavel_unidade_declaracao_rt', subfolder=subpasta_anexos)
                declaracao_responsavel_path = handle_upload('anexo_declaracao_responsavel', subfolder=subpasta_anexos)
                declaracao_rt_geral_path = handle_upload('anexo_declaracao_rt_geral', subfolder=subpasta_anexos)

                nova_licenca = LicencasPublicas(
                    protocolo_licencas_publicas=protocolo,
                    empresa_id=request.form.get('instituicao_id'),
                    unidade_nome=request.form.get('unidade_nome'),
                    unidade_cnes_inep=request.form.get('unidade_cnes_inep'),
                    unidade_endereco=request.form.get('unidade_endereco'),
                    unidade_ponto_ref=request.form.get('unidade_ponto_ref'),
                    unidade_tipo=request.form.get('unidade_tipo'),
                    unidade_tipo_outro=request.form.get('unidade_tipo_outro'),
                    responsavel_unidade_nome=request.form.get('responsavel_unidade_nome'),
                    responsavel_unidade_cpf=request.form.get('responsavel_unidade_cpf'),
                    responsavel_unidade_cargo=request.form.get('responsavel_unidade_cargo'),
                    responsavel_unidade_conselho=request.form.get('responsavel_unidade_conselho'),
                    responsavel_unidade_contato=request.form.get('responsavel_unidade_contato'),
                    responsavel_unidade_declaracao_rt_path=declaracao_rt_path,
                    atividades_desenvolvidas=request.form.get('atividades_desenvolvidas'),
                    servicos_prestados=request.form.get('servicos_prestados'),
                    possui_cozinha=bool(request.form.get('possui_cozinha')),
                    possui_farmacia=bool(request.form.get('possui_farmacia')),
                    anexo_declaracao_responsavel_path=declaracao_responsavel_path,
                    anexo_declaracao_rt_geral_path=declaracao_rt_geral_path,
                    observacoes_adicionais=request.form.get('observacoes_adicionais'),
                    ciencia_solicitante_nome=request.form.get('ciencia_solicitante_nome'),
                    ciencia_solicitante_cargo=request.form.get('ciencia_solicitante_cargo'),
                    status='Em Análise' # Status inicial
                )
                
                db.session.add(nova_licenca)
                db.session.commit()
                
                flash(f'Solicitação enviada com sucesso! Protocolo: {protocolo}', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ocorreu um erro ao registrar a solicitação: {e}', 'danger')
                print(f"ERRO AO REGISTRAR LICENÇA PÚBLICA: {e}")

    return render_template('solicitar_licenca_publica.html', instituicao=instituicao)

# ROTA 2: Listagem para o admin analisar
@app.route('/admin/licencas-publicas')
def admin_listar_licencas_publicas():
    """
    Lista as licenças públicas com base em filtros de status e um termo de busca.
    """
    # Pega os parâmetros da URL
    filtro_status = request.args.get('filtro', 'pendentes')
    termo_busca = request.args.get('busca', '').strip()

    # Inicia a query base, juntando com a tabela de Empresas para permitir a busca por CNPJ/Razão Social
    query = LicencasPublicas.query.join(Empresas, LicencasPublicas.empresa_id == Empresas.id)

    # 1. Aplica o filtro de status
    if filtro_status == 'pendentes':
        query = query.filter(LicencasPublicas.status.notin_(['Aprovado', 'Reprovado']))
        titulo = "Solicitações Pendentes"
    elif filtro_status == 'aprovadas':
        query = query.filter(LicencasPublicas.status == 'Aprovado')
        titulo = "Licenças Aprovadas"
    else: # 'todas'
        titulo = "Todas as Solicitações"
    
    # 2. Aplica o filtro de busca, se um termo for fornecido
    if termo_busca:
        cnpj_limpo = re.sub(r'[^0-9]', '', termo_busca)
        # Busca pelo termo no protocolo, na razão social ou no CNPJ
        query = query.filter(
            db.or_(
                LicencasPublicas.protocolo_licencas_publicas.ilike(f'%{termo_busca}%'),
                Empresas.razao_social.ilike(f'%{termo_busca}%'),
                Empresas.cnpj.contains(cnpj_limpo)
            )
        )
        titulo += f" (Buscando por: '{termo_busca}')"

    licencas = query.order_by(LicencasPublicas.data_solicitacao.desc()).all()
    
    return render_template(
        'admin_listar_licencas_publicas.html', 
        licencas=licencas, 
        titulo_pagina=titulo,
        filtro_ativo=filtro_status,
        termo_busca=termo_busca  # Envia o termo de busca de volta para o template
    )

# ROTA 3: Página de detalhes para análise individual
@app.route('/admin/licencas-publicas/detalhe/<int:licenca_id>')
def admin_detalhe_licenca_publica(licenca_id):
    """
    Exibe os detalhes de uma solicitação de licença pública específica para análise.
    """
    licenca = LicencasPublicas.query.get_or_404(licenca_id)
    
    # --- INÍCIO DA CORREÇÃO ---
    # O nome da variável enviada para o template foi padronizado para 'licenca' (sem ç)
    return render_template('admin_detalhe_licenca_publica.html', licenca=licenca)
    # --- FIM DA CORREÇÃO ---

# ROTA 4: Ação de atualizar o status
@app.route('/admin/licencas-publicas/atualizar/<int:licenca_id>', methods=['POST'])
def admin_atualizar_status_licenca_publica(licenca_id):
    licenca = LicencasPublicas.query.get_or_404(licenca_id)
    
    novo_status = request.form.get('status')
    observacoes = request.form.get('observacoes')

    if novo_status in ['Pendente com Observação', 'Reprovado'] and not observacoes.strip():
        flash('É obrigatório fornecer uma observação para o status selecionado.', 'danger')
        return redirect(url_for('admin_detalhe_licenca_publica', licenca_id=licenca_id))

    licenca.status = novo_status
    licenca.observacoes = observacoes
    
    if novo_status == 'Aprovado':
        licenca.data_validade = datetime.utcnow() + timedelta(days=365)

    try:
        db.session.commit()
        flash('Status da licença atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar o status: {e}', 'danger')

    return redirect(url_for('admin_listar_licencas_publicas'))


@app.route('/imprimir-alvara-publica/<int:licenca_id>')
def imprimir_alvara_publica_cidadao(licenca_id):
    """
    Rota pública para gerar e servir o PDF de um alvará de instituição pública.
    """
    licenca = LicencasPublicas.query.get_or_404(licenca_id)
    
    # Apenas permite a impressão se a licença estiver de facto aprovada
    if licenca.status != 'Aprovado':
        flash('Este alvará não está disponível para impressão.', 'warning')
        return redirect(url_for('consultar_solicitacao'))

    # Lógica para encontrar o responsável pela assinatura (ex: o coordenador)
    responsavel = Funcionario.query.filter_by(cargo='Coordenador').first()
    if not responsavel:
        flash('Erro de configuração: Nenhum responsável encontrado para assinar o documento.', 'danger')
        return redirect(url_for('consultar_solicitacao'))

    dados_assinatura = {
        'nome': responsavel.nome,
        'cargo': responsavel.cargo,
        'caminho_imagem': os.path.join(current_app.config['UPLOAD_FOLDER'], responsavel.caminho_assinatura)
    }

    try:
        nome_ficheiro_pdf = gerar_alvara_instituicao_publica_pdf(licenca, dados_assinatura)
        return send_from_directory(
            directory=current_app.config['ALVARAS_FOLDER'],
            path=nome_ficheiro_pdf,
            as_attachment=False
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar alvará público (cidadão) {licenca_id}: {e}")
        flash('Ocorreu um erro ao gerar o PDF do alvará.', 'danger')
        return redirect(url_for('consultar_solicitacao'))


@app.route('/responder-pendencia-publica/<int:licenca_id>', methods=['POST'])
def cidadao_responder_pendencia_publica(licenca_id):
    """
    Processa a resposta do cidadão a uma pendência de licença pública.
    """
    licenca = LicencasPublicas.query.get_or_404(licenca_id)
    
    # --- INÍCIO DA CORREÇÃO ---
    # Garante que os dados do formulário sejam guardados nos campos corretos da base de dados.

    # 1. Processa o anexo, se enviado
    if 'anexo_pendencia' in request.files:
        ficheiro_anexo = request.files['anexo_pendencia']
        if ficheiro_anexo.filename != '':
            # A função handle_upload deve retornar o caminho relativo do ficheiro guardado
            caminho_anexo = handle_upload(ficheiro_anexo, subfolder='respostas_pendencias')
            licenca.anexo_pendencia_path = caminho_anexo

    # 2. Guarda a resposta de texto
    resposta_texto = request.form.get('resposta_texto')
    if resposta_texto:
        licenca.resposta_pendencia_texto = resposta_texto

    # 3. Atualiza o status para notificar o admin que uma resposta foi recebida
    licenca.status = 'Em Análise (Resposta Recebida)'
    # --- FIM DA CORREÇÃO ---
    
    try:
        db.session.commit()
        flash('A sua resposta foi enviada com sucesso e a sua solicitação está em reanálise.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao enviar a sua resposta: {e}', 'danger')
        print(f"ERRO AO GUARDAR RESPOSTA DE PENDÊNCIA: {e}")

    return redirect(url_for('consultar_solicitacao'))


@app.route('/registrar-vistoria')
def registrar_vistoria_view():
    # Busque todos os funcionários/fiscais do banco de dados
    funcionarios_db = Funcionario.query.filter_by(cargo='Fiscal Sanitário').all()
    
    # Formate os dados para o template (uma lista de dicionários)
    funcionarios_list = [
        {
            'id': f.id, 
            'nome_completo': f.nome_completo, 
            'matricula': f.matricula
        } 
        for f in funcionarios_db
    ]
    
    checklists = Checklist.query.all()
    
    # Passe a lista 'funcionarios_list' para o template
    return render_template(
        'registrar_vistoria.html', 
        funcionarios=funcionarios_list, # A variável deve se chamar 'funcionarios'
        checklists=checklists
        # ... outras variáveis que você já usa ...
    )









if __name__ == '__main__':
    app.run(debug=True)