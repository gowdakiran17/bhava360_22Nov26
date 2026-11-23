CREATE TYPE "public"."approval_state" AS ENUM('draft', 'in_review', 'validated', 'approved');--> statement-breakpoint
CREATE TYPE "public"."identity_channel" AS ENUM('phone', 'email');--> statement-breakpoint
CREATE TYPE "public"."app_environment" AS ENUM('development', 'staging', 'production');--> statement-breakpoint
CREATE TYPE "public"."birth_precision" AS ENUM('known', 'approximate', 'unknown');--> statement-breakpoint
CREATE TYPE "public"."data_request_kind" AS ENUM('export', 'delete');--> statement-breakpoint
CREATE TYPE "public"."staff_role" AS ENUM('owner', 'admin', 'astrologer-reviewer', 'native-language reviewer', 'tester', 'support');--> statement-breakpoint
CREATE TABLE "ai_generations" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"provider" text NOT NULL,
	"model" text NOT NULL,
	"template_version" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ask_messages" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"thread_id" uuid NOT NULL,
	"speaker" text NOT NULL,
	"body" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ask_threads" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "audit_log" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"actor_id" uuid NOT NULL,
	"role" "staff_role" NOT NULL,
	"action" text NOT NULL,
	"target_type" text NOT NULL,
	"opaque_target_id" uuid NOT NULL,
	"reason" text NOT NULL,
	"previous_value" jsonb,
	"new_value" jsonb,
	"ip_digest" text NOT NULL,
	"user_agent" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "check_requests" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"tool_type" text NOT NULL,
	"saved" boolean DEFAULT false NOT NULL,
	"inputs" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "explicit_save" CHECK ("check_requests"."saved" or "check_requests"."inputs" is null)
);
--> statement-breakpoint
CREATE TABLE "computation_cache" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"convention" text NOT NULL,
	"module" text NOT NULL,
	"cache_key" text NOT NULL,
	"facts" jsonb NOT NULL,
	"expires_at" timestamp with time zone NOT NULL,
	CONSTRAINT "computation_cache_cache_key_unique" UNIQUE("cache_key")
);
--> statement-breakpoint
CREATE TABLE "consents" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"purpose" text NOT NULL,
	"version" text NOT NULL,
	"required" boolean NOT NULL,
	"granted" boolean NOT NULL,
	"recorded_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "data_requests" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"kind" "data_request_kind" NOT NULL,
	"status" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"due_at" timestamp with time zone NOT NULL
);
--> statement-breakpoint
CREATE TABLE "entitlements" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"capability" text NOT NULL,
	"expires_at" timestamp with time zone,
	CONSTRAINT "entitlements_user_id_capability_unique" UNIQUE("user_id","capability")
);
--> statement-breakpoint
CREATE TABLE "explanations_cache" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"entity" text NOT NULL,
	"fact_hash" text NOT NULL,
	"language" text NOT NULL,
	"explanation" text NOT NULL,
	CONSTRAINT "explanations_cache_profile_id_entity_fact_hash_language_unique" UNIQUE("profile_id","entity","fact_hash","language")
);
--> statement-breakpoint
CREATE TABLE "feature_flags" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"environment" "app_environment" NOT NULL,
	"key" text NOT NULL,
	"value" jsonb NOT NULL,
	CONSTRAINT "feature_flags_environment_key_unique" UNIQUE("environment","key")
);
--> statement-breakpoint
CREATE TABLE "feedback" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"category" text NOT NULL,
	"body" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "identities" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"kind" "identity_channel" NOT NULL,
	"identifier_digest" text NOT NULL,
	CONSTRAINT "identities_kind_identifier_digest_unique" UNIQUE("kind","identifier_digest")
);
--> statement-breakpoint
CREATE TABLE "inspector_access_log" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"actor_id" uuid NOT NULL,
	"opaque_profile_id" uuid NOT NULL,
	"reason" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "kb_entry_reviews" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"entry_id" uuid NOT NULL,
	"actor_id" uuid NOT NULL,
	"from_state" "approval_state" NOT NULL,
	"to_state" "approval_state" NOT NULL,
	"notes" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "matches" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"first_profile_id" uuid NOT NULL,
	"second_profile_id" uuid NOT NULL,
	"method" text NOT NULL
);
--> statement-breakpoint
CREATE TABLE "muhurta_searches" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"activity" text NOT NULL,
	"start_date" date NOT NULL,
	"end_date" date NOT NULL,
	"place_id" uuid NOT NULL,
	CONSTRAINT "search_date_range" CHECK ("muhurta_searches"."end_date" >= "muhurta_searches"."start_date")
);
--> statement-breakpoint
CREATE TABLE "native_review_items" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"entry_id" uuid,
	"i18n_key" text,
	"locale" text NOT NULL,
	"state" text NOT NULL,
	"proposal" text NOT NULL,
	"reviewer_id" uuid,
	CONSTRAINT "one_target" CHECK (num_nonnulls("native_review_items"."entry_id", "native_review_items"."i18n_key") = 1)
);
--> statement-breakpoint
CREATE TABLE "notification_inbox" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"notification_id" uuid NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"read_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "notification_preferences" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"channel" text NOT NULL,
	"enabled" boolean NOT NULL,
	CONSTRAINT "notification_preferences_user_id_channel_unique" UNIQUE("user_id","channel")
);
--> statement-breakpoint
CREATE TABLE "notifications" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"template_key" text NOT NULL,
	CONSTRAINT "notifications_template_key_unique" UNIQUE("template_key")
);
--> statement-breakpoint
CREATE TABLE "numerology_names" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"candidate_name" text NOT NULL,
	"system" text NOT NULL
);
--> statement-breakpoint
CREATE TABLE "otp_challenges" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"identity_id" uuid NOT NULL,
	"code_hash" text NOT NULL,
	"ip_digest" text NOT NULL,
	"expires_at" timestamp with time zone NOT NULL,
	"attempts" integer DEFAULT 0 NOT NULL,
	"consumed_at" timestamp with time zone,
	CONSTRAINT "attempts_nonnegative" CHECK ("otp_challenges"."attempts" >= 0)
);
--> statement-breakpoint
CREATE TABLE "palm_sessions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"keep_opt_in" boolean DEFAULT false NOT NULL,
	"storage_pointer" text,
	"delete_at" timestamp with time zone,
	CONSTRAINT "opted_in_storage" CHECK (("palm_sessions"."storage_pointer" is null and "palm_sessions"."delete_at" is null) or ("palm_sessions"."keep_opt_in" and "palm_sessions"."storage_pointer" is not null and "palm_sessions"."delete_at" is not null))
);
--> statement-breakpoint
CREATE TABLE "payments" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"order_id" uuid NOT NULL,
	"provider_ref" text NOT NULL,
	"status" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "payments_provider_ref_unique" UNIQUE("provider_ref")
);
--> statement-breakpoint
CREATE TABLE "places" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"city" text NOT NULL,
	"aliases" text[] NOT NULL,
	"name_kn" text NOT NULL,
	"name_hi" text NOT NULL,
	"native_review" text NOT NULL,
	"latitude" double precision NOT NULL,
	"longitude" double precision NOT NULL,
	"iana_zone" text NOT NULL,
	CONSTRAINT "places_city_unique" UNIQUE("city"),
	CONSTRAINT "city_coordinates" CHECK ("places"."latitude" between -90 and 90 and "places"."longitude" between -180 and 180)
);
--> statement-breakpoint
CREATE TABLE "profiles" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"display_name" text NOT NULL,
	"birth_instant" timestamp with time zone NOT NULL,
	"local_date" date NOT NULL,
	"local_time" time NOT NULL,
	"iana_zone" text NOT NULL,
	"place_id" uuid NOT NULL,
	"time_precision" "birth_precision" NOT NULL,
	"relation" text NOT NULL,
	"gender" text,
	CONSTRAINT "profiles_user_id_id_unique" UNIQUE("user_id","id"),
	CONSTRAINT "unknown_noon" CHECK ("profiles"."time_precision" <> 'unknown' or "profiles"."local_time" = time '12:00')
);
--> statement-breakpoint
CREATE TABLE "readings" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"module" text NOT NULL,
	"period" text NOT NULL,
	"language" text NOT NULL,
	"fact_hash" text NOT NULL,
	"body" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "report_books" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"order_id" uuid NOT NULL,
	"storage_pointer" text NOT NULL,
	"language" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "report_jobs" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"order_id" uuid NOT NULL,
	"status" text NOT NULL,
	"attempts" integer DEFAULT 0 NOT NULL,
	"available_at" timestamp with time zone DEFAULT now() NOT NULL,
	"lease_until" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "report_orders" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"report_id" uuid NOT NULL,
	"status" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "reports" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"catalogue_key" text NOT NULL,
	"price_minor" integer NOT NULL,
	"currency" text NOT NULL,
	CONSTRAINT "reports_catalogue_key_unique" UNIQUE("catalogue_key"),
	CONSTRAINT "price_nonnegative" CHECK ("reports"."price_minor" >= 0)
);
--> statement-breakpoint
CREATE TABLE "rule_catalogue" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"rule_key" text NOT NULL,
	"source_path" text NOT NULL,
	"state" "approval_state" NOT NULL,
	CONSTRAINT "rule_catalogue_rule_key_unique" UNIQUE("rule_key"),
	CONSTRAINT "dotted_rule_key" CHECK (position('.' in "rule_catalogue"."rule_key") > 1)
);
--> statement-breakpoint
CREATE TABLE "sessions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"token_hash" text NOT NULL,
	"expires_at" timestamp with time zone NOT NULL,
	"revoked_at" timestamp with time zone,
	CONSTRAINT "sessions_token_hash_unique" UNIQUE("token_hash")
);
--> statement-breakpoint
CREATE TABLE "staff_ip_allowlist" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"staff_id" uuid NOT NULL,
	"network" "cidr" NOT NULL
);
--> statement-breakpoint
CREATE TABLE "staff_mfa_devices" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"staff_id" uuid NOT NULL,
	"secret_ciphertext" text NOT NULL,
	"key_version" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "staff_recovery_codes" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"staff_id" uuid NOT NULL,
	"code_hash" text NOT NULL,
	"used_at" timestamp with time zone,
	CONSTRAINT "staff_recovery_codes_code_hash_unique" UNIQUE("code_hash")
);
--> statement-breakpoint
CREATE TABLE "staff_sessions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"staff_id" uuid NOT NULL,
	"token_hash" text NOT NULL,
	"expires_at" timestamp with time zone NOT NULL,
	"revoked_at" timestamp with time zone,
	CONSTRAINT "staff_sessions_token_hash_unique" UNIQUE("token_hash")
);
--> statement-breakpoint
CREATE TABLE "staff_users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"email" text NOT NULL,
	"role" "staff_role" NOT NULL,
	"expires_at" timestamp with time zone,
	CONSTRAINT "staff_users_email_unique" UNIQUE("email")
);
--> statement-breakpoint
CREATE TABLE "subscriptions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"provider_ref" text NOT NULL,
	"plan" text NOT NULL,
	"expires_at" timestamp with time zone NOT NULL,
	CONSTRAINT "subscriptions_provider_ref_unique" UNIQUE("provider_ref")
);
--> statement-breakpoint
CREATE TABLE "tarot_draws" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"profile_id" uuid NOT NULL,
	"spread" text NOT NULL,
	"card_ids" text[] NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "tarot_journal" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"draw_id" uuid NOT NULL,
	"note" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"deactivated_at" timestamp with time zone,
	"delete_by" timestamp with time zone,
	CONSTRAINT "delete_window" CHECK (("users"."deactivated_at" is null and "users"."delete_by" is null) or ("users"."deactivated_at" is not null and "users"."delete_by" is not null and "users"."delete_by" between "users"."deactivated_at" and "users"."deactivated_at" + interval '30 days'))
);
--> statement-breakpoint
ALTER TABLE "ai_generations" ADD CONSTRAINT "ai_generations_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "ask_messages" ADD CONSTRAINT "ask_messages_thread_id_ask_threads_id_fk" FOREIGN KEY ("thread_id") REFERENCES "public"."ask_threads"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "ask_threads" ADD CONSTRAINT "ask_threads_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "check_requests" ADD CONSTRAINT "check_requests_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "computation_cache" ADD CONSTRAINT "computation_cache_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "consents" ADD CONSTRAINT "consents_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "data_requests" ADD CONSTRAINT "data_requests_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "entitlements" ADD CONSTRAINT "entitlements_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "explanations_cache" ADD CONSTRAINT "explanations_cache_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "feedback" ADD CONSTRAINT "feedback_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "identities" ADD CONSTRAINT "identities_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "inspector_access_log" ADD CONSTRAINT "inspector_access_log_actor_id_staff_users_id_fk" FOREIGN KEY ("actor_id") REFERENCES "public"."staff_users"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "kb_entry_reviews" ADD CONSTRAINT "kb_entry_reviews_entry_id_rule_catalogue_id_fk" FOREIGN KEY ("entry_id") REFERENCES "public"."rule_catalogue"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "kb_entry_reviews" ADD CONSTRAINT "kb_entry_reviews_actor_id_staff_users_id_fk" FOREIGN KEY ("actor_id") REFERENCES "public"."staff_users"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "matches" ADD CONSTRAINT "matches_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "matches" ADD CONSTRAINT "matches_user_id_first_profile_id_profiles_user_id_id_fk" FOREIGN KEY ("user_id","first_profile_id") REFERENCES "public"."profiles"("user_id","id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "matches" ADD CONSTRAINT "matches_user_id_second_profile_id_profiles_user_id_id_fk" FOREIGN KEY ("user_id","second_profile_id") REFERENCES "public"."profiles"("user_id","id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "muhurta_searches" ADD CONSTRAINT "muhurta_searches_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "muhurta_searches" ADD CONSTRAINT "muhurta_searches_place_id_places_id_fk" FOREIGN KEY ("place_id") REFERENCES "public"."places"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "native_review_items" ADD CONSTRAINT "native_review_items_entry_id_rule_catalogue_id_fk" FOREIGN KEY ("entry_id") REFERENCES "public"."rule_catalogue"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "native_review_items" ADD CONSTRAINT "native_review_items_reviewer_id_staff_users_id_fk" FOREIGN KEY ("reviewer_id") REFERENCES "public"."staff_users"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "notification_inbox" ADD CONSTRAINT "notification_inbox_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "notification_inbox" ADD CONSTRAINT "notification_inbox_notification_id_notifications_id_fk" FOREIGN KEY ("notification_id") REFERENCES "public"."notifications"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "notification_preferences" ADD CONSTRAINT "notification_preferences_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "numerology_names" ADD CONSTRAINT "numerology_names_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "otp_challenges" ADD CONSTRAINT "otp_challenges_identity_id_identities_id_fk" FOREIGN KEY ("identity_id") REFERENCES "public"."identities"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "palm_sessions" ADD CONSTRAINT "palm_sessions_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "payments" ADD CONSTRAINT "payments_order_id_report_orders_id_fk" FOREIGN KEY ("order_id") REFERENCES "public"."report_orders"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_place_id_places_id_fk" FOREIGN KEY ("place_id") REFERENCES "public"."places"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "readings" ADD CONSTRAINT "readings_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "report_books" ADD CONSTRAINT "report_books_order_id_report_orders_id_fk" FOREIGN KEY ("order_id") REFERENCES "public"."report_orders"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "report_jobs" ADD CONSTRAINT "report_jobs_order_id_report_orders_id_fk" FOREIGN KEY ("order_id") REFERENCES "public"."report_orders"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "report_orders" ADD CONSTRAINT "report_orders_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "report_orders" ADD CONSTRAINT "report_orders_report_id_reports_id_fk" FOREIGN KEY ("report_id") REFERENCES "public"."reports"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "sessions" ADD CONSTRAINT "sessions_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "staff_ip_allowlist" ADD CONSTRAINT "staff_ip_allowlist_staff_id_staff_users_id_fk" FOREIGN KEY ("staff_id") REFERENCES "public"."staff_users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "staff_mfa_devices" ADD CONSTRAINT "staff_mfa_devices_staff_id_staff_users_id_fk" FOREIGN KEY ("staff_id") REFERENCES "public"."staff_users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "staff_recovery_codes" ADD CONSTRAINT "staff_recovery_codes_staff_id_staff_users_id_fk" FOREIGN KEY ("staff_id") REFERENCES "public"."staff_users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "staff_sessions" ADD CONSTRAINT "staff_sessions_staff_id_staff_users_id_fk" FOREIGN KEY ("staff_id") REFERENCES "public"."staff_users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "subscriptions" ADD CONSTRAINT "subscriptions_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "tarot_draws" ADD CONSTRAINT "tarot_draws_profile_id_profiles_id_fk" FOREIGN KEY ("profile_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "tarot_journal" ADD CONSTRAINT "tarot_journal_draw_id_tarot_draws_id_fk" FOREIGN KEY ("draw_id") REFERENCES "public"."tarot_draws"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "ai_generations_profile_id_index" ON "ai_generations" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "ask_messages_thread_id_index" ON "ask_messages" USING btree ("thread_id");--> statement-breakpoint
CREATE INDEX "ask_threads_profile_id_index" ON "ask_threads" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "audit_log_opaque_target_id_created_at_index" ON "audit_log" USING btree ("opaque_target_id","created_at");--> statement-breakpoint
CREATE INDEX "check_requests_profile_id_index" ON "check_requests" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "computation_cache_profile_id_index" ON "computation_cache" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "consents_user_id_index" ON "consents" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "data_requests_user_id_index" ON "data_requests" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "entitlements_user_id_index" ON "entitlements" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "explanations_cache_profile_id_index" ON "explanations_cache" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "feedback_user_id_index" ON "feedback" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "identities_user_id_index" ON "identities" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "inspector_access_log_actor_id_index" ON "inspector_access_log" USING btree ("actor_id");--> statement-breakpoint
CREATE INDEX "kb_entry_reviews_entry_id_index" ON "kb_entry_reviews" USING btree ("entry_id");--> statement-breakpoint
CREATE INDEX "kb_entry_reviews_actor_id_index" ON "kb_entry_reviews" USING btree ("actor_id");--> statement-breakpoint
CREATE INDEX "matches_user_id_index" ON "matches" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "muhurta_searches_profile_id_index" ON "muhurta_searches" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "muhurta_searches_place_id_index" ON "muhurta_searches" USING btree ("place_id");--> statement-breakpoint
CREATE INDEX "native_review_items_entry_id_index" ON "native_review_items" USING btree ("entry_id");--> statement-breakpoint
CREATE INDEX "native_review_items_reviewer_id_index" ON "native_review_items" USING btree ("reviewer_id");--> statement-breakpoint
CREATE INDEX "notification_inbox_user_id_index" ON "notification_inbox" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "notification_inbox_notification_id_index" ON "notification_inbox" USING btree ("notification_id");--> statement-breakpoint
CREATE INDEX "notification_preferences_user_id_index" ON "notification_preferences" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "numerology_names_profile_id_index" ON "numerology_names" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "otp_challenges_identity_id_index" ON "otp_challenges" USING btree ("identity_id");--> statement-breakpoint
CREATE INDEX "otp_challenges_expires_at_index" ON "otp_challenges" USING btree ("expires_at");--> statement-breakpoint
CREATE INDEX "palm_sessions_profile_id_index" ON "palm_sessions" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "payments_order_id_index" ON "payments" USING btree ("order_id");--> statement-breakpoint
CREATE INDEX "places_aliases_index" ON "places" USING gin ("aliases");--> statement-breakpoint
CREATE INDEX "profiles_user_id_index" ON "profiles" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "profiles_place_id_index" ON "profiles" USING btree ("place_id");--> statement-breakpoint
CREATE INDEX "readings_profile_id_index" ON "readings" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "report_books_order_id_index" ON "report_books" USING btree ("order_id");--> statement-breakpoint
CREATE INDEX "report_jobs_order_id_index" ON "report_jobs" USING btree ("order_id");--> statement-breakpoint
CREATE INDEX "report_jobs_status_available_at_index" ON "report_jobs" USING btree ("status","available_at");--> statement-breakpoint
CREATE INDEX "report_orders_profile_id_index" ON "report_orders" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "report_orders_report_id_index" ON "report_orders" USING btree ("report_id");--> statement-breakpoint
CREATE INDEX "sessions_user_id_index" ON "sessions" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "staff_ip_allowlist_staff_id_index" ON "staff_ip_allowlist" USING btree ("staff_id");--> statement-breakpoint
CREATE INDEX "staff_mfa_devices_staff_id_index" ON "staff_mfa_devices" USING btree ("staff_id");--> statement-breakpoint
CREATE INDEX "staff_recovery_codes_staff_id_index" ON "staff_recovery_codes" USING btree ("staff_id");--> statement-breakpoint
CREATE INDEX "staff_sessions_staff_id_index" ON "staff_sessions" USING btree ("staff_id");--> statement-breakpoint
CREATE INDEX "subscriptions_user_id_index" ON "subscriptions" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "tarot_draws_profile_id_index" ON "tarot_draws" USING btree ("profile_id");--> statement-breakpoint
CREATE INDEX "tarot_journal_draw_id_index" ON "tarot_journal" USING btree ("draw_id");
-- Preserve audit events even if an application path issues bulk SQL.
CREATE FUNCTION reject_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'audit_log is append-only';
END;
$$;
CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE OR TRUNCATE ON audit_log
FOR EACH STATEMENT EXECUTE FUNCTION reject_audit_mutation();

INSERT INTO feature_flags(environment, key, value)
SELECT env, setting.key, setting.value
FROM unnest(enum_range(NULL::app_environment)) AS env
CROSS JOIN jsonb_each('{"modern_outer":false,"vedic.houses":"whole-sign","western.houses":"Placidus","matching.default":"Ashtakoota","matching.porutham":true,"locale.en":true,"locale.kn":true,"locale.hi":true,"locale.te":false,"locale.ta":false,"locale.ml":false,"locale.es":false,"locale.fr":false,"module.vedic":true,"module.western":false,"module.numerology":true,"module.tarot":false,"module.palmistry":false,"module.lal-kitab":false,"module.vastu":false,"module.face":false}') AS setting;
