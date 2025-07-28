#!/usr/bin/env python3
"""
Cloud inference utilities for EdgeOptimizer
Centralized cloud API management for different providers
"""

import time
import requests
import os
from typing import Dict, Any, Optional


class CloudInferenceManager:
    """Centralized cloud inference management for multiple providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("cloud_api_key", "")
        self.api_url = config.get("cloud_api_url", "")
        self.provider = config.get("cloud_provider", "openai")
        
    def run_inference(self, prompt: str) -> Dict[str, Any]:
        """Run cloud inference with the configured provider"""
        try:
            # Check if we should use mock responses
            if self.config.get("inference_settings", {}).get("use_mock_cloud", False):
                return self._run_mock_inference(prompt)
            
            # Handle different API providers
            if self.provider == "huggingface" or "huggingface.co" in self.api_url:
                return self._run_huggingface_inference(prompt)
            else:
                return self._run_openai_inference(prompt)
                
        except Exception as e:
            return {
                "response": f"Cloud inference error: {e}",
                "inference_time": 0,
                "success": False,
                "provider": self.provider,
                "error": str(e)
            }
    
    def _run_mock_inference(self, prompt: str) -> Dict[str, Any]:
        """Generate mock cloud responses for testing"""
        start_time = time.time()
        time.sleep(0.5 + (len(prompt) * 0.01))  # Simulate network latency
        inference_time = time.time() - start_time
        
        return {
            "response": f"Mock cloud response to: {prompt[:50]}...",
            "inference_time": inference_time,
            "success": True,
            "provider": "mock",
            "note": "This is a simulated response for testing"
        }
    
    def _run_huggingface_inference(self, prompt: str) -> Dict[str, Any]:
        """Run inference using Hugging Face Router API (OpenAI-compatible format)"""
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add authorization if API key is provided and not a placeholder
            if self.api_key and self.api_key != "free-no-key-required":
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            max_tokens = self.config.get("inference_settings", {}).get("cloud_max_tokens", 100)
            temperature = self.config.get("inference_settings", {}).get("temperature", 0.7)
            cloud_model = self.config.get("inference_settings", {}).get("cloud_model", 
                          self.config.get("cloud_model", "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai"))
            
            # Use OpenAI-compatible chat completions format
            chat_url = f"{self.api_url}/chat/completions"
            data = {
                "model": cloud_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": min(max_tokens, 1000),
                "temperature": temperature
            }
            
            start_time = time.time()
            
            # Add retry logic for timeout and connection issues
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    response = requests.post(chat_url, headers=headers, json=data, timeout=45)
                    inference_time = time.time() - start_time
                    break
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"⚠️  Timeout on attempt {retry_count}, retrying...")
                        time.sleep(2 ** retry_count)  # Exponential backoff
                        continue
                    else:
                        inference_time = time.time() - start_time
                        return {
                            "response": f"Hugging Face Router API error: Request timed out after {max_retries} attempts",
                            "inference_time": inference_time,
                            "success": False,
                            "provider": "huggingface",
                            "status_code": 408
                        }
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"⚠️  Connection error on attempt {retry_count}, retrying...")
                        time.sleep(2 ** retry_count)
                        continue
                    else:
                        inference_time = time.time() - start_time
                        return {
                            "response": f"Hugging Face Router API error: {str(e)}",
                            "inference_time": inference_time,
                            "success": False,
                            "provider": "huggingface",
                            "status_code": 500
                        }
            
            if response.status_code == 200:
                result = response.json()
                response_text = self._parse_huggingface_chat_response(result)
                
                return {
                    "response": response_text,
                    "inference_time": inference_time,
                    "success": True,
                    "provider": "huggingface",
                    "status_code": response.status_code
                }
            else:
                error_msg = f"Hugging Face Router API Error {response.status_code}"
                try:
                    error_detail = response.json().get('error', {}).get('message', '')
                    if error_detail:
                        error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                
                return {
                    "response": error_msg,
                    "inference_time": inference_time,
                    "success": False,
                    "provider": "huggingface",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "response": f"Hugging Face Router API error: {e}",
                "inference_time": 0,
                "success": False,
                "provider": "huggingface",
                "error": str(e)
            }
    
    def _parse_huggingface_response(self, result: Any, original_prompt: str) -> str:
        """Parse Hugging Face API response format (legacy)"""
        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                generated_text = result[0]["generated_text"]
                # Remove the input prompt from the response if it's included
                if generated_text.startswith(original_prompt):
                    generated_text = generated_text[len(original_prompt):].strip()
                return generated_text or "Generated response from Hugging Face model"
            else:
                return str(result[0])
        else:
            return str(result)
    
    def _parse_huggingface_chat_response(self, result: Dict[str, Any]) -> str:
        """Parse Hugging Face Router API chat completions response (OpenAI-compatible)"""
        try:
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"].strip()
                elif "text" in choice:
                    return choice["text"].strip()
            
            # Fallback for unexpected format
            return str(result)
        except Exception as e:
            return f"Error parsing response: {e}"
    
    def _run_openai_inference(self, prompt: str) -> Dict[str, Any]:
        """Run inference using OpenAI API"""
        try:
            # Try to get API key from environment if not set in config
            api_key = self.api_key
            if not api_key or api_key == "your-openai-api-key-here":
                api_key = os.environ.get("OPENAI_API_KEY", "")
            
            if not api_key or api_key == "demo-key-disabled-for-testing":
                return {
                    "response": "Error: No valid API key configured. Please set your OpenAI API key in experiment_config.json or OPENAI_API_KEY environment variable",
                    "inference_time": 0,
                    "success": False,
                    "provider": "openai",
                    "error": "missing_api_key"
                }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            cloud_model = self.config.get("inference_settings", {}).get("cloud_model", "gpt-3.5-turbo")
            max_tokens = self.config.get("inference_settings", {}).get("cloud_max_tokens", 50)
            temperature = self.config.get("inference_settings", {}).get("temperature", 0.7)
            
            data = {
                "model": cloud_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            start_time = time.time()
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            inference_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result['choices'][0]['message']['content'].strip(),
                    "inference_time": inference_time,
                    "success": True,
                    "provider": "openai",
                    "model": cloud_model,
                    "status_code": response.status_code
                }
            else:
                error_msg = f"OpenAI API Error {response.status_code}"
                try:
                    error_detail = response.json().get('error', {}).get('message', '')
                    if error_detail:
                        error_msg += f": {error_detail}"
                except:
                    pass
                
                return {
                    "response": error_msg,
                    "inference_time": inference_time,
                    "success": False,
                    "provider": "openai",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "response": f"OpenAI API error: {e}",
                "inference_time": 0,
                "success": False,
                "provider": "openai",
                "error": str(e)
            }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the configured cloud provider"""
        return {
            "provider": self.provider,
            "api_url": self.api_url,
            "has_api_key": bool(self.api_key and self.api_key != "free-no-key-required"),
            "mock_mode": self.config.get("inference_settings", {}).get("use_mock_cloud", False),
            "max_tokens": self.config.get("inference_settings", {}).get("cloud_max_tokens", 50)
        }
