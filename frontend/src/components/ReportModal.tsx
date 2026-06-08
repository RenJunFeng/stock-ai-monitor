import type { AnalysisItem } from '../types';

interface ReportModalProps {
  analysis: AnalysisItem | null;
  onClose: () => void;
}

export function ReportModal({ analysis, onClose }: ReportModalProps) {
  if (!analysis) {
    return null;
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <p className="eyebrow">Full Research Memo</p>
            <h3>
              {analysis.stock_name} · {analysis.stock_code}
            </h3>
            <span className="modal-meta">
              {analysis.ai_action ?? '未分类'} · {analysis.valuation_conclusion ?? '无估值结论'} ·{' '}
              {new Date(analysis.analysis_time).toLocaleString()}
            </span>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            关闭
          </button>
        </div>
        <pre className="report-text">{analysis.report_markdown}</pre>
      </div>
    </div>
  );
}
