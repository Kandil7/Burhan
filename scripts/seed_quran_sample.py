#!/usr/bin/env python3
"""Seed Quran sample data using async connection with upsert logic."""
import asyncio
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config.settings import settings
from src.data.models.quran import Base, Surah, Ayah, Translation

async def seed():
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Load sample data
    with open("data/seed/quran_sample.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    async with async_session() as session:
        surah_count = 0
        ayah_count = 0
        
        for surah_data in data.get("surahs", []):
            # Check if surah exists
            result = await session.execute(
                select(Surah).where(Surah.number == surah_data["number"])
            )
            surah = result.scalar_one_or_none()
            
            if surah is None:
                # Create new surah
                surah = Surah(
                    number=surah_data["number"],
                    name_ar=surah_data["name_ar"],
                    name_en=surah_data["name_en"],
                    verse_count=surah_data["verse_count"],
                    revelation_type=surah_data.get("revelation_type", "Meccan"),
                )
                session.add(surah)
                await session.flush()
                surah_count += 1
            else:
                print(f"⏭️  Surah {surah.number} ({surah.name_en}) already exists")
            
            for ayah_data in surah_data.get("ayahs", []):
                # Check if ayah exists
                result = await session.execute(
                    select(Ayah).where(
                        Ayah.surah_id == surah.id,
                        Ayah.number_in_surah == ayah_data["number_in_surah"]
                    )
                )
                ayah = result.scalar_one_or_none()
                
                if ayah is None:
                    # Create new ayah
                    ayah = Ayah(
                        surah_id=surah.id,
                        number_in_surah=ayah_data["number_in_surah"],
                        number=ayah_data.get("number_in_surah"),
                        text_uthmani=ayah_data.get("text_uthmani", ""),
                        juz=ayah_data.get("juz", 1),
                        page=ayah_data.get("page", 1),
                    )
                    session.add(ayah)
                    await session.flush()
                    ayah_count += 1
                else:
                    # Update existing ayah
                    ayah.text_uthmani = ayah_data.get("text_uthmani", "")
                    ayah.juz = ayah_data.get("juz", 1)
                    ayah.page = ayah_data.get("page", 1)
                
                # Update/add translations
                for trans_data in ayah_data.get("translations", []):
                    result = await session.execute(
                        select(Translation).where(
                            Translation.ayah_id == ayah.id,
                            Translation.language == trans_data["language"]
                        )
                    )
                    trans = result.scalar_one_or_none()
                    
                    if trans is None:
                        trans = Translation(
                            ayah_id=ayah.id,
                            language=trans_data["language"],
                            translator=trans_data.get("translator", ""),
                            text=trans_data["text"],
                        )
                        session.add(trans)
                    else:
                        trans.text = trans_data["text"]
                        trans.translator = trans_data.get("translator", "")
        
        await session.commit()
        print(f"\n✅ Seeded: {surah_count} new surahs, {ayah_count} new ayahs")
    
    await engine.dispose()
    print("✅ Quran sample data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
