import { useState } from "react";
import { View, Text, ScrollView, useWindowDimensions } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useAuth } from "../../state/auth";
import {
  Button,
  Field,
  Logo,
  ErrorMessage,
  colors,
  Body,
  Label,
} from "../../components/ui";

export function Login() {
  const auth = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const wide = useWindowDimensions().width > 900;
  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      await auth.login(email, password);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <ScrollView
      contentContainerStyle={{
        flexGrow: 1,
        backgroundColor: colors.background,
      }}
      keyboardShouldPersistTaps="handled"
    >
      <View style={{ flex: 1, flexDirection: wide ? "row" : "column" }}>
        <View
          style={{
            flex: wide ? 1 : undefined,
            backgroundColor: colors.navy,
            padding: wide ? 64 : 28,
            justifyContent: "center",
            gap: 24,
          }}
        >
          <Logo />
          <Text
            style={{
              fontSize: wide ? 48 : 31,
              lineHeight: wide ? 57 : 39,
              fontWeight: "800",
              color: "white",
              maxWidth: 510,
              letterSpacing: -1,
            }}
          >
            Reliable air.{"\n"}Support to match.
          </Text>
          <Text
            style={{
              fontSize: 18,
              lineHeight: 28,
              color: "#C7D7EC",
              maxWidth: 420,
            }}
          >
            Your equipment, purchase records and product support. Together in
            one place.
          </Text>
          {wide && (
            <View style={{ gap: 24, marginTop: 28 }}>
              {[
                ["cube-outline", "Every machine, one place"],
                ["document-text-outline", "Answers with official sources"],
                ["headset-outline", "A direct line to support"],
              ].map(([icon, label]) => (
                <View
                  key={label}
                  style={{
                    flexDirection: "row",
                    gap: 16,
                    alignItems: "center",
                  }}
                >
                  <Ionicons
                    name={icon as "cube-outline"}
                    size={24}
                    color="#91BFFC"
                  />
                  <Text style={{ color: "white", fontSize: 16 }}>{label}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
        <View
          style={{
            flex: 1,
            padding: wide ? 64 : 28,
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <View style={{ width: "100%", maxWidth: 400, gap: 22 }}>
            <Label>CUSTOMER PORTAL</Label>
            <Text
              style={{ fontSize: 30, fontWeight: "800", color: colors.navy }}
            >
              Welcome back
            </Text>
            <Body muted>Sign in to take care of your NICE equipment.</Body>
            {auth.config?.environment !== "production" && (
              <View
                style={{
                  backgroundColor: "#FFF3D8",
                  padding: 14,
                  borderRadius: 10,
                }}
              >
                <Text style={{ color: "#785318", lineHeight: 21 }}>
                  Development review · Synthetic customer records.{" "}
                  {auth.config?.portable_review
                    ? "Document excerpts are shown in portable review mode."
                    : ""}
                </Text>
              </View>
            )}
            {Boolean(error || auth.error) && (
              <ErrorMessage
                message={error || auth.error}
                retry={!auth.config ? auth.retry : undefined}
              />
            )}
            <Field
              label="Email address"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
            <Field
              label="Password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              autoComplete="current-password"
              onSubmitEditing={() => void submit()}
            />
            <Button
              title={busy ? "Signing in…" : "Sign in"}
              disabled={busy || !email || !password || !auth.config}
              onPress={() => void submit()}
            />
            <Body muted>
              Need an account? Contact Nice Compressors to associate your
              purchases with your email.
            </Body>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}
