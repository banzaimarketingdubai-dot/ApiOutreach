import re
import math
from typing import Optional, List, Tuple
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import Lead
from app.models.contact import Contact, ContactCategory

def normalize_phone(phone: str) -> str:
    """Strip all non-digits except leading +."""
    if not phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", phone)
    if cleaned.startswith("+"):
        return "+" + re.sub(r"\D", "", cleaned[1:])
    return re.sub(r"\D", "", cleaned)

def clean_domain(url: str) -> str:
    """Extract clean domain e.g. https://www.example.com/page -> example.com"""
    if not url:
        return ""
    url = url.lower().strip()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    return url.split("/")[0].split("?")[0]

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lng points."""
    R = 6371000  # Radius of Earth in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class LeadMergerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_matching_lead(
        self,
        company_name: str,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Optional[Lead]:
        """
        Priority 1: Normalized Phone match
        Priority 2: Cleaned Website match
        Priority 3: Company Name match AND Geo distance < 50m
        """
        # Priority 1: Phone
        norm_phone = normalize_phone(phone) if phone else ""
        if norm_phone:
            stmt = select(Contact).where(
                Contact.contact_type == "phone",
                Contact.contact_value == norm_phone
            )
            result = await self.db.execute(stmt)
            contact_match = result.scalars().first()
            if contact_match:
                lead_stmt = select(Lead).where(Lead.id == contact_match.lead_id)
                lead_res = await self.db.execute(lead_stmt)
                existing_lead = lead_res.scalars().first()
                if existing_lead:
                    return existing_lead

        # Priority 2: Website
        cleaned_web = clean_domain(website) if website else ""
        if cleaned_web:
            stmt = select(Lead).where(Lead.website.ilike(f"%{cleaned_web}%"))
            result = await self.db.execute(stmt)
            existing_lead = result.scalars().first()
            if existing_lead:
                return existing_lead

        # Priority 3: Name + Geo
        if company_name and latitude is not None and longitude is not None:
            clean_name = company_name.strip().lower()
            stmt = select(Lead).where(Lead.company_name.ilike(f"%{clean_name}%"))
            result = await self.db.execute(stmt)
            candidates = result.scalars().all()
            for candidate in candidates:
                if candidate.latitude is not None and candidate.longitude is not None:
                    dist = haversine_distance_meters(latitude, longitude, candidate.latitude, candidate.longitude)
                    if dist <= 50.0:  # Within 50 meters
                        return candidate

        return None

    async def merge_or_create_lead(
        self,
        raw_lead: dict,
        campaign_id: Optional[str] = None
    ) -> Tuple[Lead, bool]:
        """
        Returns (lead_instance, is_new_created).
        """
        company_name = raw_lead.get("company_name", raw_lead.get("title", "Unknown Business"))
        phone = raw_lead.get("phone")
        website = raw_lead.get("website")
        lat = raw_lead.get("latitude")
        lng = raw_lead.get("longitude")

        existing_lead = await self.find_matching_lead(
            company_name=company_name,
            phone=phone,
            website=website,
            latitude=lat,
            longitude=lng
        )

        if existing_lead:
            # Merge fields if existing lead has empty values
            if not existing_lead.website and website:
                existing_lead.website = website
            if not existing_lead.address and raw_lead.get("address"):
                existing_lead.address = raw_lead.get("address")
            if not existing_lead.city and raw_lead.get("city"):
                existing_lead.city = raw_lead.get("city")
            if raw_lead.get("rating") and (existing_lead.rating or 0) == 0:
                existing_lead.rating = raw_lead.get("rating")
            if raw_lead.get("reviews_count") and (existing_lead.reviews_count or 0) == 0:
                existing_lead.reviews_count = raw_lead.get("reviews_count")
            
            # Merge contacts
            await self._add_contacts_if_new(existing_lead.id, raw_lead)
            await self.db.flush()
            return existing_lead, False
        else:
            # Create new Lead
            new_lead = Lead(
                company_name=company_name,
                business_type=raw_lead.get("business_type", raw_lead.get("category")),
                city=raw_lead.get("city"),
                address=raw_lead.get("address"),
                latitude=lat,
                longitude=lng,
                website=website,
                rating=raw_lead.get("rating", 0.0),
                reviews_count=raw_lead.get("reviews_count", 0),
                revo_score=raw_lead.get("revo_score", 100),
                campaign_id=campaign_id,
                custom_data=raw_lead.get("custom_data", {})
            )
            self.db.add(new_lead)
            await self.db.flush()

            # Add contacts
            await self._add_contacts_if_new(new_lead.id, raw_lead)
            await self.db.flush()
            return new_lead, True

    async def _add_contacts_if_new(self, lead_id, raw_lead: dict):
        # Handle Phone
        phone = raw_lead.get("phoneUnformatted") or raw_lead.get("phone")
        if phone:
            norm_p = normalize_phone(phone)
            if norm_p:
                await self._insert_contact_unique(lead_id, "phone", norm_p, source=raw_lead.get("source", "gmaps"), is_primary=True)

        # Handle Emails
        emails = raw_lead.get("emails", [])
        if isinstance(raw_lead.get("email"), str):
            emails.append(raw_lead.get("email"))
        for email in set(emails):
            if email and "@" in email:
                await self._insert_contact_unique(lead_id, "email", email.strip().lower(), source=raw_lead.get("source", "gmaps"))

        # Handle Social Links
        socials = raw_lead.get("socials", {})
        for soc_type, val in socials.items():
            if val:
                await self._insert_contact_unique(lead_id, soc_type, val, source="social_scrape")

    async def _insert_contact_unique(self, lead_id, contact_type: str, value: str, source: str = "gmaps", is_primary: bool = False):
        stmt = select(Contact).where(
            Contact.lead_id == lead_id,
            Contact.contact_type == contact_type,
            Contact.contact_value == value
        )
        res = await self.db.execute(stmt)
        if not res.scalars().first():
            c = Contact(
                lead_id=lead_id,
                contact_category=ContactCategory.STANDARD if contact_type in ["phone", "email"] else ContactCategory.NON_STANDARD,
                contact_type=contact_type,
                contact_value=value,
                source=source,
                is_primary=is_primary
            )
            self.db.add(c)
