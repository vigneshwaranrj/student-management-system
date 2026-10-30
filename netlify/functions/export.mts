import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { students } from "../../db/schema.js";
import { requireStaff } from "../../lib/auth.js";
import { studentFilters } from "../../lib/students.js";

function csvCell(value: string) {
  // Prefix formula-like values so spreadsheets don't execute them.
  const safe = /^[=+\-@\t\r]/.test(value) ? `'${value}` : value;
  return /[",\r\n]/.test(safe) ? `"${safe.replace(/"/g, '""')}"` : safe;
}

export default async (req: Request) => {
  const auth = await requireStaff(req);
  if (auth instanceof Response) return auth;

  const { where, orderBy } = studentFilters(new URL(req.url).searchParams);
  const rows = await db.select().from(students).where(where).orderBy(...orderBy);

  const lines = [["Name", "Email", "Phone", "Course", "Status", "Enrollment date"]];
  for (const s of rows) {
    lines.push([s.name, s.email, s.phone, s.course, s.isActive ? "Active" : "Inactive", s.enrollmentDate]);
  }
  const body = "﻿" + lines.map((line) => line.map(csvCell).join(",")).join("\r\n") + "\r\n";

  return new Response(body, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": 'attachment; filename="students.csv"',
      "Cache-Control": "private, no-store",
    },
  });
};

export const config: Config = {
  path: "/api/export",
};
