-- Grand Line Draft 5.0 online lobby storage (Supabase PostgreSQL)
-- Run this once in Supabase SQL Editor.
-- The Streamlit server uses the service_role key from secrets.toml; never put that key in browser code.

create table if not exists public.gld_online_rooms (
    room_code text primary key check (room_code ~ '^[A-Z0-9]{8}$'),
    revision bigint not null default 0 check (revision >= 0),
    variant text not null check (variant in ('classic', 'ranking')),
    host_name text not null,
    guest_name text,
    status text not null default 'waiting' check (status in ('waiting', 'active', 'finished')),
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    expires_at timestamptz not null default (now() + interval '24 hours')
);

create index if not exists gld_online_rooms_expires_at_idx
    on public.gld_online_rooms (expires_at);

alter table public.gld_online_rooms enable row level security;

-- No anon/authenticated policies are created. The app talks to this table only
-- from the Streamlit server using the Supabase service_role key.
revoke all on table public.gld_online_rooms from anon, authenticated;
grant select, insert, update, delete on table public.gld_online_rooms to service_role;

-- Optional manual cleanup of expired lobbies:
-- delete from public.gld_online_rooms where expires_at < now();
