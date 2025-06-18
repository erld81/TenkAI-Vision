# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 17:53:50 2025

@author: SERGIO
"""

import gradio as gr
import pandas as pd
import zipfile
import os
import google.generativeai as genai
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
import contextlib 
import unicodedata 
import tempfile 

# Função para normalizar texto (remover acentos e cedilhas)
def normalize_text(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

# --------------------------------------------------------------------------
# AGENTE 1: PROCESSAMENTO E CARGA DE DADOS (MANTER COMO ESTÁ)
# --------------------------------------------------------------------------
def agente1_processa_zip(zip_bytes):
    with open("notas_fiscais.zip", "wb") as f:
        f.write(zip_bytes)
    with zipfile.ZipFile("notas_fiscais.zip", "r") as z:
        z.extractall("data")
        csv_files = [f for f in os.listdir("data") if f.lower().endswith('.csv')]
        if len(csv_files) != 2:
            return None, "O ZIP deve conter exatamente dois arquivos CSV."
        
        df_nf = pd.read_csv(os.path.join("data", csv_files[0]), dtype=str) 
        df_item = pd.read_csv(os.path.join("data", csv_files[1]), dtype=str) 

        df_nf.columns = [normalize_text(col.strip().upper()) for col in df_nf.columns]
        df_item.columns = [normalize_text(col.strip().upper()) for col in df_item.columns]
        
        chave_acesso_col = normalize_text('CHAVE DE ACESSO').upper() 
        
        if chave_acesso_col not in df_nf.columns or chave_acesso_col not in df_item.columns:
            return None, f"Erro: Coluna '{chave_acesso_col}' não encontrada em um dos CSVs após normalização. Verifique os nomes das colunas originais."
            
        df_nf[chave_acesso_col] = df_nf[chave_acesso_col].astype(str)
        df_item[chave_acesso_col] = df_item[chave_acesso_col].astype(str)
        
        cols_item_to_suffix = [col for col in df_item.columns if col != chave_acesso_col]
        df_item = df_item.rename(columns={col: f"{col}_ITEM" for col in cols_item_to_suffix})

        cols_nf_to_suffix = [col for col in df_nf.columns if col != chave_acesso_col]
        df_nf = df_nf.rename(columns={col: f"{col}_NF" for col in cols_nf_to_suffix})

        df = pd.merge(df_item, df_nf, on=chave_acesso_col, how="left")
        
        cols_para_converter_numerico = [
            'QUANTIDADE_ITEM', 
            'VALOR UNITARIO_ITEM', 
            'VALOR TOTAL_ITEM', 
            'VALOR NOTA FISCAL_NF' 
        ]
        
        if normalize_text('VALOR NOTA FISCAL').upper() in df.columns and normalize_text('VALOR NOTA FISCAL').upper() not in cols_para_converter_numerico:
             cols_para_converter_numerico.append(normalize_text('VALOR NOTA FISCAL').upper())

        for col in cols_para_converter_numerico:
            if col in df.columns: 
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            else:
                print(f"Aviso: Coluna '{col}' não encontrada no DataFrame final para conversão numérica.")
                    
    return df, "Dados carregados e integrados com sucesso!"

# --------------------------------------------------------------------------
# AGENTE 2: GERAÇÃO DE CÓDIGO PANDAS (PROMPT MODIFICADO - MANTER)
# --------------------------------------------------------------------------
def agente2_gera_codigo_pandas(pergunta, api_key, df):
    if df is None:
        return "Erro: DataFrame não carregado. Faça o upload do arquivo primeiro.", None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    schema = '\n'.join([f"- {c}" for c in df.columns])

    prompt = f"""
# PERSONA E OBJETIVO PRINCIPAL
Você é um assistente especialista em análise de dados com a biblioteca Pandas do Python, chamado PandasMaster.
Sua única função é traduzir uma pergunta em linguagem natural para um código Python (Pandas) que filtre e analise um DataFrame pré-existente chamado `df`.
Você NUNCA deve explicar o código. Você DEVE gerar apenas o código Python.

# CONTEXTO DO DATAFRAME `df`
O DataFrame `df` contém dados de Notas Fiscais, com cabeçalhos e itens unidos.
As colunas já estão em MAIÚSCULAS e sem acentos/cedilhas. Colunas que existiam em ambos os CSVs têm sufixos `_ITEM` (para dados do arquivo de itens) ou `_NF` (para dados do arquivo de nota fiscal). Colunas exclusivas de um arquivo não terão sufixo.
Esquema do DataFrame:
{schema}

# REGRAS DE GERAÇÃO DE CÓDIGO (MUITO IMPORTANTE)
1.  **Sempre use `df` como o nome do DataFrame.**
2.  **Filtros de Texto Case-Insensitive:** Para filtros em texto, use `.str.lower()` ou `.str.contains(case=False)`. Ex: `df['UF DESTINATARIO_NF'].str.lower() == 'rj'`
3.  **Mapeamento de Sinônimos:** Para UFs, use `isin()` para abranger sigla e nome. Ex: "São Paulo" -> `df['UF DESTINATARIO_NF'].str.lower().isin(['sp', 'sao paulo'])`
4.  **Buscas por Texto Parcial:** Para nomes de produtos ou clientes, use `.str.contains('termo', case=False, na=False)`.
5.  **Cálculos e Agregações:**
    * **Sempre atribua o resultado final a uma variável chamada `resultado_df`**.
    * Se o resultado de uma agregação (`groupby`, `sum`, `mean`, `count`, etc.) for uma `Series` do Pandas, **sempre aplique `.reset_index()` a ela para convertê-la em um DataFrame**.
    * Após `.reset_index()`, renomeie as colunas para que sejam descritivas, por exemplo, a primeira coluna para o nome do índice original (ex: 'UF') e a segunda para o nome da métrica (ex: 'Faturamento').
    * **Faturamento de Itens:** Use a coluna `VALOR TOTAL_ITEM`. Ex: `resultado_df = df.groupby('UF DESTINATARIO_NF')['VALOR TOTAL_ITEM'].sum().reset_index()`
    * **Contagem de Clientes Únicos:** Use a coluna `CNPJ DESTINATARIO_NF`. Ex: `resultado_df = df.groupby('UF DESTINATARIO_NF')['CNPJ DESTINATARIO_NF'].nunique().reset_index()`
    * **Contagem de Notas Únicas:** Use a coluna `CHAVE DE ACESSO`. Ex: `resultado_df = df['CHAVE DE ACESSO'].nunique()`
    * Sempre use os nomes EXATOS das colunas fornecidas no esquema.
6.  **Resultado Final:** **Imprima apenas a variável `resultado_df`**. Use `print(resultado_df)`.

# PERGUNTA DO USUÁRIO
{pergunta}

# CÓDIGO PYTHON (PANDAS)
"""
    
    try:
        response = model.generate_content(prompt)
        codigo_gerado = response.text.replace("```python", "").replace("```", "").strip()
        return codigo_gerado, None
    except Exception as e:
        return f"Erro ao chamar a API do Gemini: {e}", None

# --------------------------------------------------------------------------
# NOVO PASSO: EXECUTOR DE CÓDIGO SEGURO (MANTIDO)
# --------------------------------------------------------------------------
def executa_codigo_seguro(codigo, df):
    if codigo.startswith("Erro:"):
        return codigo, None, None

    output_stream = io.StringIO()
    local_vars = {'df': df, 'pd': pd}

    try:
        with contextlib.redirect_stdout(output_stream):
            exec(codigo, {"__builtins__": __builtins__}, local_vars)
        
        resultado_texto = output_stream.getvalue().strip()
        
        resultado_df = None
        if 'resultado_df' in local_vars and isinstance(local_vars['resultado_df'], pd.DataFrame):
            resultado_df = local_vars['resultado_df']
        else:
            try:
                if resultado_texto.startswith("|") or ("  " in resultado_texto and "\n" in resultado_texto):
                    temp_df = pd.read_csv(io.StringIO(resultado_texto), sep=r'\s*\|\s*|\s\s+', engine='python', skipinitialspace=True)
                    resultado_df = temp_df.dropna(axis=1, how='all')
                    if not resultado_df.empty and resultado_df.iloc[:,0].isna().all():
                        resultado_df = resultado_df.iloc[:, 1:]
                    if not resultado_df.empty and resultado_df.iloc[:,-1].isna().all():
                        resultado_df = resultado_df.iloc[:, :-1]
            except Exception as infer_e:
                print(f"Aviso: Não foi possível inferir DataFrame da saída de texto: {infer_e}")
                resultado_df = None 
                
        return resultado_texto, resultado_df, None
    
    except Exception as e:
        error_message = f"Erro ao executar o código gerado pela IA:\n\n{e}\n\nCódigo que falhou:\n{codigo}"
        return error_message, None, error_message

# --------------------------------------------------------------------------
# AGENTE 3: FORMATAÇÃO DA APRESENTAÇÃO (AJUSTADO PARA A IMAGEM)
# --------------------------------------------------------------------------
def agente3_formatar_apresentacao(resultado_texto, resultado_df, pergunta):
    img_path = None # Alterado de img_bytes para img_path
    pdf_path = None 
    final_text_output = resultado_texto 

    if resultado_df is not None and not resultado_df.empty:
        final_text_output = resultado_df.to_markdown(index=False) 
        
        if resultado_df.shape[1] >= 2: 
            try:
                plt.figure(figsize=(10, 5))
                x_col = resultado_df.columns[0]
                y_col = resultado_df.columns[1]
                y_values = pd.to_numeric(resultado_df[y_col], errors='coerce').fillna(0)
                
                plt.bar(resultado_df[x_col].astype(str), y_values)
                plt.xlabel(str(x_col))
                plt.ylabel(str(y_col))
                plt.title(pergunta, wrap=True)
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                
                # Salva a imagem em um arquivo temporário e passa o caminho
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img_file:
                    plt.savefig(tmp_img_file.name)
                    img_path = tmp_img_file.name # Armazena o caminho do arquivo
                plt.close()
            except Exception as e:
                print(f"Erro ao gerar gráfico: {e}")
                img_path = None # Garante que seja None em caso de erro

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, final_text_output.encode('latin-1', 'replace').decode('latin-1'))
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf_file: # Renomeado para evitar conflito
            pdf.output(tmp_pdf_file.name) 
            pdf_path = tmp_pdf_file.name 

    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        pdf_path = None
    
    return final_text_output, img_path, pdf_path # Retorna img_path

# --------------------------------------------------------------------------
# INTERFACE GRÁFICA GRADIO (AJUSTADO PARA A IMAGEM)
# --------------------------------------------------------------------------
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 Consultas Inteligentes de Notas Fiscais com Gemini (Arquitetura Otimizada)")

    api_key = gr.Textbox(label="Cole sua API Key do Gemini aqui", type="password")
    zipfile_input = gr.File(label="Upload do ZIP com dois CSVs das notas fiscais", type="binary")
    status = gr.Markdown("Status: Aguardando upload.")
    data_state = gr.State(None)

    def upload_and_process(zipfile_bytes):
        if zipfile_bytes is not None:
            df, msg = agente1_processa_zip(zipfile_bytes)
            return df, gr.Markdown(f"Status: {msg}")
        return None, gr.Markdown("Status: Faça upload do arquivo ZIP.")

    upload_btn = gr.Button("1. Processar ZIP")
    upload_btn.click(upload_and_process, inputs=[zipfile_input], outputs=[data_state, status])

    pergunta = gr.Textbox(label="Pergunte em português sobre os dados fiscais:", lines=2, placeholder="Ex: Qual o faturamento total por UF? Mostre os 5 maiores em uma tabela chamada resultado_df.")
    resposta_output = gr.Markdown(label="Resposta da IA")
    img_output = gr.Image(label="Gráfico gerado (se aplicável)", type="filepath") # Adicionado type="filepath"
    pdf_output = gr.File(label="Baixar resposta em PDF (resposta.pdf)", type="filepath") 

    def pipeline_completo_ia(pergunta_usuario, api_key_val, df_val):
        codigo_gerado, _ = agente2_gera_codigo_pandas(pergunta_usuario, api_key_val, df_val)
        
        resultado_texto, resultado_df, erro = executa_codigo_seguro(codigo_gerado, df_val)

        if erro:
            return gr.Markdown(erro), None, None
            
        resposta_final, img_path, pdf_path = agente3_formatar_apresentacao(resultado_texto, resultado_df, pergunta_usuario)
        
        return resposta_final, img_path, pdf_path # Retorna img_path

    consulta_btn = gr.Button("2. Consultar IA")
    consulta_btn.click(
        pipeline_completo_ia,
        inputs=[pergunta, api_key, data_state],
        outputs=[resposta_output, img_output, pdf_output]
    )
    
    gr.Examples(
        ["Qual o faturamento total por UF? Mostre os 5 maiores em uma tabela chamada resultado_df.", 
         "Quais os 10 produtos mais vendidos em quantidade? Me dê uma tabela chamada resultado_df.", 
         "Qual o valor total vendido para o cliente 'CLIENTE X'?", 
         "Mostre o faturamento mensal, se houver uma coluna de data."],
        inputs=[pergunta]
    )

demo.launch(debug=True)