/**
 * API Client for vistaGHANA Flask Backend
 */
import { getApiBase } from './config';
const API_BASE = getApiBase();
async function fetchAPI(endpoint, options) {
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
    }
    catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}
export async function getDestinations(category = 'all', search = '') {
    const params = new URLSearchParams();
    if (category !== 'all')
        params.append('category', category);
    if (search)
        params.append('search', search);
    const query = params.toString() ? `?${params.toString()}` : '';
    return fetchAPI(`/destinations${query}`);
}
export async function getDestination(id) {
    return fetchAPI(`/destinations/${id}`);
}
export async function getFestivals() {
    return fetchAPI('/festivals');
}
export async function getFestival(id) {
    return fetchAPI(`/festivals/${id}`);
}
export async function getPracticalInfo(type) {
    return fetchAPI(`/info/${type}`);
}
export async function createBooking(data) {
    return fetchAPI('/bookings', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}
export async function getBooking(reference) {
    return fetchAPI(`/bookings/${reference}`);
}
export async function toggleWishlist(destinationId) {
    return fetchAPI('/wishlist', {
        method: 'POST',
        body: JSON.stringify({ destinationId }),
    });
}
export async function getWishlist() {
    return fetchAPI('/wishlist');
}
export async function generateItinerary(days, style) {
    return fetchAPI('/itinerary', {
        method: 'POST',
        body: JSON.stringify({ days, style }),
    });
}
//# sourceMappingURL=api.js.map