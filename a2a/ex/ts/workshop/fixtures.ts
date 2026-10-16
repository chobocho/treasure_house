// 시나리오 자료(ex/fixtures/*.json)를 읽는다.
// 세 언어가 같은 파일을 쓴다.
import { readFileSync } from "node:fs";

export type Venue = {
  id: string;
  name: string;
  capacity: number;
  roomSize: number;
  pricePerPersonNight: number;
  closed: string[];
};
export type MealType = "dinner" | "breakfast" | "lunch";
export type Menu = {
  type: MealType;
  id: string;
  name: string;
  price: number;
  vegetarian: boolean;
};
export type Bus = {
  id: string;
  seats: number;
  pricePerDay: number;
  plate: string;
};
export type Workshop = {
  venues: Venue[];
  menus: Menu[];
  defaultCaps: Record<MealType, number>;
  buses: Bus[];
  busSteps: string[];
  approvalThreshold: number;
};
export type OAuthClient = {
  clientId: string;
  clientSecret: string;
  scopes: string[];
};

function load<T>(name: string): T {
  const url = new URL(`../../fixtures/${name}`, import.meta.url);
  return JSON.parse(readFileSync(url, "utf-8")) as T;
}

// 모듈을 처음 불러올 때 한 번만 읽는다.
export const workshop: Workshop = load<Workshop>("workshop.json");
export const clients: OAuthClient[] = load<{ clients: OAuthClient[] }>(
  "clients.json",
).clients;
