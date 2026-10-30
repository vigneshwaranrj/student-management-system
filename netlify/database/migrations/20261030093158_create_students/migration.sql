CREATE TABLE "students" (
	"id" serial PRIMARY KEY,
	"name" text NOT NULL,
	"email" text NOT NULL UNIQUE,
	"phone" text DEFAULT '' NOT NULL,
	"course" text NOT NULL,
	"is_active" boolean DEFAULT true NOT NULL,
	"enrollment_date" date DEFAULT now() NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE INDEX "students_name_idx" ON "students" ("name");--> statement-breakpoint
CREATE INDEX "students_course_idx" ON "students" ("course");