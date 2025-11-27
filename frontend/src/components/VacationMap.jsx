import React, { useEffect, useRef, useState } from 'react';
import '@maptiler/sdk/dist/maptiler-sdk.css';
import * as maptilersdk from '@maptiler/sdk';

// VacationMap Component
// Displays an interactive map showing vacation destinations, routes, and points of interest.
// Uses MapTiler for rendering maps with zoom, markers, and route visualization.
const VacationMap = ({ 
  destinations = [], 
  itinerary = [], 
  route = [],
  height = '400px',
  className = ''
}) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Initialize MapTiler
    const apiKey = import.meta.env.VITE_MAPTILER_API_KEY || '';
    
    if (!apiKey) {
      setError('MapTiler API key not configured. Please set VITE_MAPTILER_API_KEY in your .env file.');
      return;
    }

    maptilersdk.config.apiKey = apiKey;

    try {
      // Create map instance
      const styleUrl = `https://api.maptiler.com/maps/streets-v2/style.json?key=${apiKey}`;
      map.current = new maptilersdk.Map({
        container: mapContainer.current,
        style: styleUrl,
        center: [0, 20],
        zoom: 2,
        navigationControl: true,
        geolocateControl: true,
        fullscreenControl: true
      });

      map.current.on('load', () => {
        setIsLoaded(true);
        // Wait for map to be fully ready before adding markers
        setTimeout(() => {
          if (map.current) {
            addMarkersAndRoute();
          }
        }, 100);
      });

    } catch (err) {
      console.error('Error initializing map:', err);
      setError('Failed to initialize map. Please check your MapTiler API key.');
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update map when destinations or itinerary change
  useEffect(() => {
    if (isLoaded && map.current) {
      addMarkersAndRoute();
    }
  }, [destinations, itinerary, route, isLoaded]);

  const addMarkersAndRoute = async () => {
    if (!map.current || !isLoaded) return;

    const apiKey = import.meta.env.VITE_MAPTILER_API_KEY || '';
    if (!apiKey) {
      console.warn('MapTiler API key not available for geocoding');
      return;
    }

    // Clear existing markers and routes
    const existingMarkers = document.querySelectorAll('.maptiler-marker');
    existingMarkers.forEach(marker => marker.remove());

    if (map.current.getSource('route')) {
      if (map.current.getLayer('route')) {
        map.current.removeLayer('route');
      }
      map.current.removeSource('route');
    }

    if (destinations.length === 0 && itinerary.length === 0) {
      return;
    }

    try {
      // Geocode destinations to get coordinates
      const coordinates = [];
      const markers = [];

      // Extract city and country from destinations, then geocode the city with country context
      const landmarkKeywords = ['tower', 'palace', 'temple', 'monument', 'museum', 'bridge', 'cathedral', 'mosque', 'mahal', 'statue', 'colosseum', 'eiffel', 'liberty'];
      
      // Separate landmarks from cities/countries
      const landmarks = destinations.filter(d => 
        landmarkKeywords.some(kw => d.toLowerCase().includes(kw))
      );
      const citiesAndCountries = destinations.filter(d => 
        !landmarkKeywords.some(kw => d.toLowerCase().includes(kw))
      );
      
      // Determine city and country
      let city = null;
      let country = null;
      let landmark = landmarks.length > 0 ? landmarks[0] : null;
      
      if (citiesAndCountries.length >= 2) {
        // Sort by length
        const sorted = [...citiesAndCountries].sort((a, b) => a.length - b.length);
        city = sorted[0];
        country = sorted[1];
      } else if (citiesAndCountries.length === 1) {
        // Single city/country - assume it's a city if it's short, country if long
        city = citiesAndCountries[0].length < 20 ? citiesAndCountries[0] : null;
        country = citiesAndCountries[0].length >= 20 ? citiesAndCountries[0] : null;
      }
      
      // Build geocoding query: prefer "City, Country" format
      let geocodeQuery = null;
      let primaryDestination = null;
      
      if (city && country) {
        geocodeQuery = `${city}, ${country}`;
        primaryDestination = landmark || city;
      } else if (city) {
        // Only city available
        geocodeQuery = city;
        primaryDestination = landmark || city;
      } else if (country) {
        // Only country available
        geocodeQuery = country;
        primaryDestination = landmark || country;
      } else if (landmark) {
        // Only landmark available
        geocodeQuery = landmark;
        primaryDestination = landmark;
      } else if (destinations.length > 0) {
        // Fallback: use first destination
        geocodeQuery = destinations[0];
        primaryDestination = destinations[0];
      }
      
      // Geocode only the primary location
      if (geocodeQuery && primaryDestination) {
        try {
          // Try geocoding with increasing specificity to avoid wrong matches
          let geocodeResult = null;
          let attempts = [geocodeQuery];
          
          // Only add fallback attempts if don't have city + country already
          if (destinations.length === 1 || !geocodeQuery.includes(',')) {
            // If we only have one destination or no comma in query, try the primary
            attempts.push(primaryDestination);
          }
          
          // If we have multiple destinations but query doesn't include country, add city + country
          if (destinations.length > 1 && !geocodeQuery.includes(',')) {
            const cityCountry = destinations.filter(d => 
              d && typeof d === 'string' && 
              d.length < 30 && 
              !landmarkKeywords.some(kw => d.toLowerCase().includes(kw))
            );
            if (cityCountry.length >= 2) {
              attempts.unshift(`${cityCountry[0]}, ${cityCountry[1]}`);
            }
          }
          
          console.log('Geocoding attempts:', attempts, 'primaryDestination:', primaryDestination, 'city:', city, 'country:', country);
          for (const query of attempts) {
            try {
              console.log('Attempting geocode for:', query);
              const result = await maptilersdk.geocoding.forward(query, {
                limit: 5,
                key: apiKey
              });
              
              console.log('Geocode result for', query, ':', result?.features?.length, 'results');
              
              if (result && result.features && result.features.length > 0) {
                console.log('All geocode results:', result.features.map(f => ({
                  name: f.properties?.name || f.properties?.place_name || f.properties?.text,
                  countryCode: f.properties?.country_code,
                  placeName: f.properties?.place_name,
                  context: f.properties?.context,
                  coordinates: f.geometry?.coordinates,
                  type: f.properties?.type || f.properties?.place_type || f.properties?.kind,
                  allProperties: f.properties
                })));
                
                // Filter and score each result to find the best match
                // Since geocoding city + country, prefer city/locality results
                const scoredResults = result.features
                  .map(f => {
                    let score = 0;
                    const props = f.properties || {};
                    const placeName = (props.text || props.name || props.place_name || '').toLowerCase();
                    const placeNameFull = (props.place_name || props.name || props.text || '').toLowerCase();
                    const context = (props.context || (props.place_name ? props.place_name.split(',').slice(1).join(',') : '') || '').toLowerCase();
                    const fullText = `${placeName} ${placeNameFull} ${context}`.toLowerCase();
                    const queryLower = query.toLowerCase();
                    // MapTiler may return place_type as array or string, also check 'kind' property
                    const placeTypeRaw = props.place_type || props.type || props.kind || '';
                    const placeType = Array.isArray(placeTypeRaw) 
                      ? (placeTypeRaw[0] || '').toLowerCase() 
                      : String(placeTypeRaw).toLowerCase();
                    
                    // Since we're geocoding city + country, prefer city/locality results
                    if (['locality', 'city', 'place', 'neighborhood'].includes(placeType) || 
                        ['locality', 'city', 'place', 'neighborhood'].includes((props.kind || '').toLowerCase())) {
                      score += 50;
                    } else if (['country', 'region', 'administrative', 'state', 'admin_area'].includes(placeType) ||
                               ['country', 'region', 'administrative', 'state', 'admin_area'].includes((props.kind || '').toLowerCase())) {
                      score -= 30;
                    }
                    
                    // Check if city name matches
                    if (city && placeName.includes(city.toLowerCase())) {
                      score += 40;
                    } else if (city && fullText.includes(city.toLowerCase())) {
                      score += 20;
                    }
                    
                    // Check if query contains country/city - prefer results with that context
                    const queryParts = queryLower.split(',').map(p => p.trim());
                    if (queryParts.length > 1) {
                      // Check all context parts
                      for (const part of queryParts.slice(1)) {
                        if (fullText.includes(part)) {
                          score += 10;
                        }
                      }
                      const countryInQuery = queryParts[queryParts.length - 1].toLowerCase();
                      const countryCode = (props.country_code || props.country || '').toLowerCase();
                      
                      // Check if result's country matches the query country
                      const resultCountryInText = fullText.toLowerCase();
                      const countryMatches = resultCountryInText.includes(countryInQuery);
                      
                      if (countryMatches) {
                        score += 50;
                      } else if (countryInQuery && countryCode) {
                        // If country name doesn't match, check country code
                        const possibleCodes = [
                          countryInQuery.substring(0, 2), // First 2 letters
                          countryInQuery.split(' ').map(w => w[0]).join(''), // First letters of words
                          ...countryInQuery.split(' ').filter(w => w.length >= 2).map(w => w.substring(0, 2)) // First 2 letters of each word
                        ];
                        
                        if (possibleCodes.includes(countryCode)) {
                          score += 30;
                        } else {
                          // Strong penalty if country code doesn't match and country name doesn't appear
                          score -= 50;
                        }
                      }
                    }
                    
                    // Check result type
                    const kind = (props.kind || '').toLowerCase();
                    if (['poi', 'place', 'locality', 'neighborhood', 'address'].includes(placeType) || 
                        ['poi', 'place', 'locality', 'neighborhood', 'address'].includes(kind)) {
                      score += 30;
                    } else if (['country', 'region', 'administrative', 'state', 'admin_area'].includes(placeType) ||
                               ['country', 'region', 'administrative', 'state', 'admin_area'].includes(kind)) {
                      score -= 50;
                    }
                    
                    if (city && !fullText.includes(city.toLowerCase())) {
                      score -= 20;
                    }
                    
                    return { feature: f, score };
                  })
                  .filter(r => r !== null && r.score > -100);
                
                console.log('Scored results after filtering:', scoredResults.length, scoredResults.map(r => ({
                  name: r.feature.properties?.name || r.feature.properties?.place_name,
                  score: r.score,
                  countryCode: r.feature.properties?.country_code,
                  coordinates: r.feature.geometry?.coordinates
                })));
                
                if (scoredResults.length === 0) {
                  // If all results were filtered, use first city/locality result
                  const cityResult = result.features.find(f => {
                    const props = f.properties || {};
                    const type = (props.place_type || props.type || props.kind || '').toLowerCase();
                    return ['locality', 'city', 'place'].includes(type);
                  });
                  if (cityResult) {
                    scoredResults.push({ feature: cityResult, score: 10 });
                  } else {
                    // Last resort: use first result
                    scoredResults.push({ feature: result.features[0], score: 0 });
                  }
                }
                
                // Sort by score and pick the best
                scoredResults.sort((a, b) => b.score - a.score);
                
                // Final validation: ensure country matches if we specified one
                // Check all results, not just scored ones, in case scoring filtered out the correct result
                if (country && result.features.length > 0) {
                  const countryLower = country.toLowerCase();
                  const bestMatch = scoredResults.length > 0 ? scoredResults[0].feature : result.features[0];
                  const bestProps = bestMatch.properties || {};
                  const bestContext = (bestProps.context || bestProps.place_name || '').toLowerCase();
                  const bestCountryCode = (bestProps.country_code || '').toLowerCase();
                  const bestPlaceName = (bestProps.place_name || '').toLowerCase();
                  const bestCoords = bestMatch.geometry?.coordinates;
                  
                  // General country matching - check if country name appears in result
                  // Generate variations of the country name for flexible matching
                  const countryVariations = [
                    countryLower,
                    countryLower.replace(/\s+/g, ''),
                    countryLower.split(' ').map(w => w[0]).join(''),
                    ...countryLower.split(' ').filter(w => w.length > 2)
                  ];
                  
                  // Check if country name appears in result text (context or place_name)
                  const fullResultText = `${bestContext} ${bestPlaceName}`.toLowerCase();
                  const hasCorrectCountry = countryVariations.some(variation => 
                    fullResultText.includes(variation)
                  );
                  
                  console.log('Country validation:', {
                    countryLower,
                    bestContext,
                    bestCountryCode,
                    bestPlaceName,
                    bestCoords,
                    hasCorrectCountry
                  });
                  
                  // If country doesn't match, find a better match
                  if (!hasCorrectCountry) {
                    console.warn('Country mismatch detected, looking for better match in ALL results');
                    
                    // Find a result that matches the country - check all results
                    // Use same general country matching logic as above
                    const countryVariations = [
                      countryLower,
                      countryLower.replace(/\s+/g, ''),
                      countryLower.split(' ').map(w => w[0]).join(''),
                      ...countryLower.split(' ').filter(w => w.length > 2)
                    ];
                    
                    const betterMatch = result.features.find(f => {
                      const rProps = f.properties || {};
                      const rContext = (rProps.context || rProps.place_name || '').toLowerCase();
                      const rCountryCode = (rProps.country_code || '').toLowerCase();
                      const rPlaceName = (rProps.place_name || '').toLowerCase();
                      
                      // Check country name variations
                      const nameMatch = countryVariations.some(variation => 
                        rContext.includes(variation) || rPlaceName.includes(variation)
                      );
                      
                      // Check if country name appears in result text
                      const rFullText = `${rContext} ${rPlaceName}`.toLowerCase();
                      return countryVariations.some(variation => rFullText.includes(variation));
                    });
                    
                    if (betterMatch) {
                      console.log('Found better match with correct country');
                      if (scoredResults.length === 0) {
                        scoredResults.push({ feature: betterMatch, score: 80 });
                      } else {
                        scoredResults[0] = { feature: betterMatch, score: 80 };
                      }
                      } else {
                        // If no better match found, check if we can find any result with the country name
                        // in the context/place_name (most reliable indicator)
                        const nameBasedMatch = result.features.find(f => {
                          const rProps = f.properties || {};
                          const rContext = (rProps.context || rProps.place_name || '').toLowerCase();
                          const rPlaceName = (rProps.place_name || '').toLowerCase();
                          const fullText = `${rContext} ${rPlaceName}`.toLowerCase();
                          return countryVariations.some(variation => fullText.includes(variation));
                        });
                        
                        if (nameBasedMatch) {
                          console.log('Found name-based match with correct country');
                          if (scoredResults.length === 0) {
                            scoredResults.push({ feature: nameBasedMatch, score: 70 });
                          } else {
                            scoredResults[0] = { feature: nameBasedMatch, score: 70 };
                          }
                        } else {
                          // Last resort: check if city name matches and use that result
                          // Even if country doesn't match, the city name is more important
                          if (city) {
                            // Normalize city name for flexible matching (handles "Danang" vs "Da Nang")
                            const normalizeCityName = (name) => name.toLowerCase().replace(/[\s-]/g, '');
                            const normalizedCity = normalizeCityName(city);
                            
                            const cityMatch = result.features.find(f => {
                              const rProps = f.properties || {};
                              const rName = normalizeCityName(rProps.name || rProps.text || rProps.place_name || '');
                              const rPlaceName = normalizeCityName(rProps.place_name || '');
                              return rName.includes(normalizedCity) || rPlaceName.includes(normalizedCity) ||
                                     normalizedCity.includes(rName) || normalizedCity.includes(rPlaceName);
                            });
                            
                            if (cityMatch) {
                              console.log('Found city name match - using despite country mismatch');
                              if (scoredResults.length === 0) {
                                scoredResults.push({ feature: cityMatch, score: 60 });
                              } else {
                                scoredResults[0] = { feature: cityMatch, score: 60 };
                              }
                            } else {
                              console.warn('No results match city or country - using best available result');
                            }
                          } else {
                            console.warn('No results match the correct country - using best available result');
                          }
                        }
                      }
                  }
                }
                
                // Get best match after validation
                if (scoredResults.length === 0) {
                  console.warn('No scored results available after validation - using first result as fallback');
                  scoredResults.push({ feature: result.features[0], score: 0 });
                }
                
                const bestMatch = scoredResults[0].feature;
                
                console.log('Selected best match:', {
                  query,
                  primaryDestination,
                  city,
                  country,
                  bestMatch: {
                    name: bestMatch.properties?.name || bestMatch.properties?.place_name || bestMatch.properties?.text,
                    type: bestMatch.properties?.type || bestMatch.properties?.place_type || bestMatch.properties?.kind,
                    countryCode: bestMatch.properties?.country_code,
                    score: scoredResults[0].score,
                    coordinates: bestMatch.geometry?.coordinates
                  }
                });
                
                geocodeResult = { features: [bestMatch] };
                break;
              }
            } catch (err) {
              console.error('Error during geocoding validation:', err, 'for query:', query);
              // Continue to next attempt
              continue;
            }
          }
          
          if (geocodeResult && geocodeResult.features && geocodeResult.features.length > 0) {
            const feature = geocodeResult.features[0];
            const [lng, lat] = feature.geometry.coordinates;
            console.log('Adding marker at coordinates:', lng, lat, 'for', primaryDestination);
            if (lng && lat) {
              coordinates.push([lng, lat]);

              // Add single marker for the primary destination
              if (map.current) {
                const props = feature.properties || {};
                const displayName = props.name || props.place_name || props.text || primaryDestination;
                const context = props.context || '';
                
                const marker = new maptilersdk.Marker({ color: '#6366f1' })
                  .setLngLat([lng, lat])
                  .setPopup(new maptilersdk.Popup().setHTML(
                    `<strong>${primaryDestination}</strong><br/>
                    <small>${displayName}${context && context !== displayName ? ', ' + context : ''}</small>`
                  ))
                  .addTo(map.current);
                
                console.log('Marker added successfully');
                markers.push(marker);
              } else {
                console.warn('Map not initialized, cannot add marker');
              }
            } else {
              console.warn('Invalid coordinates:', lng, lat);
            }
          } else {
            console.warn('No geocode result found for query:', geocodeQuery);
          }
        } catch (err) {
          console.debug(`Could not geocode destination "${geocodeQuery}":`, err.message || err);
        }
      }

      // Process itinerary items (if they have location data)
      for (const item of itinerary) {
        if (!item || !map.current) continue;
        
        const location = item.location || item.place;
        if (!location || typeof location !== 'string') continue;
        
        try {
          const geocodeResult = await maptilersdk.geocoding.forward(location, {
            limit: 1,
            key: apiKey
          });

          if (geocodeResult && geocodeResult.features && geocodeResult.features.length > 0) {
            const [lng, lat] = geocodeResult.features[0].geometry.coordinates;
            if (lng && lat && map.current) {
              coordinates.push([lng, lat]);

              // Add marker with itinerary info
              const marker = new maptilersdk.Marker({ color: '#10b981' })
                .setLngLat([lng, lat])
                .setPopup(new maptilersdk.Popup().setHTML(
                  `<div>
                    <strong>${item.name || location}</strong>
                    ${item.day ? `<br/>Day ${item.day}` : ''}
                    ${item.description ? `<br/><small>${item.description}</small>` : ''}
                  </div>`
                ))
                .addTo(map.current);
              
              markers.push(marker);
            }
          }
        } catch (err) {
          console.debug(`Could not geocode itinerary location "${location}":`, err.message || err);
        }
      }

      // Fit map to show all markers
      if (coordinates.length > 0 && map.current) {
        try {
          const bounds = new maptilersdk.LngLatBounds();
          coordinates.forEach(coord => {
            if (coord && coord.length === 2 && coord[0] && coord[1]) {
              bounds.extend(coord);
            }
          });
          
          if (bounds && map.current.fitBounds) {
            map.current.fitBounds(bounds, {
              padding: { top: 50, bottom: 50, left: 50, right: 50 },
              maxZoom: 12
            });
          }
        } catch (err) {
          console.debug('Error fitting bounds:', err);
        }
      }

      // Draw route if we have route data or multiple destinations
      if ((route.length > 0 || coordinates.length > 1) && map.current) {
        const routeCoordinates = route.length > 0 
          ? route.map(r => [r.lng || r.longitude, r.lat || r.latitude]).filter(c => c[0] && c[1])
          : coordinates.filter(c => c && c.length === 2 && c[0] && c[1]);

        if (routeCoordinates.length > 1) {
          try {
            // Remove existing route if present
            if (map.current.getSource('route')) {
              if (map.current.getLayer('route')) {
                map.current.removeLayer('route');
              }
              map.current.removeSource('route');
            }
            
            // Use MapTiler Directions API or draw simple line
            map.current.addSource('route', {
            type: 'geojson',
            data: {
              type: 'Feature',
              properties: {},
              geometry: {
                type: 'LineString',
                coordinates: routeCoordinates
              }
            }
          });

            map.current.addLayer({
              id: 'route',
              type: 'line',
              source: 'route',
              layout: {
                'line-join': 'round',
                'line-cap': 'round'
              },
              paint: {
                'line-color': '#6366f1',
                'line-width': 3,
                'line-opacity': 0.7
              }
            });
          } catch (err) {
            console.debug('Error adding route layer:', err);
          }
        }
      }

    } catch (err) {
      console.error('Error adding markers and route:', err);
    }
  };

  if (error) {
    return (
      <div className={`bg-gray-100 dark:bg-gray-800 rounded-lg p-4 ${className}`} style={{ height }}>
        <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
        <p className="text-gray-600 dark:text-gray-400 text-xs mt-2">
          Get your free API key at <a href="https://www.maptiler.com/cloud/" target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">maptiler.com</a>
        </p>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <div 
        ref={mapContainer} 
        className="w-full rounded-lg overflow-hidden shadow-lg"
        style={{ height }}
      />
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800">
          <p className="text-gray-600 dark:text-gray-400">Loading map...</p>
        </div>
      )}
    </div>
  );
};

export default VacationMap;


