import { securityHeaders } from "./security";

export type SentinelFinding = {
  id: string;
  severity: "low" | "medium" | "high";
  title: string;
  detail: string;
  remediation: string;
};

export function runDefensiveSentinel(): {
  score: number;
  findings: SentinelFinding[];
  checkedAt: string;
} {
  const headers = securityHeaders();
  const csp =
    headers["Content-Security-Policy"] ?? headers["Content-Security-Policy-Report-Only"] ?? "";
  const findings: SentinelFinding[] = [];

  if (!csp.includes("object-src 'none'")) {
    findings.push({
      id: "csp-objects",
      severity: "high",
      title: "CSP object policy missing",
      detail: "Embedded plugin content is not explicitly disabled.",
      remediation: "Keep object-src 'none' in the deployed CSP.",
    });
  }
  if (!headers["Strict-Transport-Security"]) {
    findings.push({
      id: "hsts",
      severity: "medium",
      title: "Transport policy missing",
      detail: "HTTPS downgrade protection is not configured.",
      remediation: "Enable HSTS on production HTTPS.",
    });
  }
  if (!headers["X-Content-Type-Options"]) {
    findings.push({
      id: "mime-sniffing",
      severity: "medium",
      title: "MIME sniffing protection missing",
      detail: "Browsers may infer content types unexpectedly.",
      remediation: "Set X-Content-Type-Options to nosniff.",
    });
  }
  if (process.env["NODE_ENV"] === "production" && process.env["NOUS_ALERT_WEBHOOK_URL"]) {
    findings.push({
      id: "alerting-configured",
      severity: "low",
      title: "External alerting configured",
      detail: "Health failures can be routed to the configured webhook.",
      remediation: "Keep the webhook secret outside source control and rotate it periodically.",
    });
  }

  const highCount = findings.filter((finding) => finding.severity === "high").length;
  const mediumCount = findings.filter((finding) => finding.severity === "medium").length;
  return {
    score: Math.max(0, 100 - highCount * 35 - mediumCount * 15),
    findings,
    checkedAt: new Date().toISOString(),
  };
}
