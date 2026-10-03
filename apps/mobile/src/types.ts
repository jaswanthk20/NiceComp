export type Warranty = {
  status: "Active" | "Expiring Soon" | "Expired" | "Unknown";
  starts_on: string | null;
  ends_on: string | null;
  message: string | null;
};
export type Product = {
  id: string;
  model_id: string;
  name: string;
  family: string;
  model: string;
  serial: string | null;
  purchased_on: string;
  purchase_id: string;
  image_url: string | null;
  official_url: string | null;
  warranty: Warranty;
};
export type Purchase = {
  id: string;
  invoice_number: string;
  purchased_on: string;
  currency: string;
  amount: string | null;
  payment_status: string | null;
};
export type Source = {
  title: string;
  url: string;
  page: number | null;
  version: string;
  document_id: string;
  chunk_id: string;
};
export type Message = {
  id?: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
};
export type Ticket = {
  id: string;
  number: string;
  customer_product_id: string;
  category: string;
  severity: string;
  description: string;
  approved_summary: string | null;
  status: string;
  created_at: string;
  response_due_at: string | null;
  resolution_due_at: string | null;
  sla_message: string | null;
};
export type TicketDetail = {
  ticket: Ticket;
  product: Product;
  images: { id: string; name: string }[];
  events: { id: string; status: string; note: string; created_at: string }[];
  email_status: string;
};
export type User = {
  id: string;
  name: string;
  role: "customer" | "support" | "admin";
  mapped: boolean;
};
export type Config = {
  environment: string;
  auth_provider: "supabase" | "development";
  supabase_url: string;
  supabase_anon_key: string;
  portable_review: boolean;
};
export type KnowledgeDocument = {
  id: string;
  title: string;
  source_url: string;
  version: string;
  active: boolean;
  approved: boolean;
  status: string;
  kind: string;
  error: string | null;
};
