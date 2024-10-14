import base64
import pandas as pd
import requests
import streamlit as st
from streamlit_searchbox import st_searchbox
import time


# set title & image side by side
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Google Maps Places Autocomplete Demo")
    with col2:
        st.image("img/maps_logo.png", width=200)

st.markdown(
    """This is a demo of the Google Maps \
    [Places Autocomplete API](https://developers.google.com/maps/documentation/places/web-service/place-autocomplete) \
    in streamlit."""
)

input_key = st.text_input("Please use your own Google Maps API key", type="password")
st.caption("(not saved or written to disk)")
st.write(
    "Start writing an address, your dream vacation spot🏖️, or your favorite 🌮 shop below!"
)

api_key = (
    st.secrets.google_maps_key.key
    if st.secrets.google_maps_key.key
    else input_key if input_key else ""
)


def get_places_autocomplete_json(txt_input):
    """
    Uses requests to get autocomplete predictions from Google Maps API.
    """
    url = "https://places.googleapis.com/v1/places:autocomplete?fields=*"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    data = {"input": txt_input, "includeQueryPredictions": True}
    params = {"key": (api_key)}
    try:
        response = requests.post(
            url, headers=headers, json=data, params=params, timeout=10
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
    except requests.ConnectionError as e:
        st.error(f"Connection error: {e}")
    except requests.Timeout as e:
        st.error(f"Timeout error: {e}")
    except ValueError as e:
        st.error(f"JSON decoding error: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return None


def parse_places_autocomplete_json(json):
    """
    Parses the autocomplete predictions from the Google Maps API
    json into a list of labels.
    """
    labels = []
    for i in json["suggestions"]:
        labels.append(i["placePrediction"]["text"]["text"])
    return labels


def search_places(txt_input: str) -> list[any]:
    """
    Entry point for the searchbox. Uses the defined functions to get autocomplete
    predictions from the Google Maps API and parse them into a list of labels.
    """
    st.session_state["last_autocomplete_json"] = get_places_autocomplete_json(txt_input)
    time.sleep(0.5)
    return (
        parse_places_autocomplete_json(st.session_state["last_autocomplete_json"])
        if st.session_state["last_autocomplete_json"] is not None
        else []
    )


def get_place_lat_lng(place_id):
    """
    Uses requests to get place details from Google Maps API.
    """
    url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": (api_key),
        "fields": "geometry",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return (
            response.json()["result"]["geometry"]["location"]["lat"],
            response.json()["result"]["geometry"]["location"]["lng"],
        )
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
    except requests.ConnectionError as e:
        st.error(f"Connection error: {e}")
    except requests.Timeout as e:
        st.error(f"Timeout error: {e}")
    except ValueError as e:
        st.error(f"JSON decoding error: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return None


# pass search function to searchbox
selected_value = st_searchbox(
    search_function=search_places,
    key="places_searchbox",
)

place_latitude = None
place_longitude = None


# st.write(st.session_state["last_autocomplete_json"])


def address_callback():
    if selected_value is not None and "last_autocomplete_json" in st.session_state:
        suggestions = st.session_state["last_autocomplete_json"].get("suggestions", [])

        # Filter suggestions to only include those with a placeId
        valid_suggestions = [
            suggestion
            for suggestion in suggestions
            if "placePrediction" in suggestion
            and "placeId" in suggestion["placePrediction"]
        ]

        if valid_suggestions:
            place_id = valid_suggestions[0]["placePrediction"]["placeId"]
            place_latitude, place_longitude = get_place_lat_lng(place_id)

            if place_latitude is not None and place_longitude is not None:
                df = pd.DataFrame(
                    {"latitude": [place_latitude], "longitude": [place_longitude]}
                )
                st.map(
                    data=df, latitude="latitude", longitude="longitude", zoom=12, size=2
                )
        else:
            st.warning("No valid place suggestions found.")


address_callback()
