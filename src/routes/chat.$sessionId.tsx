import { createFileRoute } from "@tanstack/react-router";
import { ChatSessionPage } from "@/components/nous/chat-session-page";

export const Route = createFileRoute("/chat/$sessionId")({
  head: () => ({
    meta: [
      { title: "NOUS — Ιστορικό συνομιλίας" },
      {
        name: "description",
        content: "Προσωπική συνομιλία με τον NOUS και τοπικό ιστορικό μηνυμάτων.",
      },
      { property: "og:title", content: "NOUS — Συνομιλία" },
      { property: "og:description", content: "Το προσωπικό workspace συνομιλίας του NOUS." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ChatSessionPage,
});
