import logging
import os
import openai
import pinecone
from dotenv import load_dotenv
from langchain.schema.document import Document
from langchain.chains import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.vectorstores import FAISS, Pinecone
from Config import *
from pinecone import Pinecone as pc_client

load_dotenv()


class ChatbotResponse:
    # General
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.pc = pc_client(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))
        openai.api_key = os.getenv("OPENAI_API_KEY")
        index = self.pc.Index(os.getenv("PINECONE_INDEX"))
        self.vectorstore = Pinecone(index, self.embeddings, 'text')
        self.llm = ChatOpenAI(temperature=0.0, model_name="gpt-4o")
        self.memory = ConversationBufferWindowMemory(k=3, memory_key="conversation_history", input_key="question")
        router_selection_prompt = self._get_inquiry_template()
        self.refined_query_chain = LLMChain(llm=self.llm, prompt=router_selection_prompt, verbose=False)
        self.output_parser = self._set_output_parser()
        self.qatemplate = self._prepare_qa_prompt()
        self.qa_chain = load_qa_chain(llm=ChatOpenAI(temperature=0.0, model="gpt-4o-mini"), chain_type="stuff",
                                      verbose=False, prompt=self.qatemplate, memory=self.memory)

    def set_stream_handler(self, handler):
        self.qa_chain = load_qa_chain(
            llm=ChatOpenAI(temperature=0.0, model="gpt-4o-mini", streaming=True, callbacks=[handler]),
            chain_type="stuff", verbose=False, prompt=self.qatemplate, memory=self.memory)

    def _get_inquiry_template(self):
        router_selection_prompt = PromptTemplate(
            input_variables=["userPrompt", "conversationHistory"], template=inquiry_prompt_template
        )
        return router_selection_prompt
    
    def get_mixed_bread_reranked_docs(self, query: str, docs) -> list[Document]:
        
        docs_list = [doc.page_content for doc in docs]
        
        len_docs = len(docs_list)
        
        docs_to_return = 0 
        
        if len_docs//2 > 15:
            docs_to_return = 15
        else:
            docs_to_return = len_docs//2
        
        
       
        result =self.pc.inference.rerank(
            model="bge-reranker-v2-m3",
            query= query,
            documents=docs_list,
            top_n= docs_to_return,
            return_documents=False,
            parameters={
                "truncate": "END"
            }
        )

        reranked_docs = []
        
        for index in result.data:
            reranked_docs.append(docs[index.index])
    
        return reranked_docs

    def _prepare_qa_prompt(self):
        prompt = PromptTemplate(
            template=qa_template,
            input_variables=["context", "conversation_history"],
        )
        system_message_prompt = SystemMessagePromptTemplate(prompt=prompt)
        human_template = """
         Question: {question}"""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt,
             human_message_prompt]
        )
        return chat_prompt

    def get_refined_query(self, query):
        previous_convos = ""
        if len(self.memory.buffer_as_messages) < 6:
            previous_convos += str(self.memory.buffer_as_messages)
        else:
            previous_convos += str(self.memory.buffer_as_messages[-6:])
        return self.refined_query_chain.run({"conversationHistory": previous_convos, "userPrompt": query})

    def _set_output_parser(self):
        response_schemas = [
            ResponseSchema(name="destination", description=dest_desc),
            ResponseSchema(name="question", description=question_desc),

        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        return output_parser

    # dealing with KSA
    def get_router_chain(self, router_dict: list[dict]):
        main_retrievers_info = ""
        for i in router_dict:
            main_retrievers_info += f'{i["name"]}:{i["description"]}\n'
        template_main_router = template_main_routerchain + f"""\n{main_retrievers_info}\n\n"""
        template_second_half = "<< INPUT >>\n{input}\n\n<< OUTPUT >>\n"
        template_main_final = template_main_router + template_second_half
        prompt_main_router = PromptTemplate(input_variables=["input"], partial_variables={},
                                            template=template_main_final)
        main_router_chain = LLMChain(llm=ChatOpenAI(temperature=0.0, model="gpt-4o"), prompt=prompt_main_router,
                                     verbose=False)
        return main_router_chain

    def make_ksa_context_pinecone(self, query: str,nmsp: list) -> list:
        context = []
        for name in nmsp:
            context.extend(
                self.vectorstore.similarity_search_with_score(query, k=10, namespace=name))

        context = sorted(context, key=lambda x: x[1], reverse=True)
        context_ = []
        for doc, score in context:
            doc.metadata['score'] = score
            context_.append(doc)
        return context_

    def get_query_response(self, query):
        context = []
        refined_query = self.get_refined_query(query)
        ###Main level Router
        main_chain = self.get_router_chain(main_desc)
        main_dest = self.output_parser.parse(main_chain.run(refined_query))['destination'][0]
        logging.info(f"\nREFINED QUERY: \n{refined_query}")
        logging.info(f"\nMain_DESTINATION: \n{main_dest}")

        if main_dest == "DEFAULT":
            return self.qa_chain, {"question": refined_query, "input_documents": context}, {
                'Destinations': main_dest}, {
                       'refined': refined_query}

        ### second level Router
        second_router_dict = None
        nmsp_ = None
        if main_dest == 'Security':
            nmsp_ = namesp_security  # Get namespaces for Security
        else:
            nmsp_ = nmsp_cbuae  # Get namespaces for CB UAE

        # Get context from the appropriate namespaces
        context = self.make_ksa_context_pinecone(refined_query, nmsp_)

        # get reranked docs
        context = self.get_mixed_bread_reranked_docs(refined_query, context)

        return self.qa_chain, \
               {"question": refined_query, "input_documents": context}, \
               {'refined': refined_query}

