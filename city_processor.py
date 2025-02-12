import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
import time
from typing import List, Dict
import numpy as np
from tqdm.asyncio import tqdm

class CityDataProcessor:
    def __init__(self, api_key: str, input_file: str, output_file: str):
        self.api_key = api_key
        self.input_file = input_file
        self.output_file = output_file
        self.batch_size = 50  # Number of concurrent requests
        self.requests_per_minute = 3500  # OpenAI's rate limit for GPT-3.5-turbo
        self.delay = 20 / self.requests_per_minute  # Delay between requests

    async def process_city(self, session: aiohttp.ClientSession, city: str) -> Dict[str, str]:
        try:
            # Get fun fact
            fun_fact = await self.ask_chatgpt(session, city, 'fun_fact')
            await asyncio.sleep(self.delay)
            
            # Get permit link
            permit_link = await self.ask_chatgpt(session, city, 'ev_permit')
            await asyncio.sleep(self.delay)
            
            return {
                'city': city,
                'fun_fact': fun_fact,
                'permit_link': permit_link,
                'status': 'completed',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            return {
                'city': city,
                'fun_fact': '',
                'permit_link': '',
                'status': f'error: {str(e)}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    async def ask_chatgpt(self, session: aiohttp.ClientSession, city: str, query_type: str) -> str:
        url = 'https://api.openai.com/v1/chat/completions'
        
        if query_type == 'fun_fact':
            system_prompt = 'You are a helpful assistant that provides a brief summary of the commercial permitting environment in a given city'
            user_prompt = f'Provide 1-2 sentences about commercial permitting in {city} in a single sentence. Focus on useful informting for potential comercial permitters'
        else:
            system_prompt = 'You are a helpful assistant that provides tips for completing tenant improvement permits in given cities.'
            user_prompt = f'what is the #1 tip for completing a tenant improvement permit specifically in {city}? DO NOT say i dont know and respond with your answer.'

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'max_tokens': 150,
            'temperature': 0.7
        }

        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 429:  # Rate limit exceeded
                await asyncio.sleep(20)  # Wait and retry
                return await self.ask_chatgpt(session, city, query_type)
            
            result = await response.json()
            return result['choices'][0]['message']['content'].strip()

    async def process_batch(self, cities: List[str]) -> List[Dict[str, str]]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.process_city(session, city) for city in cities if city]
            return await tqdm.gather(*tasks)

    def chunk_cities(self, cities: List[str]) -> List[List[str]]:
        return [cities[i:i + self.batch_size] for i in range(0, len(cities), self.batch_size)]

    async def run(self):
        # Read the Excel file
        df = pd.read_excel(self.input_file)
        cities = df['City'].dropna().tolist()  # Assuming 'City' is the column name
        
        all_results = []
        batches = self.chunk_cities(cities)
        
        print(f"Processing {len(cities)} cities in {len(batches)} batches")
        
        for batch in tqdm(batches):
            results = await self.process_batch(batch)
            all_results.extend(results)
            
            # Save intermediate results
            results_df = pd.DataFrame(all_results)
            results_df.to_excel(self.output_file, index=False)
            
            # Small delay between batches to prevent rate limiting
            await asyncio.sleep(1)
        
        print("Processing completed!")
        return all_results

def main():
    api_key = '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'
    input_file = 'input_cities.xlsx'  # Your input Excel file
    output_file = 'city_results.xlsx'  # Where results will be saved
    
    processor = CityDataProcessor(api_key, input_file, output_file)
    
    # Run the async process
    asyncio.run(processor.run())

if __name__ == "__main__":
    main()