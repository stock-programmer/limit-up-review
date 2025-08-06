"""
PDF表格提取器
用于从PDF文件中提取表格数据
支持财务报表等结构化数据提取
"""

import os
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
import pdfplumber
import re

# 可选依赖
try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False


class PDFTableExtractor:
    """PDF表格提取器"""
    
    def __init__(self):
        """初始化表格提取器"""
        self.supported_methods = ['pdfplumber', 'tabula', 'camelot']
        self.default_method = 'pdfplumber'
    
    def extract_tables_with_pdfplumber(self, pdf_path: str) -> List[pd.DataFrame]:
        """
        使用pdfplumber提取PDF表格
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            List[pd.DataFrame]: 提取的表格数据列表
        """
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_tables = page.extract_tables()
                        
                        for table_idx, table in enumerate(page_tables):
                            if table and len(table) > 1:  # 确保表格有数据
                                # 转换为DataFrame
                                df = pd.DataFrame(table[1:], columns=table[0])
                                
                                # 添加元数据
                                df.attrs['page'] = page_num
                                df.attrs['table_index'] = table_idx
                                df.attrs['source'] = 'pdfplumber'
                                
                                tables.append(df)
                                
                    except Exception as e:
                        print(f"提取第 {page_num} 页表格失败: {e}")
                        continue
            
            print(f"pdfplumber共提取到 {len(tables)} 个表格")
            return tables
            
        except Exception as e:
            print(f"pdfplumber提取表格失败: {e}")
            return []
    
    def extract_tables_with_tabula(self, pdf_path: str, pages: str = 'all') -> List[pd.DataFrame]:
        """
        使用tabula-py提取PDF表格
        
        Args:
            pdf_path (str): PDF文件路径
            pages (str): 页码范围，如 'all', '1', '1-3'
            
        Returns:
            List[pd.DataFrame]: 提取的表格数据列表
        """
        if not TABULA_AVAILABLE:
            print("tabula-py未安装，跳过tabula提取")
            return []
            
        try:
            # 使用tabula读取表格
            tables = tabula.read_pdf(
                pdf_path,
                pages=pages,
                multiple_tables=True,
                pandas_options={'header': 0}
            )
            
            # 添加元数据
            for i, table in enumerate(tables):
                table.attrs['table_index'] = i
                table.attrs['source'] = 'tabula'
            
            print(f"tabula共提取到 {len(tables)} 个表格")
            return tables
            
        except Exception as e:
            print(f"tabula提取表格失败: {e}")
            return []
    
    def extract_tables_with_camelot(self, pdf_path: str, pages: str = 'all') -> List[pd.DataFrame]:
        """
        使用camelot提取PDF表格
        
        Args:
            pdf_path (str): PDF文件路径
            pages (str): 页码范围
            
        Returns:
            List[pd.DataFrame]: 提取的表格数据列表
        """
        if not CAMELOT_AVAILABLE:
            print("camelot-py未安装，跳过camelot提取")
            return []
            
        try:
            # 使用camelot读取表格
            tables = camelot.read_pdf(pdf_path, pages=pages)
            
            dataframes = []
            for i, table in enumerate(tables):
                df = table.df
                
                # 添加元数据
                df.attrs['table_index'] = i
                df.attrs['source'] = 'camelot'
                df.attrs['accuracy'] = table.accuracy
                
                dataframes.append(df)
            
            print(f"camelot共提取到 {len(dataframes)} 个表格")
            return dataframes
            
        except Exception as e:
            print(f"camelot提取表格失败: {e}")
            return []
    
    def extract_tables(self, pdf_path: str, method: str = None, 
                      pages: str = 'all') -> List[pd.DataFrame]:
        """
        提取PDF表格数据
        
        Args:
            pdf_path (str): PDF文件路径
            method (str): 提取方法
            pages (str): 页码范围
            
        Returns:
            List[pd.DataFrame]: 提取的表格数据列表
        """
        if not os.path.exists(pdf_path):
            print(f"文件不存在: {pdf_path}")
            return []
        
        if not method:
            method = self.default_method
        
        print(f"使用 {method} 提取PDF表格: {os.path.basename(pdf_path)}")
        
        if method == 'pdfplumber':
            return self.extract_tables_with_pdfplumber(pdf_path)
        elif method == 'tabula':
            return self.extract_tables_with_tabula(pdf_path, pages)
        elif method == 'camelot':
            return self.extract_tables_with_camelot(pdf_path, pages)
        else:
            print(f"不支持的提取方法: {method}")
            return []
    
    def extract_financial_tables(self, pdf_path: str) -> Dict[str, pd.DataFrame]:
        """
        提取财务报表表格
        
        Args:
            pdf_path (str): 财务报告PDF路径
            
        Returns:
            Dict[str, pd.DataFrame]: 财务报表类型到数据的映射
        """
        financial_tables = {}
        
        # 尝试多种方法提取表格
        all_tables = []
        available_methods = ['pdfplumber']
        if TABULA_AVAILABLE:
            available_methods.append('tabula')
            
        for method in available_methods:
            try:
                tables = self.extract_tables(pdf_path, method)
                all_tables.extend(tables)
            except Exception as e:
                print(f"方法 {method} 失败: {e}")
                continue
        
        if not all_tables:
            return financial_tables
        
        # 财务报表关键词匹配
        financial_keywords = {
            'balance_sheet': ['资产负债表', '合并资产负债表', '资产', '负债', '所有者权益'],
            'income_statement': ['利润表', '合并利润表', '营业收入', '营业成本', '净利润'],
            'cash_flow': ['现金流量表', '合并现金流量表', '经营活动', '投资活动', '筹资活动'],
            'equity_statement': ['所有者权益变动表', '股东权益变动表']
        }
        
        # 分析每个表格，尝试识别财务报表类型
        for table in all_tables:
            try:
                # 获取表格的文本内容用于匹配
                table_text = ' '.join([str(cell) for row in table.values for cell in row if pd.notna(cell)])
                
                for statement_type, keywords in financial_keywords.items():
                    if any(keyword in table_text for keyword in keywords):
                        if statement_type not in financial_tables:
                            financial_tables[statement_type] = table
                            print(f"识别到 {statement_type}: {table.shape}")
                        break
                        
            except Exception as e:
                print(f"分析表格失败: {e}")
                continue
        
        return financial_tables
    
    def clean_financial_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理财务表格数据
        
        Args:
            df (pd.DataFrame): 原始表格数据
            
        Returns:
            pd.DataFrame: 清理后的表格数据
        """
        try:
            # 创建副本避免修改原数据
            cleaned_df = df.copy()
            
            # 移除完全空白的行和列
            cleaned_df = cleaned_df.dropna(how='all')
            cleaned_df = cleaned_df.dropna(axis=1, how='all')
            
            # 处理数值列
            for col in cleaned_df.columns:
                if cleaned_df[col].dtype == 'object':
                    # 尝试转换为数值
                    cleaned_df[col] = pd.to_numeric(
                        cleaned_df[col].astype(str).str.replace(',', '').str.replace('，', ''),
                        errors='ignore'
                    )
            
            # 移除标题行（通常包含"单位"等字样）
            title_pattern = r'单位|币种|Currency|Unit'
            title_rows = cleaned_df.apply(
                lambda row: any(re.search(title_pattern, str(cell), re.IGNORECASE) 
                              for cell in row if pd.notna(cell)), axis=1
            )
            cleaned_df = cleaned_df[~title_rows]
            
            return cleaned_df
            
        except Exception as e:
            print(f"清理表格数据失败: {e}")
            return df
    
    def extract_specific_table_by_keywords(self, pdf_path: str, 
                                         keywords: List[str]) -> Optional[pd.DataFrame]:
        """
        根据关键词提取特定表格
        
        Args:
            pdf_path (str): PDF文件路径
            keywords (List[str]): 搜索关键词
            
        Returns:
            Optional[pd.DataFrame]: 匹配的表格数据
        """
        tables = self.extract_tables(pdf_path)
        
        for table in tables:
            try:
                # 检查表格内容是否包含关键词
                table_text = ' '.join([str(cell) for row in table.values for cell in row if pd.notna(cell)])
                
                if any(keyword in table_text for keyword in keywords):
                    return self.clean_financial_table(table)
                    
            except Exception as e:
                print(f"搜索表格关键词失败: {e}")
                continue
        
        return None
    
    def save_tables_to_excel(self, tables: Dict[str, pd.DataFrame], 
                           output_path: str) -> bool:
        """
        保存表格到Excel文件
        
        Args:
            tables (Dict[str, pd.DataFrame]): 表格数据字典
            output_path (str): 输出文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in tables.items():
                    # 限制工作表名称长度
                    safe_sheet_name = sheet_name[:30] if len(sheet_name) > 30 else sheet_name
                    df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
            print(f"表格已保存到Excel: {output_path}")
            return True
            
        except Exception as e:
            print(f"保存Excel文件失败: {e}")
            return False
    
    def save_tables_to_csv(self, tables: List[pd.DataFrame], 
                          output_dir: str, prefix: str = "table") -> List[str]:
        """
        保存表格到CSV文件
        
        Args:
            tables (List[pd.DataFrame]): 表格数据列表
            output_dir (str): 输出目录
            prefix (str): 文件名前缀
            
        Returns:
            List[str]: 保存的文件路径列表
        """
        saved_files = []
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            for i, table in enumerate(tables):
                filename = f"{prefix}_{i+1}.csv"
                file_path = os.path.join(output_dir, filename)
                
                table.to_csv(file_path, index=False, encoding='utf-8-sig')
                saved_files.append(file_path)
            
            print(f"已保存 {len(saved_files)} 个CSV文件到: {output_dir}")
            return saved_files
            
        except Exception as e:
            print(f"保存CSV文件失败: {e}")
            return saved_files
    
    def get_table_summary(self, table: pd.DataFrame) -> Dict[str, Any]:
        """
        获取表格摘要信息
        
        Args:
            table (pd.DataFrame): 表格数据
            
        Returns:
            Dict[str, Any]: 表格摘要信息
        """
        try:
            summary = {
                'shape': table.shape,
                'columns': list(table.columns),
                'numeric_columns': list(table.select_dtypes(include=['number']).columns),
                'non_null_counts': table.count().to_dict(),
                'data_types': table.dtypes.to_dict(),
                'memory_usage': table.memory_usage(deep=True).sum()
            }
            
            # 添加元数据（如果存在）
            if hasattr(table, 'attrs'):
                summary['metadata'] = table.attrs
            
            return summary
            
        except Exception as e:
            print(f"生成表格摘要失败: {e}")
            return {'error': str(e)}