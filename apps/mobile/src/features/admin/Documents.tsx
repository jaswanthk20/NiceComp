import { useState } from "react";
import * as DocumentPicker from "expo-document-picker";
import { useResource } from "../../hooks/useResource";
import { KnowledgeDocument } from "../../types";
import { api, post } from "../../services/api";
import { uploadDocument } from "../../services/uploads";
import {
  Card,
  Label,
  Body,
  Field,
  Button,
  ErrorMessage,
  Badge,
  Loading,
} from "../../components/ui";
export function Documents() {
  const result = useResource<KnowledgeDocument[]>("/admin/documents");
  const models =
    useResource<{ id: string; name: string; family: string }[]>(
      "/admin/models",
    );
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [version, setVersion] = useState("");
  const [family, setFamily] = useState("");
  const [ids, setIds] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const perform = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
      result.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Document action failed.");
    } finally {
      setBusy(false);
    }
  };
  const upload = async () => {
    const selected = await DocumentPicker.getDocumentAsync({
      type: "application/pdf",
      copyToCacheDirectory: true,
    });
    if (selected.canceled) return;
    const f = selected.assets[0];
    if (!f) return;
    await uploadDocument("/admin/documents", f.uri, f.name, "application/pdf", {
      title,
      source_url: url,
      version,
      family,
      model_ids: ids,
    });
  };
  return (
    <>
      <Card>
        <Label>UPLOAD OFFICIAL DOCUMENT</Label>
        <Body muted>
          Verify the source and applicable models. Indexing alone does not
          activate a document.
        </Body>
        <Field label="Document title" value={title} onChangeText={setTitle} />
        <Field label="Official source URL" value={url} onChangeText={setUrl} />
        <Field
          label="Document version"
          value={version}
          onChangeText={setVersion}
        />
        <Field label="Product family" value={family} onChangeText={setFamily} />
        <Field
          label="Applicable model IDs (comma-separated)"
          value={ids}
          onChangeText={setIds}
        />
        {models.data?.map((m) => (
          <Body key={m.id}>
            {m.name} · {m.id}
          </Body>
        ))}
        <Button
          title="Choose PDF and upload"
          disabled={busy || !title || !url || !version || !family || !ids}
          onPress={() => void perform(upload)}
        />
      </Card>
      {Boolean(error) && <ErrorMessage message={error} />}
      {result.loading ? (
        <Loading />
      ) : result.error ? (
        <ErrorMessage message={result.error} retry={result.reload} />
      ) : (
        result.data?.map((d) => (
          <Card key={d.id}>
            <Body>
              {d.title} · {d.version}
            </Body>
            <Badge text={d.status} />
            <Body muted>
              {d.active ? "Active and approved" : "Inactive"} · {d.source_url}
            </Body>
            {d.error && <ErrorMessage message={d.error} />}
            <Button
              title="Index / re-index"
              secondary
              disabled={busy}
              onPress={() =>
                void perform(() => post(`/admin/documents/${d.id}/index`, {}))
              }
            />
            <Button
              title={
                d.active
                  ? "Deactivate document"
                  : "Confirm model scope and activate"
              }
              disabled={busy || (!d.active && d.status !== "indexed")}
              onPress={() =>
                void perform(() =>
                  api(`/admin/documents/${d.id}`, {
                    method: "PATCH",
                    body: JSON.stringify({
                      active: !d.active,
                      reviewed_model_scope: true,
                    }),
                  }),
                )
              }
            />
          </Card>
        ))
      )}
    </>
  );
}
