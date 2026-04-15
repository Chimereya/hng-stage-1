import httpx
import asyncio
from fastapi import HTTPException



async def get_profile_intelligence(name: str):
    async with httpx.AsyncClient() as client:
        try:
            # Make concurrent API calls to Genderize, Agify, and Nationalize
            g_req = client.get(f"https://api.genderize.io?name={name}")
            a_req = client.get(f"https://api.agify.io?name={name}")
            n_req = client.get(f"https://api.nationalize.io?name={name}")

            g_res, a_res, n_res = await asyncio.gather(g_req, a_req, n_req)
        
        except Exception:
            raise HTTPException(status_code=502, detail="Upstream server error")
        

        # Genderize response
        g_data = g_res.json()
        if not g_data.get("gender") or g_data.get("count") == 0:
            raise HTTPException(status_code=502, detail="Genderize returned an invalid response")
        

        # Agify response
        a_data = a_res.json()
        age = a_data.get("age")
        if age is None:
            raise HTTPException(status_code=502, detail="Agify returned an invalid response")

        
        # Classification logic
        if age <= 12: age_group = "child"
        elif age <= 19: age_group = "teenager"
        elif age <= 59: age_group = "adult"
        else: age_group = "senior"

        # Nationalize response
        n_data = n_res.json()
        countries = n_data.get("country", [])
        if not countries:
            raise HTTPException(status_code=502, detail="Nationalize returned an invalid response")
        
        top_country = max(countries, key=lambda x: x['probability'])


        return {
            "gender": g_data["gender"],
            "gender_probability": g_data["probability"],
            "sample_size": g_data["count"],
            "age": age,
            "age_group": age_group,
            "country_id": top_country["country_id"],
            "country_probability": top_country["probability"]
        }