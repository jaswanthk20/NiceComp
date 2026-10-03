import { View } from "react-native";
import { router } from "expo-router";
import { useResource } from "../src/hooks/useResource";
import { Ticket } from "../src/types";
import {
  Page,
  Card,
  Body,
  Label,
  Button,
  Badge,
  Loading,
  ErrorMessage,
  s,
} from "../src/components/ui";
export default function Tickets() {
  const result = useResource<Ticket[]>("/tickets");
  return (
    <Page
      title="Support tickets"
      subtitle="Follow every issue from first contact to resolution."
    >
      <Button
        title="Create support ticket"
        onPress={() => router.push("/ticket/new")}
      />
      {result.loading ? (
        <Loading />
      ) : result.error ? (
        <ErrorMessage message={result.error} retry={result.reload} />
      ) : result.data?.length ? (
        result.data.map((t) => (
          <Card key={t.id}>
            <View style={s.row}>
              <Badge text={t.status} />
              <Badge text={t.severity} />
            </View>
            <Label>{t.number}</Label>
            <Body>
              {t.category} · {t.description.slice(0, 100)}
            </Body>
            <Body muted>{new Date(t.created_at).toLocaleString()}</Body>
            <Button
              title="View ticket"
              secondary
              onPress={() => router.push(`/ticket/${t.id}`)}
            />
          </Card>
        ))
      ) : (
        <Card>
          <Body>No tickets yet. If you need help, our team is here.</Body>
        </Card>
      )}
    </Page>
  );
}
