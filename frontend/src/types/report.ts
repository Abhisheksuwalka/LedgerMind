export interface DataRun {
  id: string;
  status: 'Completed' | 'Processing' | 'Failed';
  runDate: string; // ISO 8601
  insights: string;
}

export interface PaginatedDataRuns {
  runs: DataRun[];
  total: number;
  page: number;
  pageSize: number;
}
