from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from litellm import completion
import os

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str = None, model: str = None, **kwargs):
        self.api_key = api_key
        self.model = model
        self.extra_config = kwargs
    
    @abstractmethod
    def get_completion(self, messages: List[Dict], **kwargs) -> str:
        """Get completion from the LLM provider"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the provider configuration"""
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Get list of required configuration fields"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(api_key, model, **kwargs)
    
    def get_completion(self, messages: List[Dict], **kwargs) -> str:
        try:
            # Set API key for this request
            os.environ['OPENAI_API_KEY'] = self.api_key
            
            response = completion(
                model=f"openai/{self.model}",
                messages=messages,
                **kwargs
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.model)
    
    def get_required_fields(self) -> List[str]:
        return ["api_key", "model"]

class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        super().__init__(api_key, model, **kwargs)
    
    def get_completion(self, messages: List[Dict], **kwargs) -> str:
        try:
            os.environ['ANTHROPIC_API_KEY'] = self.api_key
            
            response = completion(
                model=f"anthropic/{self.model}",
                messages=messages,
                **kwargs
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.model)
    
    def get_required_fields(self) -> List[str]:
        return ["api_key", "model"]

class GeminiProvider(LLMProvider):
    """Google Gemini API provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", **kwargs):
        super().__init__(api_key, model, **kwargs)
    
    def get_completion(self, messages: List[Dict], **kwargs) -> str:
        try:
            os.environ['GEMINI_API_KEY'] = self.api_key
            
            response = completion(
                model=f"gemini/{self.model}",
                messages=messages,
                **kwargs
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.model)
    
    def get_required_fields(self) -> List[str]:
        return ["api_key", "model"]
    
class HfProvider(LLMProvider):
    """Huggingface API provider"""
    
    def __init__(self, api_key: str, model: str = "deepseek-ai/DeepSeek-R1", **kwargs):
        super().__init__(api_key, model, **kwargs)
    
    def get_completion(self, messages: List[Dict], **kwargs) -> str:
        try:
            os.environ['HF_TOKEN'] = self.api_key
            
            response = completion(
                model=f"huggingface/{self.model}",
                messages=messages,
                **kwargs
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"Huggingface API error: {str(e)}")
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.model)
    
    def get_required_fields(self) -> List[str]:
        return ["api_key", "model"]

class OllamaProvider(LLMProvider):
    """Ollama local provider"""
    
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model=model, **kwargs)
        self.base_url = base_url
    
    def get_completion(self, messages: List[Dict], **kwargs) -> str:
        try:
            response = completion(
                model=f"ollama/{self.model}",
                messages=messages,
                api_base=self.base_url,
                **kwargs
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def validate_config(self) -> bool:
        return bool(self.model and self.base_url)
    
    def get_required_fields(self) -> List[str]:
        return ["model", "base_url"]

class LLMManager:
    """Manager class for LLM providers"""
    
    PROVIDERS = {
        "openai": {
            "class": OpenAIProvider,
            "name": "OpenAI (GPT-3.5, GPT-4)",
            "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        },
        "anthropic": {
            "class": AnthropicProvider,
            "name": "Anthropic (Claude)",
            "models": ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        },
        "gemini": {
            "class": GeminiProvider,
            "name": "Google (Gemini)",
            "models": ["gemini-1.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-exp", "gemini-2.5-flash"]
        },
        "huggingface": {
            "class": HfProvider,
            "name": "Huggingface (Hf)",
            "models": ["deepseek-ai/DeepSeek-R1"]
        },
        "ollama": {
            "class": OllamaProvider,
            "name": "Ollama (Local)",
            "models": ["llama3.1", "codellama", "mistral", "phi3"]
        }
    }
    
    def __init__(self):
        self.current_provider: Optional[LLMProvider] = None
    
    def get_available_providers(self) -> Dict:
        """Get list of available providers"""
        return {k: v["name"] for k, v in self.PROVIDERS.items()}
    
    def get_provider_models(self, provider_key: str) -> List[str]:
        """Get available models for a provider"""
        if provider_key in self.PROVIDERS:
            return self.PROVIDERS[provider_key]["models"]
        return []
    
    def create_provider(self, provider_key: str, config: Dict) -> LLMProvider:
        """Create a provider instance"""
        if provider_key not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_key}")
        
        provider_class = self.PROVIDERS[provider_key]["class"]
        return provider_class(**config)
    
    def set_provider(self, provider: LLMProvider):
        """Set the current provider"""
        if not provider.validate_config():
            raise ValueError("Invalid provider configuration")
        self.current_provider = provider
    
    def get_completion(self, messages: List[Dict], **kwargs) -> str:
        """Get completion from current provider"""
        if not self.current_provider:
            raise ValueError("No provider configured")
        
        return self.current_provider.get_completion(messages, **kwargs)