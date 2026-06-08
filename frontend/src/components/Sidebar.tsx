import type { PageKey } from '../types';

interface SidebarProps {
  currentPage: PageKey;
  onChange: (page: PageKey) => void;
}

const items: Array<{ key: PageKey; label: string; description: string }> = [
  { key: 'watchlist', label: '自选管理', description: '维护监控股票池' },
  { key: 'dashboard', label: '监控大屏', description: '查看 AI 分析结果' },
  { key: 'alerts', label: '告警日志', description: '回看触发记录' },
];

export function Sidebar({ currentPage, onChange }: SidebarProps) {
  return (
    <aside className="sidebar-shell">
      <div className="brand-block">
        <div className="signal-pill">
          <span className="signal-dot" />
          AI market desk
        </div>
        <p className="eyebrow">A-Share Research Console</p>
        <h1>股票 AI 智能监控分析系统</h1>
        <p className="brand-copy">
          把自选池、量化提醒、结构化研判和报告回看压进一个带投研气质的工作台里。
        </p>
      </div>

      <div className="sidebar-note">
        <span>工作流</span>
        <strong>录入股票 → 触发分析 → 盯盘告警 → 回看报告</strong>
      </div>

      <nav className="nav-stack">
        {items.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`nav-card ${currentPage === item.key ? 'active' : ''}`}
            onClick={() => onChange(item.key)}
          >
            <span className="nav-index">0{items.findIndex((entry) => entry.key === item.key) + 1}</span>
            <div>
              <b>{item.label}</b>
              <small>{item.description}</small>
            </div>
          </button>
        ))}
      </nav>
    </aside>
  );
}
