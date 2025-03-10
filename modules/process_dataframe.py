import pandas as pd
import re
import datetime  

def extract_reply_only(email_text):
    """
    Extract only the reply part of an email, removing any quoted original messages.
    Args:
        email_text (str): The full email text including replies and original messages    
    Returns:
        str: Only the reply part of the email
    """
    # Check if the text is NaN or None
    if pd.isna(email_text) or email_text is None:
        return ""
    
    # Pattern to find original message dividers
    divider_patterns = [
        r'[-]+\s*Original Message\s*[-]+',
        r'MAHLE internal \(CL2\)(\s*\n|\r\n|\r)From:',  # Specific MAHLE pattern
        r'From:.*Sent:.*To:.*Subject:',
        r'On .* wrote:',
        r'Begin forwarded message:'
    ]
    
    # Find the first occurrence of any divider pattern
    first_divider_index = len(email_text)
    
    for pattern in divider_patterns:
        matches = re.search(pattern, email_text, re.IGNORECASE | re.MULTILINE)
        if matches and matches.start() < first_divider_index:
            first_divider_index = matches.start()
    
    # Extract only the reply (text before the first divider)
    reply_only = email_text[:first_divider_index].strip()
    
    return reply_only

# Example usage with a DataFrame
def process_email_dataframe(df, column_name='CUSTOMER_INTERACTION_TEXT_BODY'):
    """
    Process a DataFrame with email texts and add a new column with only the reply parts.
    Args:
        df (pd.DataFrame): DataFrame containing the email texts
        column_name (str): Name of the column containing the email texts  
    Returns:
        pd.DataFrame: DataFrame with an additional column containing only the reply parts
    """
    # Create a new column with only the reply parts
    df['CUSTOMER_INTERACTION_TEXT_BODY_REPLY_ONLY'] = df[column_name].apply(extract_reply_only)
    return df