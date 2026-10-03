// Kept in memory so private chat context is never placed in navigation URLs or persistent storage.
export let ticketDraft: {
  product: string;
  description: string;
  summary: string;
} | null = null;
export function setTicketDraft(value: typeof ticketDraft) {
  ticketDraft = value;
}
