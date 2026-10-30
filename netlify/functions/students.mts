import type { Config, Context } from "@netlify/functions";
import { count, eq } from "drizzle-orm";
import { db } from "../../db/index.js";
import { students } from "../../db/schema.js";
import { error, json, requireStaff } from "../../lib/auth.js";
import { isUniqueViolation, studentFilters, validateStudent } from "../../lib/students.js";

const PAGE_SIZE = 10;
const DUPLICATE_EMAIL = { email: "A student with this email already exists." };

async function readBody(req: Request) {
  try {
    return await req.json();
  } catch {
    return null;
  }
}

export default async (req: Request, context: Context) => {
  const auth = await requireStaff(req);
  if (auth instanceof Response) return auth;

  const rawId = context.params.id;
  if (rawId === undefined) {
    if (req.method === "GET") {
      const params = new URL(req.url).searchParams;
      const { where, orderBy } = studentFilters(params);
      const [{ total }] = await db.select({ total: count() }).from(students).where(where);
      const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
      const page = Math.min(Math.max(1, Number.parseInt(params.get("page") ?? "1", 10) || 1), pages);
      const [rows, courses] = await Promise.all([
        db.select().from(students).where(where).orderBy(...orderBy).limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE),
        db.selectDistinct({ course: students.course }).from(students).orderBy(students.course),
      ]);
      return json({ students: rows, total, page, pages, courses: courses.map((c) => c.course) });
    }

    if (req.method === "POST") {
      const { data, fields } = validateStudent(await readBody(req));
      if (!data) return error("Please correct the errors below.", 422, fields);
      try {
        const [created] = await db.insert(students).values(data).returning();
        return json(created, 201);
      } catch (err) {
        if (isUniqueViolation(err)) return error("Please correct the errors below.", 409, DUPLICATE_EMAIL);
        throw err;
      }
    }

    return error("Method not allowed", 405);
  }

  const id = Number.parseInt(rawId, 10);
  if (!Number.isInteger(id) || String(id) !== rawId) return error("Student not found.", 404);

  if (req.method === "GET") {
    const [student] = await db.select().from(students).where(eq(students.id, id));
    return student ? json(student) : error("Student not found.", 404);
  }

  if (req.method === "PUT") {
    const { data, fields } = validateStudent(await readBody(req));
    if (!data) return error("Please correct the errors below.", 422, fields);
    try {
      const [updated] = await db
        .update(students)
        .set({ ...data, updatedAt: new Date() })
        .where(eq(students.id, id))
        .returning();
      return updated ? json(updated) : error("Student not found.", 404);
    } catch (err) {
      if (isUniqueViolation(err)) return error("Please correct the errors below.", 409, DUPLICATE_EMAIL);
      throw err;
    }
  }

  if (req.method === "DELETE") {
    const deleted = await db.delete(students).where(eq(students.id, id)).returning({ id: students.id });
    return deleted.length ? new Response(null, { status: 204 }) : error("Student not found.", 404);
  }

  return error("Method not allowed", 405);
};

export const config: Config = {
  path: ["/api/students", "/api/students/:id"],
};
