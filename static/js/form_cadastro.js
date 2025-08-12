// static/js/form_cadastro.js

document.addEventListener('DOMContentLoaded', function() {
    // 1. Pega os elementos do formulário pelo ID
    const cnpjInput = document.getElementById('cnpj');
    const cnpjStatus = document.getElementById('cnpj-status');
    const razaoSocialInput = document.getElementById('razao_social');
    const nomeFantasiaInput = document.getElementById('nome_fantasia');
    const porteInput = document.getElementById('porte');
    const dataAberturaInput = document.getElementById('data_abertura');
    const situacaoCadastralInput = document.getElementById('situacao_cadastral');
    const cnaePrincipalInput = document.getElementById('cnae_principal');
    const cnaeSecundarioInput = document.getElementById('cnae_secundario');
    const enderecoInput = document.getElementById('endereco');
    const telefoneInput = document.getElementById('telefone_empresa'); // Verifique se o ID no HTML é este

    // 2. Adiciona um "escutador" que dispara quando o usuário tira o foco do campo CNPJ
    cnpjInput.addEventListener('blur', function() {
        const cnpj = cnpjInput.value.replace(/\D/g, ''); // Limpa o CNPJ, deixando só números

        // Verifica se o CNPJ tem o tamanho correto
        if (cnpj.length !== 14) {
            cnpjStatus.textContent = 'CNPJ inválido.';
            cnpjStatus.className = 'form-text text-danger';
            return;
        }

        // Mostra uma mensagem de "carregando"
        cnpjStatus.textContent = 'Buscando dados do CNPJ...';
        cnpjStatus.className = 'form-text text-info';

        // 3. Faz a chamada à API (usando a BrasilAPI como exemplo, que é gratuita)
        fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('CNPJ não encontrado ou API fora do ar.');
                }
                return response.json();
            })
            .then(data => {
                // 'data' AQUI É A NOSSA VARIÁVEL 'dadosDaApi'
                // Ela só existe DENTRO deste bloco, após a API responder com sucesso.

                // 4. Preenche os campos do formulário com os dados recebidos
                cnpjStatus.textContent = 'CNPJ encontrado e dados preenchidos.';
                cnpjStatus.className = 'form-text text-success';

                razaoSocialInput.value = data.razao_social || '';
                nomeFantasiaInput.value = data.nome_fantasia || '';
                porteInput.value = data.porte || '';
                dataAberturaInput.value = data.data_inicio_atividade || '';
                situacaoCadastralInput.value = data.descricao_situacao_cadastral || '';
                
                // Preenche o endereço completo
                enderecoInput.value = `${data.logradouro || ''}, ${data.numero || ''} - ${data.bairro || ''}, ${data.municipio || ''}/${data.uf || ''}`;
                
                // Preenche o telefone (se a API retornar)
                telefoneInput.value = data.ddd_telefone_1 || '';
                
                // Preenche o CNAE principal
                if (data.cnae_fiscal_descricao) {
                    cnaePrincipalInput.value = `${data.cnae_fiscal} - ${data.cnae_fiscal_descricao}`;
                }
                
                // Preenche os CNAEs secundários
                if (data.cnaes_secundarios && data.cnaes_secundarios.length > 0) {
                    const cnaesSecundariosTexto = data.cnaes_secundarios
                        .map(cnae => `${cnae.codigo} - ${cnae.descricao}`)
                        .join('\n');
                    cnaeSecundarioInput.value = cnaesSecundariosTexto;
                } else {
                    cnaeSecundarioInput.value = 'Nenhum CNAE secundário informado.';
                }
            })
            .catch(error => {
                // 5. Se der algum erro na API, mostra uma mensagem de falha
                console.error('Erro ao buscar CNPJ:', error);
                cnpjStatus.textContent = 'Erro ao buscar CNPJ. Verifique o número e tente novamente.';
                cnpjStatus.className = 'form-text text-danger';
            });
    });
});