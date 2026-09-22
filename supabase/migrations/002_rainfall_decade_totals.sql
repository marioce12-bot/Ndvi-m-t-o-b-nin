create table if not exists public.agro_rain_decades (
  id text primary key,
  year integer not null,
  month integer not null,
  decade integer not null,
  station_id text not null references public.agro_stations(id) on delete cascade,
  hauteur_mm double precision,
  year_total_mm double precision,
  season_total_mm double precision,
  unique (station_id, year, month, decade)
);

alter table public.agro_rain_decades
  add column if not exists year_total_mm double precision,
  add column if not exists season_total_mm double precision;

create index if not exists rain_decade_period_idx
  on public.agro_rain_decades(year, month, decade, station_id);

alter table public.agro_rain_decades enable row level security;
