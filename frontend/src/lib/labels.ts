import type {
  ActionPriority,
  ActionStatus,
  ContentStatus,
  IncidentSeverity,
  IncidentStatus,
  IncidentType,
  InspectionCategory,
  InspectionStatus,
  KnowledgeCategory,
  UserRole,
} from "./types";

export type Tone = "neutral" | "brand" | "success" | "warning" | "danger";

export type Option<T extends string = string> = { value: T; label: string };

function options<T extends string>(labels: Record<T, string>): Option<T>[] {
  return (Object.keys(labels) as T[]).map((value) => ({ value, label: labels[value] }));
}

export const INSPECTION_CATEGORY: Record<InspectionCategory, string> = {
  fire: "Fire safety",
  electrical: "Electrical",
  structural: "Structural",
  chemical: "Chemical",
  ppe: "PPE",
  general: "General",
};

export const INSPECTION_STATUS: Record<InspectionStatus, string> = {
  scheduled: "Scheduled",
  completed: "Completed",
};

export const INCIDENT_TYPE: Record<IncidentType, string> = {
  injury: "Injury",
  fire: "Fire",
  electrical: "Electrical",
  chemical: "Chemical",
  structural: "Structural",
  near_miss: "Near miss",
};

export const INCIDENT_SEVERITY: Record<IncidentSeverity, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

export const INCIDENT_STATUS: Record<IncidentStatus, string> = {
  open: "Open",
  investigating: "Investigating",
  closed: "Closed",
};

export const ACTION_PRIORITY: Record<ActionPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

export const ACTION_STATUS: Record<ActionStatus, string> = {
  open: "Open",
  in_progress: "In progress",
  completed: "Completed",
};

export const KNOWLEDGE_CATEGORY: Record<KnowledgeCategory, string> = {
  labour_law: "Labour law",
  fire_safety: "Fire safety",
  electrical_safety: "Electrical safety",
  building_safety: "Building safety",
  chemical_safety: "Chemical safety",
  occupational_health: "Occupational health",
  incident_handling: "Incident handling",
  inspection: "Inspection",
  factory_procedure: "Factory procedure",
};

export const CONTENT_STATUS: Record<ContentStatus, string> = {
  official_verified: "Official, verified",
  general_guidance: "General guidance",
};

export const USER_ROLE: Record<UserRole, string> = {
  admin: "Admin",
  staff: "Staff · view only",
};

export const OPTIONS = {
  inspectionCategory: options(INSPECTION_CATEGORY),
  inspectionStatus: options(INSPECTION_STATUS),
  incidentType: options(INCIDENT_TYPE),
  incidentSeverity: options(INCIDENT_SEVERITY),
  incidentStatus: options(INCIDENT_STATUS),
  actionPriority: options(ACTION_PRIORITY),
  actionStatus: options(ACTION_STATUS),
  knowledgeCategory: options(KNOWLEDGE_CATEGORY),
  contentStatus: options(CONTENT_STATUS),
  userRole: options(USER_ROLE),
};

export const SEVERITY_TONE: Record<IncidentSeverity, Tone> = {
  low: "neutral",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

export const INCIDENT_STATUS_TONE: Record<IncidentStatus, Tone> = {
  open: "danger",
  investigating: "warning",
  closed: "success",
};

export const ACTION_STATUS_TONE: Record<ActionStatus, Tone> = {
  open: "neutral",
  in_progress: "brand",
  completed: "success",
};

export const PRIORITY_TONE: Record<ActionPriority, Tone> = {
  low: "neutral",
  medium: "warning",
  high: "danger",
};

export const INSPECTION_STATUS_TONE: Record<InspectionStatus, Tone> = {
  scheduled: "brand",
  completed: "success",
};

export function scoreTone(score: number | null | undefined): Tone {
  if (score === null || score === undefined) return "neutral";
  if (score >= 80) return "success";
  if (score >= 60) return "warning";
  return "danger";
}
