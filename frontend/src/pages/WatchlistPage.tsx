import { FormEvent, useState } from 'react';

import { api } from '../lib/api';
import type { WatchlistItem } from '../types';

interface WatchlistPageProps {
  items: WatchlistItem[];
  onReload: () => Promise<void>;
  onRunAnalysis: () => Promise<void>;
  isAnalyzing: boolean;
}

export function WatchlistPage({ items, onReload, onRunAnalysis, isAnalyzing }: WatchlistPageProps) {
  const [rawText, setRawText] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const lines = rawText
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);

    const payload = lines.map((line) => {
      const [stock_code, stock_name] = line.split(/[\s,，]+/);
      return { stock_code, stock_name };
    });

    setBusy(true);
    setMessage('');
    try {
      await api.post('/watchlist', { items: payload });
      setRawText('');
      setMessage('自选股票已更新。');
      await onReload();
    } catch {
      setMessage('提交失败，请检查每行是否为“代码 名称”。');
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (id: number) => {
    await api.delete(`/watchlist/${id}`);
    await onReload();
  };

  const handleClear = async () => {
    await api.delete('/watchlist');
    await onReload();
  };

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Watchlist</p>
          <h2>自选股票管理</h2>
          <span>把你的重点跟踪标的塞进这里，系统会围绕它们生成研判、触发价格提醒并沉淀历史记录。</span>
        </div>
        <div className="button-row">
          <button type="button" className="primary-button" onClick={onRunAnalysis} disabled={isAnalyzing}>
            {isAnalyzing ? 'AI 分析进行中...' : '立即 AI 分析'}
          </button>
          <button type="button" className="ghost-button" onClick={handleClear} disabled={isAnalyzing}>
            清空列表
          </button>
        </div>
      </header>

      <div className="watchlist-hero">
        <div className="hero-copy">
          <span>录入规范</span>
          <strong>每行一个股票，格式为“代码 名称”</strong>
          <p>示例：`600519 贵州茅台`、`000001 平安银行`。支持一次性粘贴多只，便于快速搭监控池。</p>
        </div>
        <div className="hero-chip-group">
          <span className="hero-chip">最多 10 只 / 次</span>
          <span className="hero-chip">落 SQLite</span>
          <span className="hero-chip">支持人工触发分析</span>
        </div>
      </div>

      <div className="watchlist-layout">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <label htmlFor="stocks-input">批量录入</label>
          <textarea
            id="stocks-input"
            placeholder={'600519 贵州茅台\n000001 平安银行\n300750 宁德时代'}
            value={rawText}
            onChange={(event) => setRawText(event.target.value)}
          />
          <button type="submit" className="primary-button" disabled={busy || isAnalyzing}>
            {busy ? '提交中...' : '保存到监控池'}
          </button>
          {message ? <p className="helper-text">{message}</p> : null}
        </form>

        <div className="panel">
          <div className="panel-header">
            <h3>当前监控列表</h3>
            <span>{items.length} 只股票正在盯盘</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>代码</th>
                  <th>名称</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.stock_code}</td>
                    <td>{item.stock_name}</td>
                    <td>{new Date(item.updated_at).toLocaleString()}</td>
                    <td>
                      <button type="button" className="link-button" onClick={() => handleDelete(item.id)} disabled={isAnalyzing}>
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="empty-state">
                      暂无自选股票，先把重点跟踪标的加入监控池。
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
