export type ApplicationStatus =
  | "applied"
  | "screening"
  | "interview"
  | "offer"
  | "rejected";

export interface Application {
  id: number;
  company: string;
  position: string;
  status: string;
  url: string | null;
  notes: string | null;
  follow_up_date: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  company: string;
  position: string;
  status?: string;
  url?: string | null;
  notes?: string | null;
  follow_up_date?: string | null;
}

export interface StatusEvent {
  id: number;
  from_status: string | null;
  to_status: string;
  created_at: string;
}

export interface User {
  id: number;
  email: string;
  name: string | null;
  picture: string | null;
  is_demo?: boolean;
  gmail_connected?: boolean;
}

export interface EmailClassification {
  is_job_related: boolean;
  detected_status: string | null;
  company_guess: string | null;
}

export interface GmailMessage {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
  classification: EmailClassification;
}

export interface ImportSummary {
  created: number;
  updated: number;
  unchanged: number;
}

export interface WeeklyPoint {
  week: string;
  count: number;
}

export interface ApplicationStats {
  total: number;
  by_status: Record<string, number>;
  active: number;
  responded: number;
  offers: number;
  this_week: number;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
  weekly: WeeklyPoint[];
}

export interface FunnelStage {
  stage: string;
  reached: number;
  conversion: number;
}

export interface ApplicationAnalytics {
  sample_size: number;
  funnel: FunnelStage[];
  median_days_to_response: number | null;
  median_days_to_offer: number | null;
}

export const STATUSES = [
  "applied",
  "screening",
  "interview",
  "offer",
  "rejected",
];
