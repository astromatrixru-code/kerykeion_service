import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

geolocator = Nominatim(user_agent="gadalaka_astro_client")
tf = TimezoneFinder()

@app.get("/calculate")
def calculate_chart(name: str, year: int, month: int, day: int, city: str, hour: int = 12, minute: int = 0):
    try:
        location = geolocator.geocode(city)
        if not location: raise HTTPException(404, "City not found")
        
        subject = AstrologicalSubject(
            name, year, month, day, hour, minute,
            city=city, lat=location.latitude, lng=location.longitude, 
            tz_str=tf.timezone_at(lng=location.longitude, lat=location.latitude)
        )

        output_dir = "/tmp"
        chart = KerykeionChartSVG(subject, new_output_directory=output_dir)
        chart.makeSVG()
        search_pattern = os.path.join(output_dir, f"{name}*Chart.svg")
        found_files = glob.glob(search_pattern)

        if not found_files:
            search_pattern = os.path.join(output_dir, f"*Chart.svg")
            found_files = [f for f in glob.glob(search_pattern) if name in os.path.basename(f)]

        if found_files:
            latest_file = max(found_files, key=os.path.getmtime)
            with open(latest_file, "r", encoding="utf-8") as f:
                svg_content = f.read()
            
            os.remove(latest_file)
            print(f"Successfully sent: {latest_file}")
            return {"status": "ok", "svg": svg_content}
        
        raise Exception(f"Файл не найден в {output_dir}. Проверь права доступа.")

    except Exception as e:
        print(f"Ошибка: {e}")
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)