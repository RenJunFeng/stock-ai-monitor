import { AxiosError } from 'axios';
import { startTransition, useEffect, useState } from 'react';

import { ReportModal } from './components/ReportModal';
import { Sidebar } from './components/Sidebar';
import { api } from './lib/api';
import { AlertsPage } from './pages/AlertsPage';
import { DashboardPage } from './pages/DashboardPage';
import { WatchlistPage } from './pages/WatchlistPage';
import type { AlertItem, AnalysisItem, DashboardData, PageKey, WatchlistItem } from './types';

interface AnalysisRunOptions {
  stockCodes?: string[];
  groupName?: string;
}

function App() {
  const [currentPage, setCurrentPage] = useState<PageKey>('watchlist');
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [activeReport, setActiveReport] = useState<AnalysisItem | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [analyzeStageIndex, setAnalyzeStageIndex] = useState(0);
  const [analysisScope, setAnalysisScope] = useState('全池');

  const analyzeStages = [
    '正在读取自选池并准备行情快照',
    '正在请求 DeepSeek 生成结构化投研报告',
    '正在提取关键指标并回写数据库',
    '正在刷新监控大屏与告警记录',
  ];

  const loadWatchlist = async () => {
    const response = await api.get<WatchlistItem[]>('/watchlist');
    setWatchlist(response.data);
  };

  const loadDashboard = async () => {
    const response = await api.get<DashboardData>('/dashboard');
    setDashboard(response.data);
  };

  const loadAlerts = async (stockCode = '') => {
    const response = await api.get<AlertItem[]>('/alerts', {
      params: stockCode ? { stock_code: stockCode } : undefined,
    });
    setAlerts(response.data);
  };

  const runAnalysis = async (options: AnalysisRunOptions = {}) => {
    const nextScope = options.stockCodes?.length
      ? `单股 ${options.stockCodes.join(', ')}`
      : options.groupName
        ? `分组 ${options.groupName}`
        : '全池';

    setAnalysisScope(nextScope);
    setIsAnalyzing(true);
    setAnalyzeError(null);
    setAnalyzeStageIndex(0);
    startTransition(() => setCurrentPage('dashboard'));

    try {
      await api.post(
        '/analysis/run',
        {
          manual_trigger: true,
          stock_codes: options.stockCodes,
          group_name: options.groupName,
        },
        { timeout: 300000 },
      );
      setAnalyzeStageIndex(analyzeStages.length - 1);
      await Promise.all([loadDashboard(), loadAlerts(), loadWatchlist()]);
    } catch (error) {
      if (error instanceof AxiosError && error.code === 'ECONNABORTED') {
        setAnalyzeError(`${nextScope}分析耗时超过前端等待上限。后端可能仍在继续处理，你可以稍等片刻后刷新监控大屏查看结果。`);
      } else {
        setAnalyzeError(`${nextScope}分析没有顺利完成。建议先用单股 AI 分析定位是否为个别股票、行情数据或模型返回异常。`);
      }
      await Promise.allSettled([loadDashboard(), loadAlerts(), loadWatchlist()]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    void Promise.all([loadWatchlist(), loadDashboard(), loadAlerts()]);
  }, []);

  useEffect(() => {
    if (!isAnalyzing) {
      return;
    }

    const timer = window.setInterval(() => {
      setAnalyzeStageIndex((current) => (current < analyzeStages.length - 1 ? current + 1 : current));
    }, 5000);

    return () => window.clearInterval(timer);
  }, [isAnalyzing, analyzeStages.length]);

  return (
    <div className="app-frame">
      <div className="ambient-orb ambient-orb-left" />
      <div className="ambient-orb ambient-orb-right" />
      <div className="app-shell">
        <Sidebar currentPage={currentPage} onChange={setCurrentPage} />
        <main className="content-shell">
          <section className="top-marquee">
            <span>DEEPSEEK V4 PRO</span>
            <span>AI STOCK MONITOR</span>
            <span>WATCHLIST {watchlist.length}</span>
            <span>ALERTS {alerts.length}</span>
            <span>分析范围 {analysisScope}</span>
            <span>{new Date().toLocaleDateString('zh-CN')}</span>
          </section>

          {currentPage === 'watchlist' ? (
            <WatchlistPage
              items={watchlist}
              onReload={loadWatchlist}
              onRunAnalysis={runAnalysis}
              isAnalyzing={isAnalyzing}
            />
          ) : null}

          {currentPage === 'dashboard' ? (
            <DashboardPage
              data={dashboard}
              onOpenReport={setActiveReport}
              isAnalyzing={isAnalyzing}
              analyzeStage={`${analysisScope} · ${analyzeStages[analyzeStageIndex]}`}
              analyzeError={analyzeError}
            />
          ) : null}

          {currentPage === 'alerts' ? <AlertsPage alerts={alerts} onFilter={loadAlerts} /> : null}
        </main>
        <ReportModal analysis={activeReport} onClose={() => setActiveReport(null)} />
      </div>
    </div>
  );
}

export default App;
