const blockedExtensions = new Set([
  ".exe",
  ".dll",
  ".scr",
  ".bat",
  ".cmd",
  ".com",
  ".msi",
  ".jar",
  ".js",
  ".vbs",
  ".ps1",
  ".sh",
]);

const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;

export function validateUploadMetadata(fileName: string, size: number, contentType: string) {
  const normalizedName = fileName.trim().toLowerCase();
  const extension = normalizedName.includes(".")
    ? normalizedName.slice(normalizedName.lastIndexOf("."))
    : "";
  if (!normalizedName || normalizedName.length > 180)
    return { ok: false as const, reason: "invalid_filename" };
  if (
    normalizedName.includes("..") ||
    normalizedName.includes(String.fromCharCode(0)) ||
    normalizedName.includes("/") ||
    normalizedName.includes("\\")
  )
    return { ok: false as const, reason: "unsafe_filename" };
  if (blockedExtensions.has(extension))
    return { ok: false as const, reason: "executable_upload_blocked" };
  if (!Number.isSafeInteger(size) || size <= 0 || size > MAX_UPLOAD_BYTES)
    return { ok: false as const, reason: "file_size_rejected" };
  if (!/^[\w.+-]+\/[\w.+-]+$/.test(contentType))
    return { ok: false as const, reason: "invalid_content_type" };
  return { ok: true as const };
}

export function sanitizeTextForPrompt(input: string, maxLength = 12_000) {
  return Array.from(input)
    .filter((character) => {
      const code = character.charCodeAt(0);
      return code >= 0x20 && code !== 0x7f;
    })
    .join("")
    .slice(0, maxLength);
}
