import { View, Text } from "react-native";
import { router } from "expo-router";
import { useAuth } from "../src/state/auth";
import { useResource } from "../src/hooks/useResource";
import { Product, Ticket } from "../src/types";
import {
  Page,
  Card,
  Body,
  Label,
  Button,
  Loading,
  ErrorMessage,
  colors,
  s,
} from "../src/components/ui";
import { ProductCard } from "../src/features/products/ProductCard";
export default function Dashboard() {
  const { user } = useAuth();
  const products = useResource<Product[]>("/products");
  const tickets = useResource<Ticket[]>("/tickets");
  return (
    <Page
      title={`Welcome, ${user?.name ?? ""}`}
      subtitle="Keep your equipment running. We’re here to help."
    >
      <View
        style={{
          backgroundColor: colors.navy,
          borderRadius: 18,
          padding: 28,
          gap: 16,
        }}
      >
        <Label>
          <Text style={{ color: "#99BEF0" }}>NICE AI SUPPORT</Text>
        </Label>
        <Text style={{ fontSize: 26, color: "white", fontWeight: "800" }}>
          The right support.{"\n"}For your exact machine.
        </Text>
        <Text style={{ color: "#C5D6EB", fontSize: 16, lineHeight: 24 }}>
          Find product information backed by official documentation, or get help
          from our team.
        </Text>
        <View style={s.row}>
          <Button
            title="Ask NICE AI"
            icon="chatbubble-ellipses-outline"
            onPress={() => router.push("/chat")}
          />
          <Button
            title="Create support ticket"
            secondary
            onPress={() => router.push("/ticket/new")}
          />
        </View>
      </View>
      <View style={s.row}>
        {[
          ["My products", products.data?.length],
          [
            "Active warranties",
            products.data?.filter((p) =>
              ["Active", "Expiring Soon"].includes(p.warranty.status),
            ).length,
          ],
          [
            "Open tickets",
            tickets.data?.filter(
              (t) => !["Resolved", "Closed"].includes(t.status),
            ).length,
          ],
        ].map(([label, count]) => (
          <View
            key={label}
            style={{
              flex: 1,
              minWidth: 130,
              backgroundColor: "white",
              borderRadius: 14,
              padding: 20,
              borderWidth: 1,
              borderColor: colors.border,
              gap: 8,
            }}
          >
            <Text
              style={{ fontSize: 29, fontWeight: "800", color: colors.navy }}
            >
              {count ?? "—"}
            </Text>
            <Label>{label}</Label>
          </View>
        ))}
      </View>
      <View style={[s.row, { justifyContent: "space-between" }]}>
        <Text style={{ fontSize: 21, fontWeight: "800", color: colors.navy }}>
          Your equipment
        </Text>
        <Button
          title="My purchases"
          secondary
          onPress={() => router.push("/purchases")}
        />
      </View>
      {products.loading ? (
        <Loading />
      ) : products.error ? (
        <ErrorMessage message={products.error} retry={products.reload} />
      ) : products.data?.length ? (
        products.data
          .slice(0, 3)
          .map((p) => <ProductCard product={p} key={p.id} />)
      ) : (
        <Card>
          <Body>
            No products are associated with your account yet. Contact support to
            verify your purchase records.
          </Body>
        </Card>
      )}
      {Boolean(tickets.error) && (
        <ErrorMessage message={tickets.error} retry={tickets.reload} />
      )}
    </Page>
  );
}
