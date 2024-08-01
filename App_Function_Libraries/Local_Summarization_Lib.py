# Local_Summarization_Lib.py
#########################################
# Local Summarization Library
# This library is used to perform summarization with a 'local' inference engine.
#
####
#
####################
# Function List
# FIXME - UPDATE Function Arguments
# 1. summarize_with_local_llm(text, custom_prompt_arg)
# 2. summarize_with_llama(api_url, text, token, custom_prompt)
# 3. summarize_with_kobold(api_url, text, kobold_api_token, custom_prompt)
# 4. summarize_with_oobabooga(api_url, text, ooba_api_token, custom_prompt)
# 5. summarize_with_vllm(vllm_api_url, vllm_api_key_function_arg, llm_model, text, vllm_custom_prompt_function_arg)
# 6. summarize_with_tabbyapi(tabby_api_key, tabby_api_IP, text, tabby_model, custom_prompt)
# 7. save_summary_to_file(summary, file_path)
#
###############################
# Import necessary libraries
import json
import logging
import os
from typing import Union

import requests
# Import 3rd-party Libraries
from openai import OpenAI
# Import Local
from App_Function_Libraries.Utils import load_and_log_configs
from App_Function_Libraries.Utils import extract_text_from_segments
#
#######################################################################################################################
# Function Definitions
#

logger = logging.getLogger()

# Dirty hack for vLLM
openai_api_key = "Fake_key"
client = OpenAI(api_key=openai_api_key)

def summarize_with_local_llm(input_data, custom_prompt_arg, temp):
    try:
        if isinstance(input_data, str) and os.path.isfile(input_data):
            logging.debug("Local LLM: Loading json data for summarization")
            with open(input_data, 'r') as file:
                data = json.load(file)
        else:
            logging.debug("openai: Using provided string data for summarization")
            data = input_data

        logging.debug(f"Local LLM: Loaded data: {data}")
        logging.debug(f"Local LLM: Type of data: {type(data)}")

        if isinstance(data, dict) and 'summary' in data:
            # If the loaded data is a dictionary and already contains a summary, return it
            logging.debug("Local LLM: Summary already exists in the loaded data")
            return data['summary']

        # If the loaded data is a list of segment dictionaries or a string, proceed with summarization
        if isinstance(data, list):
            segments = data
            text = extract_text_from_segments(segments)
        elif isinstance(data, str):
            text = data
        else:
            raise ValueError("Invalid input data format")

        headers = {
            'Content-Type': 'application/json'
        }

        logging.debug("Local LLM: Preparing data + prompt for submittal")
        local_llm_prompt = f"{text} \n\n\n\n{custom_prompt_arg}"
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional summarizer."
                },
                {
                    "role": "user",
                    "content": local_llm_prompt
                }
            ],
            "max_tokens": 28000,  # Adjust tokens as needed
        }
        logging.debug("Local LLM: Posting request")
        response = requests.post('http://127.0.0.1:8080/v1/chat/completions', headers=headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                summary = response_data['choices'][0]['message']['content'].strip()
                logging.debug("Local LLM: Summarization successful")
                print("Local LLM: Summarization successful.")
                return summary
            else:
                logging.warning("Local LLM: Summary not found in the response data")
                return "Local LLM: Summary not available"
        else:
            logging.debug("Local LLM: Summarization failed")
            print("Local LLM: Failed to process summary:", response.text)
            return "Local LLM: Failed to process summary"
    except Exception as e:
        logging.debug("Local LLM: Error in processing: %s", str(e))
        print("Error occurred while processing summary with Local LLM:", str(e))
        return "Local LLM: Error occurred while processing summary"

def summarize_with_llama(input_data, custom_prompt, api_url="http://127.0.0.1:8080/completion", api_key=None, temp=None, system_message=None):
    try:
        logging.debug("Llama.cpp: Loading and validating configurations")
        loaded_config_data = load_and_log_configs()
        if loaded_config_data is None:
            logging.error("Failed to load configuration data")
            llama_api_key = None
        else:
            # Prioritize the API key passed as a parameter
            if api_key and api_key.strip():
                llama_api_key = api_key
                logging.info("Llama.cpp: Using API key provided as parameter")
            else:
                # If no parameter is provided, use the key from the config
                llama_api_key = loaded_config_data['api_keys'].get('llama')
                if llama_api_key:
                    logging.info("Llama.cpp: Using API key from config file")
                else:
                    logging.warning("Llama.cpp: No API key found in config file")

        # Final check to ensure we have a valid API key
        if not llama_api_key or not llama_api_key.strip():
            logging.error("Llama.cpp: No valid API key available")
            raise ValueError("Llama.cpp: No valid Anthropic API key available")

        # Load transcript
        logging.debug("llama.cpp: Loading JSON data")
        if isinstance(input_data, str) and os.path.isfile(input_data):
            logging.debug("Llama.cpp: Loading json data for summarization")
            with open(input_data, 'r') as file:
                data = json.load(file)
        else:
            logging.debug("Llama.cpp: Using provided string data for summarization")
            data = input_data

        logging.debug(f"Llama.cpp: Loaded data: {data}")
        logging.debug(f"Llama.cpp: Type of data: {type(data)}")

        if isinstance(data, dict) and 'summary' in data:
            # If the loaded data is a dictionary and already contains a summary, return it
            logging.debug("Llama.cpp: Summary already exists in the loaded data")
            return data['summary']

        # If the loaded data is a list of segment dictionaries or a string, proceed with summarization
        if isinstance(data, list):
            segments = data
            text = extract_text_from_segments(segments)
        elif isinstance(data, str):
            text = data
        else:
            raise ValueError("Llama.cpp: Invalid input data format")

        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
        }
        if len(api_key) > 5:
            headers['Authorization'] = f'Bearer {api_key}'

        llama_prompt = f"{custom_prompt} \n\n\n\n{text}"
        system_message = "You are a professional summarizer."
        logging.debug("llama: Prompt being sent is {llama_prompt}")

        data = {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": llama_prompt}
            ],
            "max_tokens": 4096,
            "temperature": temp
        }

        logging.debug("llama: Submitting request to API endpoint")
        print("llama: Submitting request to API endpoint")
        response = requests.post(api_url, headers=headers, json=data)
        response_data = response.json()
        logging.debug("API Response Data: %s", response_data)

        if response.status_code == 200:
            # if 'X' in response_data:
            logging.debug(response_data)
            summary = response_data['content'].strip()
            logging.debug("llama: Summarization successful")
            print("Summarization successful.")
            return summary
        else:
            logging.error(f"Llama: API request failed with status code {response.status_code}: {response.text}")
            return f"Llama: API request failed: {response.text}"

    except Exception as e:
        logging.error("Llama: Error in processing: %s", str(e))
        return f"Llama: Error occurred while processing summary with llama: {str(e)}"


# https://lite.koboldai.net/koboldcpp_api#/api%2Fv1/post_api_v1_generate
def summarize_with_kobold(input_data, api_key, custom_prompt_input, kobold_api_IP="http://127.0.0.1:5001/api/v1/generate", temp=None, system_message=None):
    logging.debug("Kobold: Summarization process starting...")
    try:
        logging.debug("Kobold: Loading and validating configurations")
        loaded_config_data = load_and_log_configs()
        if loaded_config_data is None:
            logging.error("Failed to load configuration data")
            kobold_api_key = None
        else:
            # Prioritize the API key passed as a parameter
            if api_key and api_key.strip():
                kobold_api_key = api_key
                logging.info("Kobold: Using API key provided as parameter")
            else:
                # If no parameter is provided, use the key from the config
                kobold_api_key = loaded_config_data['api_keys'].get('kobold')
                if kobold_api_key:
                    logging.info("Kobold: Using API key from config file")
                else:
                    logging.warning("Kobold: No API key found in config file")

        # Final check to ensure we have a valid API key
        if not kobold_api_key or not kobold_api_key.strip():
            logging.error("Kobold: No valid API key available")
            raise ValueError("No valid Anthropic API key available")


        logging.debug(f"Kobold: Using API Key: {kobold_api_key[:5]}...{kobold_api_key[-5:]}")

        if isinstance(input_data, str) and os.path.isfile(input_data):
            logging.debug("Kobold.cpp: Loading json data for summarization")
            with open(input_data, 'r') as file:
                data = json.load(file)
        else:
            logging.debug("Kobold.cpp: Using provided string data for summarization")
            data = input_data

        logging.debug(f"Kobold.cpp: Loaded data: {data}")
        logging.debug(f"Kobold.cpp: Type of data: {type(data)}")

        if isinstance(data, dict) and 'summary' in data:
            # If the loaded data is a dictionary and already contains a summary, return it
            logging.debug("Kobold.cpp: Summary already exists in the loaded data")
            return data['summary']

        # If the loaded data is a list of segment dictionaries or a string, proceed with summarization
        if isinstance(data, list):
            segments = data
            text = extract_text_from_segments(segments)
        elif isinstance(data, str):
            text = data
        else:
            raise ValueError("Kobold.cpp: Invalid input data format")

        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
        }

        kobold_prompt = f"{custom_prompt_input}\n\n\n\n{text}"
        logging.debug("kobold: Prompt being sent is {kobold_prompt}")

        # FIXME
        # Values literally c/p from the api docs....
        data = {
            "max_context_length": 8096,
            "max_length": 4096,
            "prompt": f"{kobold_prompt}"
        }

        logging.debug("kobold: Submitting request to API endpoint")
        print("kobold: Submitting request to API endpoint")
        try:
            response = requests.post(kobold_api_IP, headers=headers, json=data)
            logging.debug("kobold: API Response Status Code: %d", response.status_code)

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logging.debug("kobold: API Response Data: %s", response_data)

                    if response_data and 'results' in response_data and len(response_data['results']) > 0:
                        summary = response_data['results'][0]['text'].strip()
                        logging.debug("kobold: Summarization successful")
                        return summary
                    else:
                        logging.error("Expected data not found in API response.")
                        return "Expected data not found in API response."
                except ValueError as e:
                    logging.error("kobold: Error parsing JSON response: %s", str(e))
                    return f"Error parsing JSON response: {str(e)}"
            else:
                logging.error(f"kobold: API request failed with status code {response.status_code}: {response.text}")
                return f"kobold: API request failed: {response.text}"
        except Exception as e:
            logging.error("kobold: Error in processing: %s", str(e))
            return f"kobold: Error occurred while processing summary with kobold: {str(e)}"
    except Exception as e:
        logging.error("kobold: Error in processing: %s", str(e))
        return f"kobold: Error occurred while processing summary with kobold: {str(e)}"


# https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API
def summarize_with_oobabooga(input_data, api_key, custom_prompt, api_url="http://127.0.0.1:5000/v1/chat/completions", temp=None, system_message=None):
    logging.debug("Oobabooga: Summarization process starting...")
    try:
        logging.debug("Oobabooga: Loading and validating configurations")
        loaded_config_data = load_and_log_configs()
        if loaded_config_data is None:
            logging.error("Failed to load configuration data")
            ooba_api_key = None
        else:
            # Prioritize the API key passed as a parameter
            if api_key and api_key.strip():
                ooba_api_key = api_key
                logging.info("Oobabooga: Using API key provided as parameter")
            else:
                # If no parameter is provided, use the key from the config
                ooba_api_key = loaded_config_data['api_keys'].get('ooba')
                if ooba_api_key:
                    logging.info("Anthropic: Using API key from config file")
                else:
                    logging.warning("Anthropic: No API key found in config file")

        # Final check to ensure we have a valid API key
        if not ooba_api_key or not ooba_api_key.strip():
            logging.error("Anthropic: No valid API key available")
            # You might want to raise an exception here or handle this case as appropriate for your application
            # For example: raise ValueError("No valid Anthropic API key available")


        logging.debug(f"Oobabooga: Using API Key: {ooba_api_key[:5]}...{ooba_api_key[-5:]}")

        if isinstance(input_data, str) and os.path.isfile(input_data):
            logging.debug("Oobabooga: Loading json data for summarization")
            with open(input_data, 'r') as file:
                data = json.load(file)
        else:
            logging.debug("Oobabooga: Using provided string data for summarization")
            data = input_data

        logging.debug(f"Oobabooga: Loaded data: {data}")
        logging.debug(f"Oobabooga: Type of data: {type(data)}")

        if isinstance(data, dict) and 'summary' in data:
            # If the loaded data is a dictionary and already contains a summary, return it
            logging.debug("Oobabooga: Summary already exists in the loaded data")
            return data['summary']

        # If the loaded data is a list of segment dictionaries or a string, proceed with summarization
        if isinstance(data, list):
            segments = data
            text = extract_text_from_segments(segments)
        elif isinstance(data, str):
            text = data
        else:
            raise ValueError("Invalid input data format")

        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
        }

        # prompt_text = "I like to eat cake and bake cakes. I am a baker. I work in a French bakery baking cakes. It
        # is a fun job. I have been baking cakes for ten years. I also bake lots of other baked goods, but cakes are
        # my favorite." prompt_text += f"\n\n{text}"  # Uncomment this line if you want to include the text variable
        ooba_prompt = f"{text}" + f"\n\n\n\n{custom_prompt}"
        logging.debug("ooba: Prompt being sent is {ooba_prompt}")

        data = {
            "mode": "chat",
            "character": "Example",
            "messages": [{"role": "user", "content": ooba_prompt}]
        }

        logging.debug("ooba: Submitting request to API endpoint")
        print("ooba: Submitting request to API endpoint")
        response = requests.post(api_url, headers=headers, json=data, verify=False)
        logging.debug("ooba: API Response Data: %s", response)

        if response.status_code == 200:
            response_data = response.json()
            summary = response.json()['choices'][0]['message']['content']
            logging.debug("ooba: Summarization successful")
            print("Summarization successful.")
            return summary
        else:
            logging.error(f"oobabooga: API request failed with status code {response.status_code}: {response.text}")
            return f"ooba: API request failed with status code {response.status_code}: {response.text}"

    except Exception as e:
        logging.error("ooba: Error in processing: %s", str(e))
        return f"ooba: Error occurred while processing summary with oobabooga: {str(e)}"


# FIXME - Install is more trouble than care to deal with right now.
def summarize_with_tabbyapi(input_data, custom_prompt_input, api_key=None, api_IP="http://127.0.0.1:5000/v1/chat/completions"):
    logging.debug("TabbyAPI: Summarization process starting...")
    try:
        logging.debug("TabbyAPI: Loading and validating configurations")
        loaded_config_data = load_and_log_configs()
        if loaded_config_data is None:
            logging.error("Failed to load configuration data")
            tabby_api_key = None
        else:
            # Prioritize the API key passed as a parameter
            if api_key and api_key.strip():
                tabby_api_key = api_key
                logging.info("TabbyAPI: Using API key provided as parameter")
            else:
                # If no parameter is provided, use the key from the config
                tabby_api_key = loaded_config_data['api_keys'].get('tabby')
                if tabby_api_key:
                    logging.info("TabbyAPI: Using API key from config file")
                else:
                    logging.warning("TabbyAPI: No API key found in config file")

        # Final check to ensure we have a valid API key
        if not tabby_api_key or not tabby_api_key.strip():
            logging.error("TabbyAPI: No valid API key available")
            # You might want to raise an exception here or handle this case as appropriate for your application
            # For example: raise ValueError("No valid Anthropic API key available")


        logging.debug(f"TabbyAPI: Using API Key: {tabby_api_key[:5]}...{tabby_api_key[-5:]}")

        if isinstance(input_data, str) and os.path.isfile(input_data):
            logging.debug("tabby: Loading json data for summarization")
            with open(input_data, 'r') as file:
                data = json.load(file)
        else:
            logging.debug("tabby: Using provided string data for summarization")
            data = input_data

        logging.debug(f"tabby: Loaded data: {data}")
        logging.debug(f"tabby: Type of data: {type(data)}")

        if isinstance(data, dict) and 'summary' in data:
            # If the loaded data is a dictionary and already contains a summary, return it
            logging.debug("tabby: Summary already exists in the loaded data")
            return data['summary']

        # If the loaded data is a list of segment dictionaries or a string, proceed with summarization
        if isinstance(data, list):
            segments = data
            text = extract_text_from_segments(segments)
        elif isinstance(data, str):
            text = data
        else:
            raise ValueError("Invalid input data format")

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data2 = {
            'text': text,
            'model': 'tabby'  # Specify the model if needed
        }
        tabby_api_ip = loaded_config_data['local_apis']['tabby']['ip']
        response = requests.post(tabby_api_ip, headers=headers, json=data2)
        response.raise_for_status()
        summary = response.json().get('summary', '')
        return summary
    except requests.exceptions.RequestException as e:
        logger.error(f"Error summarizing with TabbyAPI: {e}")
        return "Error summarizing with TabbyAPI."

def summarize_with_vllm(
        input_data: Union[str, dict, list],
        custom_prompt_input: str,
        api_key: str = None,
        vllm_api_url: str = "http://127.0.0.1:8000/v1/chat/completions",
        model: str = None
) -> str:
    logging.debug("vLLM: Summarization process starting...")
    try:
        logging.debug("vLLM: Loading and validating configurations")
        loaded_config_data = load_and_log_configs()
        if loaded_config_data is None:
            logging.error("Failed to load configuration data")
            vllm_api_key = None
        else:
            # Prioritize the API key passed as a parameter
            if api_key and api_key.strip():
                vllm_api_key = api_key
                logging.info("vLLM: Using API key provided as parameter")
            else:
                # If no parameter is provided, use the key from the config
                vllm_api_key = loaded_config_data['api_keys'].get('vllm')
                if vllm_api_key:
                    logging.info("vLLM: Using API key from config file")
                else:
                    logging.warning("vLLM: No API key found in config file")

        # Final check to ensure we have a valid API key
        if not vllm_api_key or not vllm_api_key.strip():
            logging.error("Anthropic: No valid API key available")
            raise ValueError("No valid vLLM API key available")

        logging.debug(f"vLLM: Using API Key: {vllm_api_key[:5]}...{vllm_api_key[-5:]}")
        # Process input data
        if isinstance(input_data, str) and os.path.isfile(input_data):
            logging.debug("vLLM: Loading json data for summarization")
            with open(input_data, 'r') as file:
                data = json.load(file)
        else:
            logging.debug("vLLM: Using provided data for summarization")
            data = input_data

        logging.debug(f"vLLM: Type of data: {type(data)}")

        # Extract text for summarization
        if isinstance(data, dict) and 'summary' in data:
            logging.debug("vLLM: Summary already exists in the loaded data")
            return data['summary']
        elif isinstance(data, list):
            text = extract_text_from_segments(data)
        elif isinstance(data, str):
            text = data
        elif isinstance(data, dict):
            text = json.dumps(data)
        else:
            raise ValueError("Invalid input data format")

        logging.debug(f"vLLM: Extracted text (showing first 500 chars): {text[:500]}...")

        model = model or loaded_config_data['models']['vllm']

        # Prepare the API request
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional summarizer."},
                {"role": "user", "content": f"{text}\n\n{custom_prompt_input}"}
            ]
        }

        # Make the API call
        logging.debug(f"vLLM: Sending request to {vllm_api_url}")
        response = requests.post(vllm_api_url, headers=headers, json=payload)

        # Check for successful response
        response.raise_for_status()

        # Extract and return the summary
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            summary = response_data['choices'][0]['message']['content']
            logging.debug("vLLM: Summarization successful")
            logging.debug(f"vLLM: Summary (first 500 chars): {summary[:500]}...")
            return summary
        else:
            raise ValueError("Unexpected response format from vLLM API")

    except requests.RequestException as e:
        logging.error(f"vLLM: API request failed: {str(e)}")
        return f"Error: vLLM API request failed - {str(e)}"
    except json.JSONDecodeError as e:
        logging.error(f"vLLM: Failed to parse API response: {str(e)}")
        return f"Error: Failed to parse vLLM API response - {str(e)}"
    except Exception as e:
        logging.error(f"vLLM: Unexpected error during summarization: {str(e)}")
        return f"Error: Unexpected error during vLLM summarization - {str(e)}"


def save_summary_to_file(summary, file_path):
    logging.debug("Now saving summary to file...")
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    summary_file_path = os.path.join(os.path.dirname(file_path), base_name + '_summary.txt')
    os.makedirs(os.path.dirname(summary_file_path), exist_ok=True)
    logging.debug("Opening summary file for writing, *segments.json with *_summary.txt")
    with open(summary_file_path, 'w') as file:
        file.write(summary)
    logging.info(f"Summary saved to file: {summary_file_path}")

#
#
#######################################################################################################################



