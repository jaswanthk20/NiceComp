import { useState } from "react";
import * as DocumentPicker from "expo-document-picker";
import { useResource } from "../../hooks/useResource";
import { api, post } from "../../services/api";
import { uploadDocument } from "../../services/uploads";
import {
  Card,
  Label,
  Body,
  Button,
  Field,
  Badge,
  ErrorMessage,
} from "../../components/ui";
type Events = {
  email: {
    id: string;
    ticket_id: string;
    state: string;
    attempts: number;
    error: string | null;
  }[];
  sync: { id: string; source: string; status: string; error: string | null }[];
};
export function Integrations() {
  const events = useResource<Events>("/admin/events");
  const accounts = useResource<{
    customers: { id: string; name: string; source: string }[];
    profiles: { id: string; display_name: string }[];
  }>("/admin/customers");
  const [userId, setUserId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [message, setMessage] = useState("");
  const run = async (action: () => Promise<unknown>) => {
    try {
      const r = (await action()) as { message?: string; status?: string };
      setMessage(r.message ?? r.status ?? "Saved.");
      events.reload();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Action failed.");
    }
  };
  const importFile = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ["text/csv", "application/json", "text/comma-separated-values"],
      copyToCacheDirectory: true,
    });
    if (result.canceled) return {};
    const f = result.assets[0];
    if (!f) return {};
    return uploadDocument(
      "/admin/sync/import",
      f.uri,
      f.name,
      f.mimeType ?? "text/csv",
    );
  };
  return (
    <>
      {Boolean(message) && (
        <Card>
          <Body>{message}</Body>
        </Card>
      )}
      <Card>
        <Label>POS SYNCHRONIZATION</Label>
        <Body muted>
          Use verified exports until company Odoo API access and field mapping
          are configured.
        </Body>
        <Button
          title="Import CSV / JSON export"
          onPress={() => void run(importFile)}
        />
        <Button
          title="Synchronize Odoo"
          secondary
          onPress={() => void run(() => post("/admin/sync/odoo", {}))}
        />
      </Card>
      <Card>
        <Label>ASSOCIATE A VERIFIED CUSTOMER ACCOUNT</Label>
        <Body muted>
          Confirm ownership using company records before making an association.
        </Body>
        {accounts.data?.profiles.map((p) => (
          <Body key={p.id}>
            {p.display_name} · {p.id}
          </Body>
        ))}
        {accounts.data?.customers.map((c) => (
          <Body key={c.id}>
            {c.name} · {c.source} · {c.id}
          </Body>
        ))}
        <Field label="Account ID" value={userId} onChangeText={setUserId} />
        <Field
          label="Customer record ID"
          value={customerId}
          onChangeText={setCustomerId}
        />
        <Button
          title="Save verified association"
          disabled={!userId || !customerId}
          onPress={() =>
            void run(() =>
              api("/admin/customer-mapping", {
                method: "PUT",
                body: JSON.stringify({
                  user_id: userId,
                  customer_id: customerId,
                }),
              }),
            )
          }
        />
      </Card>
      <Card>
        <Label>EMAIL DELIVERY</Label>
        {events.data?.email.map((e) => (
          <Card key={e.id}>
            <Badge text={e.state} />
            <Body>Ticket · {e.ticket_id}</Body>
            <Body muted>
              Attempts · {e.attempts}
              {e.error ?? ""}
            </Body>
            {e.state !== "sent" && (
              <Button
                title="Retry notification"
                secondary
                onPress={() =>
                  void run(() => post(`/admin/email/${e.id}/retry`, {}))
                }
              />
            )}
          </Card>
        ))}
      </Card>
      <Card>
        <Label>SYNC HISTORY</Label>
        {events.data?.sync.slice(0, 20).map((e) => (
          <Body key={e.id}>
            {e.source} · {e.status} · {e.error ?? ""}
          </Body>
        ))}
      </Card>
      {Boolean(events.error) && (
        <ErrorMessage message={events.error} retry={events.reload} />
      )}
    </>
  );
}
