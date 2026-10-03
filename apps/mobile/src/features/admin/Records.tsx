import { useState } from "react";
import * as DocumentPicker from "expo-document-picker";
import { api, post } from "../../services/api";
import { uploadDocument } from "../../services/uploads";
import { Card, Label, Field, Button, Body, Choices } from "../../components/ui";
export function Records() {
  const [name, setName] = useState("");
  const [family, setFamily] = useState("");
  const [source, setSource] = useState("csv");
  const [sourceId, setSourceId] = useState("");
  const [url, setUrl] = useState("");
  const [image, setImage] = useState("");
  const [asset, setAsset] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [evidence, setEvidence] = useState("");
  const [purchase, setPurchase] = useState("");
  const [message, setMessage] = useState("");
  const run = async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      setMessage("Record saved.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not save record.");
    }
  };
  const upload = async () => {
    const selected = await DocumentPicker.getDocumentAsync({
      type: "application/pdf",
      copyToCacheDirectory: true,
    });
    const f = selected.assets?.[0];
    if (f)
      await uploadDocument(
        `/admin/receipts/${purchase}`,
        f.uri,
        f.name,
        "application/pdf",
      );
  };
  return (
    <>
      {Boolean(message) && (
        <Card>
          <Body>{message}</Body>
        </Card>
      )}
      <Card>
        <Label>VERIFIED PRODUCT MODEL</Label>
        <Field label="Model name" value={name} onChangeText={setName} />
        <Field label="Family" value={family} onChangeText={setFamily} />
        <Choices values={["csv", "odoo"]} value={source} onChange={setSource} />
        <Field
          label="Source product ID"
          value={sourceId}
          onChangeText={setSourceId}
        />
        <Field
          label="Official product page"
          value={url}
          onChangeText={setUrl}
        />
        <Field
          label="Official model image URL (optional)"
          value={image}
          onChangeText={setImage}
        />
        <Button
          title="Add product mapping"
          disabled={!name || !family || !sourceId || !url}
          onPress={() =>
            void run(() =>
              post("/admin/models", {
                name,
                family,
                source,
                source_id: sourceId,
                official_url: url,
                image_url: image || null,
              }),
            )
          }
        />
      </Card>
      <Card>
        <Label>MANUAL WARRANTY ADJUSTMENT</Label>
        <Body muted>
          Use verified business evidence. Public marketing terms alone do not
          establish an individual machine’s eligibility.
        </Body>
        <Field
          label="Customer product ID"
          value={asset}
          onChangeText={setAsset}
        />
        <Field
          label="Warranty start (YYYY-MM-DD)"
          value={start}
          onChangeText={setStart}
        />
        <Field
          label="Warranty end (YYYY-MM-DD)"
          value={end}
          onChangeText={setEnd}
        />
        <Field
          label="Evidence / reason"
          value={evidence}
          onChangeText={setEvidence}
          multiline
        />
        <Button
          title="Save verified warranty"
          disabled={!asset || !start || !end || evidence.length < 10}
          onPress={() =>
            void run(() =>
              api(`/admin/warranties/${asset}`, {
                method: "PUT",
                body: JSON.stringify({
                  starts_on: start,
                  ends_on: end,
                  basis: "manual",
                  evidence,
                }),
              }),
            )
          }
        />
      </Card>
      <Card>
        <Label>PRIVATE RECEIPT IMPORT</Label>
        <Field
          label="Purchase ID"
          value={purchase}
          onChangeText={setPurchase}
        />
        <Button
          title="Choose receipt PDF"
          disabled={!purchase}
          onPress={() => void run(upload)}
        />
      </Card>
    </>
  );
}
