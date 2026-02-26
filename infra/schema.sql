-- FMRO initial schema (PostgreSQL)

create table if not exists company (
  id bigserial primary key,
  name text not null unique,
  official_site text,
  careers_url text,
  active boolean not null default true,
  created_at text not null,
  updated_at text not null
);

create table if not exists crawl_source (
  id bigserial primary key,
  company_id bigint not null references company(id) on delete cascade,
  url text not null,
  parser_type text not null default 'generic',
  cadence text not null default 'daily',
  last_crawled_at text,
  active boolean not null default true,
  created_at text not null
);

create table if not exists job_posting (
  id bigserial primary key,
  company_id bigint not null references company(id) on delete cascade,
  title text not null,
  location text,
  source_url text,
  apply_url text,
  deadline_at text,
  status text not null default 'open',
  source_platform text,
  first_seen_at text not null,
  last_seen_at text not null
);

create table if not exists review_queue (
  id bigserial primary key,
  source_type text not null,
  payload text not null,
  confidence double precision,
  status text not null default 'pending',
  created_at text not null,
  reviewed_at text
);

create table if not exists application (
  id bigserial primary key,
  job_posting_id bigint references job_posting(id) on delete set null,
  company_name text not null,
  role text not null,
  applied_at text,
  deadline_at text,
  stage text not null default 'applied',
  notes text,
  created_at text not null,
  updated_at text not null
);

create table if not exists interview_round (
  id bigserial primary key,
  application_id bigint not null references application(id) on delete cascade,
  round_no int not null,
  scheduled_at text,
  outcome text,
  note text,
  created_at text not null
);

create index if not exists idx_job_posting_company on job_posting(company_id);
create index if not exists idx_application_stage on application(stage);
create index if not exists idx_review_queue_status on review_queue(status);
