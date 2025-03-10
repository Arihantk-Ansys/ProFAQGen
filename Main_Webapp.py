from modules.text_enrichment import enrich_data, compiler
from modules.generateFAQ import generate_faq_with_llm
from modules.PII import OpenAI_PII_removal
from modules.DiscussionAnalysis import discussion_main, get_report_modes

def generate_faq_from_text_webapp(body, physics=None, product=None):
    """
    Generate an FAQ from a given text, where the text consists of a subject, a description, and a discussion. 
    Ensure that the body is a single combined string, starting with the subject, followed by the description, and then the sequential interactions or discussions.
    Parameters:
    -----------
    body : str
        The combined text containing subject, description, and body content
    physics : str, optional
        The physics/family information if available
    product : str, optional
        The product/application information if available
    Returns:
    --------
    str or dict
        The generated FAQ, either as a JSON string or a Python dictionary
    """
    # Clean the text to remove PII
    clean_text = OpenAI_PII_removal(body)
    
    # Generate a unique case ID for discussion analysis
    # Using a timestamp as we don't have real case numbers
    import time
    case_id = f"temp_{int(time.time())}"
    
    # Analyze the discussion
    report = discussion_main(clean_text, case_id)
    discussion_type, classification = get_report_modes(report)
    
    # Check if data should be processed based on discussion type and classification
    if discussion_type == 1:
        if classification == 'LLM Data Enrichment':
            # Enrich the data using the physics parameter if provided
            enriched_data = enrich_data(clean_text, physics=physics)
            data_summarized = True
        elif classification == 'Good to go for Classification Agent':
            # Use compiler function for this classification
            switch = 'prompt2'
            retrieved_data = ''
            enriched_data = compiler(clean_text, retrieved_data, switch)
            data_summarized = True
        else:
            print("The discussion is discarded")
            return None
    else:
        print("The discussion is open ended")
        return None
    
    # Generate FAQ if data was successfully summarized
    if data_summarized:
        # Calculate word count for the enriched data
        no_words = len(enriched_data.split())
        
        # Generate FAQ
        faq_generated = generate_faq_with_llm(enriched_data, no_words)
        
        # Try to parse as JSON, return as is if not JSON
        try:
            import json
            faq_json = json.loads(faq_generated)
            return faq_json
        except json.JSONDecodeError:
            return faq_generated
    
    return None

if __name__ == "__main__":  
    # file = "test_case_2_raw_data.xlsx"  
    body = "Fluid-structure interaction (FSI) training materials and technical notes\nHello,\n\nI am using FLUENT -ANSYS Mechanical FSI . I need more technical details and updated tutorials. Rahul Mule has helped me on related issues recently. Could you allow Rahul help me assist on this issue.\n\n\n\nThanks,\n\n\n\nRafi\nDear User, \n\n\n\nThank you for submitting your Ansys support case in the Ansys Customer Support Space. This is an automatic reply to let you know we just received the following case. \n\n\n\nCase Number:00146810\n\n\n\nSubject:Fluid-structure interaction (FSI) training materials and technical notes\n\n\n\nDescription:\n\nHello,\n\nI am using FLUENT -ANSYS Mechanical FSI . I need more technical details and updated tutorials. Rahul Mule has helped me on related issues recently. Could you allow Rahul help me assist on this issue.\n\n\n\nThanks,\n\n\n\nRafi\n\n\n\nYour support case has been routed to our support team and you should hear back from us shortly. In the meantime, if you have any questions or comments regarding your support case, please feel free to either reply directly to this email or click on the button below to navigate to your support case in the Ansys Customer Support Space.\n\n\n\n\n\n\n\nThank you. \n\nAnsys Technical Support Hello Rafi, \n \nThanks for contacting Ansys Support.\n \nPlease find some useful FSI learning resources below:\n \n1. System Coupling Tutorials \n \n2. System Coupling related settings in Mechanical: 5.15.17. System Coupling \n \n3. System Coupling related settings in Fluent: Chapter 49: Performing System Coupling Simulations Using Fluent \n \n4. FSI courses on ALH: Ansys Fluent Fluid Structure Interaction with Ansys Mechanical - Ansys Learning Hub \n \n5. You can also find quick knowledge articles on Ansys Customer Community just by searching relevant keywords: Fluids \n \n6. Refer to application best practices Flexible Valve FSI (ABP) - Ansys Learning Hub \n \nI hope this helps. Let me know if you need any further assistance.\n\nRegards,\nRahul Mule / Technical Support Engineer\nPune / India\nrahul.mule@ansys.com / www.ansys.com\n-----------------------------------------------------------------------------------------------------------------------\nThe information transmitted is intended only for the person or entity to which it is addressed and may contain confidential and/or privileged material. Any review, retransmission, dissemination, or other use of, or taking of any action in reliance upon, this information by persons or entities other than the intended recipient is prohibited. If you received this in error, please contact the sender and delete the material from any computer.\n\n*Important*\n1. Kindly use \"Reply All\" while replying to this email or ensure to add casesupport@ansys.com as a recipient while replying to this email.\n2. Please do not alter/remove the [ ref...ref ] string in the Email subject/body for all communication on this \u201cCase\u201d [External Sender]\n\nThanks, Rahul.  I will continue to learn these and open a case if needed.  I will log a SR, if I have any questions.\n\nRafi\n\n \n\n\nSLB-Private\n\nFrom: Ansys Support <casesupport@ansys.com>\nSent: Monday, February 17, 2025 11:40 PM\nTo: Rafiqul Khan <rkhan43@slb.com>\nSubject: [Ext] RE: Thank you for submitting Ansys Support Case 00146810 [ thread::iYcCO_Vxc_WEd26Cxxh9bE4:: ]\n\n \n\nHello Rafi, Thanks for contacting Ansys Support. Please find some useful FSI learning resources below: 1. System Coupling Tutorials 2. System Coupling related settings in Mechanical: 5.\u200a15.\u200a17. System Coupling 3. System Coupling related settings\n\n\nHello Rafi, \n\n \n\nThanks for contacting Ansys Support.\n\n \n\nPlease find some useful FSI learning resources below:\n\n \n\n1. System Coupling Tutorials \n\n \n\n2. System Coupling related settings in Mechanical: 5.15.17. System Coupling \n\n \n\n3. System Coupling related settings in Fluent: Chapter 49: Performing System Coupling Simulations Using Fluent \n\n \n\n4. FSI courses on ALH: Ansys Fluent Fluid Structure Interaction with Ansys Mechanical - Ansys Learning Hub \n\n \n\n5. You can also find quick knowledge articles on Ansys Customer Community just by searching relevant keywords: Fluids \n\n \n\n6. Refer to application best practices Flexible Valve FSI (ABP) - Ansys Learning Hub \n\n \n\nI hope this helps. Let me know if you need any further assistance.\n\nRegards,\nRahul Mule / Technical Support Engineer\nPune / India\nrahul.mule@ansys.com / www.ansys.com\n-----------------------------------------------------------------------------------------------------------------------\nThe information transmitted is intended only for the person or entity to which it is addressed and may contain confidential and/or privileged material. Any review, retransmission, dissemination, or other use of, or taking of any action in reliance upon, this information by persons or entities other than the intended recipient is prohibited. If you received this in error, please contact the sender and delete the material from any computer.\n\n*Important*\n1. Kindly use \"Reply All\" while replying to this email or ensure to add casesupport@ansys.com as a recipient while replying to this email.\n2. Please do not alter/remove the [ ref...ref ] string in the Email subject/body for all communication on this \u201cCase\u201d Sure, Rafi! Thanks for confirming to close.\n \nI\u2019ll go ahead and close this case. I hope you are happy with the support and information provided. Feel free to open a new ticket if you have any questions and I will be glad to assist you.\n\nIf you receive a customer satisfaction survey after your case has closed, please complete the survey with an assessment of your support experience.   In addition, you may send an e-mail at any time to ANSYS-Customer-Care@ansys.com if you have any comments or suggestions.\n\nRegards,\nRahul Dear User, \n\nYour Ansys Support Case (00146810) has now been closed by our support team. If you have any questions, please contact your Ansys Account Manager. \n\nDo not reply to this email. \n\nThank you,  \n\nAnsys Technical Support"
    generated_faq=generate_faq_from_text_webapp(body,'fluids','system coupling')
    print(generated_faq)  