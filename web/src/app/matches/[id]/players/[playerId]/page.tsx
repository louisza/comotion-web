import PlayerDetailClient from "./PlayerDetailClient";

export default async function PlayerDetailPage({
  params,
}: {
  params: Promise<{ id: string; playerId: string }>;
}) {
  const { id, playerId } = await params;
  return <PlayerDetailClient matchId={id} playerId={playerId} />;
}
