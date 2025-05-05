import aiohttp
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class Flight:
    hex: str
    type: Optional[str] = None
    flight: Optional[str] = None
    r: Optional[str] = None
    t: Optional[str] = None
    desc: Optional[str] = None
    ownOp: Optional[str] = None
    year: Optional[str] = None
    alt_baro: Optional[int] = None
    alt_geom: Optional[int] = None
    gs: Optional[float] = None
    track: Optional[float] = None
    baro_rate: Optional[int] = None
    squawk: Optional[str] = None
    emergency: Optional[str] = None
    category: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    nic: Optional[int] = None
    rc: Optional[int] = None
    seen_pos: Optional[float] = None
    r_dst: Optional[float] = None
    r_dir: Optional[float] = None
    version: Optional[int] = None
    nic_baro: Optional[int] = None
    nac_p: Optional[int] = None
    nac_v: Optional[int] = None
    sil: Optional[int] = None
    sil_type: Optional[str] = None
    gva: Optional[int] = None
    sda: Optional[int] = None
    alert: Optional[int] = None
    spi: Optional[int] = None
    mlat: Optional[List] = None
    tisb: Optional[List] = None
    messages: Optional[int] = None
    seen: Optional[float] = None
    rssi: Optional[float] = None
    nav_qnh: Optional[float] = None
    nav_altitude_mcp: Optional[int] = None
    nav_altitude_fms: Optional[int] = None
    nav_heading: Optional[float] = None
    nav_modes: Optional[List[str]] = None
    geom_rate: Optional[int] = None
    route: Optional[List[str]] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Flight':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

class Flights:
    def __init__(self, config):
        self.config = config
        self.url = config['tar1090']['url']
        self.route_url = config['tar1090']['route_url']
        logging.info(f"Flights initialized with URL: {self.url}")

    async def get_flights(self):
        logging.debug(f"Fetching all flights from {self.url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url) as response:
                    if response.status == 200:
                        data = await response.json()
                        aircraft_count = len(data.get('aircraft', []))
                        logging.info(f"Successfully fetched {aircraft_count} aircraft")
                        return data
                    else:
                        logging.error(f"Failed to fetch flights: HTTP {response.status}")
                        return {"aircraft": []}
            except Exception as e:
                logging.error(f"Error fetching flights: {str(e)}")
                raise

    async def get_flight(self, id):
        logging.debug(f"Looking for flight with hex ID: {id}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url) as response:
                    if response.status != 200:
                        logging.error(f"Failed to fetch flight data: HTTP {response.status}")
                        return None

                    data = await response.json()
                    for aircraft in data.get('aircraft', []):
                        if aircraft.get('hex') == id:
                            logging.info(f"Found flight {id}: {aircraft.get('flight', '').strip()}")
                            return Flight.from_json(aircraft)

                    logging.warning(f"Flight with hex ID {id} not found")
                    return None
            except Exception as e:
                logging.error(f"Error fetching flight {id}: {str(e)}")
                raise

    async def enrich_flights_with_routes(self, flights: List[Flight]) -> List[Flight]:
        logging.debug("Enriching flights with routes")
        request_dict = {'planes': []}
        for flight in flights:
            if flight.flight and flight.flight.strip() and flight.lat and flight.lon:
                request_dict['planes'].append({
                    'callsign': flight.flight.strip(),
                    'lat': flight.lat,
                    'lng': flight.lon
                })

        if not request_dict['planes']:
            logging.warning("No valid flights to enrich with routes")
            return flights

        logging.info(f"Requesting routes for {len(request_dict['planes'])} flights")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.route_url, json=request_dict) as response:
                    if response.status == 200:
                        route_data = await response.json()
                        logging.info(f"Received route data for {len(route_data)} flights")

                        for route_info in route_data:
                            callsign = route_info.get('callsign')
                            airports = route_info.get('_airports', [])

                            # Find matching flight
                            matching_flight = next((f for f in flights if f.flight and f.flight.strip() == callsign), None)
                            if matching_flight is not None:
                                # Build route string from location names
                                locations = []
                                for airport in airports:
                                    location = airport.get('location')
                                    if location:
                                        locations.append(location)

                                if locations:
                                    route_string = " → ".join(locations)
                                    matching_flight.route = route_string
                                    logging.debug(f"Added route '{route_string}' to flight {callsign}")
                    else:
                        logging.error(f"Failed to fetch route data: HTTP {response.status}")
        except Exception as e:
            logging.error(f"Error enriching flights with routes: {str(e)}")

        return flights

    async def get_flights_as_objects(self) -> List[Flight]:
        logging.debug("Converting flight data to Flight objects")
        try:
            data = await self.get_flights()
            flights = [Flight.from_json(aircraft) for aircraft in data.get('aircraft', [])]
            logging.info(f"Converted {len(flights)} flights to Flight objects")

            # Sort flights by distance (r_dst), with None values at the end
            flights.sort(key=lambda flight: flight.r_dst if flight.r_dst is not None else 9999999)

            # Enrich flights with route information
            flights = await self.enrich_flights_with_routes(flights)

            return flights
        except Exception as e:
            logging.error(f"Error converting flights to objects: {str(e)}")
            raise