export interface Alert {
  id: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'critical';
  isRead: boolean;
  createdAt: string;
}
