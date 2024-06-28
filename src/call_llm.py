import os
from openai import AzureOpenAI

def call_aoai(prompt):
    system_message = """你是一個專業的演講逐字稿總結AI助手，你需要根據當前演講者說明的內容進行總結，並以繁體中文輸出。
    這次演講主題是有關AI的技術分享會，你需要以一個專業的AI工程師角度進行總結，僅需要總結技術內容，無須總結情緒、動作、以及一些會議上的互動。
    以條列式展示總結內容，每一次總結內容控制在3項以內，再次提醒，只需要總結技術上的精華，若沒有值得總結的內容則回應'無'。"""

    client = AzureOpenAI(
    azure_endpoint = os.getenv('AZURE_ENDPOINT'), 
    api_key=os.getenv('AZURE_KEY'),  
    api_version=os.getenv('AZURE_API')
    )

    response = client.chat.completions.create(
        model=os.getenv('AZURE_DEPLOYMENT'), # model = "deployment_name".
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
    )
    response_content = response.choices[0].message.content
    return response_content