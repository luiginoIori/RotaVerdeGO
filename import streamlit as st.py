import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os
import json

# Configuração da página
st.set_page_config(
    page_title="Fluxo de Caixa - Rota Verde",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

class FluxoCaixaApp:
    def __init__(self):
        self.arquivo_excel = "Previsão de fluxo de caixa projetado até dezembro_2025.xlsx"
        self.arquivo_json = "dados_fluxo_caixa.json"
        self.pasta_uploads = "uploads"
        self.dados = None
        self.dados_originais = None
        
        # Cria pasta uploads se não existir
        if not os.path.exists(self.pasta_uploads):
            os.makedirs(self.pasta_uploads)
        
    def salvar_dados_json(self):
        """Salva os dados em formato JSON incluindo renegociação e prioridade"""
        if self.dados is not None:
            # Converte datas para string para serialização JSON
            dados_json = self.dados.copy()
            for col in dados_json.columns:
                if pd.api.types.is_datetime64_any_dtype(dados_json[col]):
                    dados_json[col] = dados_json[col].dt.strftime('%Y-%m-%d')
                elif col in ['Data Renegociacao'] and dados_json[col].notna().any():
                    dados_json[col] = pd.to_datetime(dados_json[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Preenche valores NaN com None para JSON
            dados_json = dados_json.where(pd.notnull(dados_json), None)
            
            # Converte para dicionário e salva
            dados_dict = dados_json.to_dict('records')
            with open(self.arquivo_json, 'w', encoding='utf-8') as f:
                json.dump(dados_dict, f, ensure_ascii=False, indent=2)
            return True
        return False
    
    def listar_arquivos_uploads(self):
        """Lista arquivos Excel na pasta uploads"""
        arquivos_excel = []
        if os.path.exists(self.pasta_uploads):
            for arquivo in os.listdir(self.pasta_uploads):
                if arquivo.lower().endswith(('.xlsx', '.xls')):
                    arquivos_excel.append(arquivo)
        return sorted(arquivos_excel)
    
    def salvar_arquivo_upload(self, arquivo_uploadado):
        """Salva arquivo enviado na pasta uploads"""
        try:
            caminho_arquivo = os.path.join(self.pasta_uploads, arquivo_uploadado.name)
            with open(caminho_arquivo, "wb") as f:
                f.write(arquivo_uploadado.getbuffer())
            return True, caminho_arquivo
        except Exception as e:
            return False, str(e)
    
    def carregar_dados_json(self):
        """Carrega os dados salvos do arquivo JSON"""
        if os.path.exists(self.arquivo_json):
            try:
                with open(self.arquivo_json, 'r', encoding='utf-8') as f:
                    dados_dict = json.load(f)
                
                df = pd.DataFrame(dados_dict)
                # Converte datas de volta
                if 'Vencto Real' in df.columns:
                    df['Vencto Real'] = pd.to_datetime(df['Vencto Real'])
                if 'Data Renegociacao' in df.columns:
                    df['Data Renegociacao'] = pd.to_datetime(df['Data Renegociacao'], errors='coerce')
                
                return df
            except Exception as e:
                st.error(f"Erro ao carregar dados JSON: {e}")
                return None
        return None
        
    def gerar_chave_unica(self, row):
        """Gera uma chave única para identificar um registro baseada em campos principais"""
        # Usa combinação de campos que identificam unicamente um registro
        filial = str(row.get('Filial', ''))
        titulo = str(row.get('No. Titulo', ''))
        parcela = str(row.get('Parcela', ''))
        fornecedor = str(row.get('Fornecedor', ''))
        vencto = str(row.get('Vencto Real', ''))
        return f"{filial}|{titulo}|{parcela}|{fornecedor}|{vencto}"
        
    def gerar_chave_vencto_razao(self, row):
        """Gera chave baseada em Vencto Real e Razão Social"""
        vencto = str(row.get('Vencto Real', ''))
        razao = str(row.get('Razão Social', ''))
        return f"{vencto}|{razao}"
        
    def atualizar_campos_renegociacao_prioridade(self, dados_excel, dados_json):
        """Atualiza apenas os campos Data Renegociacao e Prioridade dos registros existentes no JSON"""
        if dados_json is None or len(dados_json) == 0:
            st.warning("⚠️ JSON não existe. Carregando dados do Excel pela primeira vez.")
            return dados_excel
            
        # Cria dicionário com registros do Excel usando chave Vencto Real + Razão Social
        registros_excel = {}
        for _, row in dados_excel.iterrows():
            chave = self.gerar_chave_vencto_razao(row)
            registros_excel[chave] = row
        
        # Atualiza registros no JSON com dados do Excel (apenas Data Renegociacao e Prioridade)
        dados_atualizados = dados_json.copy()
        registros_atualizados = 0
        registros_encontrados = 0
        
        for idx, row_json in dados_atualizados.iterrows():
            chave = self.gerar_chave_vencto_razao(row_json)
            
            if chave in registros_excel:
                registros_encontrados += 1
                row_excel = registros_excel[chave]
                
                # Verifica e atualiza Data Renegociacao
                data_renegoc_excel = row_excel.get('Data Renegociacao')
                if pd.notna(data_renegoc_excel) and str(data_renegoc_excel) != str(row_json.get('Data Renegociacao')):
                    dados_atualizados.at[idx, 'Data Renegociacao'] = data_renegoc_excel
                    registros_atualizados += 1
                
                # Verifica e atualiza Prioridade
                prioridade_excel = row_excel.get('Prioridade')
                if pd.notna(prioridade_excel) and str(prioridade_excel) != str(row_json.get('Prioridade')):
                    dados_atualizados.at[idx, 'Prioridade'] = prioridade_excel
                    if registros_atualizados == 0:  # Só conta se não foi contado pela data
                        registros_atualizados += 1
        
        if registros_atualizados > 0:
            st.success(f"� Atualizados {registros_atualizados} registros com novos dados de renegociação/prioridade")
        else:
            st.info(f"✅ Todos os {registros_encontrados} registros já estão atualizados")
            
        return dados_atualizados
        
    def comparar_alteracoes_renegociacao(self, dados_excel, dados_json):
        """Compara dados focando em alterações de renegociação e prioridade"""
        alteracoes_encontradas = []
        
        if dados_json is None or len(dados_json) == 0:
            st.warning("⚠️ Arquivo JSON não existe ou está vazio. Não há dados para comparar.")
            return []
        
        # Cria dicionário com registros do JSON usando chave Vencto Real + Razão Social
        registros_json = {}
        for _, row in dados_json.iterrows():
            chave = self.gerar_chave_vencto_razao(row)
            registros_json[chave] = row
        
        # Compara com registros do Excel
        registros_comparados = 0
        for _, row_excel in dados_excel.iterrows():
            chave = self.gerar_chave_vencto_razao(row_excel)
            
            if chave in registros_json:
                registros_comparados += 1
                row_json = registros_json[chave]
                
                # Verifica se houve alteração em Data Renegociacao ou Prioridade
                alteracao_detectada = False
                alteracao_info = {
                    'Vencto Real': row_excel.get('Vencto Real'),
                    'Razão Social': row_excel.get('Razão Social'),
                    'alteracoes': []
                }
                
                # Compara Data Renegociacao
                data_renegoc_excel = row_excel.get('Data Renegociacao')
                data_renegoc_json = row_json.get('Data Renegociacao')
                
                if str(data_renegoc_excel) != str(data_renegoc_json):
                    alteracao_detectada = True
                    alteracao_info['alteracoes'].append({
                        'campo': 'Data Renegociacao',
                        'valor_anterior': str(data_renegoc_json),
                        'valor_novo': str(data_renegoc_excel)
                    })
                    alteracao_info['Data Renegociacao'] = data_renegoc_excel
                else:
                    alteracao_info['Data Renegociacao'] = data_renegoc_json
                
                # Compara Prioridade
                prioridade_excel = row_excel.get('Prioridade')
                prioridade_json = row_json.get('Prioridade')
                
                if str(prioridade_excel) != str(prioridade_json):
                    alteracao_detectada = True
                    alteracao_info['alteracoes'].append({
                        'campo': 'Prioridade',
                        'valor_anterior': str(prioridade_json),
                        'valor_novo': str(prioridade_excel)
                    })
                    alteracao_info['Prioridade'] = prioridade_excel
                else:
                    alteracao_info['Prioridade'] = prioridade_json
                
                # Adiciona outros campos importantes
                for campo in ['Filial', 'No. Titulo', 'Parcela', 'Fornecedor', 'Valor']:
                    if campo in row_excel:
                        alteracao_info[campo] = row_excel[campo]
                
                if alteracao_detectada:
                    alteracoes_encontradas.append(alteracao_info)
        
        st.info(f"📊 Comparados {registros_comparados} registros usando Vencto Real + Razão Social")
        
        if alteracoes_encontradas:
            st.success(f"🔍 Encontradas {len(alteracoes_encontradas)} alterações em Data Renegociacao/Prioridade")
        else:
            st.info("✅ Nenhuma alteração detectada nos campos de renegociação/prioridade")
            
        return alteracoes_encontradas
        
    def salvar_alteracoes_json(self, alteracoes):
        """Salva alterações em arquivo JSON separado"""
        if not alteracoes:
            return False
            
        arquivo_alteracoes = "alteracoes_renegociacao_prioridade.json"
        
        # Prepara dados para serialização JSON
        dados_para_salvar = []
        for alteracao in alteracoes:
            item = alteracao.copy()
            # Converte datas para string
            if 'Vencto Real' in item and pd.notna(item['Vencto Real']):
                if hasattr(item['Vencto Real'], 'strftime'):
                    item['Vencto Real'] = item['Vencto Real'].strftime('%Y-%m-%d')
            if 'Data Renegociacao' in item and pd.notna(item['Data Renegociacao']):
                if hasattr(item['Data Renegociacao'], 'strftime'):
                    item['Data Renegociacao'] = item['Data Renegociacao'].strftime('%Y-%m-%d')
            # Adiciona timestamp da análise
            item['timestamp_analise'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dados_para_salvar.append(item)
        
        try:
            with open(arquivo_alteracoes, 'w', encoding='utf-8') as f:
                json.dump(dados_para_salvar, f, ensure_ascii=False, indent=2)
            
            st.success(f"💾 Alterações salvas em: {arquivo_alteracoes}")
            return True
        except Exception as e:
            st.error(f"❌ Erro ao salvar alterações: {e}")
            return False
        
    @st.cache_data
    def carregar_dados_excel(_self, arquivo_especifico=None):
        """Carrega os dados do arquivo Excel (padrão ou específico)"""
        try:
            arquivo_para_usar = arquivo_especifico or _self.arquivo_excel
            
            # Se arquivo está na pasta uploads, usa caminho completo
            if arquivo_especifico and not os.path.exists(arquivo_especifico):
                caminho_uploads = os.path.join(_self.pasta_uploads, arquivo_especifico)
                if os.path.exists(caminho_uploads):
                    arquivo_para_usar = caminho_uploads
            
            xl = pd.ExcelFile(arquivo_para_usar)
            
            if 'Analítico' in xl.sheet_names:
                dados = pd.read_excel(arquivo_para_usar, sheet_name='Analítico', header=0)
            else:
                dados = pd.read_excel(arquivo_para_usar, header=0)
            
            # Converte a coluna de data
            if 'Vencto Real' in dados.columns:
                dados['Vencto Real'] = pd.to_datetime(dados['Vencto Real'], errors='coerce')
            
            # Adiciona colunas de renegociação e prioridade se não existirem
            if 'Data Renegociacao' not in dados.columns:
                dados['Data Renegociacao'] = pd.NaT
            if 'Prioridade' not in dados.columns:
                dados['Prioridade'] = None
            if 'Sub_Total' not in dados.columns:
                dados['Sub_Total'] = 0.0
                
            return dados, xl.sheet_names
            
        except Exception as e:
            return None, str(e)
    
    def inicializar_dados(self):
        """Inicializa os dados fazendo merge incremental entre Excel e JSON"""
        try:
            # Sempre tenta carregar do Excel para verificar novos dados
            dados_excel, msg_excel = self.carregar_dados_excel()
            
            if dados_excel is None:
                return False, f"Erro ao carregar Excel: {msg_excel}"
                
            # Tenta carregar dados existentes do JSON
            dados_json = self.carregar_dados_json()
            
            # Nota: Análise de alterações disponível em página separada
            
            # Atualiza apenas campos de renegociação e prioridade (sem adicionar novos registros)
            self.dados = self.atualizar_campos_renegociacao_prioridade(dados_excel, dados_json)
            self.dados_originais = self.dados.copy()
            
            # Remove linhas com datas inválidas
            self.dados = self.dados.dropna(subset=['Vencto Real'])
            
            # Ordena por prioridade e data de renegociação
            self.ordenar_por_prioridade_e_renegociacao()
            
            # Salva automaticamente em JSON (apenas se houver novos dados)
            self.salvar_dados_json()
            
            return True, f"Dados sincronizados. Total: {len(self.dados)} registros"
            
        except Exception as e:
            st.error(f"❌ Erro durante inicialização: {str(e)}")
            return False, f"Erro durante inicialização: {str(e)}"
    
    def calcular_subtotal(self):
        """Calcula o subtotal acumulativo dos valores"""
        if self.dados is None:
            return
            
        # Calcula o subtotal acumulativo
        self.dados['Sub_Total'] = self.dados['Valor'].cumsum()
    
    def obter_data_efetiva(self, row):
        """Retorna a data efetiva (renegociação se preenchida, senão vencimento real)"""
        if pd.notna(row['Data Renegociacao']):
            return row['Data Renegociacao']
        return row['Vencto Real']
    
    def formatar_valor_brasileiro(self, valor):
        """Formata valor com 2 casas decimais sem símbolo monetário"""
        if pd.isna(valor):
            return "0,00"
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def obter_cor_prioridade(self, prioridade):
        """Retorna a cor baseada na prioridade"""
        cores = {
            1: '#FF0000',  # Vermelho
            2: '#FF8000',  # Laranja
            3: '#FFFF00',  # Amarelo
            4: '#80FF00',  # Verde claro
            5: '#ADD8E6'   # Azul claro
        }
        return cores.get(prioridade, '#FFFFFF')  # Branco por padrão
    
    def ordenar_por_prioridade_e_renegociacao(self):
        """Ordena os dados por prioridade e depois por data de renegociação/data efetiva"""
        if self.dados is None:
            return
            
        # Cria coluna temporária com data efetiva
        self.dados['Data Efetiva'] = self.dados.apply(self.obter_data_efetiva, axis=1)
        
        # Cria coluna auxiliar para prioridade (None vira 999 para ficar por último)
        self.dados['Prioridade_Sort'] = self.dados['Prioridade'].fillna(999)
        
        # Ordena por: 1º Prioridade, 2º Data de Renegociação (se existe), 3º Data Efetiva
        self.dados = self.dados.sort_values([
            'Prioridade_Sort', 
            'Data Renegociacao', 
            'Data Efetiva'
        ], na_position='last').reset_index(drop=True)
        
        # Remove colunas temporárias
        self.dados = self.dados.drop(['Data Efetiva', 'Prioridade_Sort'], axis=1)
        
        # Recalcula o subtotal após ordenação
        self.calcular_subtotal()
    
    def ordenar_por_data_efetiva(self):
        """Mantém compatibilidade - chama a nova função de ordenação"""
        self.ordenar_por_prioridade_e_renegociacao()
    
    def gerar_html_fluxo_caixa(self, dados_para_exibir=None):
        """Gera HTML para visualização do fluxo de caixa no Streamlit"""
        if self.dados is None:
            return "<p>Nenhum dado disponível</p>"
        
        # Usa dados específicos ou todos os dados
        dados_html = dados_para_exibir.copy() if dados_para_exibir is not None else self.dados.copy()
        
        # Adiciona data efetiva se não existir
        if 'Data Efetiva' not in dados_html.columns:
            dados_html['Data Efetiva'] = dados_html.apply(self.obter_data_efetiva, axis=1)
        
        # Cria coluna auxiliar para prioridade (None vira 999 para ficar por último)
        dados_html['Prioridade_Sort'] = dados_html['Prioridade'].fillna(999)
        
        # Ordena por: 1º Prioridade, 2º Data de Renegociação, 3º Data Efetiva
        dados_html = dados_html.sort_values([
            'Prioridade_Sort',
            'Data Renegociacao', 
            'Data Efetiva'
        ], na_position='last').reset_index(drop=True)
        
        # Remove coluna auxiliar
        dados_html = dados_html.drop('Prioridade_Sort', axis=1)
        
        # Recalcula subtotal
        dados_html['Sub_Total'] = dados_html['Valor'].cumsum()
        
        # CSS embutido para o HTML
        css_style = """
        <style>
        .fluxo-container {
            font-family: Arial, sans-serif;
            max-width: 100%;
            margin: 0;
        }
        .prioridade-section {
            margin-bottom: 20px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #ddd;
        }
        .prioridade-header {
            padding: 10px 15px;
            font-weight: bold;
            font-size: 16px;
            color: white;
            margin: 0;
        }
        .prioridade-1 { background-color: #FF0000; }
        .prioridade-2 { background-color: #FF8000; }
        .prioridade-3 { background-color: #FFFF00; color: #000; }
        .prioridade-4 { background-color: #80FF00; color: #000; }
        .prioridade-5 { background-color: #ADD8E6; color: #000; }
        .sem-prioridade { background-color: #6c757d; }
        
        .fluxo-table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            font-size: 12px;
        }
        .fluxo-table th, .fluxo-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .fluxo-table th {
            background-color: #f8f9fa;
            font-weight: bold;
            font-size: 11px;
        }
        .fluxo-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .fluxo-table tr:hover {
            background-color: #f0f0f0;
        }
        .valor-col {
            text-align: right;
            font-family: 'Courier New', monospace;
            font-size: 11px;
        }
        .data-col {
            font-family: 'Courier New', monospace;
            font-size: 11px;
        }
        .renegociada-row {
            background-color: #fff3cd !important;
        }
        .total-row {
            background-color: #e9ecef !important;
            font-weight: bold;
        }
        .empresa-col {
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .historico-col {
            max-width: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 10px;
        }
        .situacao-col {
            text-align: center;
            font-weight: bold;
            font-size: 11px;
        }
        .situacao-pg {
            background-color: #d4edda;
            color: #155724;
        }
        .situacao-npg {
            background-color: #f8d7da;
            color: #721c24;
        }
        .descricao-col {
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 10px;
            font-style: italic;
        }
        </style>
        """
        
        # Agrupa por prioridade
        prioridades = {
            1: "Prioridade 1 - Urgente",
            2: "Prioridade 2 - Alta", 
            3: "Prioridade 3 - Média",
            4: "Prioridade 4 - Baixa",
            5: "Prioridade 5 - Muito Baixa",
            None: "Sem Prioridade"
        }
        
        # Início do HTML
        html_content = css_style + '<div class="fluxo-container">'
        
        for prioridade in [1, 2, 3, 4, 5, None]:
            if prioridade is None:
                dados_prioridade = dados_html[dados_html['Prioridade'].isna()]
            else:
                dados_prioridade = dados_html[dados_html['Prioridade'] == prioridade]
            
            if len(dados_prioridade) == 0:
                continue
                
            # Cabeçalho da seção
            classe_prioridade = f"prioridade-{prioridade}" if prioridade else "sem-prioridade"
            html_content += f'<div class="prioridade-section">'
            html_content += f'<div class="prioridade-header {classe_prioridade}">'
            html_content += f'{prioridades[prioridade]} ({len(dados_prioridade)} registros)'
            html_content += f'</div>'
            
            # Tabela
            html_content += '<table class="fluxo-table">'
            html_content += '<thead><tr>'
            html_content += '<th>Empresa</th>'
            html_content += '<th>Vencto Real</th>'
            html_content += '<th>Data Reneg.</th>'
            html_content += '<th>Data Efetiva</th>'
            html_content += '<th>Valor</th>'
            html_content += '<th>Subtotal</th>'
            html_content += '<th>Situação</th>'
            html_content += '<th>Descrição</th>'
            html_content += '<th>Histórico</th>'
            html_content += '</tr></thead><tbody>'
            
            # Ordena dentro da prioridade por data de renegociação primeiro
            dados_prioridade = dados_prioridade.sort_values([
                'Data Renegociacao', 
                'Data Efetiva'
            ], na_position='last').reset_index(drop=True)
            
            # Recalcula subtotal para este grupo
            dados_prioridade['Sub_Total_Grupo'] = dados_prioridade['Valor'].cumsum()
            
            for idx, row in dados_prioridade.iterrows():
                # Verifica se foi renegociada
                foi_renegociada = pd.notna(row['Data Renegociacao'])
                classe_row = "renegociada-row" if foi_renegociada else ""
                
                # Formata valores
                valor_formatado = self.formatar_valor_brasileiro(row['Valor'])
                subtotal_formatado = self.formatar_valor_brasileiro(row['Sub_Total_Grupo'])
                
                # Formata datas
                data_original = row['Vencto Real'].strftime('%Y-%m-%d')
                data_renegociacao = row['Data Renegociacao'].strftime('%Y-%m-%d') if foi_renegociada else "-"
                data_efetiva = row['Data Efetiva'].strftime('%Y-%m-%d')
                
                # Trunca texto longo
                empresa = row['Razão Social'][:30] + "..." if len(row['Razão Social']) > 30 else row['Razão Social']
                historico = row['Historico'][:25] + "..." if len(str(row['Historico'])) > 25 else str(row['Historico'])
                
                # Processa situação
                situacao = row.get('Situacao', None) if 'Situacao' in row else None
                if situacao == 'PG':
                    situacao_texto = '✅ PG'
                    situacao_classe = 'situacao-pg'
                elif situacao == 'N_PG':
                    situacao_texto = '❌ N_PG'
                    situacao_classe = 'situacao-npg'
                else:
                    situacao_texto = '-'
                    situacao_classe = ''
                
                html_content += f'<tr class="{classe_row}">'
                # Processa descrição da negociação
                descricao = row.get('Descricao_Negociacao', '') if 'Descricao_Negociacao' in row else ''
                descricao_texto = str(descricao)[:50] + "..." if len(str(descricao)) > 50 else str(descricao) if descricao else "-"
                
                html_content += f'<td class="empresa-col">{empresa}</td>'
                html_content += f'<td class="data-col">{data_original}</td>'
                html_content += f'<td class="data-col">{data_renegociacao}</td>'
                html_content += f'<td class="data-col"><strong>{data_efetiva}</strong></td>'
                html_content += f'<td class="valor-col">{valor_formatado}</td>'
                html_content += f'<td class="valor-col"><strong>{subtotal_formatado}</strong></td>'
                html_content += f'<td class="situacao-col {situacao_classe}">{situacao_texto}</td>'
                html_content += f'<td class="descricao-col" title="{descricao}">{descricao_texto}</td>'
                html_content += f'<td class="historico-col">{historico}</td>'
                html_content += '</tr>'
            
            # Total da seção
            total_prioridade = dados_prioridade['Valor'].sum()
            total_formatado = self.formatar_valor_brasileiro(total_prioridade)
            
            html_content += '<tr class="total-row">'
            html_content += f'<td colspan="4">Total {prioridades[prioridade]}</td>'
            html_content += f'<td class="valor-col">{total_formatado}</td>'
            html_content += '<td colspan="4"></td>'
            html_content += '</tr>'
            
            html_content += '</tbody></table></div>'

        # Total geral
        total_geral = dados_html['Valor'].sum()
        total_geral_formatado = self.formatar_valor_brasileiro(total_geral)
        
        html_content += f'<div style="text-align: center; font-size: 18px; font-weight: bold; margin-top: 15px; padding: 10px; background-color: #e9ecef; border-radius: 5px;">'
        html_content += f'Total Geral: {total_geral_formatado}'
        html_content += '</div>'
        
        html_content += '</div>'
        
        return html_content
    
    def listar_arquivos_extratos(self):
        """Lista todos os arquivos na pasta extratos"""
        pasta_extratos = "extratos"
        if not os.path.exists(pasta_extratos):
            os.makedirs(pasta_extratos)
            return []
        
        arquivos = []
        for arquivo in os.listdir(pasta_extratos):
            caminho_completo = os.path.join(pasta_extratos, arquivo)
            if os.path.isfile(caminho_completo) and arquivo.lower().endswith(('.xlsx', '.xls')):
                arquivos.append(arquivo)
        
        return sorted(arquivos)
    
    def verificar_arquivo_bradesco(self, caminho_arquivo):
        """Verifica se o arquivo contém a palavra 'bradesco' (case insensitive)"""
        nome_arquivo = os.path.basename(caminho_arquivo).lower()
        return 'bradesco' in nome_arquivo
    
    def processar_extrato_bradesco(self, caminho_arquivo):
        """Processa um extrato do Bradesco seguindo as regras específicas"""
        try:
            # Lê o arquivo Excel
            df = pd.read_excel(caminho_arquivo, header=None)
            
            # Procura pela linha que contém 'Total' para definir o fim
            linha_final = None
            for idx, row in df.iterrows():
                if any('total' in str(cell).lower() for cell in row if pd.notna(cell)):
                    linha_final = idx
                    break
            
            if linha_final is None:
                linha_final = len(df)
            
            # Lê a partir da linha 10 (índice 9) até a linha com 'Total'
            # Seleciona apenas as primeiras 5 colunas
            dados_extratos = df.iloc[9:linha_final, :5].copy()
            
            # Define os nomes das colunas
            dados_extratos.columns = ['Data', 'Lancamento', 'Dcto', 'Credito', 'Debito']
            
            # Remove linhas vazias
            dados_extratos = dados_extratos.dropna(how='all')
            
            # Converte a coluna Data
            dados_extratos['Data'] = pd.to_datetime(dados_extratos['Data'], errors='coerce')
            
            # Converte colunas de valores para números com 2 casas decimais
            for coluna in ['Credito', 'Debito']:
                if coluna in dados_extratos.columns:
                    # Remove caracteres não numéricos e converte
                    dados_extratos[coluna] = dados_extratos[coluna].astype(str)
                    dados_extratos[coluna] = dados_extratos[coluna].str.replace('[^0-9.,\\-]', '', regex=True)
                    dados_extratos[coluna] = dados_extratos[coluna].str.replace(',', '.')
                    dados_extratos[coluna] = pd.to_numeric(dados_extratos[coluna], errors='coerce').fillna(0)
                    dados_extratos[coluna] = dados_extratos[coluna].round(2)
            
            # Calcula o saldo
            dados_extratos['Saldo'] = (dados_extratos['Credito'] - dados_extratos['Debito']).cumsum().round(2)
            
            # Remove linhas com data inválida
            dados_extratos = dados_extratos.dropna(subset=['Data'])
            
            return dados_extratos, None
            
        except Exception as e:
            return None, f"Erro ao processar arquivo {os.path.basename(caminho_arquivo)}: {str(e)}"
    
    def processar_todos_extratos(self):
        """Processa todos os extratos da pasta extratos"""
        arquivos = self.listar_arquivos_extratos()
        
        if not arquivos:
            return None, "Nenhum arquivo encontrado na pasta extratos"
        
        extratos_processados = []
        erros = []
        
        for arquivo in arquivos:
            caminho_completo = os.path.join("extratos", arquivo)
            
            if self.verificar_arquivo_bradesco(caminho_completo):
                dados, erro = self.processar_extrato_bradesco(caminho_completo)
                
                if dados is not None:
                    dados['Arquivo_Origem'] = arquivo
                    extratos_processados.append(dados)
                else:
                    erros.append(erro)
            else:
                st.info(f"📄 Arquivo {arquivo} não contém 'bradesco' no nome - ignorado")
        
        if extratos_processados:
            # Combina todos os extratos
            df_combinado = pd.concat(extratos_processados, ignore_index=True)
            df_combinado = df_combinado.sort_values('Data').reset_index(drop=True)
            
            return df_combinado, erros
        else:
            return None, "Nenhum extrato do Bradesco foi processado com sucesso"
    
    def gerar_html_extratos(self, dados_extratos):
        """Gera HTML para visualização dos extratos bancários"""
        if dados_extratos is None or len(dados_extratos) == 0:
            return "<p>Nenhum dado de extrato disponível</p>"
        
        # Pega o último saldo como saldo final
        saldo_final = dados_extratos['Saldo'].iloc[-1] if len(dados_extratos) > 0 else 0
        
        # CSS para estilização da tabela
        css_style = """
        <style>
            .extrato-table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }
            .extrato-table th, .extrato-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .extrato-table th {
                background-color: #1f77b4;
                color: white;
                font-weight: bold;
                text-align: center;
            }
            .extrato-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .extrato-table tr:hover {
                background-color: #f5f5f5;
            }
            .credito {
                color: #28a745;
                font-weight: bold;
            }
            .debito {
                color: #dc3545;
                font-weight: bold;
            }
            .saldo-positivo {
                color: #28a745;
                font-weight: bold;
            }
            .saldo-negativo {
                color: #dc3545;
                font-weight: bold;
            }
            .data-col {
                text-align: center;
                width: 100px;
            }
            .valor-col {
                text-align: right;
                width: 120px;
            }
            .lancamento-col {
                max-width: 300px;
            }
            .saldo-final {
                background-color: #e9ecef;
                border: 2px solid #007bff;
                padding: 15px;
                margin: 15px 0;
                border-radius: 5px;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
            }
        </style>
        """
        
        # Constrói o HTML da tabela
        html_content = css_style
        html_content += '<div class="saldo-final">'
        html_content += f'💰 <strong>Saldo Final: R$ {saldo_final:,.2f}</strong>'
        html_content += '</div>'
        
        html_content += '<table class="extrato-table">'
        html_content += '''
        <thead>
            <tr>
                <th class="data-col">Data</th>
                <th class="lancamento-col">Lançamento</th>
                <th>Dcto</th>
                <th class="valor-col">Crédito</th>
                <th class="valor-col">Débito</th>
                <th class="valor-col">Saldo</th>
                <th>Arquivo</th>
            </tr>
        </thead>
        <tbody>
        '''
        
        # Adiciona linhas da tabela
        for idx, row in dados_extratos.iterrows():
            data_formatada = row['Data'].strftime('%d/%m/%Y') if pd.notna(row['Data']) else ''
            lancamento = str(row['Lancamento']) if pd.notna(row['Lancamento']) else ''
            dcto = str(row['Dcto']) if pd.notna(row['Dcto']) else ''
            
            # Formata valores
            credito = row['Credito'] if pd.notna(row['Credito']) else 0
            debito = row['Debito'] if pd.notna(row['Debito']) else 0
            saldo = row['Saldo'] if pd.notna(row['Saldo']) else 0
            
            credito_formatado = f"R$ {credito:,.2f}" if credito > 0 else ""
            debito_formatado = f"R$ {debito:,.2f}" if debito > 0 else ""
            
            # Define classe CSS para o saldo
            saldo_classe = "saldo-positivo" if saldo >= 0 else "saldo-negativo"
            saldo_formatado = f"R$ {saldo:,.2f}"
            
            arquivo_origem = row['Arquivo_Origem'] if 'Arquivo_Origem' in row and pd.notna(row['Arquivo_Origem']) else ''
            
            html_content += f'''
            <tr>
                <td class="data-col">{data_formatada}</td>
                <td class="lancamento-col">{lancamento}</td>
                <td>{dcto}</td>
                <td class="valor-col credito">{credito_formatado}</td>
                <td class="valor-col debito">{debito_formatado}</td>
                <td class="valor-col {saldo_classe}">{saldo_formatado}</td>
                <td>{arquivo_origem}</td>
            </tr>
            '''
        
        html_content += '</tbody></table>'
        
        return html_content
    
    def salvar_saldos_bancarios(self, saldo_bradesco, saldo_bb, saldo_reag):
        """Salva os saldos dos bancos em arquivo JSON"""
        try:
            saldos = {
                "ultima_atualizacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "saldos": {
                    "bradesco": float(saldo_bradesco) if saldo_bradesco else 0.0,
                    "banco_brasil": float(saldo_bb) if saldo_bb else 0.0,
                    "reag": float(saldo_reag) if saldo_reag else 0.0
                },
                "total": float(saldo_bradesco or 0) + float(saldo_bb or 0) + float(saldo_reag or 0)
            }
            
            with open('saldos_bancarios.json', 'w', encoding='utf-8') as f:
                json.dump(saldos, f, ensure_ascii=False, indent=2)
            
            return True, "Saldos salvos com sucesso!"
        except Exception as e:
            return False, f"Erro ao salvar saldos: {str(e)}"
    
    def carregar_saldos_bancarios(self):
        """Carrega os saldos dos bancos do arquivo JSON"""
        try:
            if os.path.exists('saldos_bancarios.json'):
                with open('saldos_bancarios.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Retorna estrutura padrão se arquivo não existe
            return {
                "ultima_atualizacao": None,
                "saldos": {
                    "bradesco": 0.0,
                    "banco_brasil": 0.0,
                    "reag": 0.0
                },
                "total": 0.0
            }
        except Exception as e:
            st.error(f"Erro ao carregar saldos: {str(e)}")
            return {
                "saldos": {"bradesco": 0.0, "banco_brasil": 0.0, "reag": 0.0},
                "total": 0.0
            }
    
    def calcular_disponibilidade_por_prioridade(self):
        """Calcula disponibilidade restante após descontar valores por prioridade"""
        try:
            if self.dados is None:
                return {}
            
            # Carrega saldos bancários
            info_saldos = self.carregar_saldos_bancarios()
            saldo_total = info_saldos.get('total', 0.0)
            
            # Calcula valores por prioridade
            disponibilidade = {
                'saldo_inicial': saldo_total,
                'prioridades': {},
                'saldo_restante': saldo_total
            }
            
            # Processa prioridades de 1 a 5
            for prioridade in range(1, 6):
                # Filtra dados pela prioridade
                dados_prioridade = self.dados[
                    (self.dados['Prioridade'] == prioridade) & 
                    (self.dados['Prioridade'].notna())
                ]
                
                if len(dados_prioridade) > 0:
                    valor_prioridade = dados_prioridade['Valor'].sum()
                else:
                    valor_prioridade = 0.0
                
                # Calcula saldo após desconto
                saldo_apos_desconto = disponibilidade['saldo_restante'] - valor_prioridade
                
                disponibilidade['prioridades'][prioridade] = {
                    'valor_total': valor_prioridade,
                    'quantidade_itens': len(dados_prioridade),
                    'saldo_antes': disponibilidade['saldo_restante'],
                    'saldo_depois': saldo_apos_desconto,
                    'suficiente': saldo_apos_desconto >= 0
                }
                
                # Atualiza saldo restante para próxima prioridade
                disponibilidade['saldo_restante'] = saldo_apos_desconto
            
            # Processa itens sem prioridade
            dados_sem_prioridade = self.dados[
                (self.dados['Prioridade'].isna()) | 
                (self.dados['Prioridade'] == 0)
            ]
            
            if len(dados_sem_prioridade) > 0:
                valor_sem_prioridade = dados_sem_prioridade['Valor'].sum()
            else:
                valor_sem_prioridade = 0.0
            
            # Calcula saldo após descontar itens sem prioridade
            saldo_apos_sem_prioridade = disponibilidade['saldo_restante'] - valor_sem_prioridade
            
            disponibilidade['sem_prioridade'] = {
                'valor_total': valor_sem_prioridade,
                'quantidade_itens': len(dados_sem_prioridade),
                'saldo_antes': disponibilidade['saldo_restante'],
                'saldo_depois': saldo_apos_sem_prioridade,
                'suficiente': saldo_apos_sem_prioridade >= 0
            }
            
            # Atualiza saldo final
            disponibilidade['saldo_restante'] = saldo_apos_sem_prioridade
            
            return disponibilidade
            
        except Exception as e:
            st.error(f"Erro no cálculo de disponibilidade: {str(e)}")
            return {}
    
    def atualizar_saldo_por_situacao(self, valor, situacao_anterior, situacao_nova):
        """Atualiza saldo do Bradesco baseado na mudança de situação"""
        try:
            # Carrega saldos atuais
            info_saldos = self.carregar_saldos_bancarios()
            saldo_bradesco_atual = info_saldos.get('saldos', {}).get('bradesco', 0.0)
            saldo_bb_atual = info_saldos.get('saldos', {}).get('banco_brasil', 0.0)
            saldo_reag_atual = info_saldos.get('saldos', {}).get('reag', 0.0)
            
            # Calcula novo saldo do Bradesco baseado na mudança
            novo_saldo_bradesco = saldo_bradesco_atual
            
            # Se mudou de N_PG para PG: desconta do saldo
            if situacao_anterior != 'PG' and situacao_nova == 'PG':
                novo_saldo_bradesco -= valor
                mensagem = f"Saldo Bradesco reduzido em R$ {valor:,.2f} (item marcado como PAGO)"
            
            # Se mudou de PG para N_PG: soma ao saldo
            elif situacao_anterior == 'PG' and situacao_nova != 'PG':
                novo_saldo_bradesco += valor
                mensagem = f"Saldo Bradesco aumentado em R$ {valor:,.2f} (item marcado como NÃO PAGO)"
            
            else:
                # Sem mudança no saldo
                mensagem = "Situação atualizada sem alteração no saldo"
                return True, mensagem
            
            # Salva novo saldo
            sucesso, msg_save = self.salvar_saldos_bancarios(novo_saldo_bradesco, saldo_bb_atual, saldo_reag_atual)
            
            if sucesso:
                return True, mensagem
            else:
                return False, f"Erro ao atualizar saldo: {msg_save}"
                
        except Exception as e:
            return False, f"Erro ao processar atualização de saldo: {str(e)}"

def criar_sidebar():
    """Cria a barra lateral com navegação"""
    st.sidebar.title("🏦 Rota Verde")
    st.sidebar.markdown("---")
    
    opcoes = [
        "📊 Dashboard",
        "🏦 Saldos Bancários",
        "📈 Análises",
        "🔄 Renegociação e Prioridade",
        "🔍 Análise de Alterações",
        "🏦 Leitura dos Extratos",
        "📁 Gerenciar Arquivos"
    ]
    
    return st.sidebar.selectbox("Selecione uma opção:", opcoes)

def pagina_dashboard(app):
    """Página principal do dashboard"""
    st.title("💰 Dashboard - Fluxo de Caixa")
    
    if app.dados is None:
        st.error("Dados não carregados!")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_registros = len(app.dados)
        st.metric("Total de Registros", total_registros)
    
    with col2:
        valor_total = app.dados['Valor'].sum()
        valor_total_formatado = app.formatar_valor_brasileiro(valor_total)
        st.metric("Valor Total", valor_total_formatado)
    
    with col3:
        valor_medio = app.dados['Valor'].mean()
        valor_medio_formatado = app.formatar_valor_brasileiro(valor_medio)
        st.metric("Valor Médio", valor_medio_formatado)
    
    with col4:
        registros_prioridade = len(app.dados[app.dados['Prioridade'].notna()])
        st.metric("Itens com Prioridade", registros_prioridade)
    
    # Gráfico de valores por mês
    st.subheader("📈 Distribuição de Valores por Mês")
    
    # Prepara dados para o gráfico
    dados_graf = app.dados.copy()
    dados_graf['Mes'] = dados_graf['Vencto Real'].dt.strftime('%Y-%m')
    valores_mes = dados_graf.groupby('Mes')['Valor'].sum().reset_index()
    
    fig = px.bar(valores_mes, x='Mes', y='Valor', 
                 title="Valores por Mês",
                 labels={'Valor': 'Valor (R$)', 'Mes': 'Mês'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Exibição em HTML ao invés de DataFrame
    st.subheader("📋 Fluxo de Caixa Ordenado por Prioridade e Data de Renegociação")
    
    # Gera HTML dos dados
    html_content = app.gerar_html_fluxo_caixa(app.dados.head(20))  # Mostra apenas os primeiros 20
    
    # Exibe o HTML
    st.components.v1.html(html_content, height=600, scrolling=True)

def pagina_analises(app):
    """Página de análises detalhadas"""
    st.title("📈 Análises Detalhadas")
    
    if app.dados is None:
        st.error("Dados não carregados!")
        return
    
    # Filtros
    st.sidebar.subheader("Filtros")
    
    # Filtro por data
    data_min = app.dados['Vencto Real'].min().date()
    data_max = app.dados['Vencto Real'].max().date()
    
    data_inicio = st.sidebar.date_input("Data Início", data_min)
    data_fim = st.sidebar.date_input("Data Fim", data_max)
    
    # Filtro por fornecedor
    fornecedores = ['Todos'] + sorted(app.dados['Razão Social'].unique().tolist())
    fornecedor_selecionado = st.sidebar.selectbox("Fornecedor", fornecedores)
    
    # Aplica filtros
    dados_filtrados = app.dados.copy()
    dados_filtrados = dados_filtrados[
        (dados_filtrados['Vencto Real'].dt.date >= data_inicio) &
        (dados_filtrados['Vencto Real'].dt.date <= data_fim)
    ]
    
    if fornecedor_selecionado != 'Todos':
        dados_filtrados = dados_filtrados[dados_filtrados['Razão Social'] == fornecedor_selecionado]
    
    # Estatísticas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Estatísticas do Período")
        st.write(f"**Total de registros:** {len(dados_filtrados)}")
        st.write(f"**Valor total:** {app.formatar_valor_brasileiro(dados_filtrados['Valor'].sum())}")
        st.write(f"**Valor médio:** {app.formatar_valor_brasileiro(dados_filtrados['Valor'].mean())}")
        st.write(f"**Valor mínimo:** {app.formatar_valor_brasileiro(dados_filtrados['Valor'].min())}")
        st.write(f"**Valor máximo:** {app.formatar_valor_brasileiro(dados_filtrados['Valor'].max())}")
    
    with col2:
        # Top 5 fornecedores por valor
        st.subheader("🏆 Top 5 Fornecedores")
        top_fornecedores = dados_filtrados.groupby('Razão Social')['Valor'].sum().sort_values(ascending=False).head(5)
        st.bar_chart(top_fornecedores)
    
    # Exibição em HTML dos dados filtrados
    st.subheader("📋 Dados Filtrados - Visualização HTML")
    
    if len(dados_filtrados) > 0:
        # Gera HTML dos dados filtrados
        html_content = app.gerar_html_fluxo_caixa(dados_filtrados)
        st.components.v1.html(html_content, height=700, scrolling=True)
    else:
        st.warning("Nenhum dado encontrado para os filtros aplicados.")

def pagina_renegociacao_prioridade(app):
    """Página para gerenciar renegociações e prioridades"""
    st.title("🔄 Renegociação e Prioridade")
    
    if app.dados is None:
        st.error("Dados não carregados!")
        return
    
    # Ordena por prioridade e data de renegociação
    app.ordenar_por_prioridade_e_renegociacao()
    
    # Filtro por prioridade
    col1, col2 = st.columns([3, 1])
    
    with col2:
        mostrar_apenas_prioridade = st.checkbox("Apenas itens com prioridade")
        prioridade_filtro = st.selectbox("Filtrar por prioridade", 
                                       ['Todas', '1', '2', '3', '4', '5'])
    
    # Aplica filtros
    dados_display = app.dados.copy()
    
    if mostrar_apenas_prioridade:
        dados_display = dados_display[dados_display['Prioridade'].notna()]
    
    if prioridade_filtro != 'Todas':
        dados_display = dados_display[dados_display['Prioridade'] == int(prioridade_filtro)]
    
    # Seção de edição
    st.subheader("✏️ Editar Registro")
    
    if len(dados_display) > 0:
        # Seletor de registro
        opcoes_registro = []
        for idx, row in dados_display.head(50).iterrows():  # Limita a 50 para performance
            data_efetiva = app.obter_data_efetiva(row)
            valor_formatado = app.formatar_valor_brasileiro(row['Valor'])
            opcoes_registro.append(f"{idx} - {row['Razão Social']} - {data_efetiva.strftime('%Y-%m-%d')} - {valor_formatado}")
        
        if opcoes_registro:
            registro_selecionado = st.selectbox("Selecione um registro para editar:", opcoes_registro)
            
            if registro_selecionado:
                idx_selecionado = int(registro_selecionado.split(' - ')[0])
                
                # Formulário de edição
                col1, col2 = st.columns(2)
                
                with col1:
                    nova_data_renegociacao = st.date_input(
                        "Nova Data de Renegociação",
                        value=app.dados.loc[idx_selecionado, 'Data Renegociacao'] if pd.notna(app.dados.loc[idx_selecionado, 'Data Renegociacao']) else None,
                        key=f"data_{idx_selecionado}"
                    )
                
                with col2:
                    nova_prioridade = st.selectbox(
                        "Prioridade (1=Urgente, 5=Baixa)",
                        options=[None, 1, 2, 3, 4, 5],
                        index=[None, 1, 2, 3, 4, 5].index(app.dados.loc[idx_selecionado, 'Prioridade']) if pd.notna(app.dados.loc[idx_selecionado, 'Prioridade']) else 0,
                        key=f"prioridade_{idx_selecionado}"
                    )
                
                # Nova seção para Situação
                st.markdown("**💳 Situação de Pagamento**")
                col_sit1, col_sit2 = st.columns(2)
                
                # Verifica situação atual
                situacao_atual = app.dados.loc[idx_selecionado, 'Situacao'] if 'Situacao' in app.dados.columns and pd.notna(app.dados.loc[idx_selecionado, 'Situacao']) else None
                
                with col_sit1:
                    nova_situacao = st.selectbox(
                        "Situação",
                        options=[None, 'PG', 'N_PG'],
                        index=[None, 'PG', 'N_PG'].index(situacao_atual) if situacao_atual in [None, 'PG', 'N_PG'] else 0,
                        key=f"situacao_{idx_selecionado}",
                        help="PG = Pago | N_PG = Não Pago"
                    )
                
                with col_sit2:
                    valor_item = app.dados.loc[idx_selecionado, 'Valor']
                    st.metric("Valor do Item", f"R$ {valor_item:,.2f}")
                
                # Campo de descrição da negociação
                st.markdown("**📝 Descrição da Negociação**")
                descricao_atual = app.dados.loc[idx_selecionado, 'Descricao_Negociacao'] if 'Descricao_Negociacao' in app.dados.columns and pd.notna(app.dados.loc[idx_selecionado, 'Descricao_Negociacao']) else ""
                
                nova_descricao = st.text_area(
                    "Descrição (máx. 200 caracteres)",
                    value=descricao_atual,
                    max_chars=200,
                    height=100,
                    key=f"descricao_{idx_selecionado}",
                    help="Descreva os detalhes da negociação, condições especiais, etc."
                )
                
                # Contador de caracteres mais detalhado
                caracteres_escritos = len(nova_descricao)
                caracteres_restantes = 200 - caracteres_escritos
                percentual_uso = (caracteres_escritos / 200) * 100
                
                # Exibe informações sobre os caracteres
                col_char1, col_char2, col_char3 = st.columns(3)
                
                with col_char1:
                    st.metric(
                        "📝 Caracteres Escritos", 
                        caracteres_escritos,
                        delta=f"{percentual_uso:.1f}% do limite"
                    )
                
                with col_char2:
                    st.metric(
                        "📊 Restantes", 
                        caracteres_restantes,
                        delta="Disponível"
                    )
                
                with col_char3:
                    # Barra de progresso visual
                    progresso = caracteres_escritos / 200
                    cor_barra = "🟢" if progresso < 0.8 else "🟡" if progresso < 0.95 else "🔴"
                    st.metric(
                        f"{cor_barra} Progresso",
                        f"{percentual_uso:.1f}%"
                    )
                
                # Aviso quando próximo do limite
                if caracteres_restantes < 20:
                    st.warning(f"⚠️ Atenção! Restam apenas {caracteres_restantes} caracteres")
                elif caracteres_restantes < 50:
                    st.info(f"💡 Você está usando {caracteres_escritos} de 200 caracteres")
                
                # Botões de ação
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💾 Salvar Alterações", key=f"salvar_{idx_selecionado}"):
                        # Captura situação anterior para comparar
                        situacao_anterior = app.dados.loc[idx_selecionado, 'Situacao'] if 'Situacao' in app.dados.columns else None
                        
                        # Atualiza data e prioridade
                        if nova_data_renegociacao:
                            app.dados.loc[idx_selecionado, 'Data Renegociacao'] = pd.to_datetime(nova_data_renegociacao)
                        else:
                            app.dados.loc[idx_selecionado, 'Data Renegociacao'] = pd.NaT
                        
                        app.dados.loc[idx_selecionado, 'Prioridade'] = nova_prioridade
                        
                        # Adiciona colunas se não existirem
                        if 'Situacao' not in app.dados.columns:
                            app.dados['Situacao'] = None
                        if 'Descricao_Negociacao' not in app.dados.columns:
                            app.dados['Descricao_Negociacao'] = None
                        
                        # Atualiza situação e descrição
                        app.dados.loc[idx_selecionado, 'Situacao'] = nova_situacao
                        app.dados.loc[idx_selecionado, 'Descricao_Negociacao'] = nova_descricao.strip() if nova_descricao.strip() else None
                        
                        # Atualiza saldo se houve mudança de situação
                        mensagens = []
                        if situacao_anterior != nova_situacao:
                            valor_item = app.dados.loc[idx_selecionado, 'Valor']
                            sucesso_saldo, msg_saldo = app.atualizar_saldo_por_situacao(valor_item, situacao_anterior, nova_situacao)
                            
                            if sucesso_saldo:
                                mensagens.append(msg_saldo)
                            else:
                                st.error(f"⚠️ {msg_saldo}")
                        
                        # Reordena e recalcula subtotal
                        app.ordenar_por_prioridade_e_renegociacao()
                        
                        # Salva no JSON
                        if app.salvar_dados_json():
                            st.success("✅ Alterações salvas com sucesso!")
                            for msg in mensagens:
                                st.info(f"💰 {msg}")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao salvar alterações!")
                
                with col2:
                    if st.button("🗑️ Limpar Renegociação", key=f"limpar_{idx_selecionado}"):
                        app.dados.loc[idx_selecionado, 'Data Renegociacao'] = pd.NaT
                        app.dados.loc[idx_selecionado, 'Prioridade'] = None
                        if app.salvar_dados_json():
                            st.success("Registro limpo!")
                            st.rerun()
                
                with col3:
                    if st.button("💾 Salvar Todos os Dados", key="salvar_todos"):
                        if app.salvar_dados_json():
                            st.success("Todos os dados salvos em JSON!")
    
    # Exibição em HTML ao invés de DataFrame
    st.subheader("📋 Lista Ordenada por Prioridade e Data de Renegociação")
    
    if len(dados_display) > 0:
        # Gera HTML dos dados
        html_content = app.gerar_html_fluxo_caixa(dados_display)
        st.components.v1.html(html_content, height=800, scrolling=True)
    
    # Legenda de cores
    st.subheader("🎨 Legenda de Prioridades")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div style="background-color: #FF0000; padding: 10px; text-align: center; border-radius: 5px; color: white;">Prioridade 1</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="background-color: #FF8000; padding: 10px; text-align: center; border-radius: 5px; color: white;">Prioridade 2</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div style="background-color: #FFFF00; padding: 10px; text-align: center; border-radius: 5px; color: black;">Prioridade 3</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div style="background-color: #80FF00; padding: 10px; text-align: center; border-radius: 5px; color: black;">Prioridade 4</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div style="background-color: #ADD8E6; padding: 10px; text-align: border-radius: 5px; color: black;">Prioridade 5</div>', unsafe_allow_html=True)

def pagina_gerenciar_arquivos(app):
    """Página para gerenciar uploads e seleção de arquivos"""
    st.title("📁 Gerenciar Arquivos Excel")
    
    # Seção de Upload
    st.subheader("📤 Upload de Arquivos")
    arquivo_upload = st.file_uploader(
        "Envie um arquivo Excel (.xlsx ou .xls)",
        type=['xlsx', 'xls'],
        help="Selecione um arquivo Excel para adicionar à pasta uploads"
    )
    
    if arquivo_upload is not None:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**Arquivo selecionado:** {arquivo_upload.name}")
            st.write(f"**Tamanho:** {arquivo_upload.size / 1024:.1f} KB")
            
        with col2:
            if st.button("💾 Salvar Arquivo", type="primary"):
                sucesso, resultado = app.salvar_arquivo_upload(arquivo_upload)
                
                if sucesso:
                    st.success(f"✅ Arquivo salvo: {resultado}")
                    st.rerun()  # Atualiza a lista
                else:
                    st.error(f"❌ Erro ao salvar: {resultado}")
    
    st.markdown("---")
    
    # Seção de Seleção de Arquivos
    st.subheader("📋 Arquivos Disponíveis")
    
    arquivos_disponiveis = app.listar_arquivos_uploads()
    
    if arquivos_disponiveis:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            arquivo_selecionado = st.selectbox(
                "Selecione um arquivo para carregar:",
                options=["Arquivo padrão"] + arquivos_disponiveis,
                help="Escolha um arquivo da pasta uploads ou use o arquivo padrão"
            )
        
        with col2:
            if st.button("🔄 Carregar Arquivo", type="secondary"):
                if arquivo_selecionado == "Arquivo padrão":
                    st.info("📁 Carregando arquivo padrão...")
                    # Usa arquivo padrão
                    app.arquivo_excel = "Previsão de fluxo de caixa projetado até dezembro_2025.xlsx"
                else:
                    st.info(f"📁 Carregando {arquivo_selecionado}...")
                    # Usa arquivo selecionado
                    app.arquivo_excel = os.path.join(app.pasta_uploads, arquivo_selecionado)
                
                # Recarrega os dados
                try:
                    dados_excel, msg = app.carregar_dados_excel()
                    if dados_excel is not None:
                        # Atualiza dados no app
                        dados_json = app.carregar_dados_json()
                        app.dados = app.atualizar_campos_renegociacao_prioridade(dados_excel, dados_json)
                        app.dados = app.dados.dropna(subset=['Vencto Real'])
                        app.ordenar_por_prioridade_e_renegociacao()
                        app.salvar_dados_json()
                        
                        st.success(f"✅ Dados carregados com sucesso! Total: {len(app.dados)} registros")
                    else:
                        st.error(f"❌ Erro ao carregar arquivo: {msg}")
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        
        # Lista dos arquivos disponíveis
        st.subheader("📂 Arquivos na pasta uploads:")
        for i, arquivo in enumerate(arquivos_disponiveis, 1):
            caminho_completo = os.path.join(app.pasta_uploads, arquivo)
            tamanho = os.path.getsize(caminho_completo) / 1024
            data_modificacao = datetime.fromtimestamp(os.path.getmtime(caminho_completo))
            
            st.write(f"{i}. **{arquivo}** - {tamanho:.1f} KB - {data_modificacao.strftime('%d/%m/%Y %H:%M')}")
    else:
        st.info("📭 Nenhum arquivo encontrado na pasta uploads. Use o upload acima para adicionar arquivos.")
        
    st.markdown("---")
    st.info("""
    **ℹ️ Instruções:**
    - Faça upload de arquivos Excel (.xlsx ou .xls)
    - Os arquivos são salvos na pasta `uploads/`
    - Selecione um arquivo da lista para carregar os dados
    - O sistema manterá as configurações de renegociação e prioridade
    """)

def pagina_analise_alteracoes(app):
    """Página para analisar alterações entre Excel e JSON"""
    st.title("🔍 Análise de Alterações")
    st.write("Esta página compara os dados do Excel com o JSON existente e identifica alterações nos campos Data Renegociação e Prioridade.")
    
    if app.dados is None:
        st.error("❌ Nenhum dado carregado. Verifique se o arquivo Excel existe.")
        return
    
    # Botão para executar análise
    if st.button("🔍 Executar Análise de Alterações", type="primary"):
        with st.spinner("Analisando alterações..."):
            # Carrega dados do Excel
            dados_excel, msg_excel = app.carregar_dados_excel()
            
            if dados_excel is None:
                st.error(f"Erro ao carregar Excel: {msg_excel}")
                return
                
            # Carrega dados do JSON
            dados_json = app.carregar_dados_json()
            
            if dados_json is None:
                st.warning("⚠️ Não foi possível carregar dados do JSON para comparação.")
                return
            
            # Executa análise de alterações
            alteracoes = app.comparar_alteracoes_renegociacao(dados_excel, dados_json)
            
            if alteracoes:
                st.success(f"🔍 Encontradas {len(alteracoes)} alterações!")
                
                # Salva alterações em arquivo separado
                if app.salvar_alteracoes_json(alteracoes):
                    st.info("💾 Arquivo de alterações criado com sucesso!")
                
                # Exibe resumo das alterações
                st.subheader("📄 Resumo das Alterações")
                
                for i, alteracao in enumerate(alteracoes, 1):
                    with st.expander(f"Alteração {i}: {alteracao['Razão Social']}"):
                        st.write(f"**Vencimento:** {alteracao['Vencto Real']}")
                        st.write(f"**Fornecedor:** {alteracao['Razão Social']}")
                        
                        for alt in alteracao['alteracoes']:
                            st.write(f"**{alt['campo']}:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"Anterior: `{alt['valor_anterior']}`")
                            with col2:
                                st.write(f"Novo: `{alt['valor_novo']}`")
            else:
                st.success("✅ Nenhuma alteração detectada nos campos de renegociação/prioridade")
    
    # Informações sobre o processo
    st.subheader("📈 Informações do Processo")
    st.info("""
    **Como funciona a análise:**
    1. Compara registros usando **Vencto Real** + **Razão Social** como chave de identificação
    2. Identifica alterações nos campos **Data Renegociação** e **Prioridade**
    3. Salva as alterações em um arquivo JSON separado: `alteracoes_renegociacao_prioridade.json`
    4. **Não adiciona nem remove registros**, apenas atualiza campos específicos
    """)

def pagina_saldos_bancarios(app):
    """Página para gestão de saldos bancários"""
    st.title("🏦 Gestão de Saldos Bancários")
    st.write("Configure os saldos atuais dos bancos e visualize a disponibilidade por prioridade.")
    
    # Carrega saldos atuais
    info_saldos = app.carregar_saldos_bancarios()
    saldos_atuais = info_saldos.get('saldos', {})
    
    # Seção de entrada de saldos
    st.subheader("💰 Saldos Atuais")
    
    with st.form("form_saldos"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🏛️ Bradesco**")
            saldo_bradesco = st.number_input(
                "Saldo Bradesco (R$)",
                min_value=0.0,
                value=saldos_atuais.get('bradesco', 0.0),
                step=100.0,
                format="%.2f"
            )
        
        with col2:
            st.markdown("**🏦 Banco do Brasil**")
            saldo_bb = st.number_input(
                "Saldo BB (R$)",
                min_value=0.0,
                value=saldos_atuais.get('banco_brasil', 0.0),
                step=100.0,
                format="%.2f"
            )
        
        with col3:
            st.markdown("**🏢 REAG**")
            saldo_reag = st.number_input(
                "Saldo REAG (R$)",
                min_value=0.0,
                value=saldos_atuais.get('reag', 0.0),
                step=100.0,
                format="%.2f"
            )
        
        # Mostra total calculado
        total_calculado = saldo_bradesco + saldo_bb + saldo_reag
        st.markdown(f"**💸 Total Disponível: R$ {total_calculado:,.2f}**")
        
        # Botão para salvar
        submitted = st.form_submit_button("💾 Salvar Saldos", type="primary")
        
        if submitted:
            sucesso, mensagem = app.salvar_saldos_bancarios(saldo_bradesco, saldo_bb, saldo_reag)
            
            if sucesso:
                st.success(f"✅ {mensagem}")
                st.rerun()
            else:
                st.error(f"❌ {mensagem}")
    
    # Informações da última atualização
    if info_saldos.get('ultima_atualizacao'):
        st.info(f"📅 Última atualização: {info_saldos['ultima_atualizacao']}")
    
    # Análise de disponibilidade por prioridade
    st.divider()
    st.subheader("📊 Disponibilidade por Prioridade")
    
    if app.dados is not None and info_saldos.get('total', 0) > 0:
        disponibilidade = app.calcular_disponibilidade_por_prioridade()
        
        if disponibilidade:
            # Métricas principais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Saldo Total", f"R$ {disponibilidade['saldo_inicial']:,.2f}")
            
            with col2:
                st.metric("💸 Saldo Final", f"R$ {disponibilidade['saldo_restante']:,.2f}")
            
            with col3:
                total_comprometido = disponibilidade['saldo_inicial'] - disponibilidade['saldo_restante']
                st.metric("📋 Total Comprometido", f"R$ {total_comprometido:,.2f}")
            
            # Detalhamento por prioridade
            st.subheader("🎯 Detalhamento por Prioridade")
            
            # Mostra saldo após cada prioridade cumulativamente
            st.markdown("### 💰 Saldo Cumulativo por Prioridade")
            
            # Exibe cada prioridade com o saldo restante
            for prioridade in range(1, 6):
                if prioridade in disponibilidade['prioridades']:
                    info_prioridade = disponibilidade['prioridades'][prioridade]
                    saldo_apos_prioridade = info_prioridade['saldo_depois']
                    valor_prioridade = info_prioridade['valor_total']
                    saldo_antes = info_prioridade['saldo_antes']
                    
                    # Define cores baseadas no saldo
                    cor_saldo = "🟢" if saldo_apos_prioridade >= 0 else "🔴"
                    cor_fundo = '#d4edda' if saldo_apos_prioridade >= 0 else '#f8d7da'
                    cor_borda = '#28a745' if saldo_apos_prioridade >= 0 else '#dc3545'
                    cor_texto = '#155724' if saldo_apos_prioridade >= 0 else '#721c24'
                    
                    # Container para cada prioridade
                    with st.container():
                        col1, col2, col3 = st.columns([1, 2, 1])
                        
                        with col2:
                            st.markdown(f"""
                            <div style="
                                background-color: {cor_fundo};
                                border: 2px solid {cor_borda};
                                border-radius: 10px;
                                padding: 15px;
                                text-align: center;
                                margin: 10px 0;
                            ">
                                <h4 style="margin: 0; color: {cor_texto};">
                                    {cor_saldo} Prioridade {prioridade}
                                </h4>
                                <div style="margin: 8px 0; color: {cor_texto}; font-size: 21px; font-weight: 600;">
                                    Saldo Antes: R$ {saldo_antes:,.2f} - Valor P{prioridade}: R$ {valor_prioridade:,.2f}
                                </div>
                                <h2 style="margin: 5px 0; color: {cor_texto};">
                                    = R$ {saldo_apos_prioridade:,.2f}
                                </h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Adiciona seta para próxima prioridade (exceto na última)
                        if prioridade < 5 and (prioridade + 1) in disponibilidade['prioridades']:
                            st.markdown("""
                            <div style="text-align: center; margin: 5px 0;">
                                <span style="font-size: 24px; color: #6c757d;">⬇️</span>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Adiciona itens sem prioridade no final
            if 'sem_prioridade' in disponibilidade and disponibilidade['sem_prioridade']['quantidade_itens'] > 0:
                # Seta indicando continuação para sem prioridade
                st.markdown("""
                <div style="text-align: center; margin: 15px 0;">
                    <span style="font-size: 24px; color: #6c757d;">⬇️</span>
                </div>
                """, unsafe_allow_html=True)
                
                info_sem_prioridade = disponibilidade['sem_prioridade']
                saldo_apos_sem_prioridade = info_sem_prioridade['saldo_depois']
                valor_sem_prioridade = info_sem_prioridade['valor_total']
                saldo_antes_sem_prioridade = info_sem_prioridade['saldo_antes']
                
                # Define cores baseadas no saldo
                cor_saldo = "🟢" if saldo_apos_sem_prioridade >= 0 else "🔴"
                cor_fundo = '#fff3cd' if saldo_apos_sem_prioridade >= 0 else '#f8d7da'
                cor_borda = '#ffc107' if saldo_apos_sem_prioridade >= 0 else '#dc3545'
                cor_texto = '#856404' if saldo_apos_sem_prioridade >= 0 else '#721c24'
                
                # Container para sem prioridade
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    st.markdown(f"""
                    <div style="
                        background-color: {cor_fundo};
                        border: 2px solid {cor_borda};
                        border-radius: 10px;
                        padding: 15px;
                        text-align: center;
                        margin: 10px 0;
                    ">
                        <h4 style="margin: 0; color: {cor_texto};">
                            {cor_saldo} Sem Prioridade ({info_sem_prioridade['quantidade_itens']} itens)
                        </h4>
                        <div style="margin: 8px 0; color: {cor_texto}; font-size: 21px; font-weight: 600;">
                            Saldo Antes: R$ {saldo_antes_sem_prioridade:,.2f} - Valor Sem Prioridade: R$ {valor_sem_prioridade:,.2f}
                        </div>
                        <h2 style="margin: 5px 0; color: {cor_texto};">
                            = R$ {saldo_apos_sem_prioridade:,.2f}
                        </h2>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")  # Separador visual
            
            for prioridade in range(1, 6):
                if prioridade in disponibilidade['prioridades']:
                    info_prior = disponibilidade['prioridades'][prioridade]
                    
                    with st.expander(f"🔢 Prioridade {prioridade} - {info_prior['quantidade_itens']} itens"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("💰 Valor Total", f"R$ {info_prior['valor_total']:,.2f}")
                        
                        with col2:
                            st.metric("📊 Quantidade", info_prior['quantidade_itens'])
                        
                        with col3:
                            st.metric("⚡ Saldo Antes", f"R$ {info_prior['saldo_antes']:,.2f}")
                        
                        with col4:
                            cor = "normal" if info_prior['suficiente'] else "inverse"
                            delta_color = "normal" if info_prior['saldo_depois'] >= 0 else "inverse"
                            st.metric(
                                "🎯 Saldo Depois", 
                                f"R$ {info_prior['saldo_depois']:,.2f}",
                                delta=f"{'✅ Suficiente' if info_prior['suficiente'] else '❌ Insuficiente'}"
                            )
            
            # Gráfico de cascata
            st.subheader("📈 Análise Visual")
            
            # Dados para gráfico de cascata
            categorias = ['Saldo Inicial']
            valores = [disponibilidade['saldo_inicial']]
            cores = ['blue']
            
            for prioridade in range(1, 6):
                if prioridade in disponibilidade['prioridades']:
                    info_prior = disponibilidade['prioridades'][prioridade]
                    categorias.append(f'Prioridade {prioridade}')
                    valores.append(-info_prior['valor_total'])  # Negativo para desconto
                    cores.append('red' if not info_prior['suficiente'] else 'orange')
            
            categorias.append('Saldo Final')
            valores.append(disponibilidade['saldo_restante'])
            cores.append('green' if disponibilidade['saldo_restante'] >= 0 else 'red')
            
            # Gráfico de barras para visualização
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=categorias,
                y=valores,
                marker_color=cores,
                text=[f'R$ {v:,.0f}' for v in valores],
                textposition='auto'
            ))
            
            fig.update_layout(
                title="Fluxo de Disponibilidade por Prioridade",
                xaxis_title="Categoria",
                yaxis_title="Valor (R$)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Não foi possível calcular a disponibilidade.")
    else:
        if app.dados is None:
            st.warning("⚠️ Carregue os dados do fluxo de caixa primeiro.")
        else:
            st.info("ℹ️ Configure os saldos bancários para visualizar a análise.")

def main():
    """Função principal do aplicativo"""
    # Inicializa o app
    app = FluxoCaixaApp()
    
    # Carrega os dados
    sucesso, mensagem = app.inicializar_dados()
    
    if not sucesso:
        st.error(f"Erro ao carregar dados: {mensagem}")
        return
    
    # Cria sidebar e obtém seleção
    opcao_selecionada = criar_sidebar()
    
    # Mostra status na sidebar
    st.sidebar.success(mensagem)
    
    # Roteamento de páginas
    if opcao_selecionada == "📊 Dashboard":
        pagina_dashboard(app)
    elif opcao_selecionada == "🏦 Saldos Bancários":
        pagina_saldos_bancarios(app)
    elif opcao_selecionada == "📈 Análises":
        pagina_analises(app)
    elif opcao_selecionada == "🔄 Renegociação e Prioridade":
        pagina_renegociacao_prioridade(app)
    elif opcao_selecionada == "🔍 Análise de Alterações":
        pagina_analise_alteracoes(app)
    elif opcao_selecionada == "🏦 Leitura dos Extratos":
        pagina_leitura_extratos(app)
    elif opcao_selecionada == "📁 Gerenciar Arquivos":
        pagina_gerenciar_arquivos(app)

def pagina_leitura_extratos(app):
    """Página para leitura e processamento de extratos bancários"""
    st.title("🏦 Leitura dos Extratos")
    st.write("Esta página processa automaticamente extratos do Bradesco da pasta 'extratos'.")
    
    # Cria pasta extratos se não existir
    if not os.path.exists("extratos"):
        os.makedirs("extratos")
    
    # Informações sobre o processamento
    st.subheader("📋 Regras de Processamento")
    st.info("""
    **Critérios para arquivos do Bradesco:**
    - Nome do arquivo deve conter 'bradesco' (maiúscula ou minúscula)
    - Leitura inicia na linha 10
    - Colunas processadas: Data, Lançamento, Dcto, Crédito, Débito
    - Processamento termina na linha que contém 'Total'
    - Conversão automática: datas e valores monetários
    """)
    
    # Lista arquivos disponíveis
    arquivos = app.listar_arquivos_extratos()
    
    if not arquivos:
        st.warning("⚠️ Nenhum arquivo encontrado na pasta 'extratos'. Adicione arquivos Excel (.xlsx, .xls) para processar.")
        
        # Informações sobre como adicionar arquivos
        st.subheader("📁 Como adicionar extratos")
        st.write("""
        1. Coloque os arquivos Excel na pasta: `extratos/`
        2. Certifique-se que arquivos do Bradesco contenham 'bradesco' no nome
        3. Clique em 'Processar Extratos' para analisar
        """)
        return
    
    # Mostra arquivos encontrados
    st.subheader(f"📂 Arquivos Encontrados ({len(arquivos)})")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        for arquivo in arquivos:
            caminho_completo = os.path.join("extratos", arquivo)
            eh_bradesco = app.verificar_arquivo_bradesco(caminho_completo)
            
            if eh_bradesco:
                st.success(f"✅ {arquivo} (Bradesco)")
            else:
                st.info(f"ℹ️ {arquivo} (Não será processado)")
    
    with col2:
        st.metric("Total", len(arquivos))
        bradesco_count = sum(1 for arquivo in arquivos if app.verificar_arquivo_bradesco(os.path.join("extratos", arquivo)))
        st.metric("Bradesco", bradesco_count)
    
    # Botão para processar
    if st.button("🔄 Processar Extratos", type="primary"):
        with st.spinner("Processando extratos do Bradesco..."):
            dados, erros = app.processar_todos_extratos()
            
            if dados is not None:
                st.success(f"✅ Processamento concluído! Total de {len(dados)} transações encontradas.")
                
                # Exibe estatísticas
                st.subheader("📊 Resumo dos Dados Processados")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Transações", len(dados))
                
                with col2:
                    total_credito = dados['Credito'].sum()
                    st.metric("Total Créditos", f"R$ {total_credito:,.2f}")
                
                with col3:
                    total_debito = dados['Debito'].sum()
                    st.metric("Total Débitos", f"R$ {total_debito:,.2f}")
                
                with col4:
                    # Usa o último saldo da série como saldo final
                    ultimo_saldo = dados['Saldo'].iloc[-1] if len(dados) > 0 else 0
                    st.metric("Saldo Final", f"R$ {ultimo_saldo:,.2f}")
                
                # Filtros
                st.subheader("🔍 Filtros")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Filtro por período
                    data_min = dados['Data'].min().date()
                    data_max = dados['Data'].max().date()
                    
                    data_inicio = st.date_input("Data Início", data_min)
                    data_fim = st.date_input("Data Fim", data_max)
                
                with col2:
                    # Filtro por arquivo origem
                    arquivos_origem = ['Todos'] + sorted(dados['Arquivo_Origem'].unique().tolist())
                    arquivo_selecionado = st.selectbox("Arquivo de Origem", arquivos_origem)
                
                # Aplica filtros
                dados_filtrados = dados.copy()
                dados_filtrados = dados_filtrados[
                    (dados_filtrados['Data'].dt.date >= data_inicio) &
                    (dados_filtrados['Data'].dt.date <= data_fim)
                ]
                
                if arquivo_selecionado != 'Todos':
                    dados_filtrados = dados_filtrados[dados_filtrados['Arquivo_Origem'] == arquivo_selecionado]
                
                # Exibe dados filtrados em HTML
                st.subheader(f"📋 Extratos Processados ({len(dados_filtrados)} transações)")
                
                if len(dados_filtrados) > 0:
                    # Gera HTML dos extratos
                    html_extratos = app.gerar_html_extratos(dados_filtrados)
                    st.components.v1.html(html_extratos, height=600, scrolling=True)
                    
                    # Botão para download
                    csv = dados_filtrados.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"extratos_processados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Nenhuma transação encontrada com os filtros aplicados.")
                
                # Mostra erros se houver
                if erros:
                    st.subheader("⚠️ Erros Encontrados")
                    for erro in erros:
                        st.error(erro)
            else:
                st.error(f"❌ Erro no processamento: {erros}")

if __name__ == "__main__":
    main()