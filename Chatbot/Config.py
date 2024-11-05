# NO of documents to retrieve
no_doc_to_retrieve = 10
# Router Descriptions
security_desc = [
    {
        'name': "Market Rules Approved by SCA",
        'description': """This collection encompasses critical documents such as Operational Procedures for DVP Model, Listing Rules in Module Two, Penalty Rules in Module Four, and more. These 849 documents detail the approved market rules sanctioned by the Securities and Commodities Authority (SCA), providing essential guidelines for market participants."""
    },
    {
        'name': "Automatic Exchange of Information - FATCA and CRS",
        'description': """This segment comprises pivotal documents like bilateral agreements, FAQs, guidance notes, and resolutions related to FATCA and the Common Reporting Standard (CRS). With a total of 421 documents, it serves as a comprehensive resource for understanding automatic exchange mechanisms between jurisdictions, particularly focusing on the UAE's compliance."""
    },
    {
        'name': "Regulations SCA",
        'description': """This extensive compilation of 1161 documents includes pivotal decisions and regulations issued by the Securities and Commodities Authority (SCA). From decisions concerning the functioning of the market to regulations on investment funds and central depository activities, this repository serves as a foundational reference for regulatory compliance and oversight."""
    },
    {
        'name': "Circulars, Rules, and Procedures",
        'description': """This segment features 103 documents, including notices, instructions, and guidelines, addressing various circulars, rules, and procedures pertinent to the Securities and Commodities Authority (SCA). These documents provide clarity on anti-money laundering, counter-terrorist financing, and other regulatory frameworks shaping financial activities in the UAE."""
    },
    {
        'name': "Anti-Money Laundering and Terrorist Financing",
        'description': """This comprehensive collection of 1139 documents delves deep into the anti-money laundering (AML) and combating the financing of terrorism (CFT) landscape in the UAE. Covering guidelines, thematic reviews, and federal laws, this repository is crucial for institutions and professionals navigating AML/CFT compliance."""
    },
    {
        'name': "Regulations Drafts",
        'description': """This segment encapsulates 15 draft documents and ministerial decisions, providing insights into evolving regulatory frameworks and upcoming guidelines. From economic substance regulations to resolutions, this collection offers a glimpse into the regulatory landscape under development."""
    },
    {
        'name': "Economic Substance Regulations",
        'description': """This section comprises 187 documents focusing on economic substance regulations in the UAE. With guidance notes, report templates, and resolutions, this repository elucidates the requirements and compliance mechanisms related to economic activities and substance requirements."""
    }
]

cbuae_desc = [
    {
        'name': "Banking",
        'description': """This section encompasses all regulatory frameworks and guidelines pertinent to banks, including operational standards and specific regulations. It provides comprehensive insights into the governance structures of Islamic financial institutions, highlighting the Restricted Licence Banks Regulation, model management guidance, and risk management protocols."""
    },
    {
        'name': "Insurance",
        'description': """Covering a broad spectrum of insurance-related topics, this section details regulations overseen by the Insurance Authority Board of Directors. It offers comprehensive coverage of decisions made by the Insurance Board, emphasizing matters related to health insurance and various other insurance types, ensuring adherence to regulatory standards and consumer protection."""
    },
    {
        'name': "Other Regulated Entities",
        'description': """This segment focuses on diverse regulated entities beyond traditional banking and insurance sectors. It sheds light on regulations governing loan-based crowdfunding activities, providing clarity on licensing and monitoring mechanisms. Additionally, it encompasses standards for exchange business regulations and finance companies, ensuring compliance and fostering transparency within the financial ecosystem."""
    }
]

# main router template
template_main_routerchain = f"""Given a query to a question answering system select the system best suited for the input.
        You will be given the names of the available systems and a description of what questions the system is best suited for.
        \n\n<< FORMATTING >>\nReturn a markdown code snippet with a JSON object formatted to look like:
        \n```json\n{{{{\n    "destination": List[string] \\ name of the question answering system to use.Can also be both of the names present if required.Only use "DEFAULT" if the query is not related to tax or zakat at all.Maximum 2 allowed
        \n    "question":List[string] \\ parts of the user query separated according to the retriever selected. Always equal to the number of destinations selected.Donot include the description of the retriever in the question.
        If they belong to the same retriever consider them a single question.
        Is empty when the 'DEFAULT' retriever is selected.Maxium 2 allowed
        \n }}}}\n```\n\n
        REMEMBER: "destination" can contain both candidate prompt names or it can be only one of the candidate prompt names specified below OR it can be "DEFAULT" if the input does not contain anything related to tax and is not well suited for any of the candidate prompts.
        \n.\n\n<< CANDIDATE PROMPTS >> """

# router destination description
dest_desc = "It is List of destination retrievers which are selected according to the query.Can contain multiple retrievers or single retriever."
question_desc = "It is List of user queries which are derived from the original query according to the retriever selected.Can contain single question or multiple question depending on the user query.Is empty when the 'DEFAULT' retriever is selected."

# refined query prompt template
inquiry_prompt_template = """
You are a helpful assistant who will help in making refined queries based on the User prompt if and only if the User prompt is response
 to the AI last CONVERSATION. Otherwise dont change the User prompt. change vat to value added tax and ct to Corporate tax

Example of Refined query generation:
1:  Human: What is the VAT in KSA? 
    Refined query: What is the VAT in KSA?
    AI: The general VAT rate is 5% and applies to most goods and services, with some goods and services subject to a 0% rate or an exemption from VAT (subject to specific conditions being met
    Human: Is panadol zero-rated in KSA? 
    Refined query: Is panadol zero-rated in KSA?
    AI: Pharmaceuticals are zero-rated in KSA. Is panadol considered a pharamaceutical?
    Human: Yes. 
    Refined query: Yes panadol is considered as a pharamaceutical product. 
    AI: In that case panadol is zero rated.
    Human:What is pluto?
    Refined query: What is pluto?
    AI: It is a dwarf planet.Do you need me to do research on it for you?
2:  Sometimes you donot have to generate a refined query for example
    Human:What is pluto?
    Refined query: What is pluto?
    AI: It is a dwarf planet.Do you need me to do research on it for you?
    Human: No thanks that will be all
    Refined query: No thanks that will be all


CONVERSATION LOG:
    {conversationHistory}

User prompt:
    {userPrompt}
    
Remember to output the refined query in your final answer
  Refined query:
"""

# QA template
qa_template = """You are a helpful assistant.
        Your job is to provide and guide users related to central bank of uae, Insurace and security information,given the %CONTEXT%, %Conversation History%, and Question.
        Try to make your final answer from the %CONTEXT%. 
        Always consider the context first and then conversation history.
        Try to ask further questions from the user if required.
        If the context does not contain the answer then ask the human to provide more information or else apologize.
        
        Remember below points in %Remember% tag before making your response       
        %Remember%
        1. Do not mention anything which shows you are given context and 'Yes' or 'No' "
        2. In Context document if you find answer in bullet points or number add that as it is to the final answer.
        3. 1 million AED is equal to 1,000,000 AED. deduce other equations accordingly
        4. Avoid answering  "Please consult to the tax advisor" or "Context document does not provide the info"
        5. Extract the relevant information from the CONTEXT and also keep the format
        6. If the context is empty, use the Conversation_History to answer else use Conversation_History along with
         context to answer the question and only answer questions related to tax, 
         Otherwise apologise and tell the user to ask tax related questions only.
        7. Ask the user follow-up questions like: 
            a. Do you want help with anything else?
            b. Do you need more info regarding this?
            Create more followup questions based on your response

        %TONE%:
        - Your tone should be lawyered.
        - Inquisitive
        
        %CONTEXT%: {context}
        
        %Conversation History%: {conversation_history}
        """

########### sub level router prompt

# Router Descriptions

main_desc = [ \
    {'name': "Security", 'description': """    
    The "Market Rules Approved by SCA" collection details guidelines sanctioned by the Securities and Commodities Authority (SCA). 
    The "Automatic Exchange of Information - FATCA and CRS" segment focuses on automatic exchange mechanisms like FATCA and CRS,
    emphasizing UAE's compliance. The "Regulations SCA" compilation encompasses key decisions and regulations by the SCA, serving
    as a primary reference for regulatory compliance. The "Circulars, Rules, and Procedures" section addresses anti-money laundering
    and counter-terrorist financing frameworks in the UAE. The "Anti-Money Laundering and Terrorist Financing" collection is essential 
    for AML/CFT compliance. The "Regulations Drafts" segment provides insights into evolving regulatory frameworks. Lastly, the "Economic
    Substance Regulations" section outlines requirements and compliance mechanisms related to economic activities in 
      """},
    {'name': "CBUAE", 'description': """
    This section is useful for regulatory frameworks within the financial sector. It covers three main areas: banking, insurance, and other regulated entities. In the banking realm, it emphasizes guidelines for Islamic financial institutions, such as the Restricted Licence Banks Regulation. The insurance section delves into regulations overseen by the Insurance Authority Board, with a focus on health insurance and consumer protection. Meanwhile, the section on other regulated entities sheds light on regulations governing activities like crowdfunding, exchange business, and finance companies, emphasizing transparency and adherence to established standards across the financial landscape."""}
]

namesp_security = [
    'security-faiss-db_Market Rules Approved by SCA_general',
    'security-faiss-db_Automatic Exchange of Information - FATCA and CRS_general',
    'security-faiss-db_Regulations SCAs_general',
    'security-faiss-db_Circulars, Rules and procedures_general',
    'security-faiss-db_Anti-Money Laundering and Terrorist Financing_general',
    'security-faiss-db_Regulations Drafts_general',
    'security-faiss-db_Economic Substance Regulations_general']

nmsp_cbuae = [
    'Other Regulated Entities_general',
    'Insurance_general',
    'Banking_general',
    'All Licensed Financial Institutions_general']
