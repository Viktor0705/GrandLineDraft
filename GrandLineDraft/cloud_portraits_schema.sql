-- Grand Line Draft · private shared character portrait library
-- Run once in Supabase SQL Editor after the project exists.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'gld-character-portraits',
  'gld-character-portraits',
  false,
  12582912,
  array['image/jpeg']::text[]
)
on conflict (id) do update set
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create table if not exists public.gld_character_portraits (
  character_id integer primary key,
  character_name text not null,
  storage_path text not null unique,
  content_type text not null default 'image/jpeg' check (content_type = 'image/jpeg'),
  file_size bigint not null default 0 check (file_size >= 0),
  source text not null default 'upload',
  updated_at timestamptz not null default now()
);

alter table public.gld_character_portraits enable row level security;
revoke all on table public.gld_character_portraits from anon, authenticated;
grant select, insert, update, delete on table public.gld_character_portraits to service_role;

-- Deliberately no public/authenticated policies: the private bucket and metadata table
-- are accessed only by the Streamlit server using its server-side Supabase secret.
