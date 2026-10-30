export const openApiDocument = {
  openapi: "3.1.0",
  info: { title: "Nous API", version: "1.0.0" },
  paths: {
    "/api/devices": {
      get: { summary: "List registered devices" },
      post: { summary: "Register or heartbeat a device" },
      patch: { summary: "Update device status" },
    },
    "/api/telemetry": {
      get: { summary: "Read operational telemetry" },
      post: { summary: "Record redacted telemetry" },
    },
    "/api/mobile/notify": { post: { summary: "Queue a mobile notification" } },
    "/api/capabilities": { get: { summary: "List runtime capabilities" } },
  },
} as const;
