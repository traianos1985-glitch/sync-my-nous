import { createFileRoute } from "@tanstack/react-router";
import { Index } from "@/components/nous/index-page";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "NOUS AI OS — Αυτόνομος AI agent σε Python & Flask" },
      {
        name: "description",
        content:
          "NOUS AI OS: αυτόνομο AI λειτουργικό σύστημα με chat brain, μνήμη, missions, self-healing, app builder και Android operator — όλα σε ένα service.",
      },
      { property: "og:title", content: "NOUS AI OS — Αυτόνομος AI agent" },
      {
        property: "og:description",
        content:
          "Chat brain, μνήμη, missions, self-healing, app builder, browser & Android operators και document intelligence σε ένα service.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});
