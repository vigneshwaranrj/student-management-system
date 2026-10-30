import type { Config } from "@netlify/functions";
import { asc, count, desc, eq } from "drizzle-orm";
import { db } from "../../db/index.js";
import { students } from "../../db/schema.js";
import { json, requireStaff } from "../../lib/auth.js";

export default async (req: Request) => {
  const auth = await requireStaff(req);
  if (auth instanceof Response) return auth;

  const [[totals], [active], recent, courseStats] = await Promise.all([
    db.select({ value: count() }).from(students),
    db.select({ value: count() }).from(students).where(eq(students.isActive, true)),
    db.select().from(students).orderBy(desc(students.createdAt), desc(students.id)).limit(5),
    db
      .select({ course: students.course, total: count() })
      .from(students)
      .groupBy(students.course)
      .orderBy(desc(count()), asc(students.course))
      .limit(5),
  ]);

  return json({
    totalStudents: totals.value,
    activeStudents: active.value,
    inactiveStudents: totals.value - active.value,
    recentStudents: recent,
    courseStats,
  });
};

export const config: Config = {
  path: "/api/overview",
};
