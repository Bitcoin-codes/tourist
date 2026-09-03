/**
 * API Client for vistaGHANA Flask Backend
 */

import type { ApiResponse, Destination, Festival, PracticalInfo, BookingData, BookingResponse, Itinerary } from './types';

const API_BASE = 'http://localhost:5000/api';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

export async function getDestinations(category: string = 'all', search: string = ''): Promise<ApiResponse<Destination[]>> {
  const params = new URLSearchParams();
  if (category !== 'all') params.append('category', category);
  if (search) params.append('search', search);

  const query = params.toString() ? `?${params.toString()}` : '';
  return fetchAPI<Destination[]>(`/destinations${query}`);
}

export async function getDestination(id: string): Promise<ApiResponse<Destination>> {
  return fetchAPI<Destination>(`/destinations/${id}`);
}

export async function getFestivals(): Promise<ApiResponse<Festival[]>> {
  return fetchAPI<Festival[]>('/festivals');
}

export async function getFestival(id: string): Promise<ApiResponse<Festival>> {
  return fetchAPI<Festival>(`/festivals/${id}`);
}

export async function getPracticalInfo(type: string): Promise<ApiResponse<PracticalInfo>> {
  return fetchAPI<PracticalInfo>(`/info/${type}`);
}

export async function createBooking(data: BookingData): Promise<BookingResponse> {
  return fetchAPI<any>('/bookings', {
    method: 'POST',
    body: JSON.stringify(data),
  }) as Promise<BookingResponse>;
}

export async function getBooking(reference: string): Promise<ApiResponse<any>> {
  return fetchAPI<any>(`/bookings/${reference}`);
}

export async function toggleWishlist(destinationId: string): Promise<ApiResponse<string[]>> {
  return fetchAPI<string[]>('/wishlist', {
    method: 'POST',
    body: JSON.stringify({ destinationId }),
  });
}

export async function getWishlist(): Promise<ApiResponse<string[]>> {
  return fetchAPI<string[]>('/wishlist');
}

export async function generateItinerary(days: number, style: string): Promise<ApiResponse<Itinerary>> {
  return fetchAPI<Itinerary>('/itinerary', {
    method: 'POST',
    body: JSON.stringify({ days, style }),
  });
}
