import React from "react";
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

export const colors = {
  blue: "#145ABD",
  navy: "#102C51",
  ink: "#1C2D43",
  muted: "#52647B",
  background: "#F3F6FA",
  white: "#FFFFFF",
  border: "#DFE6EF",
  pale: "#E9F1FF",
  green: "#167055",
  amber: "#8E5E12",
  red: "#B43838",
};
export const tokens = {
  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 },
  radius: { small: 8, card: 16 },
  type: { body: 16, label: 13, title: 28 },
};
export function Label({ children }: { children: React.ReactNode }) {
  return <Text style={s.label}>{children}</Text>;
}
export function Body({
  children,
  muted = false,
}: {
  children: React.ReactNode;
  muted?: boolean;
}) {
  return (
    <Text style={[s.body, muted && { color: colors.muted }]}>{children}</Text>
  );
}
export function Title({ children }: { children: React.ReactNode }) {
  return (
    <Text accessibilityRole="header" style={s.title}>
      {children}
    </Text>
  );
}
export function Card({ children }: { children: React.ReactNode }) {
  return <View style={s.card}>{children}</View>;
}
export function Logo() {
  return (
    <Image
      source={require("../../assets/official-logo.png")}
      style={{ width: 150, height: 50 }}
      resizeMode="contain"
      accessibilityLabel="NICE COMP"
    />
  );
}
export function Button({
  title,
  onPress,
  secondary = false,
  disabled = false,
  icon,
}: {
  title: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
  icon?: React.ComponentProps<typeof Ionicons>["name"];
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={title}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        s.button,
        secondary && s.secondary,
        disabled && { opacity: 0.5 },
        pressed && { opacity: 0.8 },
      ]}
    >
      {icon && (
        <Ionicons
          name={icon}
          size={19}
          color={secondary ? colors.blue : colors.white}
        />
      )}
      <Text style={[s.buttonText, secondary && { color: colors.blue }]}>
        {title}
      </Text>
    </Pressable>
  );
}
export function Field({ label, ...props }: TextInputProps & { label: string }) {
  return (
    <View style={{ gap: 8 }}>
      <Label>{label}</Label>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor={colors.muted}
        {...props}
        style={[
          s.input,
          props.multiline && { minHeight: 120, textAlignVertical: "top" },
          props.style,
        ]}
      />
    </View>
  );
}
export function Badge({ text }: { text: string }) {
  const good = ["Active", "Resolved", "Closed", "sent"].includes(text);
  const bad = ["Critical", "Expired", "failed"].includes(text);
  return (
    <View
      style={[
        s.badge,
        { backgroundColor: good ? "#E4F3EB" : bad ? "#FCEBEC" : colors.pale },
      ]}
    >
      <Text
        style={{
          fontSize: 12,
          fontWeight: "700",
          color: good ? colors.green : bad ? colors.red : colors.blue,
        }}
      >
        {text}
      </Text>
    </View>
  );
}
export function ErrorMessage({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <View accessibilityRole="alert" style={s.error}>
      <Text style={{ color: colors.red, lineHeight: 22 }}>{message}</Text>
      {retry && <Button title="Try again" secondary onPress={retry} />}
    </View>
  );
}
export function Loading() {
  return (
    <View style={{ padding: 40 }}>
      <ActivityIndicator size="large" color={colors.blue} />
      <Text style={{ textAlign: "center", color: colors.muted, marginTop: 12 }}>
        Loading…
      </Text>
    </View>
  );
}
export function Page({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}) {
  return (
    <ScrollView
      contentContainerStyle={s.page}
      keyboardShouldPersistTaps="handled"
    >
      <View style={{ gap: 8, marginBottom: 8 }}>
        <Title>{title}</Title>
        {subtitle && <Body muted>{subtitle}</Body>}
      </View>
      {children}
      <Text style={s.footer}>NICE COMP · Built around your equipment</Text>
    </ScrollView>
  );
}
export function Choices({
  values,
  value,
  onChange,
}: {
  values: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <View style={s.row}>
      {values.map((v) => (
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ selected: v === value }}
          key={v}
          onPress={() => onChange(v)}
          style={[
            s.choice,
            v === value && {
              backgroundColor: colors.blue,
              borderColor: colors.blue,
            },
          ]}
        >
          <Text
            style={{
              color: v === value ? "white" : colors.ink,
              fontWeight: "600",
            }}
          >
            {v}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}
export const s = StyleSheet.create({
  page: {
    width: "100%",
    maxWidth: 1060,
    alignSelf: "center",
    padding: 24,
    gap: 18,
    paddingBottom: 36,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    letterSpacing: -0.7,
    color: colors.navy,
  },
  label: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.muted,
    letterSpacing: 0.25,
  },
  body: { fontSize: 16, lineHeight: 24, color: colors.ink },
  card: {
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 22,
    gap: 14,
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    alignItems: "center",
  },
  button: {
    minHeight: 48,
    backgroundColor: colors.blue,
    borderRadius: 10,
    paddingHorizontal: 18,
    paddingVertical: 13,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  secondary: { backgroundColor: colors.pale },
  buttonText: { fontWeight: "700", fontSize: 15, color: "white" },
  input: {
    backgroundColor: "white",
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    minHeight: 50,
    padding: 14,
    color: colors.ink,
    fontSize: 16,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    alignSelf: "flex-start",
  },
  error: { padding: 16, borderRadius: 12, backgroundColor: "#FFF0F0", gap: 12 },
  choice: {
    paddingHorizontal: 14,
    paddingVertical: 13,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 9,
    backgroundColor: "white",
    minHeight: 44,
  },
  footer: {
    fontSize: 12,
    textAlign: "center",
    color: colors.muted,
    marginTop: 20,
  },
});
