import { Platform } from "react-native";
import * as ImageManipulator from "expo-image-manipulator";
import { api } from "./api";
export async function uploadPhoto(uri: string, width: number, height: number) {
  const actions =
    width > 1920 || height > 1920
      ? [{ resize: width >= height ? { width: 1920 } : { height: 1920 } }]
      : [];
  const compressed = await ImageManipulator.manipulateAsync(uri, actions, {
    compress: 0.82,
    format: ImageManipulator.SaveFormat.JPEG,
  });
  const form = new FormData();
  if (Platform.OS === "web")
    form.append(
      "file",
      await (await fetch(compressed.uri)).blob(),
      "diagnostic.jpg",
    );
  else
    form.append("file", {
      uri: compressed.uri,
      name: "diagnostic.jpg",
      type: "image/jpeg",
    } as unknown as Blob);
  return api<{ id: string; name: string }>("/images", {
    method: "POST",
    body: form,
  });
}
export async function uploadDocument(
  path: string,
  uri: string,
  name: string,
  mime: string,
  fields: Record<string, string> = {},
) {
  const form = new FormData();
  Object.entries(fields).forEach(([k, v]) => form.append(k, v));
  if (Platform.OS === "web")
    form.append("file", await (await fetch(uri)).blob(), name);
  else form.append("file", { uri, name, type: mime } as unknown as Blob);
  return api<{ status?: string; message?: string; id?: string }>(path, {
    method: "POST",
    body: form,
  });
}
