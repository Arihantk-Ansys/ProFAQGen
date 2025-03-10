import openai
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import (
    VectorizedQuery,
    VectorFilterMode,    
)
import os
import re
from azure.core.credentials import AzureKeyCredential
import difflib
import json
import logging
from langchain_openai import AzureChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.docstore.document import Document
from openai import AzureOpenAI
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type,stop_after_delay
from langchain.chains import SequentialChain

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler  
handler = logging.FileHandler('logger.log')
handler.setLevel(logging.INFO)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Add the handlers to the logger
logger.addHandler(handler)
logger.addHandler(console_handler)

openai.api_type = "azure"

openai.api_key = os.getenv("OPEN_AI_API_KEY_80K")
openai.api_base = os.getenv("OPEN_AI_API_BASE_80K")
api_version = "2023-11-01"
vector_store_password = os.getenv("ADMIN_KEY")
# vector_store_address = os.getenv("AZURE_SEARCH_ENDPOINT")
service_name = 'acegpt-cognitive-search-public'
vector_store_address = "https://{}.search.windows.net/".format(service_name)

index1 = "ansys-dot-com-marketing"
index2 = "external-product-documentation-public"
index3 = "external-product-documentation-public-25r1"
index4 = "external-release-notes"
index5 = "external-sfdc-km"
index6 = "external-forum"
index7 = "external-granular-public-innovation-courses"
index8 = "external-granular-public-knowledge-material"
index9 = "external-granular-public-youtube"
index10 = "external-learning-hub"
index11 = "external-nptel-data"

client = AzureOpenAI(
api_key = os.getenv("OPEN_AI_API_KEY_80K"),  
api_version = "2023-05-15",
azure_endpoint =os.getenv("OPEN_AI_API_BASE_80K") 
)

# Function to safely get the value for sorting  
def safe_get_reranker_score(item):  
    # return item.get('@search.reranker_score', float('-inf'))  
    return item.get('@search.reranker_score', float('-inf')) if item.get('@search.reranker_score') is not None else float('-inf')

def converter(results_list):
    document_list = []
    for result in results_list:
        for doc in result:
            document = doc['content']
            chunk = Document(page_content=document)
            document_list.append(chunk)
    return document_list

def extract_fields(query, physics):  
    # Defining possible values for each field  
    physics_values = ["structures", "fluids", "electronics", "structural mechanics", "discovery", "optics", "photonics", "python", "scade", "materials", "stem", "student", "fluid dynamics", "semiconductors"]
    type_of_asset_values = ["aic", "km", "documentation", "youtube", "general_faq", "alh", "article", "white-paper", "brochure"]
    product_values = ["additive prep", "additive print", "autodyn", "avxcelerate", "cfx", "cfx pre", "cfx solver", "cfx turbogrid", "clock jitter flow", "cloud direct", "composite cure sim", "composite preppost", "designmodeler", "designxplorer", "diakopto", "discovery", "embedded software", "ensight", "exalto", "fluent", "forte", "gateway", "granta", "hfss", "icem cfd", "icepak", "ls-dyna", "lsdyna", "lumerical", "maxwell", "mechanical", "mechanical apdl", "medini", "meshing", "minerva", "motion", "ncode designlife",  "pathfinder", "pathfinder-sc", "powerartist", "pragonx", "primex", "raptorh", "raptorx", "redhawk-sc", "redhawk-sc electrothermal", "redhawk-sc security", "rocky", "scade", "sherlock", "siwave", "spaceclaim", "spaceclaim directmodeler", "stk", "totem", "totem-sc", "twin builder", "velocerf", "voltage-timing", "workbench platform"] 
    
    # Initializing the fields with None  
    physics = physics  
    type_of_asset = None 
    product = None 

    # Sort the values by length in descending order
    # physics_values.sort(key=len, reverse=True)
    type_of_asset_values.sort(key=len, reverse=True)
    product_values.sort(key=len, reverse=True)


    for value in type_of_asset_values:  
        if all(re.search(r'\b' + re.escape(word) + r'\b', query, re.IGNORECASE) for word in value.split()) and type_of_asset is None:  
            type_of_asset = value  
            break
    for value in product_values:  
        if all(re.search(r'\b' + re.escape(word) + r'\b', query, re.IGNORECASE) for word in value.split()) and product is None:  
            product = value
            break

    # Split the query into words
    words = query.split()


    if type_of_asset is None:
        for value in type_of_asset_values:
            # if difflib.get_close_matches(value.lower(), [query.lower()], n=1, cutoff=0.9):
            #     type_of_asset = value
            for word in words:
                if difflib.get_close_matches(value, [word], n=1, cutoff=0.75):
                    type_of_asset = value
                    break
    if product is None:
        for value in product_values:
            for word in words:
                if difflib.get_close_matches(value, [word], n=1, cutoff=0.8):
                    product = value
                    break

    # If 'course' is in the query and we haven't found a value for type_of_asset yet  
    if 'course' in query.lower() and type_of_asset is None:  
        type_of_asset = "aic"

    if 'apdl' in query.lower():  
        product = "mechanical apdl"

    if 'lsdyna' in query.lower():  
        product = "ls-dyna"

    # Return the fields  
    return physics, type_of_asset, product


def get_embeddings(text):

    response = client.embeddings.create(
        input = text,
        model= "text-embedding-ada-002"  # model = "deployment_name".
    )
    # embeddings = response.model_dump_json(indent=2)
    embedding = response.data[0].embedding
    # print(response.model_dump_json(indent=2))
    return embedding 

def semantic_hybrid_search_with_filter(query, top_k, physics, product, product_main, type_of_asset, vector_store_password, vector_store_address, index_name, api_version, value, fields, kind, acs_fields ):
        
    search_client = SearchClient(vector_store_address, index_name, credential=AzureKeyCredential(vector_store_password), api_version=api_version)
    #Get the query embedding  
    vector_old = VectorizedQuery(kind=kind, k_nearest_neighbors=30, vector=value, fields=fields)
    
    filter_data = []
            
    if physics is not None:  
        if 'None' not in physics:  
            physics_values = physics.split(',')  
            physics_filter = ' or '.join([f"physics eq '{value.strip()}'" for value in physics_values])  
            filter_data.append(physics_filter)  
        else:  
            filter_data = None

    filter_query = ' or '.join(filter_data) if filter_data else None
    

    # print(f"filter_data is : {filter_query}")
    
    results = search_client.search(
        search_text=query,
        vector_queries=[vector_old],
        vector_filter_mode=VectorFilterMode.POST_FILTER,
        filter= filter_query, 
        query_type="semantic",
        semantic_configuration_name="my-semantic-config",
        top=top_k,
        select = acs_fields,
        # select = ["title", "url", "token_size", "physics", "typeOFasset", "content" ],
        include_total_count=True
    )
    
    # Convert the iterator to a list  
    results_list = list(results)  
    return results_list

 
llm = AzureChatOpenAI(
    api_key=openai.api_key,
    azure_endpoint=openai.api_base,
    deployment_name = "gpt-4o",
    openai_api_version = "2024-02-15-preview"
)  
  
def get_relevant_chunks(user_input,physics,product,type_of_asset):  
    acs_fields = ["token_size", "physics", "typeOFasset", "product", "version", "weight", "content", "sourceTitle_lvl1", "sourceTitle_lvl2","sourceTitle_lvl3", "sourceURL_lvl1", "sourceURL_lvl2", "sourceURL_lvl3"]
    # user_input = "I have a case from a customer MCM Technologies test pvt ltd and they are looking to model creep flow. Do you have any suggestions on what product to use and how to set it up? I am going to meet them next and I would like to have this information before I head to their office in Waterloo. The customer Rahul Kumar who is leading this project was also wondering if there is any training that Ansys provides for to map products to use case. Your timely help is appreciated.As far as I know EnSight does provide the parallel run capability and it is a powerful tool to visualize the large data such as in your case the large rotating domain. Here is the link of user guide for EnSight : 2.1. Reader Basics and here is one course on EnSight, hope this is helpful Ansys Learning Hub"
    query_vector = get_embeddings(user_input)
    # physics = None
    # type_of_asset = None
    # product = None
    chunks = []
    res1 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index1,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='content_vctr, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )
    chunks.append(res1)
    res2 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index2,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='contentVector, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res2) 
    res3 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index3,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='contentVector, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res3)  
    res4 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index4,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='contentVector, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res4) 
    res5 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index5,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='content_vctr, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res5) 
    res6 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index6,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='contentVector, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res6) 
    res7 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index7,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='contentVector, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res7) 
    res8 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index8,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='contentVector, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res8) 
    res9 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index9,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='contentVector, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res9) 
    res10 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index10,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='contentVector, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res10) 
    res11 = semantic_hybrid_search_with_filter(  
                query=user_input,   # user query
                value=query_vector,   # The vector representation of a search query
                index_name=index11,   # ACS index name
                physics=physics,   # filter value for physics
                type_of_asset=type_of_asset,   # filter value for type_of_asset
                product=product, # filter value for product
                product_main=None,  # filter value for product access-point: prod-mechanical/prod-fluent
                top_k=3,   # The number of search results to retrieve.
                fields='content_vctr, sourceTitle_lvl1_vctr',   # Vector Fields of type Collection(Edm.Single) to be included in the vector
                kind='vector',   
                vector_store_password=vector_store_password,   # ACS_SEARCH_ADMIN_KEY
                vector_store_address=vector_store_address,   # ACS_SEARCH_ENDPOINT
                api_version=api_version,   # ACS API version
                acs_fields=acs_fields   # The list of fields to retrieve as part of Context.
            )   
    chunks.append(res11) 
    return chunks

def compiler(summary, retrieved_data, switch):
    openai.api_base = "https://ansysaceaiservicegpteastus2.openai.azure.com/"
    openai.api_key = os.getenv("OPEN_AI_API_KEY_80K")
    # Set up the AzureOpenAI service
    llm = AzureChatOpenAI(
        api_key=openai.api_key,
        azure_endpoint=openai.api_base,
        deployment_name = "gpt-4o",
        openai_api_version = "2024-05-01-preview"
    )
    if switch == 'prompt1':
        system_prompt1 = (
            """You are an intelligent assistant that has been tasked with synthesizing a *Email discussion* and *related chunks* of information into a clear, coherent, and concise response. \n"
            "Imagine you are explaining this to a third person who has no prior knowledge of the subject. \n"
            "Try filling the knowledge gap in the summary with the help of related chunks provided. \n"
            "Your response should be *technically sound*, *akin to a science journal paper*, and should not deviate from the topic. \n"  
            "The length of the final response should be proportionate to the length of the summary and the chunks combined. \n"  
            "Use the provided summary and chunks to generate this response. Do not hallucinate or use your base knowledge, strictly rely on the provided summary and chunks. \n" 
            "\n\n"  
            "email_discussion: {summary}"  
            "\n\n"  
            "Chunks:"  
            '\n{context}'
            """
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt1),
        ])

        # Create the chain to combine the documents
        combine_chain = create_stuff_documents_chain(llm, prompt)

        final_response = combine_chain.invoke({"email_discussion": summary, "context": retrieved_data})
        # print(final_response)
        return final_response
    
    if switch == 'prompt2':
        system_prompt2 = (
            """
            An AI Assistant for Summarizing Email Discussion.
            You are an AI assistant that has been tasked with summarizing an email discussion of information, ensuring all topics are covered in the summary that are there in  email discussion\n"
            "Imagine you are explaining this to a third person who has no prior knowledge of the subject. \n"
            "Your response should be *technically sound*, *akin to a science journal paper*, and should not deviate from the topic. \n"  
            "The length of the final response should be proportionate to the length of the email discussion. \n"  
            "Use only the provided email discussion to generate this response. Do not hallucinate or use your base knowledge, strictly rely on the provided email discussion.\n
            
            
            "Email discussion: {context}" 
            """
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt2),
        ])

        # Create the chain to combine the documents
        combine_chain = create_stuff_documents_chain(llm, prompt)
        
        # Invoke the chain to get the summary
        # Then in your prompt2 branch:
        summary_doc = Document(page_content=summary)
        final_response = combine_chain.invoke({"context": [summary_doc]})
        print(final_response)
        return final_response  

def enrich_data(user_input,physics=None,product=None,type_of_asset=None):     

    system_prompt_template = (    
        "You are an intelligent assistant that has been tasked with enriching the given conversation with the help of chunks provided. "    
        "Imagine you are explaining this to a third person who has no prior knowledge of the subject. "    
        "Your response should be technically sound, akin to a science journal paper, and should not deviate from the topic. "    
        "The length of the final response should be proportionate to the length of the summary and the chunks combined. "
        "Don't lose track of actual conversation, don't change facts and methods (steps) provided." 
        "Keep the enriched text as concise as possible, do not exceed more than 150% of total words provided in Text."
        "Use the provided text and chunks to generate this response. Do not hallucinate or use your base knowledge, strictly rely on the provided summary and chunks. "    
        "\n\n"    
        "Text: {summary}"    
        "\n\n"    
        "Chunks:"    
        '\n{context}'    
    ) 

    prompt = ChatPromptTemplate.from_messages([    
        ("system", system_prompt_template),    
    ])    
      
    # Create the chain to combine the documents    
    combine_chain = create_stuff_documents_chain(llm, prompt)    
      
    # Get relevant chunks data    
    chunks = get_relevant_chunks(user_input,physics,product,type_of_asset)  
    # chunks.sort(key=safe_get_reranker_score, reverse=True)
    # final_list = converter(results_list=context)
    final_list = converter(results_list=chunks[:20]) 
    final_response = combine_chain.invoke({"summary": user_input, "context": final_list})    
    # print(final_response)   
    return final_response 

# user_input = "I have a case from a customer MCM Technologies test pvt ltd and they are looking to model creep flow. Do you have any suggestions on what product to use and how to set it up? I am going to meet them next and I would like to have this information before I head to their office in Waterloo. The customer Rahul Kumar who is leading this project was also wondering if there is any training that Ansys provides for to map products to use case. Your timely help is appreciated.As far as I know EnSight does provide the parallel run capability and it is a powerful tool to visualize the large data such as in your case the large rotating domain. Here is the link of user guide for EnSight : 2.1. Reader Basics and here is one course on EnSight, hope this is helpful Ansys Learning Hub"
# print(enrich_data(user_input))