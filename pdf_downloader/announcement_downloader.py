"""
公告PDF下载器
支持从多个数据源获取上市公司公告PDF文件
"""

import os
import requests
import tushare as ts
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime
import time
from urllib.parse import urljoin, urlparse


class AnnouncementDownloader:
    """公告PDF下载器"""
    
    def __init__(self, download_dir: str = "downloads/announcements"):
        """
        初始化下载器
        
        Args:
            download_dir (str): PDF文件下载目录
        """
        self.download_dir = download_dir
        self.token = os.getenv('TUSHARE_TOKEN')
        if not self.token:
            print("警告：未找到TUSHARE_TOKEN环境变量")
        else:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        
        # 创建下载目录
        os.makedirs(download_dir, exist_ok=True)
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_announcements_list(self, ts_code: str, start_date: str = None, 
                             end_date: str = None, ann_type: str = None) -> pd.DataFrame:
        """
        获取公告列表数据
        
        Args:
            ts_code (str): 股票代码，如 000001.SZ
            start_date (str): 开始日期 YYYYMMDD
            end_date (str): 结束日期 YYYYMMDD  
            ann_type (str): 公告类型
            
        Returns:
            pd.DataFrame: 公告列表数据
        """
        try:
            if not self.token:
                print("无法获取公告列表：缺少tushare token")
                return pd.DataFrame()
            
            # 使用tushare获取公告数据（如果可用）
            # 注意：实际的接口可能不同，需要根据tushare实际API调整
            params = {'ts_code': ts_code}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            if ann_type:
                params['ann_type'] = ann_type
            
            # 模拟公告数据结构（实际使用时需要根据真实API调整）
            mock_data = {
                'ts_code': [ts_code] * 3,
                'ann_date': ['20240801', '20240715', '20240630'],
                'ann_type': ['年报', '中报', '一季报'],
                'title': ['2024年年度报告', '2024年中期报告', '2024年第一季度报告'],
                'ann_url': [
                    f'http://example.com/ann/{ts_code}_2024_annual.pdf',
                    f'http://example.com/ann/{ts_code}_2024_interim.pdf', 
                    f'http://example.com/ann/{ts_code}_2024_q1.pdf'
                ]
            }
            
            return pd.DataFrame(mock_data)
            
        except Exception as e:
            print(f"获取公告列表失败: {e}")
            return pd.DataFrame()
    
    def download_pdf_from_url(self, url: str, filename: str = None) -> str:
        """
        从URL下载PDF文件
        
        Args:
            url (str): PDF文件URL
            filename (str): 保存的文件名，不指定则自动生成
            
        Returns:
            str: 下载的文件路径，失败返回空字符串
        """
        try:
            if not filename:
                # 从URL解析文件名
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
            
            file_path = os.path.join(self.download_dir, filename)
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                print(f"文件已存在: {file_path}")
                return file_path
            
            print(f"正在下载: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                print(f"警告：文件可能不是PDF格式，Content-Type: {content_type}")
            
            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"下载完成: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"下载PDF失败 {url}: {e}")
            return ""
    
    def download_announcements(self, ts_code: str, start_date: str = None, 
                             end_date: str = None, ann_types: List[str] = None) -> List[str]:
        """
        批量下载公告PDF文件
        
        Args:
            ts_code (str): 股票代码
            start_date (str): 开始日期
            end_date (str): 结束日期
            ann_types (List[str]): 公告类型列表
            
        Returns:
            List[str]: 下载成功的文件路径列表
        """
        downloaded_files = []
        
        try:
            # 获取公告列表
            announcements = self.get_announcements_list(ts_code, start_date, end_date)
            
            if announcements.empty:
                print(f"未找到 {ts_code} 的公告数据")
                return downloaded_files
            
            # 筛选公告类型
            if ann_types:
                announcements = announcements[announcements['ann_type'].isin(ann_types)]
            
            print(f"找到 {len(announcements)} 个公告，开始下载...")
            
            for _, row in announcements.iterrows():
                try:
                    # 生成文件名
                    filename = f"{row['ts_code']}_{row['ann_date']}_{row['ann_type']}.pdf"
                    filename = filename.replace('/', '_').replace('\\', '_')  # 处理特殊字符
                    
                    # 下载PDF
                    if 'ann_url' in row and row['ann_url']:
                        file_path = self.download_pdf_from_url(row['ann_url'], filename)
                        if file_path:
                            downloaded_files.append(file_path)
                    
                    # 添加延迟避免频繁请求
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"下载公告失败 {row.get('title', 'Unknown')}: {e}")
                    continue
            
            print(f"批量下载完成，成功下载 {len(downloaded_files)} 个文件")
            return downloaded_files
            
        except Exception as e:
            print(f"批量下载公告失败: {e}")
            return downloaded_files
    
    def search_announcements_by_keyword(self, ts_code: str, keywords: List[str], 
                                      start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        根据关键词搜索公告
        
        Args:
            ts_code (str): 股票代码
            keywords (List[str]): 搜索关键词列表
            start_date (str): 开始日期
            end_date (str): 结束日期
            
        Returns:
            pd.DataFrame: 符合条件的公告列表
        """
        try:
            announcements = self.get_announcements_list(ts_code, start_date, end_date)
            
            if announcements.empty:
                return pd.DataFrame()
            
            # 关键词过滤
            keyword_filter = announcements['title'].str.contains('|'.join(keywords), case=False, na=False)
            filtered_announcements = announcements[keyword_filter]
            
            print(f"关键词 {keywords} 搜索到 {len(filtered_announcements)} 个公告")
            return filtered_announcements
            
        except Exception as e:
            print(f"搜索公告失败: {e}")
            return pd.DataFrame()
    
    def get_financial_report_announcements(self, ts_code: str, year: str) -> pd.DataFrame:
        """
        获取指定年度的财务报告公告
        
        Args:
            ts_code (str): 股票代码
            year (str): 年份，如 2024
            
        Returns:
            pd.DataFrame: 财务报告公告列表
        """
        financial_keywords = ['年报', '年度报告', '中报', '中期报告', '季报', '季度报告']
        start_date = f"{year}0101"
        end_date = f"{year}1231"
        
        return self.search_announcements_by_keyword(ts_code, financial_keywords, start_date, end_date)