import { View } from "react-native";
import { useLocalSearchParams, router } from "expo-router";
import { useResource } from "../../src/hooks/useResource";
import { Purchase, Product } from "../../src/types";
import {
  Page,
  Card,
  Label,
  Body,
  Button,
  Loading,
  ErrorMessage,
} from "../../src/components/ui";
type Detail = {
  purchase: Purchase;
  items: {
    id: string;
    model: string;
    quantity: number;
    amount: string | null;
  }[];
  products: Product[];
  receipts: { id: string; name: string }[];
};
export default function PurchaseDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const result = useResource<Detail>(`/purchases/${id}`);
  const d = result.data;
  return (
    <Page
      title={d?.purchase.invoice_number ?? "Purchase details"}
      subtitle={d?.purchase.purchased_on}
    >
      {result.loading ? (
        <Loading />
      ) : result.error ? (
        <ErrorMessage message={result.error} retry={result.reload} />
      ) : (
        d && (
          <>
            <Card>
              <Label>PURCHASED ITEMS</Label>
              {d.items.map((i) => (
                <View key={i.id}>
                  <Body>{i.model}</Body>
                  <Body muted>Quantity · {i.quantity}</Body>
                </View>
              ))}
              <Body>
                {d.purchase.amount
                  ? `${d.purchase.currency} ${d.purchase.amount}`
                  : "Amount not recorded"}
              </Body>
              {d.receipts.length ? (
                d.receipts.map((r) => (
                  <Button
                    key={r.id}
                    title="View receipt"
                    onPress={() => router.push(`/receipt/${r.id}`)}
                  />
                ))
              ) : (
                <Body muted>Receipt unavailable. Contact support.</Body>
              )}
            </Card>
            {d.products.map((p) => (
              <Card key={p.id}>
                <Body>
                  {p.model} · {p.serial ?? "Serial not recorded"}
                </Body>
                <Body>Warranty · {p.warranty.status}</Body>
                <Button
                  title="View product"
                  secondary
                  onPress={() => router.push(`/product/${p.id}`)}
                />
              </Card>
            ))}
          </>
        )
      )}
    </Page>
  );
}
