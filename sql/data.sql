-- perfiles de usuario (puede contener el id anon de supabase o un device_id propio)
create table profiles (
  id uuid primary key default gen_random_uuid(),
  supabase_user_id text, -- opcional si usas auth anon
  device_id text unique,
  username text,
  avatar_url text,
  created_at timestamptz default now()
);

-- mensajes de chat
create table messages (
  id bigserial primary key,
  room_id text default 'global',
  sender_profile_id uuid references profiles(id),
  sender_device_id text,
  sender_display text,
  content text,
  metadata jsonb,
  created_at timestamptz default now()
);

-- index para lecturas por room
create index on messages (room_id, created_at);
