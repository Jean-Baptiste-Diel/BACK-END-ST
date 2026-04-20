from api.utils.utils_func import call_tuya_api

def get_devices(access_token: str, uid: str):
    path = f"/v1.0/users/{uid}/devices"

    res = call_tuya_api(
        method="GET",
        path=path,
        access_token=access_token
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