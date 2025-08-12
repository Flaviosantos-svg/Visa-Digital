import sqlite3
import os

NOME_BANCO_DE_DADOS = "visa_digital.db"

def limpar_cnpjs():
    """
    Percorre a tabela de empresas e remove a pontuação de todos os CNPJs,
    garantindo um formato de dados consistente.
    """
    # Verifica se o ficheiro da base de dados existe
    if not os.path.exists(NOME_BANCO_DE_DADOS):
        print(f"ERRO: O ficheiro da base de dados '{NOME_BANCO_DE_DADOS}' não foi encontrado.")
        print("Por favor, execute a aplicação principal (app.py) primeiro para criar a base de dados.")
        return

    try:
        conn = sqlite3.connect(NOME_BANCO_DE_DADOS)
        # Permite que acessemos as linhas por nome de coluna
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("A procurar CNPJs para limpar na tabela 'empresas'...")
        cursor.execute("SELECT id, cnpj FROM empresas")
        empresas = cursor.fetchall()
        
        cnpjs_para_atualizar = []
        for empresa in empresas:
            cnpj_bruto = empresa['cnpj']
            # Remove tudo o que não for um dígito
            cnpj_limpo = "".join(filter(str.isdigit, cnpj_bruto or ""))
            
            # Se o CNPJ limpo for diferente do original, adiciona à lista para atualizar
            if cnpj_bruto != cnpj_limpo:
                cnpjs_para_atualizar.append((cnpj_limpo, empresa['id']))
                print(f"  -> CNPJ ID {empresa['id']} ({cnpj_bruto}) será limpo para {cnpj_limpo}")

        if not cnpjs_para_atualizar:
            print("Nenhum CNPJ precisou de ser limpo. A base de dados já está correta.")
        else:
            # Executa a atualização de todos os CNPJs de uma só vez
            cursor.executemany("UPDATE empresas SET cnpj = ? WHERE id = ?", cnpjs_para_atualizar)
            conn.commit()
            print(f"\n{len(cnpjs_para_atualizar)} CNPJs foram limpos e atualizados com sucesso!")

    except sqlite3.Error as e:
        print(f"ERRO ao limpar os CNPJs: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    limpar_cnpjs()
