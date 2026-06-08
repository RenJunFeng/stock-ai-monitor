import { FormEvent, useState } from 'react';

import type { AlertItem } from '../types';

interface AlertsPageProps {
  alerts: AlertItem[];
  onFilter: (stockCode: string) => Promise<void>;
}

export function AlertsPage({ alerts, onFilter }: AlertsPageProps) {
  const [stockCode, setStockCode] = useState('');

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await onFilter(stockCode.trim());
  };

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Alerts</p>
          <h2>告警历史记录</h2>
          <span>这里是系统的交易记忆层，用来回看哪些价格区间真的被打到，以及当时的 AI 操作建议。</span>
        </div>
      </header>

      <div className="panel">
        <form className="filter-row" onSubmit={handleSubmit}>
          <input
            type="text"
            value={stockCode}
            onChange={(event) => setStockCode(event.target.value)}
            placeholder="输入股票代码筛选"
          />
          <button type="submit" className="primary-button">
            查询
          </button>
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>股票</th>
                <th>触发类型</th>
                <th>价格</th>
                <th>AI 建议</th>
                <th>邮件状态</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr key={alert.id}>
                  <td>{new Date(alert.created_at).toLocaleString()}</td>
                  <td>
                    {alert.stock_name} ({alert.stock_code})
                  </td>
                  <td>{alert.trigger_type}</td>
                  <td>{alert.current_price}</td>
                  <td>{alert.ai_action ?? '--'}</td>
                  <td>{alert.email_status}</td>
                </tr>
              ))}
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-state">
                    暂无符合条件的告警数据。
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
