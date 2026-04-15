import httpx
import asyncio
from fastapi import HTTPException

async def get_profile_intelligence(name: str):
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # Gather responses concurrently
            responses = await asyncio.gather(
                client.get(f"https://api.genderize.io?name={name}"),
                client.get(f"https://api.agify.io?name={name}"),
                client.get(f"https://api.nationalize.io?name={name}"),
                return_exceptions=True
            )
        except Exception:
            # This catches network-level failures
            raise HTTPException(status_code=502, detail="Upstream server error")

        # Unpack responses
        g_res, a_res, n_res = responses

        if isinstance(g_res, Exception) or g_res.status_code != 200:
            raise HTTPException(status_code=502, detail="Genderize returned an invalid response")
        
        g_data = g_res.json()
        if not g_data.get("gender") or g_data.get("count") == 0:
            raise HTTPException(status_code=502, detail="Genderize returned an invalid response")

        if isinstance(a_res, Exception) or a_res.status_code != 200:
            raise HTTPException(status_code=502, detail="Agify returned an invalid response")
            
        a_data = a_res.json()
        age = a_data.get("age")
        if age is None:
            raise HTTPException(status_code=502, detail="Agify returned an invalid response")

        if age <= 12: age_group = "child"
        elif age <= 19: age_group = "teenager"
        elif age <= 59: age_group = "adult"
        else: age_group = "senior"

        if isinstance(n_res, Exception) or n_res.status_code != 200:
            raise HTTPException(status_code=502, detail="Nationalize returned an invalid response")
            
        n_data = n_res.json()
        countries = n_data.get("country", [])
        if not countries:
            raise HTTPException(status_code=502, detail="Nationalize returned an invalid response")
        
        # Pick highest probability
        top_country = max(countries, key=lambda x: x['probability'])

        return {
            "gender": g_data["gender"],
            "gender_probability": round(g_data["probability"], 2),
            "sample_size": g_data["count"],
            "age": age,
            "age_group": age_group,
            "country_id": top_country["country_id"],
            "country_probability": round(top_country["probability"], 2),
        }