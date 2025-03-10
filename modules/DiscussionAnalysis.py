import os
import time 
import openai
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.chains import SequentialChain
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type,stop_after_delay
import pandas as pd

openai.api_type = "azure"
openai.api_key = os.getenv("OPEN_AI_API_KEY_80K")
openai.api_base = "https://ansysaceaiservicegpteastus2.openai.azure.com/"
api_version = "2024-05-01-preview"
vector_store_password = os.getenv("ADMIN_KEY")
service_name = 'acegpt-cognitive-search-public'
vector_store_address = "https://{}.search.windows.net/".format(service_name)

chat_llm = AzureChatOpenAI(
    streaming=True,
    api_key=openai.api_key,
    azure_endpoint=openai.api_base,
    deployment_name = "gpt-4o",
    openai_api_version = "2024-05-01-preview",
    verbose=True
)

###Classification chain starts here 
# Guideline as backup 
# Technical depth on the ANSYS technical forum refers to the extent
# to which discussions and solutions explore complex and advanced topics related to ANSYS software, simulation, and engineering. It often involves in-depth analysis, problem-solving, and the sharing of advanced techniques and insights by experienced users and experts."
# In other words, technical depth on the ANSYS technical forum signifies the degree to which discussions delve into intricate details and advanced aspects of ANSYS software, engineering science, physics, simulations, computational modelling or industrial specific discussion.
prompt1_template = """
# AI Assistant for Conversation/Discussion Analysis
As an AI assistant specialized in engineering science, physics, all kinds of numerical methods used in simulation, computational modeling, and Ansys tools, your role is to critically analyze email discussions and classify them based on specified criteria.
For evaluation be highly critical, as a bad evaluation will affect the Ansys business, Throughly understand, focus on  Attention to Detail, keep High Expectations, excercise Thoroughness and use Deep Subject Matter Expertise to provide final judgement. After the task is completed, re-review the final score and classification,  
and if the task is not completed with higher accuracy and satisfaction re-perform the task. Keep iterating till the satisfaction and accuracy in evaluation is acheived.
## Discussion Quality Analysis
1. **Read the Discussions**:
	-Carefully read the email discussions. Comprehend it assuming it can be a complex nested technical discussion where Ansys customer are raising discussion to resolve there pain points.
	-Assess if the data, coming from a technical forum, is suitable and sufficient to be summarized as technical knowledge content like knowledge material, technical bits , FAQ,probable solution for Ansys customers. Be extremely thorough in this analysis given the impact on Ansys' reputation.
2. **Scoring**: Rate the combined discussions on a scale of 0 to 1 based on how suitable it is as Ansys technical knowledge content.
    - **Bad (< 0.4)**:combined discussions contains inaccurate or misleading information, off topic conversation, lacks technical depth, lacks Technical soundness and provides no value to the Ansys community.
    - **Ok (0.4-0.8)**:combined discussions not comprehensive; but could serve as a basic resource; or combined discussions is insightful, accurate, and could serve as a base content for solid technical knowledge content.
    - **Good (>0.8)**:combined discussions is exceptionally detailed, comprehensive, provided workable, definative solution providing high value as an expert-level base content for solid technical knowledge content.
3. **Guideline for Decision Making**: 
	-Your decision should focus on the technical depth,soundness, quality, and completeness of the discussion.
    -Keep in mind that some solutions specific to Ansys tools may not require extensive technical depth but are nonetheless valuable; such cases should be considered a "LLM"
    -Cross check that the provided resolutions for the raised requests in the discussion had sufficient technical depth / soundness/claritty. If not classify as fail or Human. Be cautious as sometime low technical depth solution can be to the point tool solution, use the judgement cautiously.
    -If the raised questions/requests is ambiguos, long without much technical depth like code snippet/out file of ansys such that provided context is not enough to explain the customer pain point clearly, classify as fail.
	-When uncertain between LLM  and  Human, choose Human  to protect Ansys' reputation.
4. **Uncertainty**: If uncertain whether to score as( Bad/Ok: opt for Bad,Ok/Good: opt for Ok)to protect Ansys'   reputation.
5. **Final Score**: Return a final score based on collective judgment from steps 1-3.
## Classification Rules
	-**Good to go for Classification Agent**:Score>0.8
	-**LLM Data Enrichment**: 0.4<Score<0.8
	-**Discarded**: Score <0.4
6.  **Guidelines for deciding open-ended and close-ended discussions
    **open ended**
    - Check if the discussion had some conclusion. If the discussion don't have any conlusion it is a open ended discussion.
    - Scan the discussion for mentions of words such as 'call', 'meeting', 'catch-up', or any synonyms that suggest a verbal or real-time conversation.
    - If any such keywords are present, infer that the discussion likely occurred in a conversational setting, making it open-ended. Mark it accordingly.
    **close ended**
    - If no such keywords are found, analyze the discussion from a third-person perspective.
    - Determine if the main question or topic is clearly presented.
    - Evaluate whether the question was answered clearly and comprehensively within the text.
    - If the topic is clear and the question is answered, classify it as a close-ended discussion. 
7. If the discussion is close ended mark it as integer *1* else if discussion is open ended then mark it as integer *0*.
### Output Format
The final result1 must be in the following data structure:
[
   "classification":Classification as Good to go for Classification Agent/LLM Data Enrichment/Discarded,
   "explanation":Reason for classification as Good to go for Classification Agent/LLM Data Enrichment/Discarded,
   "score":Final Score score for classification // floating point value,
   "discussion_type": Discussion type as *close ended* mark it 1/ *open ended* mark it 0. 
]	
Respond only with the output in the exact format specified, with no explanation or conversation.
**input**: {text}
result1:	
"""
prompt1_prompt_template = PromptTemplate(input_variables=["text"], template=prompt1_template)
prompt1_chain = LLMChain(llm=chat_llm, prompt=prompt1_prompt_template, output_key="result1")
prompt2_template="""
Only provide the Associated value of classification as Good to go for Classification Agent/LLM Data Enrichment/Discarded and score from input data , and if key value are missing report none.
Use this format to report
[
    "classification":as Good to go for Classification Agent/LLM Data Enrichment/Discarded,
    "explanation":Reason for classification as Good to go for Classification Agent/LLM Data Enrichment/Discarded,
    "score":score from result1// floating point value
    "discussion_type": Discussion type as *close ended* mark it 1/ *open ended* mark it 0.
]
Respond only with the output in the exact format specified, no need to further trying to make it in Json, with no explanation or extra detail.
input:{result1}
Associated value:
"""
prompt2_prompt_template = PromptTemplate(input_variables=["result1"], template=prompt2_template)
prompt2_chain = LLMChain(llm=chat_llm, prompt=prompt2_prompt_template, output_key="Associated value")
overall_chain = SequentialChain(
    chains=[prompt1_chain,prompt2_chain],
    input_variables=["text"],
    # Here we may or may not return multiple variables
    output_variables=["Associated value"],
    )
@retry(retry=retry_if_exception_type(openai.RateLimitError), wait=wait_random_exponential(min=30, max=240), stop=stop_after_attempt(10) | stop_after_delay(10))  
def run_overall_chain(input_data):  
    result = overall_chain.run(input_data)  # Your main function call 
    return result

def discussion_main(BODY, case_no=None):
    output_folder_path_discussion_analysis = "discussion_analysis_report" 
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder_path_discussion_analysis):
        os.makedirs(output_folder_path_discussion_analysis)
        print(f"Created output directory: {output_folder_path_discussion_analysis}")                 
    input_data = {"text": BODY}
    report = []
    
    # If case_no is not provided, use a default name
    if case_no is None:
        case_no = f"unnamed_case_{time.strftime('%Y%m%d_%H%M%S')}"
    
    for i in range(1, 6):  # Iterates 5 times
        data = run_overall_chain(input_data)
        print(f"Raw output in iteration {i}: {data}")
        
        try:  
            # First clean the data  
            data_clean = data.replace("Associated value:", "").strip()  
        
            # Create a proper JSON structure with regex patterns  
            import re  
        
            # Extract values from the malformed JSON using regex  
            classification_match = re.search(r'"classification":?\s*(?:as\s*)?(.*?)(?:,|\n|$)', data_clean)  
            explanation_match = re.search(r'"explanation":?\s*(?:Reason for classification as\s*)?(.*?)(?:,|\n|$)', data_clean)  
            score_match = re.search(r'"score":?\s*(?:score from result1\/\/\s*floating point value|)(.*?)(?:,|\n|$)', data_clean)  
            discussion_type_match = re.search(r'"discussion_type":?\s*(?:Discussion type as \*close ended\* mark it 1\/\s*open ended mark it 0\.|)(.*?)(?:,|\n|\]|$)', data_clean)  
        
            # Determine classification based on found keywords  
            if classification_match:  
                classification_value = classification_match.group(1).strip() 
                # discussion_type = int(discussion_type_match.group(1).strip()) if discussion_type_match and discussion_type_match.group(1).strip().isdigit() else 0 
                if "LLM Data Enrichment" in classification_value:  
                    classification = "LLM Data Enrichment" 
                    discussion_type = 1 
                elif "Classification" in classification_value:  
                    classification = "Good to go for Classification Agent"
                    discussion_type = 1  
                else:  
                    classification = "Discarded"
                    discussion_type = 0  
            else:  
                classification = "Unknown" 
                discussion_type = 0 
        
            # Create a proper JSON object  
            extracted_data = {  
                "classification": classification,  
                "explanation": explanation_match.group(1).strip() if explanation_match else "No explanation provided",  
                "score": float(score_match.group(1).strip()) if score_match and score_match.group(1).strip() else 0.0,  
                "discussion_type": discussion_type  
            }  
        
            list_data = [extracted_data]  
            
        except Exception as e:
            print(f"Failed to parse in iteration {i}: {str(e)}")
            # Create fallback data
            list_data = [{
                'classification': 'Error in parsing',
                'explanation': f'Could not parse response: {str(e)}',
                'score': 0.0,
                'discussion_type': 0
            }]

        excel_filename = 'report.xlsx'
        sheet_name = 'report'
        # Save the report in excel file.  
        output_path = os.path.join(output_folder_path_discussion_analysis, excel_filename)  
        try:  
            df = pd.read_excel(output_path, sheet_name=sheet_name, engine='openpyxl')    
        except FileNotFoundError:  
            df = pd.DataFrame(columns=['iteration','case_no','classification', 'explanation', 'score', 'discussion_type'])
        except ValueError:
            df = pd.DataFrame(columns=['iteration','case_no','classification', 'explanation', 'score', 'discussion_type'])
        
        report.append({
            'iteration': i,
            'case_no': case_no,  
            'classification': list_data[0]['classification'],  
            'explanation': list_data[0]['explanation'],  
            'score': list_data[0]['score'],  
            'discussion_type': list_data[0]['discussion_type']
        })
        
    # Save the complete report to Excel
    new_df = pd.DataFrame(report)  
    updated_df = pd.concat([df, new_df], ignore_index=True)  
    updated_df.to_excel(output_path, sheet_name=sheet_name, index=False)  
    print(f"report saved for case: {case_no}")
    
    return report

def get_report_modes(report):
    """
    Takes a report list and returns the most common (mode) values for discussion_type and classification.
    Args:
        report (list): List of dictionaries containing report data   
    Returns:
        tuple: A tuple containing (mode_discussion_type, mode_classification)
    """
    from collections import Counter
    
    # Extract discussion_types and classifications from the report
    discussion_types = [entry['discussion_type'] for entry in report]
    classifications = [entry['classification'] for entry in report]
    
    # Find the most common values
    mode_discussion_type = Counter(discussion_types).most_common(1)[0][0]
    mode_classification = Counter(classifications).most_common(1)[0][0]
    
    return mode_discussion_type, mode_classification
                    
# body=["It appears that you are encountering an issue with retrieving the mixture-level variables (CFFs) from your saved case and data files in an Eulerian 2-phase simulation using the Steady Statistics sampling option in Ansys Fluent. Here are a few steps and considerations that might help you diagnose and potentially recover the missing data:\n\n1. **Check Sampling Settings**: Ensure that the sampling settings were correctly configured and saved in the case file. Verify that the CFFs were properly defined and selected in the Sampling Options panel and zone-specific sampling settings.\n\n2. **Verify Data Integrity**: Confirm that the case and data files were not corrupted during the saving or reopening process. Sometimes, file corruption can lead to loss of data or incorrect data being displayed.\n\n3. **Review Sampling Session**: When reopening the case and data files, check if the sampling session is still active and if the statistics have not been reset. If the session was inadvertently closed or reset, the statistics might not be available.\n\n4. **Check for Updates or Patches**: Ensure that you are using the latest version of Ansys Fluent. Sometimes, software updates or patches can resolve issues related to data handling and retrieval.\n\n5. **Consult Documentation**: Review the Ansys Fluent documentation for any specific instructions or known issues related to the Steady Statistics sampling option and CFFs. The documentation might provide insights or solutions to the problem you are facing.\n\n6. **Contact Ansys Support**: If the issue persists, consider reaching out to Ansys support for assistance. Provide them with detailed information about your simulation setup, the steps you followed, and the problem you are encountering. They might be able to offer a solution or workaround.\n\n7. **Backup and Redo Sampling**: As a last resort, if you are unable to recover the missing data, you might need to redo the sampling process. Ensure that you create backups of your case and data files at different stages to prevent data loss in the future.\n\nBy following these steps, you should be able to identify the cause of the issue and potentially recover the missing mixture-level variables in your simulation.","Dear User,\n\nThank you for submitting your Ansys support case in the Ansys Customer Support Space. This is an automatic reply to let you know we just received the following case.\n\nCase Number:00146437  \nSubject: Steady statistics results are missing after reopening the saved case and data files  \nDescription: I have computed a long run to obtain iteration-averaged results in an Eulerian 2-phase simulation using the Steady Statistics sampling option. I have created some CFFs for variables to be averaged and then selected them in the Sampling Options panel, as well as in zone-specific sampling for selected zones. I performed the run over many iterations and the averages were computed. At the time when the active averaging session was still open, I was able to extract as many of the averages that I needed at the time without issue through the Volume and Surface Reports, Steady-Statistics category for either mixture or phase-specific variables. The case and data files were saved with the sampling still activate, the statistics not reset and the session closed. The problem is that some time later, I needed to go back an reopen the saved case & data files with what I believed had the statistics still saved in it. Opening the cas/dat files, I can see the number of iterations that were sampled and is correct. Using surface and volume reports for the Steady-Statistics category, the phase-specific averages for Mean Velocity, Volume fraction, Static Temperature, etc. seem to be present but the mixture-level variables (i.e., the CFFs) are mostly zero including the \"-dataset\" variables. \n\nWould you know what went wrong and how to recover?\n\nYour support case has been routed to our support team and you should hear back from us shortly. In the meantime, if you have any questions or comments regarding your support case, please feel free to either reply directly to this email or click on the button below to navigate to your support case in the Ansys Customer Support Space.\n\nThank you.\n\nAnsys Technical Support"]
# reports=discussion_main(body,case_no=146437)
# discussion_type,classification=get_report_modes(reports)
# print(discussion_type,classification)
