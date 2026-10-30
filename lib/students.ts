import { and, asc, desc, eq, ilike, or, type SQL } from "drizzle-orm";
import { students } from "../db/schema.js";

const SORTS: Record<string, SQL[]> = {
  name: [asc(students.name)],
  "-name": [desc(students.name)],
  enrollment_date: [asc(students.enrollmentDate)],
  "-enrollment_date": [desc(students.enrollmentDate)],
  course: [asc(students.course)],
};

export function studentFilters(params: URLSearchParams) {
  const conditions: SQL[] = [];
  const query = (params.get("q") ?? "").trim();
  const status = params.get("status") ?? "";
  const course = (params.get("course") ?? "").trim();

  if (query) {
    const pattern = `%${query.replace(/[\\%_]/g, (c) => `\\${c}`)}%`;
    conditions.push(
      or(ilike(students.name, pattern), ilike(students.email, pattern), ilike(students.course, pattern))!,
    );
  }
  if (status === "active") conditions.push(eq(students.isActive, true));
  else if (status === "inactive") conditions.push(eq(students.isActive, false));
  if (course) conditions.push(eq(students.course, course));

  const sort = SORTS[params.get("sort") ?? "name"] ?? SORTS.name;
  return {
    where: conditions.length ? and(...conditions) : undefined,
    orderBy: [...sort, asc(students.id)],
  };
}

export interface StudentInput {
  name: string;
  email: string;
  phone: string;
  course: string;
  enrollmentDate: string;
  isActive: boolean;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateStudent(body: unknown): { data?: StudentInput; fields?: Record<string, string> } {
  const input = (body ?? {}) as Record<string, unknown>;
  const str = (key: string) => (typeof input[key] === "string" ? (input[key] as string).trim() : "");
  const data: StudentInput = {
    name: str("name"),
    email: str("email"),
    phone: str("phone"),
    course: str("course"),
    enrollmentDate: str("enrollmentDate"),
    isActive: input.isActive !== false,
  };
  const fields: Record<string, string> = {};

  if (!data.name) fields.name = "This field is required.";
  else if (data.name.length > 120) fields.name = "Ensure this value has at most 120 characters.";
  if (!data.email) fields.email = "This field is required.";
  else if (!EMAIL_RE.test(data.email) || data.email.length > 254) fields.email = "Enter a valid email address.";
  if (data.phone.length > 30) fields.phone = "Ensure this value has at most 30 characters.";
  if (!data.course) fields.course = "This field is required.";
  else if (data.course.length > 120) fields.course = "Ensure this value has at most 120 characters.";
  if (!data.enrollmentDate) fields.enrollmentDate = "This field is required.";
  else if (!/^\d{4}-\d{2}-\d{2}$/.test(data.enrollmentDate) || Number.isNaN(Date.parse(data.enrollmentDate)))
    fields.enrollmentDate = "Enter a valid date.";

  return Object.keys(fields).length ? { fields } : { data };
}

export function isUniqueViolation(err: unknown): boolean {
  let current = err as { code?: string; cause?: unknown } | undefined;
  while (current) {
    if (current.code === "23505") return true;
    current = current.cause as typeof current;
  }
  return false;
}
