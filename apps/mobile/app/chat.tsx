import { useEffect, useState } from "react";
import { View, Text, Linking, ActivityIndicator } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { useResource } from "../src/hooks/useResource";
import { Product, Message, Source } from "../src/types";
import { post } from "../src/services/api";
import {
  Page,
  Card,
  Label,
  Body,
  Button,
  Field,
  Choices,
  ErrorMessage,
  Loading,
  colors,
  s,
} from "../src/components/ui";
import { setTicketDraft } from "../src/state/ticketDraft";
type History = { session_id: string | null; messages: Message[] };
export default function Chat() {
  const params = useLocalSearchParams<{ product?: string }>();
  const products = useResource<Product[]>("/products");
  const [selected, setSelected] = useState(params.product ?? "");
  const history = useResource<History>(selected ? `/chat/${selected}` : null);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const product = products.data?.find((p) => p.id === selected);
  useEffect(() => {
    if (!selected && products.data?.[0]) setSelected(products.data[0].id);
  }, [products.data, selected]);
  const send = async () => {
    if (!question.trim() || !selected || busy) return;
    setBusy(true);
    setError("");
    const sent = question;
    try {
      const result = await post<{
        session_id: string;
        answer: string;
        sources: Source[];
      }>("/chat", {
        customer_product_id: selected,
        session_id: history.data?.session_id ?? null,
        question: sent,
      });
      history.setData({
        session_id: result.session_id,
        messages: [
          ...(history.data?.messages ?? []),
          { role: "user", content: sent, sources: [] },
          {
            role: "assistant",
            content: result.answer,
            sources: result.sources,
          },
        ],
      });
      setQuestion("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "NICE AI is unavailable.");
    } finally {
      setBusy(false);
    }
  };
  const escalate = () => {
    const messages = history.data?.messages ?? [];
    setTicketDraft({
      product: selected,
      description:
        [...messages].reverse().find((m) => m.role === "user")?.content ??
        question,
      summary: messages
        .slice(-4)
        .map((m) => `${m.role}: ${m.content}`)
        .join("\n")
        .slice(0, 4000),
    });
    router.push({ pathname: "/ticket/new", params: { product: selected } });
  };
  return (
    <Page
      title="NICE AI Support"
      subtitle="Product-specific help, backed by official documentation."
    >
      {products.loading ? (
        <Loading />
      ) : products.error ? (
        <ErrorMessage message={products.error} retry={products.reload} />
      ) : !products.data?.length ? (
        <Card>
          <Body>
            Associate a purchased product with your account to use NICE AI.
          </Body>
        </Card>
      ) : (
        <>
          <Card>
            <Label>CURRENTLY HELPING WITH</Label>
            <Text
              style={{ fontSize: 23, fontWeight: "800", color: colors.navy }}
            >
              {product?.model ?? "Choose a product"}
            </Text>
            <Body muted>{product?.serial ?? "Serial number not recorded"}</Body>
            {!busy && (
              <Choices
                values={products.data.map(
                  (p) => p.model + " · " + (p.serial ?? p.id.slice(0, 8)),
                )}
                value={
                  product
                    ? product.model +
                      " · " +
                      (product.serial ?? product.id.slice(0, 8))
                    : ""
                }
                onChange={(label) => {
                  const p = products.data?.find(
                    (p) =>
                      p.model + " · " + (p.serial ?? p.id.slice(0, 8)) ===
                      label,
                  );
                  if (p) {
                    setSelected(p.id);
                    setError("");
                  }
                }}
              />
            )}
          </Card>
          {history.loading ? (
            <Loading />
          ) : history.error ? (
            <ErrorMessage message={history.error} retry={history.reload} />
          ) : (
            <>
              {!history.data?.messages.length && (
                <Card>
                  <Label>HOW CAN WE HELP?</Label>
                  <Body>
                    Ask about your model’s published product information. If a
                    specification or procedure is missing, we’ll help you
                    contact support.
                  </Body>
                  <Button
                    title="Show technical specifications"
                    secondary
                    onPress={() => setQuestion("Show technical specifications")}
                  />
                </Card>
              )}
              {history.data?.messages.map((m, i) => (
                <View
                  key={m.id ?? i}
                  style={{
                    alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                    maxWidth: "94%",
                    backgroundColor: m.role === "user" ? colors.blue : "white",
                    padding: 20,
                    borderRadius: 16,
                    gap: 12,
                    borderWidth: m.role === "user" ? 0 : 1,
                    borderColor: colors.border,
                  }}
                >
                  <Text
                    style={{
                      fontSize: 11,
                      fontWeight: "800",
                      letterSpacing: 1,
                      color: m.role === "user" ? "#D6E6FF" : colors.blue,
                    }}
                  >
                    {m.role === "user" ? "YOU" : "NICE AI"}
                  </Text>
                  <Text
                    selectable
                    style={{
                      fontSize: 16,
                      lineHeight: 25,
                      color: m.role === "user" ? "white" : colors.ink,
                    }}
                  >
                    {m.content}
                  </Text>
                  {m.sources.map((source, j) => (
                    <Button
                      key={j}
                      title={`Source: ${source.title}${source.page ? ` · Page ${source.page}` : ""}`}
                      secondary
                      onPress={() => void Linking.openURL(source.url)}
                    />
                  ))}
                </View>
              ))}
              {busy && (
                <View style={s.row}>
                  <ActivityIndicator color={colors.blue} />
                  <Body muted>Checking your product documentation…</Body>
                </View>
              )}
              {Boolean(error) && (
                <ErrorMessage message={error} retry={() => void send()} />
              )}
              <Card>
                <Field
                  label="Your question"
                  placeholder="Ask about your equipment…"
                  value={question}
                  onChangeText={setQuestion}
                  multiline
                  editable={!busy}
                />
                <Button
                  title={busy ? "Checking sources…" : "Send question"}
                  onPress={() => void send()}
                  disabled={busy || !question.trim()}
                />
                <Button
                  title="Issue unresolved? Create ticket"
                  secondary
                  onPress={escalate}
                  disabled={busy}
                />
                <Body muted>
                  NICE AI cannot replace qualified technical service. Never open
                  pressurized components or bypass safety devices.
                </Body>
              </Card>
            </>
          )}
        </>
      )}
    </Page>
  );
}
