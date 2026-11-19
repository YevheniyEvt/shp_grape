import { createTranslator } from "@/i18n/gettext";
import type { Photo, VarietyDetail, VarietyListItem } from "@/lib/api/catalog";

/** Translator without a catalog: returns the English msgids. */
export const { t, nt } = createTranslator(null);

export function makePhoto(overrides: Partial<Photo> = {}): Photo {
  return {
    id: 1,
    alt: "Photo",
    width: 1200,
    height: 900,
    thumb: "http://api/media/thumb.webp",
    medium: "http://api/media/medium.webp",
    large: "http://api/media/large.webp",
    ...overrides,
  };
}

export function makeVariety(overrides: Partial<VarietyListItem> = {}): VarietyListItem {
  return {
    id: 1,
    slug: "rankovyi-ametyst",
    name: "Ранковий Аметист",
    main_photo: makePhoto(),
    ripening: { slug: "rannii", name: "Ранній" },
    berry_color: { slug: "fioletovyi", name: "Фіолетовий" },
    bunch_weight_min: 0.5,
    bunch_weight_max: 0.8,
    berry_weight_min: 8,
    berry_weight_max: 10,
    frost_resistance: -23,
    cutting_price: 30,
    cutting_available: true,
    sapling_price: 120,
    sapling_available: false,
    is_featured: false,
    ...overrides,
  };
}

export function makeVarietyDetail(overrides: Partial<VarietyDetail> = {}): VarietyDetail {
  return {
    ...makeVariety(),
    alt_names: "",
    author: "О. Демченко",
    pulp: { slug: "khrustka", name: "Хрустка" },
    taste: { slug: "muskatnyi", name: "Мускатний" },
    vigor: null,
    berry_size_min: 24,
    berry_size_max: 28,
    disease_susceptibility_min: 2.5,
    disease_susceptibility_max: 3,
    description: "<p>Опис</p>",
    photos: [makePhoto(), makePhoto({ id: 2, alt: "Second" })],
    videos: [],
    views_count: 5,
    similar: [],
    ...overrides,
  };
}
