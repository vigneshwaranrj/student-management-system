import { getUser, type User } from "@netlify/identity";

export type Access = "admin" | "staff";

export interface StaffUser {
  user: User;
  access: Access;
}

export function accessFor(user: User): Access | null {
  if (user.appMetadata?.deactivated) return null;
  const roles = user.roles ?? [];
  if (roles.includes("admin")) return "admin";
  if (roles.includes("staff")) return "staff";
  return null;
}

export function json(data: unknown, status = 200) {
  return Response.json(data, { status });
}

export function error(message: string, status: number, fields?: Record<string, string>) {
  return json({ error: message, fields }, status);
}

/**
 * Resolves the signed-in Identity user and checks they have staff access.
 * Returns a Response when the request should be rejected.
 */
export async function requireStaff(req: Request, adminOnly = false): Promise<StaffUser | Response> {
  if (req.method !== "GET" && req.method !== "HEAD") {
    const origin = req.headers.get("origin");
    if (origin && origin !== new URL(req.url).origin) {
      return error("Cross-site request rejected.", 403);
    }
  }
  const user = await getUser();
  if (!user) return error("Please sign in to continue.", 401);
  const access = accessFor(user);
  if (!access) return error("Your account does not have access to Student Desk.", 403);
  if (adminOnly && access !== "admin") return error("Only administrators can manage the team.", 403);
  return { user, access };
}
