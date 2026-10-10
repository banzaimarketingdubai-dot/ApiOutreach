import asyncio
import os
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.models.email_sequence import OutreachTemplate, FunnelType

# Template content for the 3 Funnel Types (Touch 1-5)
templates_data = [
    # ================== HIDDEN GEMS ==================
    {
        "funnel_type": FunnelType.HIDDEN_GEMS,
        "touch_level": 1,
        "subject_template": "Quick question about {company_name}",
        "body_template": "<p>Hi team!</p><p>You have a great Revo Score, but you might be missing out on local traffic.</p>{audit_link}",
        "ai_prompt_context": "The lead has a high Revo Score but is losing out on local search traffic. Write a friendly, warm Touch 1 email praising their quality. CRITICAL: You must include {audit_link} and explicitly mention that this link contains a personalized online report with the first-priority steps they need to take right now to boost their GBP (Google Business Profile) ranking and get more local clients."
    },
    {
        "funnel_type": FunnelType.HIDDEN_GEMS,
        "touch_level": 2,
        "subject_template": "Did you see the local audit?",
        "body_template": "<p>Following up on my last email.</p>",
        "ai_prompt_context": "Touch 2. Follow up on the previous email. Ask if they saw the audit. Be very brief, 2-3 sentences max."
    },
    {
        "funnel_type": FunnelType.HIDDEN_GEMS,
        "touch_level": 3,
        "subject_template": "How your competitors are stealing your clients",
        "body_template": "<p>Value drop here.</p>",
        "ai_prompt_context": "Touch 3. Value-add email. Give them 1 actionable tip they can do today to improve their Google Maps ranking. Soft pitch our AI tool."
    },
    {
        "funnel_type": FunnelType.HIDDEN_GEMS,
        "touch_level": 4,
        "subject_template": "Free trial for {company_name}",
        "body_template": "<p>Try it out for 14 days.</p>",
        "ai_prompt_context": "Touch 4. Offer a 14-day free trial of our AI auto-pilot tool. Explain how it saves them 10 hours a week."
    },
    {
        "funnel_type": FunnelType.HIDDEN_GEMS,
        "touch_level": 5,
        "subject_template": "Closing the loop",
        "body_template": "<p>Breakup email.</p>",
        "ai_prompt_context": "Touch 5. The breakup email. Tell them you won't bother them again, but leave the door open if they ever want to fix their local SEO."
    },
    
    # ================== SINKING GIANTS ==================
    {
        "funnel_type": FunnelType.SINKING_GIANTS,
        "touch_level": 1,
        "subject_template": "Reputation issues for {company_name}",
        "body_template": "<p>Hi team!</p><p>We noticed your rating has dropped.</p>{audit_link}",
        "ai_prompt_context": "The lead has a low rating and many negative reviews. Write a professional Touch 1 email offering help to salvage their reputation. CRITICAL: Include {audit_link} and explain that this is a free, personalized online report showing the exact steps they need to take immediately to stop losing clients and start raising their GBP rating."
    },
    {
        "funnel_type": FunnelType.SINKING_GIANTS,
        "touch_level": 2,
        "subject_template": "Negative reviews cost you clients",
        "body_template": "<p>Follow up.</p>",
        "ai_prompt_context": "Touch 2. Cite a statistic about how 80% of customers won't visit a business with less than 4 stars. Ask for a 5 min chat."
    },
    {
        "funnel_type": FunnelType.SINKING_GIANTS,
        "touch_level": 3,
        "subject_template": "Case study: How to fix a {rating} star rating",
        "body_template": "<p>Value drop.</p>",
        "ai_prompt_context": "Touch 3. Explain how consistently responding to all reviews (even bad ones) with SEO keywords can slowly repair their ranking."
    },
    {
        "funnel_type": FunnelType.SINKING_GIANTS,
        "touch_level": 4,
        "subject_template": "Let our AI handle the angry customers",
        "body_template": "<p>Free trial offer.</p>",
        "ai_prompt_context": "Touch 4. Direct pitch. Offer 14-day free trial of our AI responder that professionally handles bad reviews and boosts local SEO."
    },
    {
        "funnel_type": FunnelType.SINKING_GIANTS,
        "touch_level": 5,
        "subject_template": "Moving on...",
        "body_template": "<p>Breakup email.</p>",
        "ai_prompt_context": "Touch 5. Breakup email. Reiterate that ignoring bad reviews is a ticking time bomb, but you'll stop reaching out."
    },

    # ================== GHOSTS ==================
    {
        "funnel_type": FunnelType.GHOSTS,
        "touch_level": 1,
        "subject_template": "Is {company_name} still open?",
        "body_template": "<p>Hi team!</p><p>Your Google profile looks abandoned.</p>{audit_link}",
        "ai_prompt_context": "The lead has almost zero reviews or profile activity. Touch 1 email: use the 'Are you still open?' angle because their Google Maps profile is so inactive. CRITICAL: Include {audit_link} and tell them this is their personalized audit report that outlines the 3 most urgent steps they must take to revive their GBP and start getting free inbound calls."
    },
    {
        "funnel_type": FunnelType.GHOSTS,
        "touch_level": 2,
        "subject_template": "Your competitors are getting your calls",
        "body_template": "<p>Follow up.</p>",
        "ai_prompt_context": "Touch 2. Educate them on what 'Local SEO' is and why having an active Google Maps profile generates free inbound calls."
    },
    {
        "funnel_type": FunnelType.GHOSTS,
        "touch_level": 3,
        "subject_template": "3 steps to rank in {city}",
        "body_template": "<p>Value drop.</p>",
        "ai_prompt_context": "Touch 3. Give them a quick 3-step guide: 1. Add photos. 2. Get 5 reviews. 3. Post weekly updates."
    },
    {
        "funnel_type": FunnelType.GHOSTS,
        "touch_level": 4,
        "subject_template": "Automation for your Google Profile",
        "body_template": "<p>Pitch.</p>",
        "ai_prompt_context": "Touch 4. Offer our software that will automatically post weekly SEO updates to bring their 'Ghost' profile back to life. Free trial."
    },
    {
        "funnel_type": FunnelType.GHOSTS,
        "touch_level": 5,
        "subject_template": "Last email - {company_name}",
        "body_template": "<p>Breakup.</p>",
        "ai_prompt_context": "Touch 5. Breakup email. Short and sweet, leaving contact info if they ever decide to focus on digital presence."
    },
]

async def seed_templates():
    async with AsyncSessionLocal() as db:
        print("Clearing old templates...")
        await db.execute(delete(OutreachTemplate))
        await db.commit()

        print("Seeding new templates...")
        for data in templates_data:
            tmpl = OutreachTemplate(**data)
            db.add(tmpl)
        
        await db.commit()
        print("Successfully seeded 15 templates (3 Funnels x 5 Touches)!")

if __name__ == "__main__":
    asyncio.run(seed_templates())
