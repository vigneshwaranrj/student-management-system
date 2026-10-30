import type { Config, Context } from "@netlify/functions";
import { admin, AuthError, type User } from "@netlify/identity";
import { accessFor, error, json, requireStaff } from "../../lib/auth.js";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function isTeamMember(user: User) {
  const roles = user.roles ?? [];
  return roles.includes("admin") || roles.includes("staff") || Boolean(user.appMetadata?.deactivated);
}

function serialize(user: User) {
  const access = accessFor(user);
  const isAdmin = (user.roles ?? []).includes("admin");
  return {
    id: user.id,
    email: user.email ?? "",
    name: (user.userMetadata?.full_name as string | undefined) ?? user.name ?? "",
    role: isAdmin ? "admin" : "staff",
    active: access !== null,
    lastSignInAt: user.lastSignInAt ?? null,
  };
}

async function listAllUsers() {
  const all: User[] = [];
  for (let page = 1; page <= 50; page++) {
    const batch = await admin.listUsers({ page, perPage: 100 });
    all.push(...batch);
    if (batch.length < 100) break;
  }
  return all;
}

export default async (req: Request, context: Context) => {
  const auth = await requireStaff(req, true);
  if (auth instanceof Response) return auth;

  const id = context.params.id;

  if (id === undefined && req.method === "GET") {
    const members = (await listAllUsers()).filter(isTeamMember).map(serialize);
    members.sort((a, b) => (a.role === b.role ? a.email.localeCompare(b.email) : a.role === "admin" ? -1 : 1));
    return json({ members, currentUserId: auth.user.id });
  }

  if (id === undefined && req.method === "POST") {
    const body = ((await req.json().catch(() => null)) ?? {}) as Record<string, unknown>;
    const str = (key: string) => (typeof body[key] === "string" ? (body[key] as string).trim() : "");
    const email = str("email").toLowerCase();
    const firstName = str("firstName");
    const lastName = str("lastName");
    const password = typeof body.password === "string" ? body.password : "";
    const fields: Record<string, string> = {};
    if (!EMAIL_RE.test(email)) fields.email = "Enter a valid email address.";
    if (firstName.length > 150) fields.firstName = "Ensure this value has at most 150 characters.";
    if (lastName.length > 150) fields.lastName = "Ensure this value has at most 150 characters.";
    if (password.length < 8) fields.password = "This password is too short. It must contain at least 8 characters.";
    if (password !== body.passwordConfirm) fields.passwordConfirm = "The two password fields didn’t match.";
    if (Object.keys(fields).length) return error("Please correct the errors below.", 422, fields);

    try {
      const created = await admin.createUser({
        email,
        password,
        data: {
          app_metadata: { roles: ["staff"] },
          user_metadata: { full_name: [firstName, lastName].filter(Boolean).join(" ") },
        },
      });
      return json(serialize(created), 201);
    } catch (err) {
      if (err instanceof AuthError && (err.status === 422 || err.status === 400)) {
        return error("Please correct the errors below.", 422, {
          email: "An account with this email already exists, or the details were rejected.",
        });
      }
      throw err;
    }
  }

  if (id !== undefined && req.method === "PATCH") {
    if (id === auth.user.id) return error("You can’t change your own account here.", 400);
    const target = await admin.getUser(id).catch(() => null);
    if (!target || !isTeamMember(target)) return error("Staff account not found.", 404);
    if ((target.roles ?? []).includes("admin")) return error("Administrator accounts are protected.", 400);

    const activate = !accessFor(target);
    const updated = await admin.updateUser(id, {
      app_metadata: {
        ...target.appMetadata,
        roles: ["staff"],
        deactivated: !activate,
      },
    });
    return json(serialize(updated));
  }

  return error("Method not allowed", 405);
};

export const config: Config = {
  path: ["/api/team", "/api/team/:id"],
};
