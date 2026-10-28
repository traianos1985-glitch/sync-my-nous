import { getRouteApi } from "@tanstack/react-router";
import { Dashboard } from "./dashboard-page";
const route = getRouteApi("/chat/$sessionId");
export function ChatSessionPage() {
  const { sessionId } = route.useParams();
  return <Dashboard key={sessionId} sessionId={sessionId} />;
}