import React from 'react';

const CITY_NAMES = {
  santarosa: 'Santa Rosa',
  davis: 'Davis',
  bloomington: 'Bloomington',
  petaluma: 'Petaluma',
  toronto: 'Toronto',
  raleighdurham: 'Raleigh-Durham',
  montclair: 'Montclair',
  roanoke: 'Roanoke',
  matsu: 'MatSu',
};

export default function Header({ city }) {
  const cityName = CITY_NAMES[city] || city;

  return (
    <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-4 truncate">
      {cityName}
    </h1>
  );
}
