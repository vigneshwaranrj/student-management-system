import { boolean, date, index, pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";

export const students = pgTable(
  "students",
  {
    id: serial().primaryKey(),
    name: text().notNull(),
    email: text().notNull().unique(),
    phone: text().notNull().default(""),
    course: text().notNull(),
    isActive: boolean("is_active").notNull().default(true),
    enrollmentDate: date("enrollment_date", { mode: "string" }).notNull().defaultNow(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [index("students_name_idx").on(table.name), index("students_course_idx").on(table.course)],
);

export type Student = typeof students.$inferSelect;
export type NewStudent = typeof students.$inferInsert;
