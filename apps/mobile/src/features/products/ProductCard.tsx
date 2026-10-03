import { Image, View, Text } from "react-native";
import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { Product } from "../../types";
import {
  Card,
  Label,
  Body,
  Badge,
  Button,
  colors,
  s,
} from "../../components/ui";
export function ProductCard({ product }: { product: Product }) {
  return (
    <Card>
      <View style={s.row}>
        <View
          style={{
            width: 82,
            height: 82,
            backgroundColor: colors.background,
            borderRadius: 10,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {product.image_url ? (
            <Image
              source={{ uri: product.image_url }}
              style={{ width: 78, height: 78 }}
              resizeMode="contain"
            />
          ) : (
            <Ionicons name="construct-outline" size={36} color={colors.blue} />
          )}
        </View>
        <View style={{ flex: 1, gap: 6 }}>
          <Label>{product.family}</Label>
          <Text style={{ fontWeight: "800", fontSize: 21, color: colors.navy }}>
            {product.model}
          </Text>
          <Badge text={product.warranty.status} />
        </View>
      </View>
      <Body muted>Serial · {product.serial ?? "Not recorded"}</Body>
      <View style={s.row}>
        <Button
          title="View product"
          secondary
          onPress={() => router.push(`/product/${product.id}`)}
        />
        <Button
          title="Ask NICE AI"
          icon="chatbubble-ellipses-outline"
          onPress={() =>
            router.push({ pathname: "/chat", params: { product: product.id } })
          }
        />
      </View>
    </Card>
  );
}
