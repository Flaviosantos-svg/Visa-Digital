import sqlite3

NOME_BANCO_DE_DADOS = "visa_digital.db"

def get_db_connection():
    conn = sqlite3.connect(NOME_BANCO_DE_DADOS)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = sqlite3.connect(NOME_BANCO_DE_DADOS)
        cursor = conn.cursor()
        print("Conectado ao banco de dados. Verificando tabelas...")
        
        # Tabela de empresas ATUALIZADA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo TEXT, cnpj TEXT NOT NULL UNIQUE, razao_social TEXT NOT NULL,
                nome_fantasia TEXT, porte TEXT, data_abertura TEXT, situacao_cadastral TEXT, cnae_principal TEXT,
                cnae_secundario TEXT, endereco TEXT, telefone_empresa TEXT, responsavel_juridico_nome TEXT,
                responsavel_juridico_cpf TEXT, responsavel_juridico_tel TEXT, contador_nome TEXT, contador_cpf TEXT,
                contador_tel TEXT, horario_funcionamento TEXT, data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Aprovado', justificativa_status TEXT,
                orgao_responsavel TEXT -- NOVA COLUNA
            );
        """)
        
        # ... (outras tabelas sem alterações) ...
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licencas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER NOT NULL, protocolo_licenca TEXT NOT NULL UNIQUE,
                ano_exercicio INTEGER NOT NULL, data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, data_emissao DATE,
                data_vencimento DATE, status TEXT DEFAULT 'Pendente', justificativa_status TEXT, necessita_rt TEXT,
                rt_nome TEXT, rt_cpf TEXT, rt_tel TEXT, rt_conselho TEXT, rt_numero_conselho TEXT, rt_declaracao_path TEXT,
                vende_controlados TEXT, manipula_medicamentos TEXT, vende_animais TEXT, rt_vet_nome TEXT, rt_vet_cpf TEXT,
                rt_vet_tel TEXT, rt_vet_conselho TEXT, rt_vet_numero_conselho TEXT, rt_vet_declaracao_path TEXT,
                atividade_principal_descrita TEXT, afe_path TEXT, realizou_dedetizacao TEXT, data_dedetizacao DATE,
                certificado_dedetizacao_path TEXT, alvara_pdf_path TEXT,
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS denuncias (
                id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo_denuncia TEXT NOT NULL UNIQUE, data_denuncia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                anonimato INTEGER, denunciante_nome TEXT, denunciante_telefone TEXT, denunciante_email TEXT,
                denunciado_nome TEXT, denunciado_rua TEXT NOT NULL, denunciado_numero TEXT NOT NULL,
                denunciado_bairro TEXT NOT NULL, denunciado_municipio TEXT NOT NULL, denunciado_ponto_ref TEXT,
                denunciado_tipo_local TEXT, motivo_classificacao TEXT, motivo_descricao TEXT NOT NULL,
                anexos_path TEXT, status TEXT DEFAULT 'Recebida', despacho_fiscal TEXT,
                empresa_id INTEGER, fiscal_anexos_path TEXT,
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vistorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo_vistoria TEXT NOT NULL UNIQUE, empresa_id INTEGER,
                cpf_vinculado TEXT, tipo_vistoria TEXT, data_vistoria TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                horario_inicio TEXT, horario_termino TEXT, responsavel_estabelecimento TEXT,
                est_paredes TEXT, est_ventilacao TEXT, est_iluminacao TEXT, est_infiltracoes TEXT, est_ralos TEXT, est_sanitarios TEXT,
                hig_geral TEXT, hig_frequencia TEXT, hig_materiais TEXT, hig_equipamentos TEXT,
                pra_ausencia TEXT, pra_dedetizacao TEXT, pra_armazenamento TEXT, pra_lixeiras TEXT,
                man_higiene TEXT, man_lavagem_maos TEXT, man_armazenamento TEXT, man_separacao TEXT, man_rotulos TEXT, man_validade TEXT,
                equ_uso_exclusivo TEXT, equ_bom_estado TEXT, equ_higienizacao TEXT, equ_calibracao TEXT,
                doc_alvara TEXT, doc_manual_pops TEXT, doc_dedetizacao TEXT, doc_capacitacao TEXT, doc_fichas_controle TEXT,
                res_coleta_seletiva TEXT, res_armazenamento TEXT, res_frequencia TEXT, res_contrato_coleta TEXT,
                rt_presenca TEXT, rt_registro_conselho TEXT, rt_declaracao TEXT,
                req_consultorios TEXT, req_farmacias TEXT, req_saloes TEXT, req_industrias TEXT,
                irregularidades_encontradas TEXT, providencias_recomendadas TEXT, classificacao_vistoria TEXT,
                justificativa_classificacao TEXT, fiscal_nome TEXT, fiscal_matricula TEXT, anexos_vistoria_path TEXT,
                status_analise TEXT DEFAULT 'Pendente de Análise',
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notificacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo_notificacao TEXT NOT NULL UNIQUE, empresa_id INTEGER,
                data_notificacao DATE, data_vistoria_origem DATE, irregularidades_constatadas TEXT, prazo TEXT,
                ciencia_nome TEXT, ciencia_documento TEXT, fiscal_nome TEXT, fiscal_matricula TEXT,
                observacoes_adicionais TEXT, anexos_path TEXT, parecer_final TEXT, justificativa_parecer TEXT,
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
            );
        """)

        # Tabela de licenças públicas REESTRUTURADA
        # Tabela de licenças públicas REESTRUTURADA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licencas_publicas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocolo_licenca_publica TEXT NOT NULL UNIQUE,
                instituicao_id INTEGER NOT NULL,
                data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Dados da Unidade
                unidade_nome TEXT,
                unidade_cnes_inep TEXT,
                unidade_endereco TEXT,
                unidade_ponto_ref TEXT,
                unidade_tipo TEXT,
                unidade_tipo_outro TEXT,

                -- Responsável pela Unidade
                responsavel_unidade_nome TEXT,
                responsavel_unidade_cpf TEXT,
                responsavel_unidade_cargo TEXT,
                responsavel_unidade_conselho TEXT,
                responsavel_unidade_contato TEXT,
                responsavel_unidade_declaracao_rt_path TEXT,

                -- Atividades
                atividades_desenvolvidas TEXT,
                servicos_prestados TEXT,
                possui_cozinha TEXT,
                possui_farmacia TEXT,

                -- Anexos
                anexo_declaracao_responsavel_path TEXT,
                anexo_declaracao_rt_geral_path TEXT,

                -- Finalização
                observacoes_adicionais TEXT,
                ciencia_solicitante_nome TEXT,
                ciencia_solicitante_cargo TEXT,
                
                status TEXT DEFAULT 'Pendente',
                
                FOREIGN KEY (instituicao_id) REFERENCES empresas (id)
            );
        """)
        
        conn.commit()
        conn.close()
        print("Todas as tabelas, incluindo 'licencas_publicas', estão prontas para uso.")
    except sqlite3.Error as e:
        print(f"!!! ERRO ao inicializar o banco de dados: {e}")
