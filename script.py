import os
import sys
import glob
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Verificar e instalar dependências necessárias
def verificar_instalar_dependencias():
    try:
        import pip
        dependencias = [
            "crewai",
            "langchain-community",
            "langchain-openai",
            "langchain",
            "pypdf",
            "python-dotenv"  # Adicionando python-dotenv como dependência
        ]
        
        for dep in dependencias:
            try:
                __import__(dep.replace("-", "_"))
                print(f"✓ {dep} já está instalado")
            except ImportError:
                print(f"Instalando {dep}...")
                pip.main(['install', dep])
                print(f"✓ {dep} instalado com sucesso")
    except Exception as e:
        print(f"Erro ao instalar dependências: {str(e)}")
        sys.exit(1)

# Verificar e instalar dependências antes de importar
verificar_instalar_dependencias()

# Agora importamos os módulos necessários
from crewai import Agent, Task, Crew, Process
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI

# Configuração da API OpenAI (agora usando variável de ambiente)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Erro: Chave da API OpenAI não encontrada no arquivo .env")
    print("Por favor, crie um arquivo .env com sua chave OPENAI_API_KEY")
    sys.exit(1)

# Modelo de linguagem
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Agente para extrair texto do PDF
extrator_pdf = Agent(
    role="Extrator de PDF",
    goal="Extrair todo o conteúdo textual de arquivos PDF com precisão",
    backstory="Sou especializado em processar documentos PDF e extrair seu conteúdo textual completo, mantendo a estrutura original do documento tanto quanto possível.",
    verbose=True,
    llm=llm
)

# Agente para resumir o conteúdo
resumidor = Agent(
    role="Resumidor de Conteúdo",
    goal="Criar resumos concisos e informativos que capturam as informações essenciais do texto",
    backstory="Sou especializado em analisar grandes volumes de texto e identificar os pontos-chave, criando resumos que preservam as informações mais importantes.",
    verbose=True,
    llm=llm
)

# Agente para salvar o resultado
salvamento = Agent(
    role="Gerenciador de Arquivos",
    goal="Salvar os dados processados em arquivos de texto de forma organizada",
    backstory="Sou responsável por garantir que todas as informações processadas sejam salvas corretamente em arquivos de texto, com nomes apropriados e em locais acessíveis.",
    verbose=True,
    llm=llm
)

def extract_text_pdf(pdf_path):
    """Function to extract text from PDF using LangChain."""
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        full_text = ""
        for page in pages:
            full_text += page.page_content + "\n\n"
        
        return full_text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_structured_fields(text):
    """Function to extract specific fields from text using LLM."""
    try:
        prompt = f"""
        Please extract the following fields from the text below. If a field is not found, return "N/A".
        Maintain the exact format specified:
        
        Text:
        {text}
        
        Required fields (FORMAT FIELD: VALUE):
        ORDER_DATE:
        ORDER_NUMBER:
        CONTRACT_NUMBER:
        ORDERER:
        BILLING_ADDRESS:
        DELIVERY_ADDRESS:
        SUPPLIER_ADDRESS:
        OUR_RANGE:
        OFFER_DATE:
        DELIVERY_DATE:
        DELIVERY_CONDITIONS:
        PAYMENT_TERMS:
        REMARKS:
        MATERIAL_NUMBER_KUNDE:
        MATERIAL_NUMBER_CCL:
        MATERIAL_DESCRIPTION:
        DRAWING_NUMBER:
        CROWD:
        PRICE_PER_UNIT:
        PRICE_PIECE:
        NET_AMOUNT:
        CURRENCY:
        COMMODITY_NUMBER:
        """
        
        response = llm.invoke(prompt).content
        return response
    except Exception as e:
        return f"Error extracting fields: {str(e)}"

def summarize_text(text, max_tokens=4000):
    """Function to extract complete information from text using LLM."""
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(text)
        
        final_summary = ""
        
        for i, chunk in enumerate(chunks):
            prompt = f"""
            Detailed analysis of text (part {i+1}/{len(chunks)}):
            
            {chunk}
            
            Please extract ALL relevant information from this text. Do not omit any important details.
            Your goal is to create a complete document containing all significant information from the original text.
            Include:
            - All facts, data, and statistics
            - All important dates and events
            - All names and entities mentioned
            - All conclusions and recommendations
            - Any technical or specific information
            
            Organize the information clearly and structured, but maintain ALL important details.
            """
            
            response = llm.invoke(prompt).content
            final_summary += response + "\n\n"
        
        if len(chunks) > 1:
            prompt_final = f"""
            Based on the detailed analyses below, create a complete and cohesive final document:
            
            {final_summary}
            
            Your goal is to consolidate all this information into a comprehensive single document.
            DO NOT simplify or omit important information.
            Organize the content logically and structured, maintaining ALL relevant details.
            """
            final_summary = llm.invoke(prompt_final).content
        
        return final_summary
    except Exception as e:
        return f"Error processing text: {str(e)}"

def salvar_texto(texto, caminho_saida):
    """Função para salvar texto em um arquivo."""
    try:
        # Garantir que o diretório exista
        diretorio = os.path.dirname(caminho_saida)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio)
        
        # Salvar o texto no arquivo
        with open(caminho_saida, 'w', encoding='utf-8') as arquivo:
            arquivo.write(texto)
        
        return f"Arquivo salvo com sucesso em: {caminho_saida}"
    except Exception as e:
        return f"Erro ao salvar o arquivo: {str(e)}"

def processar_pdf(caminho_pdf, caminho_saida):
    """Processa um único arquivo PDF e salva o resumo."""
    print(f"\n{'='*50}")
    print(f"Processando: {os.path.basename(caminho_pdf)}")
    print(f"{'='*50}")
    
    # Extrair texto do PDF
    print("Extraindo texto do PDF...")
    texto_extraido = extract_text_pdf(caminho_pdf)
    
    # Resumir o conteúdo
    print("Resumindo o conteúdo...")
    resumo = summarize_text(texto_extraido)
    
    # Salvar o resumo
    print("Salvando o resumo...")
    resultado = salvar_texto(resumo, caminho_saida)
    
    print(resultado)
    print(f"{'='*50}\n")

def main():
    # Criar pastas input e output se não existirem
    pasta_input = "input"
    pasta_output = "output"
    
    if not os.path.exists(pasta_input):
        os.makedirs(pasta_input)
        print(f"Pasta '{pasta_input}' criada. Por favor, coloque seus arquivos PDF nesta pasta.")
        return
    
    if not os.path.exists(pasta_output):
        os.makedirs(pasta_output)
    
    # Obter todos os arquivos PDF na pasta input
    arquivos_pdf = glob.glob(os.path.join(pasta_input, "*.pdf"))
    
    if not arquivos_pdf:
        print(f"Nenhum arquivo PDF encontrado na pasta '{pasta_input}'.")
        return
    
    print(f"Encontrados {len(arquivos_pdf)} arquivos PDF para processar.")
    
    # Processar cada arquivo PDF
    for pdf in arquivos_pdf:
        nome_arquivo = os.path.basename(pdf)
        nome_saida = os.path.splitext(nome_arquivo)[0] + ".txt"
        caminho_saida = os.path.join(pasta_output, nome_saida)
        
        processar_pdf(pdf, caminho_saida)
    
    print(f"Processamento concluído! Todos os resumos foram salvos na pasta '{pasta_output}'.")

if __name__ == "__main__":
    main()
