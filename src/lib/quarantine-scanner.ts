const SUSPICIOUS_MARKERS = [
  "<script",
  "javascript:",
  "powershell -enc",
  "cmd.exe /c",
  "base64 -d",
  "eval(",
];

export type ScanResult = {
  clean: boolean;
  reason: string;
  signatures: string[];
};

export function scanUpload(bytes: Uint8Array, contentType: string): ScanResult {
  const sample = new TextDecoder("latin1").decode(bytes.slice(0, 1_000_000)).toLowerCase();
  const signatures = SUSPICIOUS_MARKERS.filter((marker) => sample.includes(marker));
  if (signatures.length) {
    return { clean: false, reason: "Suspicious active-content marker detected", signatures };
  }
  if (contentType === "application/pdf" && !sample.includes("%pdf-")) {
    return { clean: false, reason: "PDF header is missing", signatures: ["invalid-pdf-header"] };
  }
  return { clean: true, reason: "No known active-content marker detected", signatures: [] };
}

export function shouldReleaseFromQuarantine(contentType: string, scan: ScanResult) {
  return scan.clean && !contentType.startsWith("image/");
}

// This is a defense-in-depth prefilter, not a replacement for ClamAV or a managed malware scanner.
