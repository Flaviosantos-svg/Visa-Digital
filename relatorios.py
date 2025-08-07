from fpdf import FPDF
import os

def gerar_relatorio_denuncia_pdf(denuncia):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Relatório de Denúncia - Vigilância Sanitária", ln=True, align='C')

    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Protocolo: {denuncia.get('protocolo', '')}", ln=True)
    pdf.cell(0, 10, f"Data: {denuncia.get('data', '')}", ln=True)
    pdf.cell(0, 10, f"Denunciante: {denuncia.get('denunciante', '')}", ln=True)
    pdf.cell(0, 10, f"Telefone: {denuncia.get('telefone', '')}", ln=True)
    pdf.multi_cell(0, 10, f"Endereço: {denuncia.get('endereco', '')}")
    pdf.multi_cell(0, 10, f"Descrição: {denuncia.get('descricao', '')}")
    pdf.cell(0, 10, f"Status: {denuncia.get('status', '')}", ln=True)

    # Diretório onde o PDF será salvo
    diretorio = "static/relatorios"
    os.makedirs(diretorio, exist_ok=True)

    # Nome do arquivo
    nome_arquivo = f"{diretorio}/denuncia_{denuncia.get('protocolo', '0000')}.pdf"
    pdf.output(nome_arquivo)

    return nome_arquivo
