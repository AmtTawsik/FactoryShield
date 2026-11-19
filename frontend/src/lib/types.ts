export type Page<T> = { items: T[]; total: number; page: number; size: number };

export type UserRole = "super_admin" | "admin" | "staff";

export type OrganizationSummary = { id: number; name: string };

export type CurrentUser = {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  organization: OrganizationSummary | null;
};

export type UserDetail = Omit<CurrentUser, "organization"> & {
  factory_ids: number[];
  created_at: string;
  updated_at: string;
};

export type Factory = {
  id: number;
  name: string;
  license_number: string;
  address: string;
  district: string;
  worker_count: number;
  floor_count: number;
  contact_person: string;
  contact_phone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type InspectionCategory = "fire" | "electrical" | "structural" | "chemical" | "ppe" | "general";
export type InspectionStatus = "scheduled" | "completed";

export type Inspection = {
  id: number;
  factory_id: number;
  inspector_id: number | null;
  inspection_date: string;
  category: InspectionCategory;
  status: InspectionStatus;
  score: number | null;
  findings: string | null;
  created_at: string;
  updated_at: string;
};

export type IncidentType = "injury" | "fire" | "electrical" | "chemical" | "structural" | "near_miss";
export type IncidentSeverity = "low" | "medium" | "high" | "critical";
export type IncidentStatus = "open" | "investigating" | "closed";

export type Incident = {
  id: number;
  factory_id: number;
  reported_by_id: number | null;
  occurred_at: string;
  incident_type: IncidentType;
  severity: IncidentSeverity;
  location: string;
  injured_count: number;
  description: string;
  status: IncidentStatus;
  created_at: string;
  updated_at: string;
};

export type ActionPriority = "low" | "medium" | "high";
export type ActionStatus = "open" | "in_progress" | "completed";

export type CorrectiveAction = {
  id: number;
  factory_id: number;
  inspection_id: number | null;
  incident_id: number | null;
  title: string;
  description: string | null;
  priority: ActionPriority;
  assigned_to: string;
  due_date: string;
  status: ActionStatus;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  is_overdue: boolean;
};

export type KnowledgeCategory =
  | "labour_law"
  | "fire_safety"
  | "electrical_safety"
  | "building_safety"
  | "chemical_safety"
  | "occupational_health"
  | "incident_handling"
  | "inspection"
  | "factory_procedure";
export type ContentStatus = "official_verified" | "general_guidance";

export type KnowledgeDocument = {
  id: number;
  source_key: string;
  title: string;
  source_authority: string;
  source_url: string | null;
  category: KnowledgeCategory;
  content_status: ContentStatus;
  verified_on: string | null;
  organization_id: number | null;
  factory_id: number | null;
  created_at: string;
  updated_at: string;
  chunk_count: number;
};

export type OrganizationItem = {
  id: number;
  name: string;
  is_active: boolean;
  user_count: number;
  factory_count: number;
  created_at: string;
  updated_at: string;
};

export type OrganizationDetail = OrganizationItem & {
  admins: { id: number; full_name: string; email: string; is_active: boolean }[];
};

export type IngestResult = {
  document: Omit<KnowledgeDocument, "updated_at" | "chunk_count">;
  status: "created" | "updated" | "unchanged";
  chunk_count: number;
};

export type KnowledgeSource = {
  document_id: number;
  title: string;
  source_authority: string;
  source_url: string | null;
  content_status: ContentStatus;
  verified_on: string | null;
};

export type Conversation = {
  id: number;
  title: string;
  factory_id: number | null;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type ConversationDetail = Conversation & { messages: ChatMessage[] };

export type ChatResponse = {
  conversation_id: number;
  factory_id: number | null;
  reply: string;
  tools_used: string[];
  sources: KnowledgeSource[];
};

export type DashboardSummary = {
  as_of: string;
  factories: number;
  workers: number;
  inspections: {
    completed_last_90_days: number;
    average_score_last_90_days: number | null;
    scheduled_upcoming: number;
  };
  incidents: { not_closed: number; serious_not_closed: number; last_30_days: number };
  actions: { not_completed: number; overdue: number; completed_last_30_days: number };
  score_trend: { month: string; inspections: number; average_score: number | null }[];
  incidents_by_severity: { severity: IncidentSeverity; count: number }[];
  overdue_by_factory: { factory_id: number; factory_name: string; overdue: number }[];
  upcoming_inspections: {
    id: number;
    factory_id: number;
    factory_name: string;
    inspection_date: string;
    category: InspectionCategory;
  }[];
};
