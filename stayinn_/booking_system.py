import json
from datetime import date

from models import Property, Booking


class PropertyNotFoundError(Exception):
    """Բարձրացվում է, երբ property-ն չի գտնվել։"""

    pass


class NotAvailableError(Exception):
    """Բարձրացվում է, երբ property-ն զբաղված է։"""

    pass


class BookingSystem:

    def __init__(self, data_file: str = "data.json"):
        self.data_file = data_file
        self.properties: dict[str, Property] = {}

        self._load()

    # -------------------------
    # Property management
    # -------------------------

    def add_property(
        self,
        property_id: str,
        name: str,
        price_per_night: float,
    ) -> Property:

        if price_per_night <= 0:
            raise ValueError("Գինը պետք է լինի 0-ից մեծ։")

        if property_id in self.properties:
            raise ValueError(
                f"Property '{property_id}' արդեն գոյություն ունի։"
            )

        property_obj = Property(
            property_id,
            name,
            price_per_night,
        )

        self.properties[property_id] = property_obj

        self._save()

        return property_obj

    def list_properties(self) -> list[Property]:
        return list(self.properties.values())

    # -------------------------
    # Availability
    # -------------------------

    def is_available(
        self,
        property_id: str,
        check_in: date,
        check_out: date,
    ) -> bool:

        if property_id not in self.properties:
            raise PropertyNotFoundError(
                f"Property '{property_id}' չի գտնվել։"
            )

        if check_in >= check_out:
            raise ValueError(
                "Check-in-ը պետք է լինի check-out-ից առաջ։"
            )

        property_obj = self.properties[property_id]

        for booking in property_obj.bookings:

            if booking.overlaps_with(
                check_in,
                check_out,
            ):
                return False

        return True

    # -------------------------
    # Booking
    # -------------------------

    def book(
        self,
        property_id: str,
        guest_name: str,
        check_in: date,
        check_out: date,
    ) -> Booking:

        if not self.is_available(
            property_id,
            check_in,
            check_out,
        ):
            raise NotAvailableError(
                f"Property '{property_id}' զբաղված է "
                f"{check_in} - {check_out} ամսաթվերին։"
            )

        booking = Booking(
            guest_name,
            check_in,
            check_out,
        )

        self.properties[property_id].bookings.append(booking)

        self._save()

        return booking

    # -------------------------
    # Price
    # -------------------------

    def calculate_price(
        self,
        property_id: str,
        check_in: date,
        check_out: date,
    ) -> float:

        if property_id not in self.properties:
            raise PropertyNotFoundError(
                f"Property '{property_id}' չի գտնվել։"
            )

        if check_in >= check_out:
            raise ValueError(
                "Check-in-ը պետք է լինի check-out-ից առաջ։"
            )

        nights = (check_out - check_in).days

        price_per_night = self.properties[
            property_id
        ].price_per_night

        return nights * price_per_night

    # -------------------------
    # JSON persistence
    # -------------------------

    def _save(self):
        data = {
            property_id: property_obj.to_dict()
            for property_id, property_obj
            in self.properties.items()
        }

        with open(
            self.data_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def _load(self):

        try:
            with open(
                self.data_file,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

                self.properties = {
                    property_id: Property.from_dict(property_data)
                    for property_id, property_data
                    in data.items()
                }

        except FileNotFoundError:
            self.properties = {}

        except json.JSONDecodeError:
            print("Warning: data.json-ը վնասված է։")
            self.properties = {}