/** Type definitions for vistaGHANA Tourism Platform */

export interface Destination {
  id: string;
  name: string;
  category: string;
  categoryName: string;
  region: string;
  location: string;
  image: string;
  rating: number;
  reviews: number;
  fee: string;
  hours: string;
  bestTime: string;
  accessibility: string;
  lat: number;
  lng: number;
  shortDesc: string;
  fullDesc: string;
  highlights: string[];
  nearbyHotels: string[];
  guideContact: string;
}

export interface Festival {
  id: string;
  name: string;
  culture: string;
  month: string;
  duration: string;
  location: string;
  region: string;
  image: string;
  shortDesc: string;
  fullDesc: string;
  keyRituals: string[];
}

export interface PracticalInfo {
  title: string;
  badge: string;
  content: string;
}

export interface BookingData {
  fullName: string;
  email: string;
  phone: string;
  arrivalDate: string;
  arrivalTime?: string;
  airport: string;
  flightNumber?: string;
  travelers: number;
  services: BookingService[];
  totalGHS: number;
  totalUSD: number;
  paymentMethod: string;
  specialRequests?: string;
}

export interface BookingService {
  name: string;
  price: number;
  value: string;
}

export interface BookingResponse {
  success: boolean;
  message: string;
  data: {
    reference: string;
    booking: BookingData & { id: string; status: string; createdAt: string };
  };
}

export interface ApiResponse<T> {
  success: boolean;
  count?: number;
  data: T;
}

export interface ItineraryDay {
  day: string;
  title: string;
  activities: string[];
}

export interface Itinerary {
  days: number;
  style: string;
  plan: ItineraryDay[];
}

export interface ChatMessage {
  type: 'user' | 'bot';
  content: string;
  timestamp: number;
}

export type Theme = 'light' | 'dark';
export type Category = 'all' | 'national-parks' | 'historical' | 'waterfalls' | 'cultural';
