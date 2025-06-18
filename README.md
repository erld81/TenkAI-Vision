# Consultas Inteligentes de Notas Fiscais com Gemini e Gradio

Este projeto implementa uma solução interativa para análise de dados fiscais, permitindo que usuários consultem informações de notas fiscais (em arquivos CSV zipados) usando linguagem natural. A aplicação utiliza o modelo de linguagem Gemini 1.5 Flash para gerar código Python (Pandas) que executa as consultas, e uma interface web construída com Gradio para facilitar a interação.

## Funcionalidades

-   *Processamento de Dados:* Carrega e integra dados de notas fiscais de arquivos CSV contidos em um ZIP.
-   *Geração de Código Inteligente:* Traduz perguntas em português para código Pandas, utilizando o Gemini 1.5 Flash.
-   *Execução Segura:* Executa o código Pandas gerado em um ambiente controlado.
-   *Visualização de Resultados:* Apresenta as respostas em formato textual, com gráficos (se aplicável) e em PDF para download.
-   *Interface Intuitiva:* Interface web amigável para upload de arquivos e realização de consultas.

## Pré-requisitos

Antes de começar, certifique-se de ter o Python 3.8 ou superior instalado em seu sistema. É altamente recomendável usar um ambiente virtual para gerenciar as dependências do projeto.

-   [Python 3.8+](https://www.python.org/downloads/)
-   pip (gerenciador de pacotes do Python)
-   virtualenv (recomendado para ambientes virtuais)

## Configuração do Ambiente

Siga os passos abaixo para configurar e executar o projeto:

1.  *Clone o Repositório:*

    bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DO_SEU_REPOSITORIO>
    

2.  *Crie e Ative o Ambiente Virtual:*

    bash
    python3 -m venv venv
    source venv/bin/activate  # No Linux/macOS
    # ou
    .\venv\Scripts\activate  # No Windows
    

3.  *Instale as Dependências:*

    bash
    pip install -r requirements.txt
    

4.  *Obtenha sua API Key do Google Gemini:*

    Para utilizar o modelo Gemini, você precisará de uma API Key. Siga as instruções em [Google AI Studio](https://aistudio.google.com/app/apikey) para gerar sua chave.

5.  *Configure a API Key:*

    Você pode colar sua API Key diretamente no campo da interface Gradio ao executar a aplicação, ou pode configurá-la como uma variável de ambiente. Para a segunda opção, crie um arquivo .env na raiz do projeto com o seguinte conteúdo:

    
    GOOGLE_API_KEY=SUA_API_KEY_AQUI
    

    *Nota: O código atual espera que a API Key seja inserida diretamente na interface. Se você preferir usar uma variável de ambiente, precisará ajustar o código app.py para ler de os.environ.get('GOOGLE_API_KEY').*

## Como Executar a Aplicação

Com o ambiente configurado e as dependências instaladas, execute o arquivo principal:

bash
python app.py


Após executar o comando, uma URL local (geralmente http://127.0.0.1:7860) será exibida no seu terminal. Abra esta URL em seu navegador para acessar a interface Gradio.

## Uso da Interface

1.  *Cole sua API Key do Gemini:* Insira sua chave no campo indicado.
2.  *Upload do ZIP:* Clique em "Upload do ZIP com dois CSVs das notas fiscais" e selecione seu arquivo ZIP. Este ZIP deve conter exatamente dois arquivos CSV com dados de notas fiscais e itens, e uma coluna comum para mesclagem (ex: "CHAVE DE ACESSO").
3.  *Processar ZIP:* Clique no botão "1. Processar ZIP" para carregar e integrar os dados.
4.  *Faça sua Pergunta:* No campo "Pergunte em português sobre os dados fiscais:", digite sua consulta em linguagem natural (ex: "Qual o faturamento total por UF?").
5.  *Consultar IA:* Clique no botão "2. Consultar IA" para obter a resposta.

Os resultados serão exibidos na interface, incluindo a resposta textual, um gráfico (se aplicável) e um link para download do PDF.


## Estrutura de Pastas do Projeto

```
TenkAI-Vision/
├── app.py
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```


## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.


