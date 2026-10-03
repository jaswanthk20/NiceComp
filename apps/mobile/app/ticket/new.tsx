import { useEffect, useState } from "react";
import { Image, View, Switch, Platform } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import * as Crypto from "expo-crypto";
import { useResource } from "../../src/hooks/useResource";
import { Product, Ticket } from "../../src/types";
import { post } from "../../src/services/api";
import { uploadPhoto } from "../../src/services/uploads";
import { ticketDraft, setTicketDraft } from "../../src/state/ticketDraft";
import {
  Page,
  Card,
  Label,
  Body,
  Button,
  Choices,
  Field,
  ErrorMessage,
  Loading,
  s,
} from "../../src/components/ui";
export default function NewTicket() {
  const params = useLocalSearchParams<{ product?: string }>();
  const products = useResource<Product[]>("/products");
  const categories = useResource<string[]>("/categories");
  const [selected, setSelected] = useState(params.product ?? "");
  const [category, setCategory] = useState("Other");
  const [severity, setSeverity] = useState("Medium");
  const [description, setDescription] = useState(
    ticketDraft && ticketDraft.product === params.product
      ? ticketDraft.description
      : "",
  );
  const [summary] = useState(
    ticketDraft && ticketDraft.product === params.product
      ? ticketDraft.summary
      : "",
  );
  const [share, setShare] = useState(false);
  const [photos, setPhotos] = useState<{ id: string; uri: string }[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [key] = useState(() => Crypto.randomUUID());
  useEffect(() => {
    if (!selected && products.data?.[0]) setSelected(products.data[0].id);
  }, [selected, products.data]);
  const product = products.data?.find((p) => p.id === selected);
  const pick = async (camera: boolean) => {
    setError("");
    setUploading(true);
    try {
      if (camera) {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted)
          throw new Error(
            "Camera permission is required. You can also choose a photo.",
          );
      }
      const result = camera
        ? await ImagePicker.launchCameraAsync({
            mediaTypes: ["images"],
            quality: 0.85,
          })
        : await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ["images"],
            allowsMultipleSelection: true,
            selectionLimit: 6 - photos.length,
            quality: 0.85,
          });
      if (!result.canceled) {
        for (const asset of result.assets.slice(0, 6 - photos.length)) {
          const uploaded = await uploadPhoto(
            asset.uri,
            asset.width,
            asset.height,
          );
          setPhotos((p) => [...p, { id: uploaded.id, uri: asset.uri }]);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Photo upload failed.");
    } finally {
      setUploading(false);
    }
  };
  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      const ticket = await post<Ticket>("/tickets", {
        customer_product_id: selected,
        category,
        severity,
        description,
        approved_summary: share ? summary : null,
        image_ids: photos.map((p) => p.id),
        idempotency_key: key,
      });
      setTicketDraft(null);
      router.replace(`/ticket/${ticket.id}`);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Ticket could not be created. Retry safely.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <Page
      title="Create support ticket"
      subtitle="Tell us what’s happening. Our team will take it from here."
    >
      {products.loading ? (
        <Loading />
      ) : products.error ? (
        <ErrorMessage message={products.error} retry={products.reload} />
      ) : !products.data?.length ? (
        <Card>
          <Body>
            A verified purchased product is required to create a ticket.
          </Body>
        </Card>
      ) : (
        <>
          <Card>
            <Label>YOUR EQUIPMENT</Label>
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
              onChange={(v) => {
                const p = products.data?.find(
                  (p) => p.model + " · " + (p.serial ?? p.id.slice(0, 8)) === v,
                );
                if (p) {
                  setSelected(p.id);
                  setShare(false);
                }
              }}
            />
            <Body>Model · {product?.model}</Body>
            <Body muted>Serial · {product?.serial ?? "Not recorded"}</Body>
          </Card>
          <Card>
            <Label>ISSUE CATEGORY</Label>
            {categories.error ? (
              <ErrorMessage
                message={categories.error}
                retry={categories.reload}
              />
            ) : (
              <Choices
                values={categories.data ?? []}
                value={category}
                onChange={setCategory}
              />
            )}
            <Label>SEVERITY</Label>
            <Choices
              values={["Low", "Medium", "High", "Critical"]}
              value={severity}
              onChange={setSeverity}
            />
            <Body muted>
              Safety-related faults are automatically raised to Critical.
              Response targets appear only after company SLA approval.
            </Body>
            <Field
              label="Problem description"
              multiline
              value={description}
              onChangeText={setDescription}
              maxLength={6000}
              placeholder="What happened? When did it start?"
            />
            {Boolean(summary) && selected === ticketDraft?.product && (
              <>
                <View style={s.row}>
                  <Switch
                    accessibilityLabel="Include reviewed chat context"
                    value={share}
                    onValueChange={setShare}
                  />
                  <Body>Include reviewed chat context</Body>
                </View>
                <Body muted>{summary}</Body>
              </>
            )}
          </Card>
          <Card>
            <Label>DIAGNOSTIC PHOTOS · UP TO 6</Label>
            <Body muted>
              Only photograph equipment from a safe position. Do not remove
              guards or open components.
            </Body>
            <View style={s.row}>
              {photos.map((p) => (
                <View key={p.id} style={{ gap: 8 }}>
                  <Image
                    source={{ uri: p.uri }}
                    accessibilityLabel="Attached diagnostic photo"
                    style={{ width: 110, height: 100, borderRadius: 10 }}
                  />
                  <Button
                    title="Remove"
                    secondary
                    onPress={() =>
                      setPhotos(photos.filter((x) => x.id !== p.id))
                    }
                  />
                </View>
              ))}
            </View>
            <View style={s.row}>
              {Platform.OS !== "web" && (
                <Button
                  title="Take photo"
                  secondary
                  disabled={uploading || photos.length >= 6}
                  onPress={() => void pick(true)}
                />
              )}
              <Button
                title={uploading ? "Uploading photo…" : "Choose photo"}
                secondary
                disabled={uploading || photos.length >= 6}
                onPress={() => void pick(false)}
              />
            </View>
          </Card>
          {Boolean(error) && <ErrorMessage message={error} />}
          <Button
            title={busy ? "Submitting…" : "Submit support ticket"}
            disabled={
              busy ||
              uploading ||
              description.trim().length < 10 ||
              !selected ||
              !categories.data?.includes(category)
            }
            onPress={() => void submit()}
          />
        </>
      )}
    </Page>
  );
}
