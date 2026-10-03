import { View, Linking } from "react-native";
import { useLocalSearchParams, router } from "expo-router";
import { useResource } from "../../src/hooks/useResource";
import { Product, KnowledgeDocument } from "../../src/types";
import {
  Page,
  Loading,
  ErrorMessage,
  Card,
  Body,
  Label,
  Badge,
  Button,
  s,
} from "../../src/components/ui";
export default function ProductDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const result = useResource<Product>(`/products/${id}`);
  const docs = useResource<KnowledgeDocument[]>(`/products/${id}/documents`);
  const p = result.data;
  return (
    <Page title={p?.model ?? "Product details"} subtitle={p?.family}>
      {result.loading ? (
        <Loading />
      ) : result.error ? (
        <ErrorMessage message={result.error} retry={result.reload} />
      ) : (
        p && (
          <>
            <Card>
              <Badge text={p.warranty.status} />
              <Label>SERIAL NUMBER</Label>
              <Body>{p.serial ?? "Not recorded"}</Body>
              <Label>PURCHASE DATE</Label>
              <Body>{p.purchased_on}</Body>
              <Label>WARRANTY</Label>
              <Body>
                {p.warranty.message ??
                  `${p.warranty.starts_on} to ${p.warranty.ends_on}`}
              </Body>
              <Button
                title="View purchase"
                secondary
                onPress={() => router.push(`/purchase/${p.purchase_id}`)}
              />
            </Card>
            <View style={s.row}>
              <Button
                title="Ask NICE AI"
                onPress={() =>
                  router.push({ pathname: "/chat", params: { product: p.id } })
                }
              />
              <Button
                title="Create ticket"
                secondary
                onPress={() =>
                  router.push({
                    pathname: "/ticket/new",
                    params: { product: p.id },
                  })
                }
              />
            </View>
            <Card>
              <Label>PRODUCT INFORMATION & MANUALS</Label>
              {p.official_url && (
                <Button
                  title="Official product information"
                  secondary
                  onPress={() => void Linking.openURL(p.official_url!)}
                />
              )}
              {docs.data?.length ? (
                docs.data.map((d) => (
                  <View key={d.id} style={{ gap: 8 }}>
                    <Body>
                      {d.title} · {d.version}
                    </Body>
                    <Button
                      title={
                        d.kind === "manual"
                          ? "Open manual"
                          : "Open official source"
                      }
                      secondary
                      onPress={() => void Linking.openURL(d.source_url)}
                    />
                  </View>
                ))
              ) : (
                <Body muted>
                  No approved manual is currently available. Contact support for
                  the correct manual.
                </Body>
              )}
              {Boolean(docs.error) && (
                <ErrorMessage message={docs.error} retry={docs.reload} />
              )}
            </Card>
          </>
        )
      )}
    </Page>
  );
}
