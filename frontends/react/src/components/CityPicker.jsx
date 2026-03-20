import React from 'react';
import { Button } from 'flowbite-react';

const CITIES = [
  { id: 'santarosa', name: 'Santa Rosa' },
  { id: 'petaluma', name: 'Petaluma' },
  { id: 'davis', name: 'Davis' },
  { id: 'bloomington', name: 'Bloomington' },
  { id: 'toronto', name: 'Toronto' },
  { id: 'raleighdurham', name: 'Raleigh-Durham' },
  { id: 'montclair', name: 'Montclair' },
  { id: 'roanoke', name: 'Roanoke' },
  { id: 'matsu', name: 'MatSu' },
  { id: 'jweekly', name: 'JWeekly' },
  { id: 'evanston', name: 'Evanston' },
  { id: 'portland', name: 'Portland' },
  { id: 'boston', name: 'Boston' },
  { id: 'publisher-resources', name: 'Publisher Resources' },
];

export default function CityPicker() {
  return (
    <div className="flex flex-col items-center w-full py-16 px-4">
      <h1 className="text-4xl font-bold tracking-tight text-gray-900 mb-8">
        Community Calendar
      </h1>
      <div className="flex flex-col gap-3 max-w-sm w-full">
        {CITIES.map(city => (
          <Button
            key={city.id}
            color="light"
            size="lg"
            href={`?city=${city.id}`}
            className="w-full"
          >
            {city.name}
          </Button>
        ))}
      </div>
    </div>
  );
}
