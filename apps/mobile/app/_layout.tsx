import { Slot, router, usePathname } from "expo-router";
import { useEffect } from "react";
import { View, Text, Pressable, useWindowDimensions } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { AuthProvider, useAuth } from "../src/state/auth";
import { Login } from "../src/features/auth/Login";
import { colors, Logo, Loading } from "../src/components/ui";

const nav = [
  { path: "/dashboard", label: "Home", icon: "grid-outline" },
  { path: "/products", label: "Products", icon: "cube-outline" },
  { path: "/purchases", label: "Purchases", icon: "receipt-outline" },
  { path: "/tickets", label: "Support", icon: "headset-outline" },
] as const;
function Shell() {
  const auth = useAuth();
  const path = usePathname();
  const wide = useWindowDimensions().width >= 900;
  useEffect(() => {
    if (auth.user && auth.user.role !== "customer" && (path === "/dashboard" || path === "/")) router.replace("/admin");
  }, [auth.user, path]);
  if (auth.loading) return <Loading />;
  if (!auth.user) return <Login />;
  const navigation = (
    <>
      {nav.map((item) => (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={item.label}
          key={item.path}
          onPress={() => router.push(item.path)}
          style={{
            flexDirection: wide ? "row" : "column",
            alignItems: "center",
            gap: wide ? 14 : 4,
            padding: wide ? 16 : 10,
            borderRadius: 10,
            backgroundColor: path === item.path ? colors.pale : "transparent",
            flex: wide ? undefined : 1,
          }}
        >
          <Ionicons
            name={item.icon}
            size={22}
            color={path === item.path ? colors.blue : colors.muted}
          />
          <Text
            style={{
              fontSize: wide ? 15 : 11,
              color: path === item.path ? colors.blue : colors.muted,
              fontWeight: "700",
            }}
          >
            {item.label}
          </Text>
        </Pressable>
      ))}
    </>
  );
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
      <StatusBar style="dark" />
      <View style={{ flex: 1, flexDirection: "row" }}>
        {wide && (
          <View
            style={{
              width: 236,
              backgroundColor: "white",
              borderRightWidth: 1,
              borderRightColor: colors.border,
              padding: 22,
              gap: 14,
            }}
          >
            <Logo />
            <Text
              style={{
                fontSize: 11,
                color: colors.muted,
                letterSpacing: 1.4,
                marginBottom: 28,
              }}
            >
              CUSTOMER SUPPORT
            </Text>
            {navigation}
            <View style={{ flex: 1 }} />
            <Text style={{ fontWeight: "700", color: colors.ink }}>
              {auth.user.name}
            </Text>
            <Text style={{ fontSize: 12, color: colors.muted }}>
              NICE COMP Support
            </Text>
          </View>
        )}
        <View style={{ flex: 1 }}>
          <View
            style={{
              height: 70,
              backgroundColor: "white",
              paddingHorizontal: 24,
              borderBottomWidth: 1,
              borderBottomColor: colors.border,
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            {wide ? (
              <Text style={{ color: colors.muted }}>
                Your equipment. Our commitment.
              </Text>
            ) : (
              <Logo />
            )}
            <View style={{ flexDirection: "row", gap: 18 }}>
              {auth.user.role !== "customer" && (
                <Pressable
                  accessibilityRole="button"
                  onPress={() => router.push("/admin")}
                >
                  <Text style={{ color: colors.blue, fontWeight: "700" }}>
                    Admin
                  </Text>
                </Pressable>
              )}
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Sign out"
                onPress={() => void auth.logout()}
              >
                <Ionicons
                  name="log-out-outline"
                  size={23}
                  color={colors.muted}
                />
              </Pressable>
            </View>
          </View>
          {auth.config?.environment !== "production" && (
            <View
              style={{
                backgroundColor: "#FFF3D8",
                paddingHorizontal: 24,
                paddingVertical: 7,
              }}
            >
              <Text style={{ fontSize: 12, color: "#785318" }}>
                DEVELOPMENT · Synthetic accounts{" "}
                {auth.config?.portable_review
                  ? "· Portable document review"
                  : ""}
              </Text>
            </View>
          )}
          <Slot />
          {!wide && (
            <View
              style={{
                flexDirection: "row",
                backgroundColor: "white",
                borderTopWidth: 1,
                borderTopColor: colors.border,
              }}
            >
              {navigation}
            </View>
          )}
        </View>
      </View>
    </SafeAreaView>
  );
}
export default function Layout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </SafeAreaProvider>
  );
}
