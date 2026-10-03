import React, { createContext, useContext, useEffect, useState } from "react";
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { api, post, setToken, onExpired } from "../services/api";
import { Config, User } from "../types";

const secureStorage = {
  getItem: async (key: string) =>
    Platform.OS === "web"
      ? sessionStorage.getItem(key)
      : SecureStore.getItemAsync(key),
  setItem: async (key: string, value: string) => {
    if (Platform.OS === "web") sessionStorage.setItem(key, value);
    else await SecureStore.setItemAsync(key, value);
  },
  removeItem: async (key: string) => {
    if (Platform.OS === "web") sessionStorage.removeItem(key);
    else await SecureStore.deleteItemAsync(key);
  },
};
type Auth = {
  user: User | null;
  config: Config | null;
  loading: boolean;
  error: string;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  retry: () => void;
};
const Context = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [supabase, setSupabase] = useState<SupabaseClient | null>(null);
  useEffect(() => {
    let unsubscribe: (() => void) | undefined;
    let cancelled = false;
    const init = async () => {
      setLoading(true);
      setError("");
      try {
        const cfg = await api<Config>("/config");
        if (cancelled) return;
        setConfig(cfg);
        let token: string | null = null;
        if (cfg.auth_provider === "supabase") {
          const client = createClient(cfg.supabase_url, cfg.supabase_anon_key, {
            auth: {
              storage: secureStorage,
              persistSession: true,
              autoRefreshToken: true,
              detectSessionInUrl: false,
            },
          });
          setSupabase(client);
          const { data } = await client.auth.getSession();
          token = data.session?.access_token ?? null;
          const listener = client.auth.onAuthStateChange((_event, session) => {
            setToken(session?.access_token ?? null);
            if (!session) setUser(null);
          });
          unsubscribe = () => listener.data.subscription.unsubscribe();
        } else token = await secureStorage.getItem("nicecomp-dev-token");
        setToken(token);
        if (token) setUser(await api<User>("/me"));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unable to connect.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void init();
    onExpired(() => {
      setToken(null);
      setUser(null);
      void secureStorage.removeItem("nicecomp-dev-token");
    });
    return () => {
      cancelled = true;
      unsubscribe?.();
    };
  }, [attempt]);
  const login = async (email: string, password: string) => {
    if (!config) throw new Error("Connect to the backend first.");
    if (config.auth_provider === "development") {
      const result = await post<{ access_token: string }>(
        "/auth/development-login",
        { email, password },
      );
      setToken(result.access_token);
      await secureStorage.setItem("nicecomp-dev-token", result.access_token);
    } else {
      if (!supabase) throw new Error("Sign-in service is not ready.");
      const result = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (result.error)
        throw new Error(
          "Email or password is incorrect, or sign-in is unavailable.",
        );
      setToken(result.data.session.access_token);
    }
    setUser(await api<User>("/me"));
    setError("");
  };
  const logout = async () => {
    await supabase?.auth.signOut();
    await secureStorage.removeItem("nicecomp-dev-token");
    setToken(null);
    setUser(null);
  };
  return (
    <Context.Provider
      value={{
        user,
        config,
        loading,
        error,
        login,
        logout,
        retry: () => setAttempt((a) => a + 1),
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useAuth() {
  const value = useContext(Context);
  if (!value) throw new Error("Auth provider missing");
  return value;
}
