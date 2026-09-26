import { jsonb, pgTable, text, timestamp, integer } from "drizzle-orm/pg-core";

export const nousMissions = pgTable("nous_missions", {
  id: text("id").primaryKey(),
  userId: text("user_id").notNull(),
  title: text("title").notNull(),
  objective: text("objective").notNull(),
  status: text("status").notNull().default("queued"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export const nousMessages = pgTable("nous_messages", {
  id: text("id").primaryKey(),
  missionId: text("mission_id"),
  userId: text("user_id").notNull(),
  role: text("role").notNull(),
  content: text("content").notNull(),
  citations: jsonb("citations").notNull().default([]),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const nousApprovals = pgTable("nous_approvals", {
  id: text("id").primaryKey(),
  missionId: text("mission_id"),
  userId: text("user_id").notNull(),
  tool: text("tool").notNull(),
  input: jsonb("input").notNull().default({}),
  status: text("status").notNull().default("pending"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  resolvedAt: timestamp("resolved_at", { withTimezone: true }),
});

export const nousToolRuns = pgTable("nous_tool_runs", {
  id: text("id").primaryKey(),
  missionId: text("mission_id"),
  userId: text("user_id").notNull(),
  tool: text("tool").notNull(),
  status: text("status").notNull(),
  input: jsonb("input").notNull().default({}),
  output: jsonb("output").notNull().default({}),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const nousObservabilityEvents = pgTable("nous_observability_events", {
  id: text("id").primaryKey(),
  userId: text("user_id"),
  provider: text("provider"),
  model: text("model"),
  event: text("event").notNull(),
  latencyMs: integer("latency_ms"),
  metadata: jsonb("metadata").notNull().default({}),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});
