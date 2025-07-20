export interface DailySummary {
  date: string;
  message: string;
  events_count: number;
  events: any[];
  daily_recap: string;
}

export interface WidgetProps {
  onCardClick?: () => void;
  isFlipped?: boolean;
  dailySummary?: DailySummary | null;
  loading?: boolean;
  error?: string | null;
} 