"""
LLM客户端
支持多种大语言模型API进行财务报告分析
"""

import os
import json
import base64
import time
from typing import Dict, Optional, Any, List
import requests
from abc import ABC, abstractmethod
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    def analyze_text(self, text: str, prompt: str) -> str:
        """分析文本内容"""
        pass
    
    @abstractmethod
    def analyze_pdf_directly(self, pdf_path: str, prompt: str) -> str:
        """直接分析PDF文件（如果API支持）"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        """
        初始化OpenAI客户端
        
        Args:
            api_key (str): OpenAI API密钥
            base_url (str): API基础URL
            model (str): 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_text(self, text: str, prompt: str) -> str:
        """
        分析文本内容
        
        Args:
            text (str): 文本内容
            prompt (str): 分析提示词
            
        Returns:
            str: 分析结果
        """
        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 4000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"OpenAI API错误: {response.status_code}, {response.text}")
                
        except Exception as e:
            print(f"OpenAI分析文本失败: {e}")
            return ""
    
    def analyze_pdf_directly(self, pdf_path: str, prompt: str) -> str:
        """
        直接分析PDF文件（GPT-4V支持）
        
        Args:
            pdf_path (str): PDF文件路径
            prompt (str): 分析提示词
            
        Returns:
            str: 分析结果
        """
        try:
            # 将PDF转换为base64
            with open(pdf_path, "rb") as pdf_file:
                pdf_base64 = base64.b64encode(pdf_file.read()).decode()
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ]
            
            payload = {
                "model": "gpt-4o",  # 使用支持文件上传的模型
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 4000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"PDF直接分析失败，使用文本分析: {response.status_code}")
                # 降级到文本分析
                return ""
                
        except Exception as e:
            print(f"OpenAI直接分析PDF失败: {e}")
            return ""


class ClaudeClient(BaseLLMClient):
    """Claude客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com", model: str = "claude-3-sonnet-20240229"):
        """
        初始化Claude客户端
        
        Args:
            api_key (str): Claude API密钥
            base_url (str): API基础URL
            model (str): 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def analyze_text(self, text: str, prompt: str) -> str:
        """
        分析文本内容
        
        Args:
            text (str): 文本内容
            prompt (str): 分析提示词
            
        Returns:
            str: 分析结果
        """
        try:
            payload = {
                "model": self.model,
                "max_tokens": 4000,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": f"{prompt}\n\n以下是需要分析的财务报告内容:\n{text}"
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                raise Exception(f"Claude API错误: {response.status_code}, {response.text}")
                
        except Exception as e:
            print(f"Claude分析文本失败: {e}")
            return ""
    
    def analyze_pdf_directly(self, pdf_path: str, prompt: str) -> str:
        """Claude目前不支持直接PDF分析"""
        print("Claude暂不支持直接PDF分析，请使用文本分析")
        return ""


class GeminiClient(BaseLLMClient):
    """Google Gemini客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com/v1beta", model: str = "gemini-1.5-pro"):
        """
        初始化Gemini客户端
        
        Args:
            api_key (str): Google Gemini API密钥
            base_url (str): API基础URL (仅用于兼容性，官方SDK会自动处理)
            model (str): 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.headers = {"Content-Type": "application/json"}
        
        # 配置代理（如果设置了环境变量）
        self.proxy_config = self._setup_proxy()
        
        # 尝试使用官方SDK
        self.use_official_sdk = genai is not None
        if self.use_official_sdk:
            try:
                # 配置官方SDK
                genai.configure(api_key=api_key)
                
                # 配置安全设置 - 降低安全限制以减少被阻止的可能性
                self.safety_settings = {
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                
                # 初始化模型
                self.genai_model = genai.GenerativeModel(
                    model_name=self.model,
                    safety_settings=self.safety_settings
                )
                print(f"使用Google官方SDK初始化Gemini客户端成功: {model}")
            except Exception as e:
                print(f"官方SDK初始化失败，将使用HTTP请求: {e}")
                self.use_official_sdk = False
        else:
            print("Google GenerativeAI SDK未安装，使用HTTP请求")
    
    def _setup_proxy(self) -> Dict[str, str]:
        """设置代理配置"""
        proxy_config = {}
        
        # 检查环境变量中的代理配置
        http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
        
        if http_proxy:
            proxy_config['http'] = http_proxy
        if https_proxy:
            proxy_config['https'] = https_proxy
            
        return proxy_config
    
    def _retry_with_backoff(self, func, max_retries: int = 3, initial_delay: float = 1.0):
        """带指数退避的重试机制"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                    
                delay = initial_delay * (2 ** attempt)
                print(f"请求失败，{delay:.1f}秒后重试 (尝试 {attempt + 1}/{max_retries}): {str(e)[:100]}")
                time.sleep(delay)
    
    def analyze_text(self, text: str, prompt: str) -> str:
        """
        分析文本内容
        
        Args:
            text (str): 文本内容
            prompt (str): 分析提示词
            
        Returns:
            str: 分析结果
        """
        # 使用官方SDK
        if self.use_official_sdk:
            return self._analyze_text_with_sdk(text, prompt)
        
        # 降级到HTTP请求
        return self._analyze_text_with_http(text, prompt)
    
    def _analyze_text_with_sdk(self, text: str, prompt: str) -> str:
        """使用官方SDK分析文本"""
        try:
            def make_request():
                full_prompt = f"{prompt}\n\n以下是需要分析的财务报告内容:\n{text}"
                
                # 配置生成参数
                generation_config = {
                    'temperature': 0.1,
                    'max_output_tokens': 4000,
                }
                
                response = self.genai_model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                if response.text:
                    return response.text
                elif response.candidates:
                    return response.candidates[0].content.parts[0].text
                else:
                    raise Exception(f"Gemini SDK响应为空: {response}")
            
            return self._retry_with_backoff(make_request, max_retries=3)
            
        except Exception as e:
            print(f"Gemini SDK分析文本失败: {e}")
            # 尝试降级到HTTP请求
            print("尝试降级到HTTP请求...")
            return self._analyze_text_with_http(text, prompt)
    
    def _analyze_text_with_http(self, text: str, prompt: str) -> str:
        """使用HTTP请求分析文本"""
        try:
            def make_request():
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"{prompt}\n\n以下是需要分析的财务报告内容:\n{text}"
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 4000
                    },
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }
                
                # 尝试多个API端点
                endpoints = [
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self.api_key}",
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                ]
                
                last_error = None
                for endpoint in endpoints:
                    try:
                        # 准备请求参数
                        request_kwargs = {
                            'headers': self.headers,
                            'json': payload,
                            'timeout': 120  # 增加超时时间
                        }
                        
                        # 如果配置了代理，添加代理设置
                        if self.proxy_config:
                            request_kwargs['proxies'] = self.proxy_config
                            print(f"使用代理: {self.proxy_config}")
                        
                        response = requests.post(endpoint, **request_kwargs)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if "candidates" in result and result["candidates"]:
                                return result["candidates"][0]["content"]["parts"][0]["text"]
                            else:
                                raise Exception(f"Gemini API响应格式错误: {result}")
                        else:
                            raise Exception(f"HTTP {response.status_code}: {response.text}")
                            
                    except Exception as e:
                        last_error = e
                        print(f"端点 {endpoint} 请求失败: {e}")
                        continue
                        
                raise last_error or Exception("所有API端点都无法访问")
            
            return self._retry_with_backoff(make_request, max_retries=2)
            
        except Exception as e:
            print(f"Gemini HTTP分析文本失败: {e}")
            return ""
    
    def analyze_pdf_directly(self, pdf_path: str, prompt: str) -> str:
        """
        直接分析PDF文件（Gemini支持文件上传）
        
        Args:
            pdf_path (str): PDF文件路径
            prompt (str): 分析提示词
            
        Returns:
            str: 分析结果
        """
        # 使用官方SDK
        if self.use_official_sdk:
            return self._analyze_pdf_with_sdk(pdf_path, prompt)
        
        # 降级到HTTP请求
        return self._analyze_pdf_with_http(pdf_path, prompt)
    
    def _analyze_pdf_with_sdk(self, pdf_path: str, prompt: str) -> str:
        """使用官方SDK分析PDF"""
        try:
            def make_request():
                # 上传文件到Gemini
                uploaded_file = genai.upload_file(pdf_path)
                print(f"PDF文件已上传: {uploaded_file.name}")
                
                try:
                    # 等待文件处理完成
                    while uploaded_file.state.name == "PROCESSING":
                        print("正在处理PDF文件...")
                        time.sleep(2)
                        uploaded_file = genai.get_file(uploaded_file.name)
                    
                    if uploaded_file.state.name == "FAILED":
                        raise Exception(f"PDF文件处理失败: {uploaded_file.state}")
                    
                    # 生成内容
                    response = self.genai_model.generate_content(
                        [prompt, uploaded_file],
                        generation_config={'temperature': 0.1, 'max_output_tokens': 4000}
                    )
                    
                    if response.text:
                        return response.text
                    elif response.candidates:
                        return response.candidates[0].content.parts[0].text
                    else:
                        raise Exception(f"Gemini SDK PDF响应为空: {response}")
                        
                finally:
                    # 清理上传的文件
                    try:
                        genai.delete_file(uploaded_file.name)
                        print("已清理上传的PDF文件")
                    except:
                        pass
            
            return self._retry_with_backoff(make_request, max_retries=2)
            
        except Exception as e:
            print(f"Gemini SDK分析PDF失败: {e}")
            # 尝试降级到HTTP请求
            print("尝试降级到HTTP请求...")
            return self._analyze_pdf_with_http(pdf_path, prompt)
    
    def _analyze_pdf_with_http(self, pdf_path: str, prompt: str) -> str:
        """使用HTTP请求分析PDF"""
        try:
            import base64
            
            def make_request():
                # 将PDF转换为base64
                with open(pdf_path, "rb") as pdf_file:
                    pdf_base64 = base64.b64encode(pdf_file.read()).decode()
                
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": pdf_base64
                                }
                            }
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 4000
                    },
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }
                
                # 尝试多个API端点
                endpoints = [
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self.api_key}",
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                ]
                
                last_error = None
                for endpoint in endpoints:
                    try:
                        request_kwargs = {
                            'headers': self.headers,
                            'json': payload,
                            'timeout': 180  # PDF处理需要更长时间
                        }
                        
                        if self.proxy_config:
                            request_kwargs['proxies'] = self.proxy_config
                        
                        response = requests.post(endpoint, **request_kwargs)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if "candidates" in result and result["candidates"]:
                                return result["candidates"][0]["content"]["parts"][0]["text"]
                            else:
                                raise Exception(f"PDF分析响应格式错误: {result}")
                        else:
                            raise Exception(f"HTTP {response.status_code}: {response.text}")
                            
                    except Exception as e:
                        last_error = e
                        print(f"PDF端点 {endpoint} 请求失败: {e}")
                        continue
                        
                raise last_error or Exception("所有PDF API端点都无法访问")
            
            return self._retry_with_backoff(make_request, max_retries=1)
            
        except Exception as e:
            print(f"Gemini HTTP直接分析PDF失败: {e}")
            return ""


class LocalLLMClient(BaseLLMClient):
    """本地LLM客户端（如Ollama）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:14b"):
        """
        初始化本地LLM客户端
        
        Args:
            base_url (str): 本地LLM API地址
            model (str): 模型名称
        """
        self.base_url = base_url
        self.model = model
        self.headers = {"Content-Type": "application/json"}
    
    def analyze_text(self, text: str, prompt: str) -> str:
        """
        分析文本内容
        
        Args:
            text (str): 文本内容
            prompt (str): 分析提示词
            
        Returns:
            str: 分析结果
        """
        try:
            payload = {
                "model": self.model,
                "prompt": f"{prompt}\n\n以下是需要分析的财务报告内容:\n{text}",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 4000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"本地LLM API错误: {response.status_code}, {response.text}")
                
        except Exception as e:
            print(f"本地LLM分析文本失败: {e}")
            return ""
    
    def analyze_pdf_directly(self, pdf_path: str, prompt: str) -> str:
        """本地LLM通常不支持直接PDF分析"""
        print("本地LLM暂不支持直接PDF分析，请使用文本分析")
        return ""


class LLMClient:
    """LLM客户端管理器"""
    
    def __init__(self):
        """初始化LLM客户端管理器"""
        self.clients = {}
        self.active_client = None
        self._setup_clients()
    
    def _setup_clients(self):
        """设置可用的LLM客户端"""
        # 尝试设置OpenAI客户端
        openai_key = os.getenv('OPENAI_API_KEY')
        openai_base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        if openai_key:
            self.clients['openai'] = OpenAIClient(openai_key, openai_base_url)
            print("OpenAI客户端已配置")
        
        # 尝试设置Claude客户端
        claude_key = os.getenv('CLAUDE_API_KEY')
        if claude_key:
            self.clients['claude'] = ClaudeClient(claude_key)
            print("Claude客户端已配置")
        
        # 尝试设置Gemini客户端
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if gemini_key:
            try:
                self.clients['gemini'] = GeminiClient(gemini_key)
                print("Gemini客户端已配置")
            except Exception as e:
                print(f"Gemini客户端配置失败: {e}")
                print("💡 如遇网络问题，请参考 NETWORK_TROUBLESHOOTING.md")
        
        # 尝试设置本地LLM客户端
        local_url = os.getenv('LOCAL_LLM_URL', 'http://localhost:11434')
        try:
            # 测试本地LLM连接
            response = requests.get(f"{local_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.clients['local'] = LocalLLMClient(local_url)
                print("本地LLM客户端已配置")
        except:
            pass
        
        # 设置默认客户端
        if 'openai' in self.clients:
            self.active_client = self.clients['openai']
            print("使用OpenAI作为默认客户端")
        elif 'gemini' in self.clients:
            self.active_client = self.clients['gemini']
            print("使用Gemini作为默认客户端")
        elif 'claude' in self.clients:
            self.active_client = self.clients['claude']
            print("使用Claude作为默认客户端")
        elif 'local' in self.clients:
            self.active_client = self.clients['local']
            print("使用本地LLM作为默认客户端")
        else:
            print("警告: 未配置任何LLM客户端，请设置API密钥")
    
    def set_active_client(self, client_name: str) -> bool:
        """
        设置活跃客户端
        
        Args:
            client_name (str): 客户端名称 ('openai', 'claude', 'gemini', 'local')
            
        Returns:
            bool: 设置是否成功
        """
        if client_name in self.clients:
            self.active_client = self.clients[client_name]
            print(f"已切换到 {client_name} 客户端")
            return True
        else:
            print(f"客户端 {client_name} 不存在或未配置")
            return False
    
    def analyze_text(self, text: str, prompt: str) -> str:
        """
        使用活跃客户端分析文本
        
        Args:
            text (str): 文本内容
            prompt (str): 分析提示词
            
        Returns:
            str: 分析结果
        """
        if not self.active_client:
            raise Exception("未配置任何LLM客户端，请设置API密钥")
        
        return self.active_client.analyze_text(text, prompt)
    
    def analyze_pdf_directly(self, pdf_path: str, prompt: str) -> str:
        """
        使用活跃客户端直接分析PDF
        
        Args:
            pdf_path (str): PDF文件路径
            prompt (str): 分析提示词
            
        Returns:
            str: 分析结果
        """
        if not self.active_client:
            raise Exception("未配置任何LLM客户端，请设置API密钥")
        
        return self.active_client.analyze_pdf_directly(pdf_path, prompt)
    
    def get_available_clients(self) -> List[str]:
        """
        获取可用客户端列表
        
        Returns:
            List[str]: 可用客户端名称列表
        """
        return list(self.clients.keys())
    
    def is_configured(self) -> bool:
        """
        检查是否有配置的客户端
        
        Returns:
            bool: 是否有可用客户端
        """
        return self.active_client is not None