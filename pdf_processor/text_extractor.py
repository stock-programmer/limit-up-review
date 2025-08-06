"""
PDF文本提取器
用于从PDF文件中提取文本内容
支持多种PDF格式和编码
"""

import os
import re
from typing import List, Dict, Optional, Tuple
import PyPDF2
import pdfplumber
from io import StringIO


class PDFTextExtractor:
    """PDF文本提取器"""
    
    def __init__(self):
        """初始化文本提取器"""
        self.supported_methods = ['pdfplumber', 'pypdf2']
        self.default_method = 'pdfplumber'
    
    def extract_text_with_pdfplumber(self, pdf_path: str) -> str:
        """
        使用pdfplumber提取PDF文本
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            str: 提取的文本内容
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"=== 第 {page_num} 页 ===\n")
                            text_content.append(page_text)
                            text_content.append("\n\n")
                    except Exception as e:
                        print(f"提取第 {page_num} 页失败: {e}")
                        continue
                
                return "".join(text_content)
                
        except Exception as e:
            print(f"pdfplumber提取文本失败: {e}")
            return ""
    
    def extract_text_with_pypdf2(self, pdf_path: str) -> str:
        """
        使用PyPDF2提取PDF文本
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            str: 提取的文本内容
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"=== 第 {page_num} 页 ===\n")
                            text_content.append(page_text)
                            text_content.append("\n\n")
                    except Exception as e:
                        print(f"提取第 {page_num} 页失败: {e}")
                        continue
                
                return "".join(text_content)
                
        except Exception as e:
            print(f"PyPDF2提取文本失败: {e}")
            return ""
    
    def extract_text(self, pdf_path: str, method: str = None) -> str:
        """
        提取PDF文本内容
        
        Args:
            pdf_path (str): PDF文件路径
            method (str): 提取方法，'pdfplumber' 或 'pypdf2'
            
        Returns:
            str: 提取的文本内容
        """
        if not os.path.exists(pdf_path):
            print(f"文件不存在: {pdf_path}")
            return ""
        
        if not method:
            method = self.default_method
        
        print(f"使用 {method} 提取PDF文本: {os.path.basename(pdf_path)}")
        
        if method == 'pdfplumber':
            text = self.extract_text_with_pdfplumber(pdf_path)
        elif method == 'pypdf2':
            text = self.extract_text_with_pypdf2(pdf_path)
        else:
            print(f"不支持的提取方法: {method}")
            return ""
        
        # 如果主要方法失败，尝试备用方法
        if not text and method != 'pypdf2':
            print("主要方法失败，尝试备用方法...")
            text = self.extract_text_with_pypdf2(pdf_path)
        
        return text
    
    def extract_text_by_pages(self, pdf_path: str, start_page: int = 1, 
                            end_page: int = None) -> Dict[int, str]:
        """
        按页提取PDF文本
        
        Args:
            pdf_path (str): PDF文件路径
            start_page (int): 起始页码（从1开始）
            end_page (int): 结束页码，None表示到最后一页
            
        Returns:
            Dict[int, str]: 页码到文本内容的映射
        """
        result = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                if end_page is None:
                    end_page = total_pages
                
                # 调整页码范围
                start_page = max(1, start_page)
                end_page = min(total_pages, end_page)
                
                for page_num in range(start_page, end_page + 1):
                    try:
                        page = pdf.pages[page_num - 1]  # pdfplumber使用0-based索引
                        page_text = page.extract_text()
                        if page_text:
                            result[page_num] = page_text
                    except Exception as e:
                        print(f"提取第 {page_num} 页失败: {e}")
                        continue
                
                return result
                
        except Exception as e:
            print(f"按页提取文本失败: {e}")
            return {}
    
    def search_text_in_pdf(self, pdf_path: str, keywords: List[str], 
                          case_sensitive: bool = False) -> Dict[str, List[Tuple[int, str]]]:
        """
        在PDF中搜索关键词
        
        Args:
            pdf_path (str): PDF文件路径
            keywords (List[str]): 搜索关键词列表
            case_sensitive (bool): 是否区分大小写
            
        Returns:
            Dict[str, List[Tuple[int, str]]]: 关键词到(页码, 包含该关键词的文本行)列表的映射
        """
        search_results = {keyword: [] for keyword in keywords}
        
        try:
            pages_text = self.extract_text_by_pages(pdf_path)
            
            for page_num, page_text in pages_text.items():
                lines = page_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    for keyword in keywords:
                        search_term = keyword if case_sensitive else keyword.lower()
                        search_line = line if case_sensitive else line.lower()
                        
                        if search_term in search_line:
                            search_results[keyword].append((page_num, line))
            
            return search_results
            
        except Exception as e:
            print(f"搜索关键词失败: {e}")
            return search_results
    
    def extract_sections_by_headers(self, pdf_path: str, 
                                  headers: List[str]) -> Dict[str, str]:
        """
        根据标题提取PDF章节内容
        
        Args:
            pdf_path (str): PDF文件路径
            headers (List[str]): 章节标题列表
            
        Returns:
            Dict[str, str]: 标题到章节内容的映射
        """
        sections = {}
        
        try:
            full_text = self.extract_text(pdf_path)
            
            if not full_text:
                return sections
            
            # 为每个标题查找内容
            for i, header in enumerate(headers):
                try:
                    # 查找当前标题的位置
                    pattern = re.compile(rf'{re.escape(header)}', re.IGNORECASE)
                    match = pattern.search(full_text)
                    
                    if not match:
                        continue
                    
                    start_pos = match.end()
                    
                    # 查找下一个标题的位置作为结束位置
                    end_pos = len(full_text)
                    if i + 1 < len(headers):
                        next_header = headers[i + 1]
                        next_pattern = re.compile(rf'{re.escape(next_header)}', re.IGNORECASE)
                        next_match = next_pattern.search(full_text, start_pos)
                        if next_match:
                            end_pos = next_match.start()
                    
                    # 提取章节内容
                    section_content = full_text[start_pos:end_pos].strip()
                    sections[header] = section_content
                    
                except Exception as e:
                    print(f"提取章节 '{header}' 失败: {e}")
                    continue
            
            return sections
            
        except Exception as e:
            print(f"按标题提取章节失败: {e}")
            return {}
    
    def clean_text(self, text: str) -> str:
        """
        清理提取的文本
        
        Args:
            text (str): 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除页眉页脚模式（根据实际情况调整）
        text = re.sub(r'=== 第 \d+ 页 ===', '', text)
        
        # 移除多余的换行
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def save_text_to_file(self, text: str, output_path: str) -> bool:
        """
        保存文本到文件
        
        Args:
            text (str): 文本内容
            output_path (str): 输出文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"文本已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"保存文本文件失败: {e}")
            return False