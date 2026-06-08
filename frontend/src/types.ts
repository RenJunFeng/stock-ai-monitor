export type PageKey = 'watchlist' | 'dashboard' | 'alerts';

export interface WatchlistItem {
  id: number;
  stock_code: string;
  stock_name: string;
  created_at: string;
  updated_at: string;
}

export interface AnalysisItem {
  id: number;
  stock_code: string;
  stock_name: string;
  provider: string;
  analysis_time: string;
  manual_trigger: boolean;
  current_price: number | null;
  total_market_cap: number | null;
  circulating_market_cap: number | null;
  pe_dynamic: number | null;
  pb: number | null;
  gross_margin: number | null;
  roe: number | null;
  latest_profit_growth: number | null;
  strong_support: number | null;
  weak_support: number | null;
  weak_resistance: number | null;
  strong_resistance: number | null;
  short_stop_loss: number | null;
  short_take_profit: number | null;
  buy_range_min: number | null;
  buy_range_max: number | null;
  sell_range_min: number | null;
  sell_range_max: number | null;
  valuation_conclusion: string | null;
  ai_action: string | null;
  main_fund_flow: string | null;
  turnover_rate: number | null;
  core_theme: string | null;
  short_term_catalyst: string | null;
  main_risk: string | null;
  report_markdown: string;
}

export interface AlertItem {
  id: number;
  stock_code: string;
  stock_name: string;
  trigger_type: string;
  current_price: number;
  ai_action: string | null;
  email_status: string;
  email_error: string | null;
  created_at: string;
}

export interface DashboardData {
  tracked_count: number;
  latest_analysis_count: number;
  recommendation_breakdown: Array<{ name: string; value: number }>;
  latest_alerts: AlertItem[];
  stocks: AnalysisItem[];
}

