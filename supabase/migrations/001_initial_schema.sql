create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  created_at timestamptz not null default now()
);

create table if not exists public.jobs (
  id text primary key,
  owner_id uuid references auth.users(id) on delete set null,
  product text not null,
  pentade_id text not null,
  label text,
  email text,
  status text not null default 'pending',
  progress integer not null default 0,
  step text,
  image_url text,
  thumbnail_url text,
  error text,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);

create table if not exists public.pentade_catalog (
  product text primary key,
  pentades jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists public.agro_stations (
  id text primary key,
  name text not null,
  department text not null,
  locality text not null,
  principal boolean not null default false,
  etp_station_id text,
  longitude double precision,
  latitude double precision,
  created_at timestamptz not null default now()
);

create table if not exists public.agro_rain_daily (
  id text primary key,
  year integer not null,
  month integer not null,
  decade integer not null,
  station_id text not null references public.agro_stations(id) on delete cascade,
  jour integer not null,
  hauteur_mm double precision,
  unique (station_id, year, month, decade, jour)
);

create table if not exists public.agro_observations (
  id text primary key,
  year integer not null,
  month integer not null,
  decade integer not null,
  station_id text not null references public.agro_stations(id) on delete cascade,
  jour integer not null,
  pluie double precision,
  temp_min double precision,
  temp_max double precision,
  temp_10cm double precision,
  temp_50cm double precision,
  vent_moyen double precision,
  vent_max double precision,
  insolation double precision,
  humidite_min double precision,
  humidite_max double precision,
  tension_vapeur double precision,
  evapo_bac_a double precision,
  unique (station_id, year, month, decade, jour)
);

create table if not exists public.agro_ew_etp (
  id text primary key,
  year integer not null,
  month integer not null,
  decade integer not null,
  station_id text not null references public.agro_stations(id) on delete cascade,
  ew double precision,
  etp double precision,
  unique (station_id, year, month, decade)
);

create table if not exists public.rainfall_normals (
  station_id text not null,
  decade_code text not null,
  normal_decade double precision,
  normal_annual double precision,
  normal_season double precision,
  primary key (station_id, decade_code)
);

create index if not exists jobs_owner_status_idx on public.jobs(owner_id, status, completed_at desc);
create index if not exists rain_period_idx on public.agro_rain_daily(year, month, decade, station_id);
create index if not exists observations_period_idx on public.agro_observations(year, month, decade, station_id);
create index if not exists ew_etp_period_idx on public.agro_ew_etp(year, month, decade);

alter table public.profiles enable row level security;
alter table public.jobs enable row level security;
alter table public.agro_stations enable row level security;
alter table public.agro_rain_daily enable row level security;
alter table public.agro_observations enable row level security;
alter table public.agro_ew_etp enable row level security;
alter table public.pentade_catalog enable row level security;
alter table public.rainfall_normals enable row level security;

create policy "users read own jobs" on public.jobs for select using (auth.uid() = owner_id);
create policy "public read stations" on public.agro_stations for select using (true);
create policy "public read catalog" on public.pentade_catalog for select using (true);
