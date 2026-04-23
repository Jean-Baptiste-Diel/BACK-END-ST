from api.utils.utils_func import call_tuya_api

def get_devices(access_token: str):
    path = "/v2.0/cloud/thing/device?page_size=20"

    res = call_tuya_api(
        method="GET",
        path=path,
        access_token=access_token,
        body={}
    )

    if not res or not res.get("success"):
        return {
            "success": False,
            "error": res
        }
    return {
        "success": True,
        "devices": res.get("result", [])
    }
