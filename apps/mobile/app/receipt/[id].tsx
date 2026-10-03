import { Image, View, useWindowDimensions } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useResource } from "../../src/hooks/useResource";
import { Page, Body, Loading, ErrorMessage } from "../../src/components/ui";
export default function Receipt() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const result = useResource<{
    pages: { url: string; width: number; height: number }[];
  }>(`/receipts/${id}/pages`);
  const width = Math.min(useWindowDimensions().width - 64, 920);
  return (
    <Page
      title="Your receipt"
      subtitle="Private view · File links expire after two minutes."
    >
      {result.loading ? (
        <Loading />
      ) : result.error ? (
        <ErrorMessage message={result.error} retry={result.reload} />
      ) : (
        result.data?.pages.map((p, i) => (
          <View key={i}>
            <Body muted>Page {i + 1}</Body>
            <Image
              accessibilityLabel={`Receipt page ${i + 1}`}
              source={{ uri: p.url }}
              style={{
                width,
                height: (width * p.height) / p.width,
                alignSelf: "center",
              }}
              resizeMode="contain"
            />
          </View>
        ))
      )}
    </Page>
  );
}
