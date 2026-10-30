import type { Config } from "@netlify/functions";
import { getUser } from "@netlify/identity";
import { accessFor, error, json } from "../../lib/auth.js";

export default async () => {
  const user = await getUser();
  if (!user) return error("Please sign in to continue.", 401);
  return json({
    id: user.id,
    email: user.email,
    name: user.name ?? (user.userMetadata?.full_name as string | undefined) ?? null,
    access: accessFor(user),
  });
};

export const config: Config = {
  path: "/api/me",
};
