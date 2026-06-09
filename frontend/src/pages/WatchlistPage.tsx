import { FormEvent, useState } from 'react';

import { api } from '../lib/api';
import type { WatchlistItem } from '../types';

interface AnalysisRunOptions {
  stockCodes?: string[];
  groupName?: string;
}

interface WatchlistPageProps {
  items: WatchlistItem[];
  onReload: () => Promise<void>;
  onRunAnalysis: (options?: AnalysisRunOptions) => Promise<void>;
  isAnalyzing: boolean;
}

function parseWatchlistLine(line: string) {
  const parts = line.split(/[\s,，]+/).map((part) => part.trim()).filter(Boolean);
  const [stock_code, stock_name, ...groupParts] = parts;
  return {
    stock_code,
    stock_name,
    group_name: groupParts.join(' ') || '默认分组',
  };
}

export function WatchlistPage({ items, onReload, onRunAnalysis, isAnalyzing }: WatchlistPageProps) {
  const [rawText, setRawText] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const groups = Array.from(new Set(items.map((item) => item.group_name || '默认分组')));

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const lines = rawText
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
    const payload = lines.map(parseWatchlistLine);

    if (payload.some((item) => !item.stock_code || !item.stock_name)) {
      setMessage('请检查录入格式：每行至少包含“代码 名称”，第三列可填写分组。');
      return;
    }

    setBusy(true);
    setMessage('');
    try {
      await api.post('/watchlist', { items: payload });
      setRawText('');
      setMessage('自选股票已更新，同代码会自动更新名称和分组。');
      await onReload();
    } catch {
      setMessage('提交失败，请检查每行是否为“代码 名称 分组”。');
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
          <span>把重点跟踪标的按行业、主题或策略分组，既可以全池分析，也可以单股或按组触发 AI 投研。</span>
        </div>
        <div className="button-row">
          <button type="button" className="primary-button" onClick={() => onRunAnalysis()} disabled={isAnalyzing || items.length === 0}>
            {isAnalyzing ? 'AI 分析进行中...' : '全池 AI 分析'}
          </button>
          <button type="button" className="ghost-button" onClick={handleClear} disabled={isAnalyzing || items.length === 0}>
            清空列表
          </button>
        </div>
      </header>

      <div className="watchlist-hero">
        <div className="hero-copy">
          <span>录入规范</span>
          <strong>每行一个股票，格式为“代码 名称 分组”</strong>
          <p>示例：600519 贵州茅台 白酒、000001 平安银行 银行。分组可不填，系统会放入“默认分组”。</p>
        </div>
        <div className="hero-chip-group">
          <span className="hero-chip">单股分析更稳</span>
          <span className="hero-chip">支持按组分析</span>
          <span className="hero-chip">同代码自动更新</span>
        </div>
      </div>

      <div className="watchlist-layout">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <label htmlFor="stocks-input">批量录入</label>
          <textarea
            id="stocks-input"
            placeholder={'600519 贵州茅台 白酒\n000001 平安银行 银行\n300724 捷佳伟创 光伏设备'}
            value={rawText}
            onChange={(event) => setRawText(event.target.value)}
          />
          <button type="submit" className="primary-button" disabled={busy || isAnalyzing}>
            {busy ? '提交中...' : '保存到监控池'}
          </button>
          {message ? <p className="helper-text">{message}</p> : null}
        </form>

        <div className="panel watchlist-panel">
          <div className="panel-header">
            <h3>当前监控列表</h3>
            <span>{items.length} 只股票正在盯盘</span>
          </div>

          {groups.length ? (
            <div className="group-action-strip" aria-label="按分组分析">
              {groups.map((group) => {
                const count = items.filter((item) => (item.group_name || '默认分组') === group).length;
                return (
                  <button
                    key={group}
                    type="button"
                    className="group-action-card"
                    onClick={() => onRunAnalysis({ groupName: group })}
                    disabled={isAnalyzing}
                  >
                    <span>{group}</span>
                    <strong>{count} 只</strong>
                    <small>按组 AI 分析</small>
                  </button>
                );
              })}
            </div>
          ) : null}

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>代码</th>
                  <th>名称</th>
                  <th>分组</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.stock_code}</td>
                    <td>{item.stock_name}</td>
                    <td>
                      <span className="group-badge">{item.group_name || '默认分组'}</span>
                    </td>
                    <td>{new Date(item.updated_at).toLocaleString()}</td>
                    <td>
                      <div className="row-actions">
                        <button
                          type="button"
                          className="link-button"
                          onClick={() => onRunAnalysis({ stockCodes: [item.stock_code] })}
                          disabled={isAnalyzing}
                        >
                          AI 分析
                        </button>
                        <button type="button" className="link-button danger-link" onClick={() => handleDelete(item.id)} disabled={isAnalyzing}>
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="empty-state">
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
