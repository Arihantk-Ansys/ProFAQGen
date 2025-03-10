import os  
import json  
import time  
from openai import AzureOpenAI 
from retry import retry 

api_base = os.environ.get('api_base_300k')  
api_key = os.environ.get('api_key_300k')  
deployment_name = "gpt-4o"  
api_version = "2024-02-15-preview"  
client = AzureOpenAI(  
    api_key=api_key,  
    api_version=api_version,  
    base_url=f"{api_base}/openai/deployments/{deployment_name}"  
) 

def OpenAI_PII_removal(incoming_chunk, document_context=""):

    Ansys_products = ['Discovery', 'Spaceclaim', 'Sound', 'Additive Print', 'Additive Suite', 'Avxcelerate Autonomy', 'Avxcelerate Headlamp', 'Avxcelerate Sensors', 'Cloud Direct', 'Gateway Powered by AWS', 'Minerva', 'ModelCenter', 'Optislang', 'Odtk', 'Stk', 'Dme Component Libraries', 'Rf Channel Modeler', 'Twin Builder', 'Emc Plus', 'Charge Plus', 'Hfss', 'Icepak', 'Maxwell', 'Motor-cad', 'Nuhertz Filtersolutions', 'Q3d Extractor', 'Siwave', 'Synmatrix Filter', 'Conceptev', 'Scade Architect', 'Scade Display', 'Scade One', 'Scade Solutions for Arinc 661 Compliant Systems', 'Scade Suite', 'Scade Test', 'Blademodeler', 'Cfx', 'Chemkin-pro', 'EnSight', 'Fensap-ice', 'Fluent', 'Forte', 'Model Fuel Library', 'Polyflow', 'Rocky', 'Thermal Desktop', 'Turbogrid', 'Vista Tf', 'Granta Selector', 'Granta Mi Enterprise', 'Granta Mi Pro', 'Granta Materials Data', 'Materials Data for Simulation', 'Granta Edupack', 'Granta Collaborations & Partnerships', 'Lumerical Fdtd', 'Lumerical Mode', 'Lumerical Multiphysics', 'Lumerical Interconnect', 'Lumerical Cml Compiler', 'Zemax Opticstudio', 'Speos', 'Digital Safety Manager', 'Medini Analyze', 'Medini Analyze for Cybersecurity', 'Medini Analyze for Semiconductors', 'Clock Fx', 'Exalto', 'Paragonx', 'Pathfinder', 'Pathfinder-sc', 'Powerartist', 'Raptorh', 'Raptorqu', 'Raptorx', 'RedHawk-sc', 'Redhawk-sc Electrothermal', 'Redhawk-sc Security', 'Totem', 'Totem-sc', 'Velocerf', 'Voltage-timing Flow', 'Autodyn', 'Forming', 'Ls-dyna', 'Mechanical', 'Motion', 'Ncode Designlife', 'Sherlock', 'Mechanical Apdl', 'Mapdl', 'Apdl', 'Workbench', 'SimAI', 'AnsysGPT', 'EMIT', 'HFSS SBR+']
    system_message = f"""
      You are a legal expert in data anonymization, tasked with ensuring privacy and confidentiality in the provided text. Please review the guidelines below carefully before commencing the anonymization process. In case you are unable to locate any identifiers as outlined in the guidelines below, and believe that anonymization isn't necessary, strictly rewrite the input text precisely as provided.: \n
      0. Strictly do not remove any text which is not a PII or company's internal information. It was observed that while anonymizing the provided text, there rephrased (or rewritten) version by you has a significant drop in the word count, which is not advisable. \n
      1. Personal Information: Anonymize all personal names, emails, phone numbers, and any other identifiable personal information. For personal names, rather than using placeholders like '[Person A]' or '[Person B]', opt for general terms that are informed by the context. While anonymizing personal names, you can refer to the context from here: {document_context}.\n Try to remove email IDs, phone numbers, websites if contextual anonymization is not possible. 
      2: Priority should be given to anonymize emails, phone numbers, websites, and website links by replacing with more general phrases based on the context. For instance, if the original text contains 'john_doe@gmail.com', replace it with something like 'contact the provided email'. Similarly, if there is a phone number like '123-456-7890', substitute it with something like 'contact the provided phone number'. If the original text has a website address such as 'www.example.com', replace it with something like 'visit the provided website. \n
      3. Do not anonymize any references to the company 'Ansys'. Anonymize the names of all entities other than Ansys, including but not limited to other companies, institutes, organizations, government authorities, universities, schools, sports teams, student teams, events, programs, and projects. Replace the names with generic descriptors (e.g., 'a government energy agency' instead of 'UK Atomic Energy Authority'. 'a major aerospace and defense company' instead of 'Lockheed Martin'. 'a prominent European research organization ' instead of 'European Organization for Nuclear Research (CERN)'. 'a German university' instead of 'the University of Stuttgart'.). While anonymizing, you can refer to the context from here: {document_context}. \n
      4. Handling References to Ansys Products: Do not anonymize, replace or remove references to Ansys Products in the provided text. Refer to the provided list of Ansys products: '{Ansys_products}'. Be aware that references to these products in the text might precede with the 'Ansys' prefix. This product list serves as a guide and is not exhaustive. If you encounter a tool or product that is not on the list, check for contextual clues or common naming conventions, such as the use of 'Ansys' in the product name (e.g., 'Ansys Workbench', 'Ansys Path FX'). If the association with Ansys is ambiguous, assume the product is an Ansys product and do not anonymize, replace or remove it. \n 
      5: When you come across any non-Ansys tools, products, softwares, hardware products, trademark in the text, strictly anonymize them. To do this, use generic descriptions that encapsulate the type of products, tools, or software without exposing their brand or model. For example, instead of "TL4X-SAP", use "a certain object lens", or replace specific camera models like "Hammamatsu Orca-Flash4.0 V3" and "Andor Zyla 4.2 PLUS" with "certain popular cameras". While anonymizing, you can refer to the context from here: {document_context}.  \n
      6. If you encounter any ambiguous PII that is not clearly outlined in these instructions, use your best judgment to anonymize it while preserving the context of the text. \n
      7. Maintain the original context and meaning of the text. \n
      8. Avoid Placeholders: Rather than using placeholders like 'Person A' or 'Company X', opt for general terms that are informed by the context (e.g., 'a leading automotive manufacturer' or 'a senior researcher'). \n
      9. Handling Scientific Models: Do not anonymize mentions of physical or scientific models, even if they are named after inventors or scientists. These models are considered general knowledge and their names do not constitute personally identifiable information. Maintain these names to preserve the scientific context and meaning of the text.
      """
    # Prepare the user prompt with additional details  
    user_message = (  
        "Remove personal information from this text using the guidelines provided:\n"  
        f"{incoming_chunk}"  
    )  
    
    @retry(Exception, tries=3, delay=2)
    def llm_call():
        response = client.chat.completions.create(  
            model=deployment_name,  
            messages=[  
                {"role": "system", "content": system_message},  
                {"role": "user", "content": user_message}  
            ],  
            temperature=0.01,
            max_tokens=2000,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0
        ) 
        return response 
    
    try:
        response = llm_call()  
    except Exception as e:  
        if e.status_code == 429:  
            print("Rate limit exceeded, sleeping for 2 seconds")  
            time.sleep(2)  
        else:  
            raise e  # If it's a different error, raise it  
  
    res = response.choices[0].message.content 
    return res