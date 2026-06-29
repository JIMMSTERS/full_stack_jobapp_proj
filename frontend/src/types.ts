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
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  company: string;
  position: string;
  status?: string;
  url?: string | null;
  notes?: string | null;
}

export interface User {
  id: number;
  email: string;
  name: string | null;
  picture: string | null;
}

export const STATUSES = [
  "applied",
  "screening",
  "interview",
  "offer",
  "rejected",
];
