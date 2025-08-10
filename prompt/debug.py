now, the output is something wrong when we run python3 main.py and select 2                                        │
│   mode,--------------------------------------------------------------------------------                              │
│                                                                                                                      │
│   📈 股票 4: 688108 赛诺医疗                                                                                         │
│      💰 市场表现: 涨幅 20.0235% | 成交额 138,240千元                                                                 │
│      🏭 主营业务: 许可项目：第三类医疗器械生产；第三类医疗器械经营；第二类医疗器械生产。（依                         │
│      🏷️  所属行业: 未知                                                                                              │
│      📊 财务指标:                                                                                                    │
│         营业收入: 91,062,637                                                                                         │
│         净利润: -1,672,840                                                                                           │
│      📢 最近公告:                                                                                                    │
│         📋 赛诺医疗科学技术股份有限公司关于子公司产品获得FDA突破性医疗器械认证的自愿性披露公告                       │
│         📋 赛诺医疗科学技术股份有限公司2025年半年度业绩预告的自愿性披露公告                                          │
│         📋 赛诺医疗关于公司新型药物洗脱支架系统获得美国FDA附条件批准的自愿性披露公告                                 │
│      🔍 可能原因: 业绩超预期; 可能为题材炒作或跟风上涨, the output 主营业务is not enough ,because we had downloaded  │
│   the financial report, there is a lot of content in it,so now you need debug it and find out why the content in     │
│   pdf financial report are not output ,and fix this problem

---------------------------------------------------------------------------
尝试直接分析PDF文件...
Gemini直接分析PDF失败: HTTPSConnectionPool(host='generativelanguage.googleapis.com', port=443): Max retries exceeded with url: /v1beta/models/gemini-1.5-pro:generateContent?key=AIzaSyDUBwyRs4t6OTXISoAaDArjzAjv2Z_EOEI (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x7a08ac63a110>: Failed to establish a new connection: [Errno 101] Network is unreachable'))

we get this error, and use the same gemini key in other project,
like import { GoogleGenerativeAI } from "@google/generative-ai"; const genAI = new GoogleGenerativeAI("gemini-api-key");
const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" }); const result = await model.generateContent(prompt);
it is work, so maybe it is not the key problem, please debug it and try other way to fix this problem