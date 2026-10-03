import { Image, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useResource } from "../../src/hooks/useResource";
import { TicketDetail } from "../../src/types";
import {
  Page,
  Card,
  Body,
  Label,
  Badge,
  Button,
  Loading,
  ErrorMessage,
  s,
} from "../../src/components/ui";
function Photo({ id }: { id: string }) {
  const result = useResource<{ url: string }>(`/images/${id}/url`);
  return result.data ? (
    <Image
      source={{ uri: result.data.url }}
      accessibilityLabel="Ticket photo"
      style={{ width: 240, height: 180, borderRadius: 12 }}
    />
  ) : result.error ? (
    <ErrorMessage message={result.error} retry={result.reload} />
  ) : (
    <Loading />
  );
}
export default function TicketPage() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const result = useResource<TicketDetail>(`/tickets/${id}`);
  const d = result.data;
  return (
    <Page
      title={d?.ticket.number ?? "Support ticket"}
      subtitle="Your issue is saved. Follow progress here."
    >
      {result.loading ? (
        <Loading />
      ) : result.error ? (
        <ErrorMessage message={result.error} retry={result.reload} />
      ) : (
        d && (
          <>
            <Card>
              <View style={s.row}>
                <Badge text={d.ticket.status} />
                <Badge text={d.ticket.severity} />
              </View>
              <Label>
                {d.product.model} · {d.product.serial ?? "Serial not recorded"}
              </Label>
              <Body>{d.ticket.description}</Body>
              <Body muted>
                {d.ticket.response_due_at
                  ? `Expected response: ${new Date(d.ticket.response_due_at).toLocaleString()}`
                  : d.ticket.sla_message}
              </Body>
              <Body muted>
                {d.email_status === "sent"
                  ? "Support notification delivered."
                  : d.email_status === "failed" || d.email_status === "retry"
                    ? "Your ticket is saved. The support notification is delayed and will be retried."
                    : "Support notification queued."}
              </Body>
              <Button
                title="Refresh status"
                secondary
                onPress={result.reload}
              />
            </Card>
            {d.images.length > 0 && (
              <Card>
                <Label>ATTACHED PHOTOS</Label>
                <View style={s.row}>
                  {d.images.map((i) => (
                    <Photo id={i.id} key={i.id} />
                  ))}
                </View>
              </Card>
            )}
            <Card>
              <Label>TICKET TIMELINE</Label>
              {d.events.map((e) => (
                <View
                  key={e.id}
                  style={{
                    gap: 7,
                    borderLeftWidth: 3,
                    borderLeftColor: "#A8C6F0",
                    paddingLeft: 16,
                    paddingBottom: 18,
                  }}
                >
                  <Badge text={e.status} />
                  <Body>{e.note}</Body>
                  <Body muted>{new Date(e.created_at).toLocaleString()}</Body>
                </View>
              ))}
            </Card>
          </>
        )
      )}
    </Page>
  );
}
