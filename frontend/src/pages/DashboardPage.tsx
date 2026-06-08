import { useEffect, useRef } from 'react';

import { StatCard } from '../components/StatCard';
import type { AnalysisItem, DashboardData } from '../types';

interface DashboardPageProps {
  data: DashboardData | null;
  onOpenReport: (analysis: AnalysisItem) => void;
  isAnalyzing: boolean;
  analyzeStage: string;
  analyzeError: string | null;
}

function formatMetric(value: number | null, suffix = '') {
  if (value === null || Number.isNaN(value)) {
    return '--';
  }
  return `${value}${suffix}`;
}

export function DashboardPage({ data, onOpenReport, isAnalyzing, analyzeStage, analyzeError }: DashboardPageProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chartRef.current || !data) {
      return;
    }

    let disposed = false;
    let cleanup = () => {};

    void import('../lib/recommendationChart').then(({ mountRecommendationChart }) => {
      if (disposed || !chartRef.current) {
        return;
      }
      cleanup = mountRecommendationChart(chartRef.current, data.recommendation_breakdown);
    });

    return () => {
      disposed = true;
      cleanup();
    };
  }, [data]);

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h2>股票监控大屏</h2>
          <span>既能快速扫全局，也能从一张卡片钻进完整报告，不需要在多个页面之间反复切换。</span>
        </div>
      </header>

      <section className="market-banner">
        <div>
          <span>AI 监控状态</span>
          <strong>{isAnalyzing ? '分析引擎运行中' : `${data?.latest_analysis_count ?? 0} 份最新分析已就位`}</strong>
        </div>
        <p>
          {isAnalyzing
            ? analyzeStage
            : '本页展示的卡片字段和数据库落盘字段保持一一对应，避免“大屏好看但数据脱节”。'}
        </p>
      </section>

      {isAnalyzing ? (
        <section className="analysis-overlay-card">
          <div className="analysis-loader-ring" />
          <div>
            <span>DeepSeek 正在逐只生成结构化投研结论</span>
            <strong>{analyzeStage}</strong>
            <p>这一步通常需要 20 到 90 秒，股票越多、报告越长，等待时间越久。</p>
          </div>
        </section>
      ) : null}

      {analyzeError ? (
        <section className="analysis-error-card">
          <strong>本轮分析没有顺利完成</strong>
          <p>{analyzeError}</p>
        </section>
      ) : null}

      <div className="stats-grid">
        <StatCard label="跟踪股票数" value={String(data?.tracked_count ?? 0)} hint="自选池总量" />
        <StatCard label="最新分析数" value={String(data?.latest_analysis_count ?? 0)} hint="最新落盘分析" tone="dark" />
        <StatCard label="最近告警数" value={String(data?.latest_alerts.length ?? 0)} hint="最近 10 条记录" />
      </div>

      <div className="dashboard-grid">
        <div className="panel chart-panel">
          <div className="panel-header">
            <h3>AI 建议分布</h3>
            <span>Recommendation Mix</span>
          </div>
          <div ref={chartRef} className="chart-box" />
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3>最近告警</h3>
            <span>Latest Alerts</span>
          </div>
          <div className="alert-list">
            {data?.latest_alerts.length ? (
              data.latest_alerts.map((alert) => (
                <article key={alert.id} className="alert-item">
                  <strong>
                    {alert.stock_name} · {alert.trigger_type}
                  </strong>
                  <span>{alert.current_price} 元</span>
                  <small>{new Date(alert.created_at).toLocaleString()}</small>
                </article>
              ))
            ) : (
              <div className="empty-state-box">还没有告警记录，说明当前触发条件还比较平静。</div>
            )}
          </div>
        </div>
      </div>

      <div className="stock-grid">
        {data?.stocks.map((item) => (
          <article key={item.id} className="stock-card">
            <header>
              <div>
                <p>{item.stock_name}</p>
                <span>{item.stock_code}</span>
              </div>
              <button type="button" className="ghost-button" onClick={() => onOpenReport(item)}>
                查看报告
              </button>
            </header>
            <div className="stock-card-topline">
              <span>{item.valuation_conclusion ?? '--'}</span>
              <b>{item.ai_action ?? '--'}</b>
            </div>
            <div className="metric-grid">
              <div>
                <label>当前价</label>
                <strong>{formatMetric(item.current_price, ' 元')}</strong>
              </div>
              <div>
                <label>动态PE</label>
                <strong>{formatMetric(item.pe_dynamic)}</strong>
              </div>
              <div>
                <label>PB</label>
                <strong>{formatMetric(item.pb)}</strong>
              </div>
              <div>
                <label>ROE</label>
                <strong>{formatMetric(item.roe, '%')}</strong>
              </div>
              <div>
                <label>估值结论</label>
                <strong>{item.valuation_conclusion ?? '--'}</strong>
              </div>
              <div>
                <label>AI 建议</label>
                <strong>{item.ai_action ?? '--'}</strong>
              </div>
            </div>
            <div className="stock-card-summary">
              <p>
                <span>主题</span>
                {item.core_theme ?? '--'}
              </p>
              <p>
                <span>催化</span>
                {item.short_term_catalyst ?? '--'}
              </p>
              <p>
                <span>风险</span>
                {item.main_risk ?? '--'}
              </p>
            </div>
            <footer>
              <span>买入区间：{formatMetric(item.buy_range_min)} - {formatMetric(item.buy_range_max)}</span>
              <span>卖出区间：{formatMetric(item.sell_range_min)} - {formatMetric(item.sell_range_max)}</span>
            </footer>
          </article>
        ))}
      </div>
    </section>
  );
}
