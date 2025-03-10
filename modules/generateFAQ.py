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
  
def generate_faq_with_llm(context_from_database,no_words=200): 
    if no_words<50: FAQ_limit=1
    elif 50<no_words<150: FAQ_limit=2
    elif 150<no_words<250: FAQ_limit=3
    else: FAQ_limit=4 
    format = """{"Question1": "question1 over here","Answer1": "answer for Question1","Question2": "question2 over here","Answer2": "answer for Question2",...}"""
    # Prepare the system message and user prompt  
    system_message = f"""
        You are a highly specialized technical knowledge extraction AI, focused on converting complex technical content into clear, precise, and universally understandable FAQ format.

        CORE EXTRACTION GUIDELINES:

        1. QUESTION GENERATION RULES:
        - Create questions that are:
            * Technically precise
            * Universally comprehensible
            * Completely independent of any specific conversation context
            * Focused on core technical concepts
        - AVOID:
            * Questions referencing specific support cases
            * Conversational or context-dependent phrasing
            * Customer service-related inquiries
            * Generic or vague technical questions

        2. ANSWER COMPOSITION PRINCIPLES:
        - Provide technically rigorous, comprehensive answers
        - Minimum answer length: 3-4 sentences
        - Maximum answer length: 150 words
        - Use domain-specific technical terminology
        - Explain complex concepts with clarity
        - Focus on fundamental principles and methodologies

        3. TECHNICAL CONTENT FOCUS:
        - Prioritize deep technical insights
        - Extract core scientific and engineering principles
        - Highlight advanced computational techniques
        - Explain complex methodological approaches

        4. CONTENT TRANSFORMATION GUIDELINES:
        - Generalize specific technical scenarios
        - Remove all references to:
            * Customer support interactions
            * Specific support cases
            * Individual user experiences
        - Transform narrow, context-specific information into broad, universally applicable knowledge

        5. STRUCTURAL REQUIREMENTS:
        - Generate {FAQ_limit} most technically significant question-answer pairs
        - Ensure no repetition of core concepts
        - Maintain logical flow and technical progression
        - Cover diverse technical dimensions of the source material

        6. STRICT OUTPUT FORMATTING:
        - Produce perfectly formatted JSON
        - No extra whitespaces
        - No newline characters
        - Valid dictionary structure
        - Proper JSON escape sequences

        OUTPUT FORMAT EXAMPLE:
        {format}

        CRITICAL CONSTRAINTS:
        - TECHNICAL DEPTH IS PARAMOUNT
        - REMOVE ALL NON-TECHNICAL CONTEXT
        - FOCUS ON SCIENTIFIC AND ENGINEERING PRINCIPLES
"""
  
    # Prepare the user prompt with additional details  
    user_message = (  
        "Generate FAQ from the following piece of data with the guidelines provided:\n"  
        f"{context_from_database}"  
    )  
    
    @retry(Exception, tries=3, delay=2)
    def llm_call():
        response = client.chat.completions.create(  
            model=deployment_name,  
            messages=[  
                {"role": "system", "content": system_message},  
                {"role": "user", "content": user_message}  
            ],  
            max_tokens=2000  
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
  
    faq = response.choices[0].message.content 
    return faq

def generate_solution_with_llm(context_from_database):  
    # Prepare the system message and user prompt  
    system_message = f"""
        # An AI assistant for creating brief question-answer out of provided piece of text.\n 
        You are an expert in creating the question-answer from the piece of text.\n
        Please follow these guidelines:"  
        1. Provide the question and answer in a detailed format.  
        2. Filter out any sensitive or personal information such as company or individual names.
        3. Highlight key attributes and their values. 
        4. Ensure the Q/A is clear and easy to understand, avoiding technical jargon if possible.
        5. Create *SOLUTION* focussing on the Physics and Product attribute values provided in the JSON file.For example: if the summary is about any topic on Structures, the FAQ's generated should be focussed on Structures."
        6. When there is summary about any Training session, Introduction of a topic, Overview of any topic, create at least one FAQ with summary/overview of the topic in bullet points."
        7. Provide the answer in bullet format. Meaning if there are any best practices given in the text it should answered stepwise   
        8. If there are any nested structures, summarize them appropriately while maintaining context.  
        9. Do not mention 'user' keyword and give the output as if it is not a conversation going on between users, and just information on a particular topic.   
        10.Instead of 'Sharepoint URL' just use 'Links' keyword. And do not add any kind of URL's in the summary.  
        11.Do not include keywords like 'response', 'discussion', 'concern raised', 'inquiry'. 
        12.Avoid questions with one line answers.
        13.Avoid questions and answers that are based on timely updates, like example: 'When are the 2024 R1 Technical Training Sessions for Mechanical commencing?'.
        14. Return a maximum of 2 question-answer pair that are important in terms of complexity and criticality, keep the FAQ as precise as possible, focus on the unique details of the message.
        15. Make sure the output is a correctly formatted json string.
        16.The final output should be strictly a dictionary format as follows: 
        {"Quesion1": question1 over here ,
         "Answer1": answer for Question1 , 
         "Quesion2": question2 over here ,
         "Answer2": answer for Question2 ,
         ....
         }         
    """
  
    # Prepare the user prompt with additional details  
   
    # # Make a request to the OpenAI API  
    # response = openai.ChatCompletion.create(  
    #     engine="gpt-4-32k",  # Use the deployment name as engine  
    #     messages=[  
    #         {"role": "system", "content": system_message},  
    #         {"role": "user", "content": user_message}  
    #     ]  
    # )  
  
    # faq = response['choices'][0]['message']['content'] 
    
    response = client.chat.completions.create(  
        model=deployment_name,  
        messages=[  
            {"role": "system", "content": system_message},  
            {"role": "user", "content": context_from_database}  
        ],  
        max_tokens=2000  
    )  
  
    solution = response.choices[0].message.content 
    return solution
  
def main_solution_and_faq(json_file,SWITCH):  
    input_directory = r"D:\\Project_Guru\\Mech\\KM_generated"
    
    # Define the output directory  
    output_dir = r"D:\\Project_Guru\\Mech\\FAQ"  

    # Check if the directory exists  
    if not os.path.isdir(output_dir):  
        # If not, create it  
        os.makedirs(output_dir)
    
    file_path = os.path.join(input_directory, json_file)    
    # Specify the encoding to avoid UnicodeDecodeError  
    with open(file_path, 'r', encoding='utf-8') as file:  
        json_data = json.load(file)  
        context_from_database = json_data.get("context_from_database", "")  

        if context_from_database:
            if SWITCH  == 'Certain - FAQ type':
                faq = generate_faq_with_llm(context_from_database)  

                output_filename = os.path.splitext(json_file)[0] + "_faq.json"  
                output_path = os.path.join(output_dir, output_filename)  

                with open(output_path, 'w', encoding='utf-8') as output_file:  
                    output_file.write(faq)
            elif SWITCH == 'Certain - Solution type':
                solution = generate_solution_with_llm(context_from_database)  

                output_filename = os.path.splitext(json_file)[0] + "_solution.json"  
                output_path = os.path.join(output_dir, output_filename)  

                with open(output_path, 'w', encoding='utf-8') as output_file:  
                    output_file.write(solution)
            else:
                print("The classification is neither FAQ or Solution type. It is Uncertain")                
  
    print("FAQs have been generated and stored in the output directory.")   
# message = """MCM Technologies test pvt ltd is seeking to build a model to study creep flow and have appealed for suggestions regarding which product to utilize and how to configure it. The customer\'s project lead, Rahul Kumar, is also interested in benefiting from any relevant training practically offered by Ansys.\n\nA plausible recommendation for their predicament lies in using Ansys EnSight, a proficient tool used often for visualizing large data sets. It can run simultaneously on several machines or CPUs of a multiprocessor host due to its capability to provide coarse-grained parallelism for large data sets. The advanced functionality offered by EnSight includes shaping particle support which can render non-sphere shapes in 2024 R2 release, lighting improvements, and support for cutting plane surfaces and scenes. Since version 2021 R1, Ansys EnSight has been identified as the primary tool for the combined post-processing of Ansys CFD (CFX or Fluent) and Ansys Structural co-simulation results. \n\nFluent Aero users are also treated with the capability to open EnSight directly via a command file or by selecting the files in the Open File dialog. The software also offers direct methods like "View with EnSight" to open EnSight directly from Project View, or via EnSight Viewer. In fact, a salient feature is that Fluent solution case and data files can be saved for post-processing in Ansys EnSight Enterprise using the parallel EnSight export option in Fluent.\n\nA compelling feature by Ansys EnSight, parallel processing, allows for meticulous simulation efficiency and performance optimization. As a progressive way of achieving cost reduction, Ansys uses cloud simulations, thereby reducing the time to solution. Data management is visually represented by showing different \'Partitions\' with their names and allocated sizes along with visual indicators for usage.\n\nThere\'s also an opportunity to use a new tool, RedHawk-SC Electrothermal Flow Wizard by ANSYS. This tool includes functionalities critical to IC design such as 2.5D/3D IC Analysis with Model Generation that includes package and board layout extraction, Signal/Power Integrity, and Thermal/Stress Integrity Model Generation.\n\nIt is worth noting that ANSYS offers online courses that can equip the MCM Technologies team with the necessary knowledge to optimize the use of Ensight. The self-paced \'Introduction to Ansys EnSight\' course may serve as a pertinent starting point for their needs. A point to consider would be that the training materials are developed and tested on the mentioned release and are expected to behave similarly in later ones.\n\nThis information should equip you with an insightful perspective to engage the customer, MCM Technologies, in Waterloo."""
# out = generate_faq_with_llm(message)
# print(out)
    # format = """{"Question1": "question1 over here","Answer1": "answer for Question1","Question2": "question2 over here","Answer2": "answer for Question2",...}"""
    # # Prepare the system message and user prompt  
    # system_message = f"""
    #     # An AI assistant who helps in summarizing JSON data into meaningful FAQ content.\n 
    #     You are an expert in creating the question-answer from the piece of text.\n
    #     Please follow these guidelines:\n"   
    #     1. Provide the answers in a detailed format.  
    #     2. Strictly remove any personal information such as company/individual names from the output and make the FAQ generalised.  
    #     3. Highlight key attributes and their values, and provide a concise overview.  
    #     4. Ensure the question-answer is clear and easy to understand, it should not deviate from the data given.  
    #     5. Create very detailed answers for questions using the data provided, avoid 1-2 sentence answers.   
    #     6. When there is summary about any Training session, Introduction of a topic, Overview of any topic, create at least one question-answer with summary/overview of the topic in bullet points.  
    #     7. If there are any nested structures, summarize them appropriately while maintaining context.  
    #     8. Avoid using the keyword 'user' and present the information as standalone content on the topic, not as part of an ongoing conversation.  
    #     9. Instead of writing questions with words like 'this discussion', 'suggested', 'issues' it should describe the topic of discussion.
    #     10. Instead of 'Sharepoint URL' just use 'Links' keyword. And do not add any kind of URL's in the summary.  
    #     11. The question and answer should not mention this particular conversation such as 'what issue' and 'as discussed', it should not be referring to any particular case and should be general.  
    #     12. Avoid questions with one line answers and answers should not be very specific to the conversation in context provided.  
    #     13. Avoid questions and answers that are based on timely updates, like example: 'When are the 2024 R1 Technical Training Sessions for Mechanical commencing?'.
    #     14. The question should be written in a way that a third person, who is not familiar with the ongoing discussion, can fully understand it. It must include all necessary details and context from the given conversation without using phrases like 'as discussed in this conversation' or 'in this context.' If the question pertains to a specific case, the case should be thoroughly described.
    #     15. Ensure every Question has a corresponding Answer and questions should not sound specific to a case like "What issue was encountered with the solver?". 
    #     16. Return a maximum of {FAQ_limit} question-answer pair that are important in terms of complexity and criticality, keep the question-answer as precise as possible, focus on the unique details of the message. 
    #     17. Make sure the output is a correctly formatted json string and do not include space characters such as \n or unicode.  
    #     18. The final output should be strictly in dictionary format as follows:  
    #     {format}
    # """