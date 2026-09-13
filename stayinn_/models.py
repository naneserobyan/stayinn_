from datetime import date


class Property:
    """Ներկայացնում է մեկ rental property։"""

    def __init__(self, property_id: str, name: str, price_per_night: float):
        self.property_id = property_id
        self.name = name
        self.price_per_night = price_per_night
        self.bookings: list["Booking"] = []

    def to_dict(self) -> dict:
        return {
            "property_id": self.property_id,
            "name": self.name,
            "price_per_night": self.price_per_night,
            "bookings": [booking.to_dict() for booking in self.bookings],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Property":
        prop = cls(
            data["property_id"],
            data["name"],
            data["price_per_night"],
        )

        prop.bookings = [
            Booking.from_dict(booking)
            for booking in data.get("bookings", [])
        ]

        return prop

    def __repr__(self):
        return (
            f"Property({self.property_id}, "
            f"{self.name}, "
            f"{self.price_per_night}$/night)"
        )


class Booking:
    """Ներկայացնում է մեկ booking։"""

    def __init__(
        self,
        guest_name: str,
        check_in: date,
        check_out: date,
    ):
        self.guest_name = guest_name
        self.check_in = check_in
        self.check_out = check_out

    def nights(self) -> int:
        return (self.check_out - self.check_in).days

    def overlaps_with(
        self,
        other_check_in: date,
        other_check_out: date,
    ) -> bool:
        return (
            self.check_in < other_check_out
            and self.check_out > other_check_in
        )

    def to_dict(self) -> dict:
        return {
            "guest_name": self.guest_name,
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Booking":
        return cls(
            data["guest_name"],
            date.fromisoformat(data["check_in"]),
            date.fromisoformat(data["check_out"]),
        )

    def __repr__(self):
        return (
            f"Booking({self.guest_name}, "
            f"{self.check_in} → {self.check_out})"
        )