import { claimNextJob, updateJob } from "./db/jobs";
import { NOUS_LIMITS } from "./platform-policy";
import { createExecutionReceipt } from "./execution-receipt";
import { persistExecutionReceipt } from "./receipt-service";

type MobilePayload = { deviceId: string; title: string; message: string; deliveryId: string };

export async function processNextMobileDelivery(userId: string) {
  const job = await claimNextJob(userId, "mobile_notification");
  if (!job) return { status: "empty" as const };
  const payload = job.payload as Partial<MobilePayload>;
  if (!payload.deviceId || !payload.title || !payload.message) {
    await updateJob(job.id, userId, "dead-letter", { error: "invalid_mobile_payload" });
    return { status: "dead-letter" as const, jobId: job.id };
  }

  const endpoint = process.env["FCM_DELIVERY_ENDPOINT"];
  const workerToken = process.env["NOUS_WORKER_TOKEN"];
  if (!endpoint || !workerToken) {
    const nextStatus = job.retryCount + 1 >= NOUS_LIMITS.maxJobRetries ? "dead-letter" : "failed";
    await updateJob(job.id, userId, nextStatus, { error: "fcm_provider_not_configured" });
    return { status: nextStatus as "failed" | "dead-letter", jobId: job.id };
  }

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${workerToken}`,
        "x-nous-delivery": payload.deliveryId ?? "",
      },
      body: JSON.stringify({
        deviceId: payload.deviceId,
        title: payload.title,
        message: payload.message,
        deliveryId: payload.deliveryId,
      }),
    });
    if (!response.ok) throw new Error(`provider_${response.status}`);
    await updateJob(job.id, userId, "completed", {
      delivered: true,
      deliveryId: payload.deliveryId,
    });
    const receipt = createExecutionReceipt({
      id: payload.deliveryId ?? job.id,
      operation: "fcm",
      startedAt: job.createdAt.toISOString(),
      evidence: { provider: "fcm-delivery", model: "push", researchUsed: false, persisted: true },
    });
    await persistExecutionReceipt(userId, receipt);
    return { status: "completed" as const, jobId: job.id, receipt };
  } catch {
    const nextStatus = job.retryCount + 1 >= NOUS_LIMITS.maxJobRetries ? "dead-letter" : "failed";
    await updateJob(job.id, userId, nextStatus, { error: "fcm_delivery_failed" });
    return { status: nextStatus as "failed" | "dead-letter", jobId: job.id };
  }
}
