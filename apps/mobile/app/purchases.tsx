import { router } from "expo-router";
import { useResource } from "../src/hooks/useResource";
import { Purchase } from "../src/types";
import {
  Page,
  Card,
  Label,
  Body,
  Button,
  Loading,
  ErrorMessage,
  Badge,
} from "../src/components/ui";
export default function Purchases() {
  const result = useResource<Purchase[]>("/purchases");
  return (
    <Page
      title="My purchases"
      subtitle="Your orders, invoices and purchase records."
    >
      {result.loading ? (
        <Loading />
      ) : result.error ? (
        <ErrorMessage message={result.error} retry={result.reload} />
      ) : result.data?.length ? (
        result.data.map((p) => (
          <Card key={p.id}>
            <Label>{p.purchased_on}</Label>
            <Body>{p.invoice_number}</Body>
            {p.payment_status && <Badge text={p.payment_status} />}
            <Body>
              {p.amount
                ? `${p.currency} ${Number(p.amount).toLocaleString()}`
                : "Amount not provided by source system"}
            </Body>
            <Button
              title="View purchase details"
              secondary
              onPress={() => router.push(`/purchase/${p.id}`)}
            />
          </Card>
        ))
      ) : (
        <Card>
          <Body>No purchases available yet.</Body>
        </Card>
      )}
    </Page>
  );
}
