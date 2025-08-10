"""
PDF文本转换器
将PDF文件转换为文本，专注于提取财务报告的关键章节
"""

import os
import re
from typing import Dict, Optional, List
import pdfplumber
import PyPDF2


class PDFTextConverter:
    """PDF文本转换器"""
    
    def __init__(self):
        """初始化转换器"""
        self.target_sections = [
            '第二节', '公司简介', '主要财务指标',
            '第三节', '管理层讨论与分析'
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        从PDF文件提取文本
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            str: 提取的文本内容
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        text_content = ""
        
        # 首先尝试使用pdfplumber
        try:
            text_content = self._extract_with_pdfplumber(pdf_path)
            if text_content.strip():
                print(f"使用pdfplumber成功提取PDF文本: {os.path.basename(pdf_path)}")
                return text_content
        except Exception as e:
            print(f"pdfplumber提取失败: {e}")
        
        # 备用方案：使用PyPDF2
        try:
            text_content = self._extract_with_pypdf2(pdf_path)
            if text_content.strip():
                print(f"使用PyPDF2成功提取PDF文本: {os.path.basename(pdf_path)}")
                return text_content
        except Exception as e:
            print(f"PyPDF2提取失败: {e}")
        
        raise Exception(f"所有PDF文本提取方法都失败了: {pdf_path}")
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """使用pdfplumber提取PDF文本"""
        text_content = []
        
        with pdfplumber.open(pdf_path) as pdf:
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
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """使用PyPDF2提取PDF文本"""
        text_content = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
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
    
    def extract_target_sections(self, pdf_path: str) -> Dict[str, str]:
        """
        提取目标章节内容（第二节和第三节）
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            Dict[str, str]: 章节内容字典
        """
        full_text = self.extract_text_from_pdf(pdf_path)
        
        sections = {
            '第二节_公司简介和主要财务指标': '',
            '第三节_管理层讨论与分析': ''
        }
        
        try:
            # 查找第二节
            section2_match = re.search(
                r'第二节[\s\S]*?(?=第三节|第四节|$)', 
                full_text, 
                re.IGNORECASE
            )
            if section2_match:
                sections['第二节_公司简介和主要财务指标'] = section2_match.group(0)
            
            # 查找第三节
            section3_match = re.search(
                r'第三节[\s\S]*?(?=第四节|第五节|$)', 
                full_text, 
                re.IGNORECASE
            )
            if section3_match:
                sections['第三节_管理层讨论与分析'] = section3_match.group(0)
            
            # 如果没有找到标准格式的章节，尝试其他模式
            if not sections['第二节_公司简介和主要财务指标']:
                company_info_match = re.search(
                    r'(公司.*?简介[\s\S]*?(?=管理层讨论|第三节|主要业务|$))', 
                    full_text, 
                    re.IGNORECASE
                )
                if company_info_match:
                    sections['第二节_公司简介和主要财务指标'] = company_info_match.group(0)
            
            if not sections['第三节_管理层讨论与分析']:
                analysis_match = re.search(
                    r'(管理层讨论[\s\S]*?(?=第四节|董事会|$))', 
                    full_text, 
                    re.IGNORECASE
                )
                if analysis_match:
                    sections['第三节_管理层讨论与分析'] = analysis_match.group(0)
        
        except Exception as e:
            print(f"章节提取失败: {e}")
        
        return sections
    
    def clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        Args:
            text (str): 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除页眉页脚
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
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"文本已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"保存文本文件失败: {e}")
            return False