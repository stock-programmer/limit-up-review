#!/usr/bin/env python3
"""
股票市场数据分析程序
使用tushare pro接口获取各种股票数据和分析
支持涨停股票综合分析功能
"""

import pandas as pd
from datetime import datetime
import sys
import os
from market_data import MarketAnalyzer
from comprehensive_analyzer import ComprehensiveStockAnalyzer

def print_separator(title: str):
    """打印分隔线和标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_dataframe(df: pd.DataFrame, title: str, max_rows: int = 30):
    """打印DataFrame，限制最大行数"""
    if df.empty:
        print(f"{title}: 无数据")
        return
    
    # 限制显示行数
    display_df = df.head(max_rows) if len(df) > max_rows else df
    
    print(f"{title} (共{len(df)}条，显示前{len(display_df)}条):")
    print("-" * 80)
    print(display_df.to_string(index=False))
    print()

def save_to_csv(df: pd.DataFrame, filename: str):
    """保存DataFrame到CSV文件"""
    if not df.empty:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已保存到: {filename}")

def analyze_market_data(trade_date: str):
    """
    综合分析市场数据
    
    Args:
        trade_date (str): 交易日期，格式为 YYYYMMDD
    """
    try:
        # 初始化市场分析器
        analyzer = MarketAnalyzer()
        
        print_separator("股票市场数据综合分析")
        print(f"分析日期: {trade_date}")
        
        # 1. 获取每日涨停股票
        print_separator("1. 每日涨停股票")
        limit_up_stocks = analyzer.get_daily_limit_up_stocks(trade_date)
        print_dataframe(limit_up_stocks, "涨停股票")
        save_to_csv(limit_up_stocks, f"limit_up_stocks_{trade_date}.csv")
        
        # 2. 获取每日成交金额大于4亿且涨幅大于5%的股票
        print_separator("2. 成交额>4亿且涨幅>5%股票")
        high_vol_gain = analyzer.get_high_volume_high_gain_stocks(trade_date)
        print_dataframe(high_vol_gain, "高成交额高涨幅股票")
        save_to_csv(high_vol_gain, f"high_volume_high_gain_{trade_date}.csv")
        
        # 3. 获取每日成交金额大于4亿且涨停的股票
        print_separator("3. 成交额>4亿且涨停股票")
        high_vol_limit = analyzer.get_high_volume_limit_up_stocks(trade_date)
        print_dataframe(high_vol_limit, "高成交额涨停股票")
        save_to_csv(high_vol_limit, f"high_volume_limit_up_{trade_date}.csv")
        
        # 4. 获取近5日A股涨幅排名（前30名）
        print_separator("4. 近5日A股涨幅排名")
        ranking_5d = analyzer.get_5day_return_ranking(trade_date)
        print_dataframe(ranking_5d, "近5日涨幅排名", max_rows=30)
        save_to_csv(ranking_5d.head(30), f"5day_ranking_{trade_date}.csv")
        
        # 5. 获取近10日A股涨幅排名（前30名）
        print_separator("5. 近10日A股涨幅排名")
        ranking_10d = analyzer.get_10day_return_ranking(trade_date)
        print_dataframe(ranking_10d, "近10日涨幅排名", max_rows=30)
        save_to_csv(ranking_10d.head(30), f"10day_ranking_{trade_date}.csv")
        
        # 6. 获取近20日A股涨幅排名（前30名）
        print_separator("6. 近20日A股涨幅排名")
        ranking_20d = analyzer.get_20day_return_ranking(trade_date)
        print_dataframe(ranking_20d, "近20日涨幅排名", max_rows=30)
        save_to_csv(ranking_20d.head(30), f"20day_ranking_{trade_date}.csv")
        
        # 7. 获取当年股票涨幅排行（前30名）
        print_separator("7. 当年股票涨幅排行")
        ytd_ranking = analyzer.get_ytd_return_ranking(trade_date)
        print_dataframe(ytd_ranking, "年度涨幅排行", max_rows=30)
        save_to_csv(ytd_ranking.head(30), f"ytd_ranking_{trade_date}.csv")
        
        # 8. 获取每日成交金额大于4亿且跌幅大于5%的股票
        print_separator("8. 成交额>4亿且跌幅>5%股票")
        high_vol_decline = analyzer.get_high_volume_high_decline_stocks(trade_date)
        print_dataframe(high_vol_decline, "高成交额高跌幅股票")
        save_to_csv(high_vol_decline, f"high_volume_high_decline_{trade_date}.csv")
        
        # 9. 获取每日新高且市值>300亿的股票（按市值排序，前30名）
        print_separator("9. 新高且市值>300亿股票")
        new_high_large_cap = analyzer.get_new_high_large_cap_stocks(trade_date)
        print_dataframe(new_high_large_cap, "新高大市值股票", max_rows=30)
        save_to_csv(new_high_large_cap.head(30), f"new_high_large_cap_{trade_date}.csv")
        
        # 统计汇总
        print_separator("分析结果汇总")
        print(f"涨停股票数量: {len(limit_up_stocks)}")
        print(f"高成交额高涨幅股票数量: {len(high_vol_gain)}")
        print(f"高成交额涨停股票数量: {len(high_vol_limit)}")
        print(f"高成交额高跌幅股票数量: {len(high_vol_decline)}")
        print(f"新高大市值股票数量: {len(new_high_large_cap)}")
        
        print_separator("分析完成")
        print("所有数据已保存为CSV文件，可用于进一步分析")
        
    except Exception as e:
        print(f"市场数据分析失败: {e}")

def main():
    """主函数"""
    print("=== 股票市场数据综合分析程序 ===")
    print("基于tushare pro接口的全方位股票数据分析工具")
    print("1. 市场数据综合分析")
    print("2. 涨停股票深度分析")
    print()
    
    # 获取用户选择
    choice = input("请选择分析模式 (1-市场分析 / 2-涨停分析): ").strip()
    
    # 获取用户输入的日期
    if len(sys.argv) > 1:
        input_date = sys.argv[1]
    else:
        input_date = input("请输入分析日期 (格式: YYYYMMDD，如 20240801): ").strip()
    
    # 验证日期格式
    try:
        datetime.strptime(input_date, '%Y%m%d')
    except ValueError:
        print("日期格式错误，请使用 YYYYMMDD 格式，例如: 20240801")
        return
    
    # 根据选择执行不同的分析
    if choice == "2":
        # 涨停股票深度分析
        analyze_limit_up_comprehensive(input_date)
    else:
        # 默认市场数据分析
        analyze_market_data(input_date)

def analyze_limit_up_comprehensive(trade_date: str):
    """
    涨停股票综合深度分析
    
    Args:
        trade_date (str): 交易日期
    """
    try:
        print_separator("涨停股票综合深度分析")
        print(f"分析日期: {trade_date}")
        print("正在整合行情数据、财报信息、公告数据...")
        print("注意: 此分析需要下载PDF文件，可能需要较长时间")
        print()
        
        # 获取分析股票数量
        max_stocks = input("请输入最大分析股票数量 (默认5只，建议不超过10只): ").strip()
        try:
            max_stocks = int(max_stocks) if max_stocks else 5
            max_stocks = min(max_stocks, 20)  # 限制最大数量
        except ValueError:
            max_stocks = 5
        
        # 初始化综合分析器
        comprehensive_analyzer = ComprehensiveStockAnalyzer()
        
        # 执行综合分析
        analysis_result = comprehensive_analyzer.analyze_limit_up_stocks(trade_date, max_stocks)
        
        # 显示分析结果
        comprehensive_analyzer.print_analysis_summary(analysis_result)
        
        # 显示详细信息
        if analysis_result['limit_up_stocks']:
            print_separator("详细分析结果")
            
            for i, stock in enumerate(analysis_result['limit_up_stocks'], 1):
                print(f"\n📈 股票 {i}: {stock['stock_code']} {stock['stock_name']}")
                print(f"   💰 市场表现: 涨幅 {stock['market_data'].get('change_pct', 0)}% | "
                      f"成交额 {stock['market_data'].get('amount', 0):,.0f}千元")
                
                # 主营业务
                business = stock['business_info'].get('main_business', '暂未获取到主营业务信息')
                print(f"   🏭 主营业务: {business[:200]}{'...' if len(business) > 200 else ''}")
                
                # 行业信息
                industry = stock['business_info'].get('industry', '未知')
                print(f"   🏷️  所属行业: {industry}")
                
                # 财务数据
                financial_data = stock['financial_data']
                if financial_data.get('key_indicators'):
                    indicators = financial_data['key_indicators']
                    print(f"   📊 财务指标:")
                    if 'revenue' in indicators:
                        print(f"      营业收入: {indicators['revenue']:,.0f}")
                    if 'net_profit' in indicators:
                        print(f"      净利润: {indicators['net_profit']:,.0f}")
                
                # 最近公告
                announcements = stock['recent_announcements']
                if announcements:
                    print(f"   📢 最近公告:")
                    for ann in announcements[:3]:
                        status = "📈" if ann['is_positive'] else "📋"
                        print(f"      {status} {ann['title'][:50]}{'...' if len(ann['title']) > 50 else ''}")
                
                # 涨停分析
                insights = stock['analysis_insights']
                if insights.get('possible_reasons'):
                    print(f"   🔍 可能原因: {'; '.join(insights['possible_reasons'])}")
                
                print("-" * 80)
        
        # 保存结果提示
        print(f"\n💾 详细分析结果已保存到 analysis_output/ 目录")
        print(f"   - JSON报告: limit_up_analysis_{trade_date}.json")
        print(f"   - Excel报告: limit_up_report_{trade_date}.xlsx")
        
    except Exception as e:
        print(f"涨停股票综合分析失败: {e}")
        print("建议检查网络连接和tushare token配置")

if __name__ == "__main__":
    main()