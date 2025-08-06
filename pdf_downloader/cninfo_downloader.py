"""
巨潮资讯网PDF下载器
真实可用的巨潮资讯网公告和财报PDF下载功能
"""

import os
import json
import requests
import time
from typing import List, Dict, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta


class CninfoDownloader:
    """巨潮资讯网PDF下载器"""
    
    def __init__(self, download_dir: str = "downloads/cninfo"):
        """
        初始化下载器
        
        Args:
            download_dir (str): PDF文件下载目录
        """
        self.download_dir = download_dir
        self.base_url = "http://www.cninfo.com.cn"
        self.static_url = "https://static.cninfo.com.cn"
        
        # 创建下载目录
        os.makedirs(download_dir, exist_ok=True)
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://www.cninfo.com.cn",
            "Referer": "http://www.cninfo.com.cn/new/disclosure/stock",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })
        
        # 股票代码和机构ID映射
        self.stock_mapping = {}
        self._load_stock_mapping()
        
        # 公告类型映射
        self.announcement_categories = {
            'annual_report': 'category_ndbg_szsh',      # 年报
            'interim_report': 'category_bndbg_szsh',    # 中报  
            'quarterly_report': 'category_sjdbg_szsh',  # 季报
            'all_reports': 'category_ndbg_szsh;category_bndbg_szsh;category_sjdbg_szsh',  # 所有财报
            'major_events': 'category_zdsxgk_szsh',     # 重大事项
            'all': ''  # 所有公告
        }
    
    def _load_stock_mapping(self):
        """加载股票代码和机构ID的映射关系"""
        try:
            # 加载深交所股票
            szse_url = f"{self.base_url}/new/data/szse_stock.json"
            szse_response = self.session.get(szse_url)
            if szse_response.status_code == 200:
                szse_data = szse_response.json()
                
                # 处理不同的数据格式
                if isinstance(szse_data, dict):
                    # 如果是字典格式，查找包含股票数据的字段
                    stock_list = szse_data
                    for key, value in szse_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            stock_list = value
                            break
                elif isinstance(szse_data, list):
                    stock_list = szse_data
                else:
                    stock_list = []
                
                if isinstance(stock_list, list):
                    for item in stock_list:
                        if isinstance(item, dict):
                            stock_code = item.get('code')
                            org_id = item.get('orgId')
                            if stock_code and org_id:
                                self.stock_mapping[stock_code] = {
                                    'orgId': org_id,
                                    'exchange': 'szse',
                                    'name': item.get('zwjc', '')
                                }
                
                # 如果没有从API获取到数据，添加一些常用股票的硬编码映射
                if not self.stock_mapping:
                    self._add_hardcoded_stocks()
            
            # 加载上交所股票
            sse_url = f"{self.base_url}/new/data/sse_stock.json"
            sse_response = self.session.get(sse_url)
            if sse_response.status_code == 200:
                sse_data = sse_response.json()
                if isinstance(sse_data, list):
                    for item in sse_data:
                        if isinstance(item, dict):
                            stock_code = item.get('code')
                            org_id = item.get('orgId')
                            if stock_code and org_id:
                                self.stock_mapping[stock_code] = {
                                    'orgId': org_id,
                                    'exchange': 'sse',
                                    'name': item.get('zwjc', '')
                                }
            
            print(f"已加载 {len(self.stock_mapping)} 只股票的映射关系")
            
        except Exception as e:
            print(f"加载股票映射失败: {e}")
            # 如果API失败，使用硬编码数据
            self._add_hardcoded_stocks()
    
    def _add_hardcoded_stocks(self):
        """添加常用股票的硬编码映射"""
        hardcoded_stocks = {
            # 深交所主要股票
            '000001': {'orgId': '9900001915', 'exchange': 'szse', 'name': '平安银行'},
            '000002': {'orgId': '9900000088', 'exchange': 'szse', 'name': '万科A'},
            '000858': {'orgId': '9900002306', 'exchange': 'szse', 'name': '五粮液'},
            '002415': {'orgId': '9900006464', 'exchange': 'szse', 'name': '海康威视'},
            '300059': {'orgId': '9900013208', 'exchange': 'szse', 'name': '东方财富'},
            
            # 上交所主要股票  
            '600000': {'orgId': '9900000018', 'exchange': 'sse', 'name': '浦发银行'},
            '600036': {'orgId': '9900000054', 'exchange': 'sse', 'name': '招商银行'},
            '600519': {'orgId': '9900000657', 'exchange': 'sse', 'name': '贵州茅台'},
            '600887': {'orgId': '9900000825', 'exchange': 'sse', 'name': '伊利股份'},
            '601318': {'orgId': '9900001431', 'exchange': 'sse', 'name': '中国平安'},
        }
        
        self.stock_mapping.update(hardcoded_stocks)
        print(f"已添加 {len(hardcoded_stocks)} 只硬编码股票映射")
    
    def get_org_id(self, stock_code: str) -> Optional[str]:
        """
        获取股票代码对应的机构ID
        
        Args:
            stock_code (str): 股票代码，如 000001
            
        Returns:
            Optional[str]: 机构ID
        """
        stock_info = self.stock_mapping.get(stock_code)
        return stock_info['orgId'] if stock_info else None
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        Args:
            stock_code (str): 股票代码
            
        Returns:
            Optional[Dict]: 股票信息
        """
        return self.stock_mapping.get(stock_code)
    
    def query_announcements(self, stock_code: str, start_date: str = None, 
                          end_date: str = None, category: str = 'all',
                          page_num: int = 1, page_size: int = 30) -> Tuple[List[Dict], int]:
        """
        查询股票公告
        
        Args:
            stock_code (str): 股票代码
            start_date (str): 开始日期 YYYY-MM-DD
            end_date (str): 结束日期 YYYY-MM-DD
            category (str): 公告类型
            page_num (int): 页码
            page_size (int): 每页数量
            
        Returns:
            Tuple[List[Dict], int]: (公告列表, 总页数)
        """
        try:
            # 获取机构ID
            org_id = self.get_org_id(stock_code)
            if not org_id:
                print(f"未找到股票代码 {stock_code} 的机构ID")
                return [], 0
            
            # 构建查询URL
            query_url = f"{self.base_url}/new/hisAnnouncement/query"
            
            # 构建日期范围
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            date_range = f"{start_date}~{end_date}"
            
            # 获取公告类型
            category_value = self.announcement_categories.get(category, '')
            
            # 构建请求数据
            data = {
                "pageNum": str(page_num),
                "pageSize": str(page_size),
                "column": "szse" if self.stock_mapping[stock_code]['exchange'] == 'szse' else "sse",
                "tabName": "fulltext",
                "stock": f"{stock_code},{org_id}",
                "category": category_value,
                "seDate": date_range,
                "searchkey": "",
                "plate": "",
                "trade": "",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true"
            }
            
            print(f"查询 {stock_code} 的公告，日期范围: {date_range}")
            
            # 发送请求
            response = self.session.post(query_url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            # 解析公告数据
            announcements = []
            if 'announcements' in result and result['announcements'] is not None:
                for item in result['announcements']:
                    if item:  # 确保item不为None
                        announcement = {
                            'title': item.get('announcementTitle', ''),
                            'secName': item.get('secName', ''),
                            'secCode': item.get('secCode', ''),
                            'announcementTime': item.get('announcementTime', ''),
                            'adjunctUrl': item.get('adjunctUrl', ''),
                            'adjunctSize': item.get('adjunctSize', ''),
                            'adjunctType': item.get('adjunctType', ''),
                            'storageTime': item.get('storageTime', ''),
                            'columnId': item.get('columnId', ''),
                            'pdf_url': f"{self.static_url}/{item.get('adjunctUrl', '')}" if item.get('adjunctUrl') else '',
                            'file_size': item.get('adjunctSize', 0)
                        }
                        announcements.append(announcement)
            
            total_pages = result.get('totalpages', 0)
            
            print(f"找到 {len(announcements)} 条公告，共 {total_pages} 页")
            return announcements, total_pages
            
        except Exception as e:
            print(f"查询公告失败: {e}")
            return [], 0
    
    def download_pdf(self, pdf_url: str, filename: str, stock_code: str = None) -> str:
        """
        下载PDF文件
        
        Args:
            pdf_url (str): PDF下载URL
            filename (str): 保存的文件名
            stock_code (str): 股票代码（用于创建子目录）
            
        Returns:
            str: 下载的文件路径，失败返回空字符串
        """
        try:
            # 创建股票专用目录
            if stock_code:
                stock_dir = os.path.join(self.download_dir, stock_code)
                os.makedirs(stock_dir, exist_ok=True)
                save_dir = stock_dir
            else:
                save_dir = self.download_dir
            
            # 处理文件名，移除非法字符
            safe_filename = "".join(c for c in filename if c not in '\\/:*?"<>|').strip()
            if not safe_filename.endswith('.pdf'):
                safe_filename += '.pdf'
            
            file_path = os.path.join(save_dir, safe_filename)
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                print(f"文件已存在: {safe_filename}")
                return file_path
            
            print(f"正在下载: {safe_filename}")
            
            # 下载文件
            response = self.session.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and len(response.content) < 1000:
                print(f"下载的文件可能不是PDF: {safe_filename}")
                return ""
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"下载完成: {safe_filename} ({len(response.content)} bytes)")
            return file_path
            
        except Exception as e:
            print(f"下载PDF失败 {filename}: {e}")
            return ""
    
    def download_financial_reports(self, stock_code: str, year: int = None, 
                                 report_types: List[str] = None) -> List[str]:
        """
        下载指定股票的财务报告
        
        Args:
            stock_code (str): 股票代码
            year (int): 年份，默认当前年份
            report_types (List[str]): 报告类型列表
            
        Returns:
            List[str]: 下载成功的文件路径列表
        """
        if not year:
            year = datetime.now().year
        
        if not report_types:
            report_types = ['annual_report', 'interim_report', 'quarterly_report']
        
        downloaded_files = []
        
        for report_type in report_types:
            try:
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                
                announcements, _ = self.query_announcements(
                    stock_code, start_date, end_date, report_type
                )
                
                for announcement in announcements:
                    if announcement['pdf_url']:
                        file_path = self.download_pdf(
                            announcement['pdf_url'],
                            announcement['title'],
                            stock_code
                        )
                        if file_path:
                            downloaded_files.append(file_path)
                
                # 添加延迟避免频繁请求
                time.sleep(1)
                
            except Exception as e:
                print(f"下载 {report_type} 失败: {e}")
                continue
        
        return downloaded_files
    
    def download_all_announcements(self, stock_code: str, start_date: str = None,
                                 end_date: str = None, max_pages: int = 10) -> List[str]:
        """
        下载股票所有公告
        
        Args:
            stock_code (str): 股票代码
            start_date (str): 开始日期
            end_date (str): 结束日期
            max_pages (int): 最大下载页数
            
        Returns:
            List[str]: 下载成功的文件路径列表
        """
        downloaded_files = []
        
        try:
            # 查询第一页获取总页数
            announcements, total_pages = self.query_announcements(
                stock_code, start_date, end_date, 'all', 1
            )
            
            # 限制下载页数
            pages_to_download = min(total_pages, max_pages)
            
            print(f"开始下载 {stock_code} 的公告，共 {pages_to_download} 页")
            
            for page in range(1, pages_to_download + 1):
                if page > 1:
                    announcements, _ = self.query_announcements(
                        stock_code, start_date, end_date, 'all', page
                    )
                
                for announcement in announcements:
                    if announcement['pdf_url']:
                        file_path = self.download_pdf(
                            announcement['pdf_url'],
                            announcement['title'],
                            stock_code
                        )
                        if file_path:
                            downloaded_files.append(file_path)
                
                # 添加延迟避免频繁请求
                time.sleep(2)
                print(f"已完成第 {page}/{pages_to_download} 页")
            
            print(f"下载完成，共成功下载 {len(downloaded_files)} 个文件")
            return downloaded_files
            
        except Exception as e:
            print(f"批量下载公告失败: {e}")
            return downloaded_files
    
    def search_announcements_by_keyword(self, stock_code: str, keywords: List[str],
                                      start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        根据关键词搜索公告
        
        Args:
            stock_code (str): 股票代码
            keywords (List[str]): 搜索关键词
            start_date (str): 开始日期
            end_date (str): 结束日期
            
        Returns:
            pd.DataFrame: 符合条件的公告列表
        """
        try:
            announcements, _ = self.query_announcements(stock_code, start_date, end_date)
            
            filtered_announcements = []
            for announcement in announcements:
                title = announcement['title'].lower()
                if any(keyword.lower() in title for keyword in keywords):
                    filtered_announcements.append(announcement)
            
            df = pd.DataFrame(filtered_announcements)
            print(f"关键词 {keywords} 搜索到 {len(filtered_announcements)} 个公告")
            
            return df
            
        except Exception as e:
            print(f"搜索公告失败: {e}")
            return pd.DataFrame()
    
    def get_available_stocks(self) -> pd.DataFrame:
        """
        获取所有可用的股票列表
        
        Returns:
            pd.DataFrame: 股票列表
        """
        stock_list = []
        for code, info in self.stock_mapping.items():
            stock_list.append({
                'stock_code': code,
                'stock_name': info['name'],
                'exchange': info['exchange'],
                'org_id': info['orgId']
            })
        
        return pd.DataFrame(stock_list)