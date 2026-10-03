import { useState } from "react";
import { View, Switch } from "react-native";
import { api } from "../../services/api";
import {
  Card,
  Label,
  Body,
  Choices,
  Field,
  Button,
  ErrorMessage,
  s,
} from "../../components/ui";
export function SLAEditor({ onSaved }: { onSaved: () => void }) {
  const [severity, setSeverity] = useState("High");
  const [response, setResponse] = useState("");
  const [resolution, setResolution] = useState("");
  const [zone, setZone] = useState("Asia/Kolkata");
  const [days, setDays] = useState("0,1,2,3,4");
  const [start, setStart] = useState("9");
  const [end, setEnd] = useState("17");
  const [escalation, setEscalation] = useState("60");
  const [official, setOfficial] = useState(false);
  const [message, setMessage] = useState("");
  const save = async () => {
    try {
      await api("/admin/sla", {
        method: "PUT",
        body: JSON.stringify({
          severity,
          response_minutes: Number(response),
          resolution_minutes: Number(resolution),
          timezone: zone,
          weekdays: days.split(",").map(Number),
          start_hour: Number(start),
          end_hour: Number(end),
          escalation_minutes: Number(escalation),
          official,
        }),
      });
      setMessage("Rule saved. Existing ticket deadlines remain unchanged.");
      onSaved();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not save.");
    }
  };
  return (
    <Card>
      <Label>CONFIGURE RESPONSE POLICY</Label>
      <Body muted>
        Enter company-approved values. Unapproved rules are test fixtures and
        their deadlines are hidden from customers.
      </Body>
      <Choices
        values={["Critical", "High", "Medium", "Low"]}
        value={severity}
        onChange={setSeverity}
      />
      <Field
        label="Initial response (business minutes)"
        value={response}
        onChangeText={setResponse}
        keyboardType="numeric"
      />
      <Field
        label="Resolution (business minutes)"
        value={resolution}
        onChangeText={setResolution}
        keyboardType="numeric"
      />
      <Field label="Timezone" value={zone} onChangeText={setZone} />
      <Field
        label="Working weekdays (Monday=0, Sunday=6)"
        value={days}
        onChangeText={setDays}
      />
      <Field
        label="Opening hour (0–23)"
        value={start}
        onChangeText={setStart}
      />
      <Field label="Closing hour (1–24)" value={end} onChangeText={setEnd} />
      <Field
        label="Escalate after breach (minutes)"
        value={escalation}
        onChangeText={setEscalation}
      />
      <View style={s.row}>
        <Switch
          value={official}
          onValueChange={setOfficial}
          accessibilityLabel="Company-approved official SLA"
        />
        <Body>Company-approved official SLA</Body>
      </View>
      {Boolean(message) && <Body>{message}</Body>}
      <Button
        title="Save SLA rule"
        onPress={() => void save()}
        disabled={!response || !resolution}
      />
    </Card>
  );
}
