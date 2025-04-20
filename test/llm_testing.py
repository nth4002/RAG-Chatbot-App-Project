from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv, find_dotenv
import os
import base64
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage



# Force reload the .env file
load_dotenv(find_dotenv(), override=True)

# print("Current API Key:", os.getenv('GOOGLE_API_KEY'))
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0,
    max_tokens=None,
    timeout=None, 
    max_retries=3,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# step2 : Output Parser
output_parser = StrOutputParser()

# step 3: Structured output

class MobileReview(BaseModel):
    phone_model: str = Field(description="The model of the phone")
    rating: float = Field(description="Overall rating out of 5")
    pros: List[str] = Field(description="List of positive aspects")
    cos: List[str] = Field(description="List of negative aspects")
    summary: str = Field(description="Brief summary of the review")

review_text = """
Just got my hands on the new Galaxy S21 and wow, this thing is slick! The screen is gorgeous,
colors pop like crazy. Camera's insane too, especially at night - my Insta game's never been
stronger. Battery life's solid, lasts me all day no problem.
Not gonna lie though, it's pretty pricey. And what's with ditching the charger? C'mon Samsung.
Also, still getting used to the new button layout, keep hitting Bixby by mistake.
Overall, I'd say it's a solid 8 out of 10. Great phone, but a few annoying quirks keep it from
being perfect. If you're due for an upgrade, definitely worth checking out!
"""

# structured_llm = llm.with_structured_output(
#     MobileReview,
# )
# output = structured_llm.invoke(review_text)
# print(output)
# print(output.pros)

# step 4: Prompt Template

prompt = ChatPromptTemplate.from_template(
    "Tell me a a short remark about {input} and give your  thinkings about{input}"
)
chain = prompt  | llm | output_parser
# result = chain.invoke({"input": "Naruto Uzumaki"})
# print(result)

# step 5: LLM Message
messages = [
    SystemMessage(
        content="You are a helpful assistant the help answer my question accurately and succintly and yet concisely!"
    ),
    HumanMessage(
        content="Tell me about Naruto's childhood and what makes him so obsessed with becoming Hokage."
    )
]
# response = llm.invoke(messages)
# print(response.content)

template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "Tell me about {input}")
])
chain = template | llm | output_parser
result = chain.invoke({"input": {"Naruto's Nindo, his ninja way"}})
print(result)