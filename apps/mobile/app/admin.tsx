import { useState } from "react";
import { View } from "react-native";
import { router } from "expo-router";
import { useAuth } from "../src/state/auth";
import { useResource } from "../src/hooks/useResource";
import { api } from "../src/services/api";
import { Ticket } from "../src/types";
import {
  Page,
  Card,
  Label,
  Body,
  Button,
  Choices,
  Badge,
  Field,
  Loading,
  ErrorMessage,
  s,
} from "../src/components/ui";
import { SLAEditor } from "../src/features/admin/SLAEditor";
import { Documents } from "../src/features/admin/Documents";
import { Integrations } from "../src/features/admin/Integrations";
import { Records } from "../src/features/admin/Records";
const transitions: Record<string, string[]> = {
  Open: ["Acknowledged", "In Progress"],
  Acknowledged: ["In Progress", "Waiting for Customer"],
  "In Progress": ["Waiting for Customer", "Resolved"],
  "Waiting for Customer": ["In Progress", "Resolved"],
  Resolved: ["Closed", "In Progress"],
  Closed: [],
};
function TicketRow({
  row,
  reload,
}: {
  row: {
    ticket: Ticket;
    customer: { name: string; email: string };
    response_breached: boolean;
  };
  reload: () => void;
}) {
  const [status, setStatus] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const update = async () => {
    try {
      await api(`/admin/tickets/${row.ticket.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status, note }),
      });
      setNote("");
      setStatus("");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed.");
    }
  };
  return (
    <Card>
      <View style={s.row}>
        <Badge text={row.ticket.severity} />
        <Badge text={row.ticket.status} />
        {row.response_breached && <Badge text="Response overdue" />}
      </View>
      <Label>{row.ticket.number}</Label>
      <Body>
        {row.customer.name} · {row.customer.email}
      </Body>
      <Body>{row.ticket.description}</Body>
      <Button
        title="Open ticket and photos"
        secondary
        onPress={() => router.push(`/ticket/${row.ticket.id}`)}
      />
      <Choices
        values={transitions[row.ticket.status] ?? []}
        value={status}
        onChange={setStatus}
      />
      {Boolean(status) && (
        <>
          <Field label="Timeline note" value={note} onChangeText={setNote} />
          <Button
            title="Update ticket status"
            disabled={!note}
            onPress={() => void update()}
          />
        </>
      )}
      {Boolean(error) && <ErrorMessage message={error} />}
    </Card>
  );
}
export default function Admin() {
  const { user } = useAuth();
  const allowed = user?.role === "admin" || user?.role === "support";
  const [tab, setTab] = useState("Tickets");
  const [priority, setPriority] = useState("All");
  const tickets = useResource<
    {
      ticket: Ticket;
      customer: { name: string; email: string };
      response_breached: boolean;
    }[]
  >(
    allowed
      ? `/admin/tickets${priority === "All" ? "" : `?priority=${priority}`}`
      : null,
  );
  const rules = useResource<
    {
      id: string;
      severity: string;
      official: boolean;
      response_minutes: number;
      resolution_minutes: number;
    }[]
  >(allowed ? "/admin/sla" : null);
  if (!allowed)
    return (
      <Page title="Restricted access">
        <Body>Administrator or support access is required.</Body>
      </Page>
    );
  return (
    <Page
      title="Support workspace"
      subtitle="Review issues, maintain knowledge and manage service policy."
    >
      <Choices
        values={
          user?.role === "admin"
            ? ["Tickets", "SLA rules", "Knowledge", "Integrations", "Records"]
            : ["Tickets"]
        }
        value={tab}
        onChange={setTab}
      />
      {tab === "Tickets" ? (
        <>
          <Choices
            values={["All", "Critical", "High", "Medium", "Low"]}
            value={priority}
            onChange={setPriority}
          />
          <Button title="Refresh tickets" secondary onPress={tickets.reload} />
          {tickets.loading ? (
            <Loading />
          ) : tickets.error ? (
            <ErrorMessage message={tickets.error} retry={tickets.reload} />
          ) : (
            tickets.data?.map((row) => (
              <TicketRow
                key={row.ticket.id}
                row={row}
                reload={tickets.reload}
              />
            ))
          )}
        </>
      ) : tab === "SLA rules" ? (
        <>
          <SLAEditor onSaved={rules.reload} />
          {rules.data?.map((r) => (
            <Card key={r.id}>
              <Label>{r.severity}</Label>
              <Badge
                text={r.official ? "Official" : "Development / unapproved"}
              />
              <Body>
                {r.response_minutes} business minutes to respond ·{" "}
                {r.resolution_minutes} to resolve
              </Body>
            </Card>
          ))}
        </>
      ) : tab === "Knowledge" ? (
        <Documents />
      ) : tab === "Records" ? (
        <Records />
      ) : (
        <Integrations />
      )}
    </Page>
  );
}
