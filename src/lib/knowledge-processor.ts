import { embedMany, gateway } from "ai";

const embeddingModel = gateway.embedding("google/gemini-embedding-2");

export async function embedKnowledgeChunks(contents: string[]) {
  if (!contents.length) return [];
  const result = await embedMany({ model: embeddingModel, values: contents, maxParallelCalls: 4 });
  return result.embeddings;
}

export function cosineSimilarity(left: number[], right: number[]) {
  let dot = 0;
  let leftMagnitude = 0;
  let rightMagnitude = 0;
  for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
    dot += left[index] * right[index];
    leftMagnitude += left[index] ** 2;
    rightMagnitude += right[index] ** 2;
  }
  return leftMagnitude && rightMagnitude ? dot / Math.sqrt(leftMagnitude * rightMagnitude) : 0;
}

export function buildSecurityLesson(input: {
  category: string;
  severity: string;
  title: string;
  lesson: string;
  remediation: string;
  sourceEvent: string;
}) {
  return {
    ...input,
    fingerprint: `${input.category}:${input.title}:${input.sourceEvent}`
      .toLowerCase()
      .replace(/[^a-z0-9:_-]+/g, "-"),
  };
}
