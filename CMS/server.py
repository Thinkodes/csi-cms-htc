"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import time
import flask
from flask_websockets import WebSocket, WebSockets
import os
import logging
import traceback
from functools import wraps
import base64
from googletrans import Translator

from .utils import (
    logger_file, 
    logger, 
    get_image_file, 
    get_images_file, 
    cv2image_to_base64, 
    recognize_from_wav_bytes,
    DetectionPrompts)
from .florence import florence_endpoint
if "CMS_ACTIVE" in os.environ:
    from .alerts_database import alerts_database
from .room import Room
from .graph_solver import rooms_to_nodes, get_optimal_path, Node
if "CMS_ACTIVE" in os.environ:
    from .tts import generate_tts
    from .facial_recognition.database import face_database
from .gradient import create_gradient

app = flask.Flask(__name__)

websocket_app = WebSockets(app)
translator = Translator()

PA_SYSTEM_AUTHERIZED = False
ADMIN_IP = "127.0.0.1" if "CMS_LOCAL_ADMIN" in os.environ else None
AUTHERIZED_IPS = ["127.0.0.1"] # localhost is already autherized.

ROOMS: dict[str, Room] = {}

#region setup logging
def safe_runner(url, *, router=app.route, **flask_kwargs):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger.info(f"Calling the Endpoint: {url}")
            logger.debug(f"Calling: {f.__qualname__}")
            try:
                return f(*args, **kwargs)
            except:
                error_string = traceback.format_exc()
                logger.error(f"During request: {f.__qualname__}, There was an error: \n{error_string}")
                return flask.jsonify({"error": error_string}), 500
        return router(url, **flask_kwargs)(wrapper)
    return decorator

def intercept_flask_logging():
    flask_logger = logging.getLogger('werkzeug')
    
    flask_logger.handlers.clear()
    
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
                
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # flask_logger.addHandler(InterceptHandler())
    
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
intercept_flask_logging()

#endregion
#region setup error handing
@app.errorhandler(404)
def http_error_handler(_):
    return flask.jsonify({"error": "Page Not found."}), 404

@app.errorhandler(405)
def http_error_handler(_):
    return flask.jsonify({"error": "Unautherized."}), 405
#endregion

@safe_runner("/")
def get_logs():
    return open(logger_file, "r").read(), 200

#region Analyze
@safe_runner("/analyze", methods=["POST"])
def analyze():
    """Analyze the given image using florence, 
    the prompts must either be yes or no, or counting
    as florence is simply a model for detection.

    request must contain "image" in flask.request.json, containing .png in base64 format.
    request must contain "prompts" in flask.request.json, containing  list of prompts.

    Returns:
        flask.Response: json response which contains results these are the results of the prompts
        with the given image
    """
    logger.info("Analyzing...")
    logger.debug(f"{flask.request.json['prompts']}")
    results = florence_endpoint(get_image_file(), flask.request.json['prompts'])
    return flask.jsonify({"results": results}), 200

#endregion
#region Alerts
#region set-alerts
@safe_runner("/set-urgent", methods=["POST"])
def set_urgent():
    """Add a urgent message through the alerts channel

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    if not flask.request.remote_addr in AUTHERIZED_IPS:
        logger.warning(f"UNAUTHERIZED IP: {flask.request.remote_addr} tried to access.")
        logger.debug(f"AUTHERIZED IPS: {AUTHERIZED_IPS}")
        return "", 405
    logger.info(f"Adding Urgent Message: {flask.request.json["message"]} from Autherized IP: {flask.request.remote_addr}")
    alerts_database.register_urgent_alert(dict(flask.request.json))
    return "", 200

@safe_runner("/set-warning", methods=["POST"])
def set_warning():
    """Add a warning message through the alerts channel

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    if not flask.request.remote_addr in AUTHERIZED_IPS:
        logger.warning(f"UNAUTHERIZED IP: {flask.request.remote_addr} tried to access.")
        logger.debug(f"AUTHERIZED IPS: {AUTHERIZED_IPS}")
        return "", 405
    logger.info(f"Adding Warning Message: {flask.request.json["message"]} from Autherized IP: {flask.request.remote_addr}")
    alerts_database.register_warning_alert(dict(flask.request.json))
    return "", 200

@safe_runner("/set-information", methods=["POST"])
def set_information():
    """Add a information message through the alerts channel

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    if not flask.request.remote_addr in AUTHERIZED_IPS:
        logger.warning(f"UNAUTHERIZED IP: {flask.request.remote_addr} tried to access.")
        logger.debug(f"AUTHERIZED IPS: {AUTHERIZED_IPS}")
        return "", 405
    logger.info(f"Adding Informational Message: {flask.request.json["message"]} from Autherized IP: {flask.request.remote_addr}")
    alerts_database.register_information_alert(dict(flask.request.json))
    return "", 200
#endregion
#region automate

@safe_runner("/automate/alerts/urgent")
def automate_urgent():
    """check for a urgent message through the alerts channel

    THIS IS A MOBILE ENDPOINT AND WILL NOT GIVE A JSON RESPONSE.

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    if not flask.request.remote_addr in AUTHERIZED_IPS:
        logger.warning(f"UNAUTHERIZED IP: {flask.request.remote_addr} tried to access.")
        return "", 405
    logger.debug(f"Autherized IP: {flask.request.remote_addr} is fetching urgent channel alerts.")
    res = alerts_database.get_newest_urgent_alert()
    if res == None:
        return "", 204
    return res, 200

@safe_runner("/automate/alerts/warning")
def automate_warning():
    """check for a warning message through the alerts channel

    THIS IS A MOBILE ENDPOINT AND WILL NOT GIVE A JSON RESPONSE.

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    if not flask.request.remote_addr in AUTHERIZED_IPS:
        logger.warning(f"UNAUTHERIZED IP: {flask.request.remote_addr} tried to access.")
        return "", 405
    logger.debug(f"Autherized IP: {flask.request.remote_addr} is fetching warning channel alerts.")
    res = alerts_database.get_newest_warning_alert()
    if res == None:
        return "", 204
    return res, 200

@safe_runner("/automate/alerts/information")
def automate_information():
    """check for a information message through the alerts channel

    THIS IS A MOBILE ENDPOINT AND WILL NOT GIVE A JSON RESPONSE.

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    if not flask.request.remote_addr in AUTHERIZED_IPS:
        logger.warning(f"UNAUTHERIZED IP: {flask.request.remote_addr} tried to access.")
        return "", 405
    logger.debug(f"Autherized IP: {flask.request.remote_addr} is fetching information channel alerts.")
    res = alerts_database.get_newest_information_alert()
    if res == None:
        return "", 204
    return res, 200
#endregion
#region get-alerts
@safe_runner("/alerts/urgent")
def urgent():
    """check for a urgent message through the alerts channel

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    res = alerts_database._get_newest_alert("urgent")
    if res == None:
        return flask.jsonify({"message": "", "exists": False, "timestamp": ""}), 200
    res["exists"] = True
    return flask.jsonify(res), 200

@safe_runner("/alerts/warning")
def warning():
    """check for a warning message through the alerts channel

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    res = alerts_database._get_newest_alert("warnings")
    if res == None:
        return flask.jsonify({"message": "", "exists": False, "timestamp": ""}), 200
    res["exists"] = True
    return flask.jsonify(res), 200

@safe_runner("/alerts/information")
def information():
    """check for a information message through the alerts channel

    Returns:
        flask.Response: success if from an autherized IP address, must be autherized from /autherize by
        the admin IP. otherwise 405
    """
    res = alerts_database._get_newest_alert("information")
    if res == None:
        return flask.jsonify({"message": "", "exists": False, "timestamp": ""}), 200
    res["exists"] = True
    return flask.jsonify(res), 200
#endregion
#region autherize-alerts
@safe_runner("/alerts/unautherized-urgent", methods=["POST"])
def to_autherize_alerts():
    return flask.jsonify(alerts_database.get_unautherized(flask.request.json["room_id"] if "room_id" in flask.request.json else None)), 200

@safe_runner("/alerts/autherize-urgent", methods=["POST"])
def autherize_alerts():
    alerts_database.autherize(int(flask.request.json["alert_id"])) # autherize the urgent alert.
    return flask.jsonify({"success": True}), 200
#endregion
#endregion
#region PA-system
@safe_runner("/pa-system")
def pa_system():
    if not PA_SYSTEM_AUTHERIZED:
        return flask.jsonify({"message": "The PA System is not currently announcing. If required ask admin to autherize."}), 405
    res: dict = alerts_database._get_newest_alert("urgent")
    if res["room_id"] != None:
        room_id = res["room_id"]
        room = ROOMS[room_id]
        logger.info(f"Getting Escape route from room_id: {room_id}")
        nodes = rooms_to_nodes(ROOMS)
        logger.debug(f"Nodes: {nodes}")
        path: list[Node] = get_optimal_path(nodes[room_id], [nodes[room_id] for room_id in nodes if nodes[room_id].is_outer])
        logger.debug(f"Path: {path}")

        # we are not considering what happens when we can't find an escape route in such a situation.
        # because the crowd doesn't need to know that, it would only make a already panaking situation
        # much much worse.
        if path != None:
            res["escape-path"] = {"path": " ->".join([node.name for node in path[0]])}
        tts_res = generate_tts(" ".join([f"WARNING WARNING, {res["message"]}, In Room {room.room_name}, this is not a drill, I repeat"]*5))
    else:
        tts_res = generate_tts(f"WARNING WARNING, {res["message"]}")
    
    res["mp3"] = tts_res["mp3"]
    res["wav"] = tts_res["wav"]
        
    return flask.jsonify(res), 200
#endregion
#region Security

@safe_runner("/admin")
def register_admin():
    global ADMIN_IP
    """Register an IP address as the Admin IP, this admin can this call /autherize.

    Returns:
        flask.Response: if an Admin IP already exists then 405, otherwise the admin
        is registered and success is returned.
    """
    if ADMIN_IP == None:
        ADMIN_IP = flask.request.remote_addr
        AUTHERIZED_IPS.append(ADMIN_IP)
    else:
        return "", 405
    return "", 200

@safe_runner("/autherize", methods=["POST"])
def autherize_ips():
    """add an autherized ip address

    must contain "ip" in flask.request.json, flask.reques.remote_addr of the device so that it may be checked
    as equal on a autherized endpoint.

    Returns:
        _type_: _description_
    """
    if flask.request.remote_addr == ADMIN_IP:
        AUTHERIZED_IPS.append(flask.request.json["ip"])
    else:
        return "", 405
    return "", 200

@safe_runner("/autherize-pa")
def autherize_pa_system():
    # TODO: Make this Possible with the special token given to each user.
    global PA_SYSTEM_AUTHERIZED
    if flask.request.remote_addr != ADMIN_IP:
        return "", 405
    PA_SYSTEM_AUTHERIZED = True
    logger.warning("The PA System has been autherized by the admin, the latest urgent message will now be given to the PA system, this is meant only for urgent emergencies.")
    return "", 200

@safe_runner("/is-autherized", methods=["POST"])
def check_autherization_ip():
    """Check if the IP given has autherization

    requred post argument "ip", the ip to check

    Returns:
        flask.Response: 200 if autherized. 405 otherwise.
    """
    if (flask.request.json["ip"] in AUTHERIZED_IPS):
        return "", 200
    return "", 405

#endregion
#region Rooms

@safe_runner("/room/get-all-escape-routes")
def get_all_escape_routes():
    rooms_to_escape = {}
    for room_id in ROOMS.keys():
        logger.info(f"Getting Escape route from room_id: {room_id}")
        nodes = rooms_to_nodes(ROOMS)
        logger.debug(f"Nodes: {nodes}")
        path: list[Node] = get_optimal_path(nodes[room_id], [nodes[room_id] for room_id in nodes if nodes[room_id].is_outer])
        logger.debug(f"Path: {path}")
        if path == None:
            rooms_to_escape[ROOMS[room_id].room_name] = []
        else:
            rooms_to_escape[ROOMS[room_id].room_name] = [node.name for node in path[0]]
    return flask.jsonify(rooms_to_escape), 200

@safe_runner("/room/create/<room_id>", methods=["POST"])
def create_room(room_id):
    """Create an Room Object

    must be in the format /room/create/<room_id>
    room_id being replaced by the string which is to identify
    the room.

    must contain "name" in flask.request.json, name of the room, will be used for escape route
    calculations.

    must contain "capacity" in flask.request.json, capacity of the room.

    must contain "exit" in flask.request.json, boolean value of whether or not the room
    contains an exit to the building.

    Args:
        room_id (str): the id of the room being created.

    Returns:
        flask.Response: 200
    """
    logger.info(f"Creating Room: {flask.request.json["name"]}")
    logger.debug(f"Creating Room with info: {dict(flask.request.json)}")
    if room_id in ROOMS:
        logger.warning("Room Already Exists."), 203
    ROOMS[room_id] = Room(room_id, flask.request.json["name"], int(flask.request.json["capacity"]), flask.request.json["exit"])
    logger.debug(ROOMS)
    return "", 200

@safe_runner("/room/get-exit-rooms")
def get_room_status():
    exits = []
    for room_id in ROOMS.keys():
        room = ROOMS[room_id]
        if room.is_exit:
            exits.append(room.room_name)
    return flask.jsonify({"exits": exits})


@safe_runner("/room/<room_id>", router=websocket_app.route)
def room_stream(ws: WebSocket, room_id: str):
    """A websocket, this will continously recieve the frames of the cctv footage.
    the last two frames will be kept, as to be used in calculating the vector map.
    and other room calculations.

    must be in the format /room/<room_id>
    room_id being replaced by the string which is to identify
    the room.

    websocket connections only.


    Args:
        room_id (str): the id of the room to which this feed belongs.
        ws (WebSocket): the websocket connection.
    
    no return.
    """
    if not room_id in ROOMS:
        logger.warning("The websocket is being closed, since the room_id requested does not exist.")
        return "", 404
    while True:
        try:
            recieved_data = get_image_file(ws.receive())
        except:
            logger.error(f"Error Recieving Data: {traceback.format_exc()}")
        ROOMS[room_id].append_frame(recieved_data)

@safe_runner("/room/add-connection", methods=["POST"])
def add_connection():
    """Define two rooms rooms as having a connected corridoor
    for the purposes of escape room calculations only.

    must contain "room_id" in flask.request.json, the id of the room in question.
    must contain "connected_rooms" in flask.request.json, the ids of the rooms
    to connect to the room in question.

    Returns:
        flask.Response: 200
    """
    room = ROOMS[flask.request.json["room_id"]]
    logger.info(f"Adding connection between {flask.request.json["room_id"]} and {flask.request.json["connected_rooms"]}")
    logger.debug(f"{room}")
    for room_id in flask.request.json["connected_rooms"]:
        room.connect_room(room_id)
    return "", 200

@safe_runner("/room/remove", methods={"POST"})
def remove_room():
    """Remove the Room specified

    a "room_id" must be given, this is the room removed.

    Returns:
        flask.Resposne: 200 is removed properly.
    """

    room = ROOMS[flask.request.json["room_id"]]
    room.remove()
    del ROOMS[flask.request.json["room_id"]]
    return "", 200

@safe_runner("/room/reset")
def reset_all_rooms():
    """Reset all rooms.

    Returns:
        flask.Response: 200
    """
    room_ids = list(ROOMS.keys())
    for room_id in room_ids:
        room = ROOMS[room_id]
        room.remove()
        del ROOMS[room_id]
    return "", 200

@safe_runner("/room/population/<room_id>")
def population(room_id):
    """Calculates the number of people in the given
    room.

    Args:
        room_id (str): the room id of the room in question.

    Returns:
        flask.Response: 200
    """
    logger.info(f"Getting the population of the room: {room_id}")
    return flask.jsonify({"population": ROOMS[room_id].population()}), 200

@safe_runner("/room/density/<room_id>")
def density(room_id):
    """Calculates density of people in the given
    room.

    Args:
        room_id (str): the room id of the room in question.

    Returns:
        flask.Response: 200
    """
    logger.info(f"Getting the density of the room: {room_id}")
    return flask.jsonify({"density": ROOMS[room_id].density()}), 200

@safe_runner("/room/vectormap/<room_id>")
def vector_map(room_id):
    """Calculates a vector map of people in the given
    room.

    Args:
        room_id (str): the room id of the room in question.

    Returns:
        flask.Response: 200, vector_data which contains track_history
    """
    logger.info(f"Getting the Vector Map of the room: {room_id}")
    return flask.jsonify({"vector_data": ROOMS[room_id].vector_map()}), 200

@safe_runner("/room/escape-route/<room_id>")
def escape_route(room_id):
    """Closest Escape route from the given room

    Args:
        room_id (str): room id of the room in question

    Returns:
        flask.Response: 200
    """
    logger.info(f"Getting Escape route from room_id: {room_id}")
    nodes = rooms_to_nodes(ROOMS)
    logger.debug(f"Nodes: {nodes}")
    path: list[Node] = get_optimal_path(nodes[room_id], [nodes[room_id] for room_id in nodes if nodes[room_id].is_outer])
    logger.debug(f"Path: {path}")
    if path == None:
        return flask.jsonify({"error": "No Path found...."}), 204
    return flask.jsonify({"path": " ->".join([node.name for node in path[0]])}), 200

@safe_runner("/room/is-autherized/<room_id>")
def is_autherized(room_id):
    """Get a List of people within the room, and whether any of them are autherized.
    this uses a very different machanism to get-people so it makes sure that 

    Args:
        room_id (str): The Room ID.

    Returns:
        flask.Response: "people" and "image" keys.
    """
    room = ROOMS[room_id]

    autherization, frame = room._check_for_autherization()

    return flask.jsonify({"people": autherization, "image": cv2image_to_base64(frame)}), 200

@safe_runner("/room/get-people/<room_id>")
def get_people(room_id):
    """Get the description of every autherized person in the room as per
    database.

    Args:
        room_id (str): the id of the room.

    Returns:
        flask.Response: detailes of every autherized person in the room.
    """
    room = ROOMS[room_id]
    
    while room._processing_frame:
        logger.warning("ASked for number people, room is getting processed, this will take some time...")
        time.sleep(1)
    
    result = [{
            'unique_key': person['unique_key'],
            # 'image': person['image_data'],
            'timestamp': person['timestamp'],
            "name": person["name"],
            "desc": person["desc"],
        } for person in room.people]
    return flask.jsonify({"people":result}), 200

@safe_runner("/room/check-danger/<room_id>")
def check_danger_room(room_id):
    """Check for dangers, same as the danger utility automatically apply to room.

    Args:
        room_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    room = ROOMS[room_id]
    return flask.jsonify(room.danger_checks()), 200

@safe_runner("/room/gradient/<room_id>")
def room_create_gradient(room_id):
    """Create Gradient from the Room CCTV

    Args:
        room_id (str): The ID of the room

    Returns:
        flask.Response: either Null or the image.
    """
    room = ROOMS[room_id]
    return flask.jsonify(room._create_gradient(flask.request.json["kernel_size"], flask.request.json["scale_factor"])), 200

#endregion
#region Utility
#region Danger Detection

@safe_runner("/utility/generate/vector-map", methods=["POST"])
def generate_vector_map():
    room = Room("", "ABC", 100, False)
    room.past_frames.append(get_image_file())
    return flask.jsonify({"vector_data": room.vector_map()}), 200

@safe_runner("/utility/detection/fire", methods=["POST"])
def ultility_fire():
    """Utility function to check for fire, can be done by analyze.

    request must contain "image" in flask.request.json, containing .png in base64 format.

    Returns:
        flask.Response: yes or no.
    """
    result = florence_endpoint(get_image_file(), [DetectionPrompts.FIRE])[0]
    return flask.jsonify({"result":"yes" in result.lower()}), 200

@safe_runner("/utility/detection/stampeed", methods=["POST"])
def ultility_stampeed():
    """Utility function to check for stampeed, can be done by analyze.

    request must contain "image" in flask.request.json, containing .png in base64 format.

    Returns:
        flask.Response: yes or no.
    """
    result = florence_endpoint(get_image_file(), [DetectionPrompts.STAMPEED])[0]
    return flask.jsonify({"result":"yes" in result.lower()}), 200

@safe_runner("/utility/detection/fall", methods=["POST"])
def ultility_fall():
    """Utility function to check for fall, can be done by analyze.

    request must contain "image" in flask.request.json, containing .png in base64 format.

    Returns:
        flask.Response: yes or no.
    """
    result = florence_endpoint(get_image_file(), [DetectionPrompts.FALL])[0]
    return flask.jsonify({"result":"yes" in result.lower()}), 200

@safe_runner("/utility/detection/smoke", methods=["POST"])
def ultility_smoke():
    """Utility function to check for smoke, can be done by analyze.

    request must contain "image" in flask.request.json, containing .png in base64 format.

    Returns:
        flask.Response: yes or no.
    """
    result = florence_endpoint(get_image_file(), [DetectionPrompts.SMOKE])[0]
    return flask.jsonify({"result":"yes" in result.lower()}), 200

@safe_runner("/utility/detection/voilence", methods=["POST"])
def ultility_voilence():
    """Utility function to check for voilence, can be done by analyze.

    request must contain "image" in flask.request.json, containing .png in base64 format.

    Returns:
        flask.Response: yes or no.
    """
    result = florence_endpoint(get_image_file(), [DetectionPrompts.VOILENCE])[0]
    return flask.jsonify({"result":"yes" in result.lower()}), 200

@safe_runner("/utility/detection/danger", methods=["POST"])
def ultility_danger():
    """Utility function to check for danger, can be done by analyze.

    request must contain "image" in flask.request.json, containing .png in base64 format.

    Returns:
        flask.Response: yes or no.
    """
    result = florence_endpoint(get_image_file(), [DetectionPrompts.DANGER])[0]
    return flask.jsonify({"result":"yes" in result.lower()}), 200
#endregion
#region Alternatives to websocket

@safe_runner("/utility/room/<room_id>", methods=["POST"])
def utility_update_room(room_id):
    room = ROOMS[room_id]

    room.append_frame(get_image_file())

    return "", 200

@safe_runner("/utility/audio/", methods=["POST"])
def utility_audio():
    """Transcribe Audio and return result

    Returns:
        flask.Response: Transcribed text from audio
    """
    if not "audio" in flask.request.json:
        logger.error("Audio was not given to /utility/audio")
        return flask.jsonify({"erorr": "audio json key, is required"}), 405

    recog = recognize_from_wav_bytes( base64.b64decode(flask.request.json["audio"]))

    logger.debug(f"Audio Recognized: {recog}")

    return flask.jsonify({"text": recog }), 200

@safe_runner("/utility/translate/", methods=["POST"])
def utility_translate():
    """translate text and return result

    Returns:
        flask.Response: translated text
    """
    if not "text" in flask.request.json:
        logger.error("text was not given to /utility/translate")
        return flask.jsonify({"erorr": "text json key, is required"}), 405

    return flask.jsonify({"text": translator.translate(flask.request.json["text"], dest='en').text.encode()}), 200

#endregion
#endregion
#region Facial Detection

@safe_runner("/facial-detection/insert-entry", methods=["POST"])
def facial_detect_insert():
    """Add a face, to the facial detection database

    Returns:
        flask.Response: 200
    """
    import random
    code = 200
    if not "names" in flask.request.json:
        return flask.jsonify({"error": "Must Contain names"}), 405
    if not "descs" in flask.request.json:
        return flask.jsonify({"error": "Must Contain descs"}), 405

    for i, face in enumerate(get_images_file()):
        name = flask.request.json["names"][i] if len(flask.request.json["names"]) > i else ""
        desc = flask.request.json["descs"][i] if len(flask.request.json["descs"]) > i else ""
        uid = "".join(random.choices("1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM", k=20))

        logger.debug(f"Added Face:\n {name=}\n {desc=}\n {uid=}")
        if not face_database.add_face(face,uid,name,desc):
            logger.warning("no face was detected in a given face.")
            code = 204
    
    return "", code

@safe_runner("/facial-detection/check-face", methods=["POST"])
def check_face():
    """Check if a face exists in the facial deteciton database.

    Returns:
        flask.Response: if found it will be that entry on the database, otherwise empty string and 404.
    """
    result = face_database.find_match(face_database._encode_face(get_image_file()))
    return flask.jsonify(result), 200

#endregion
#region Gradients
@safe_runner("/gradient", methods=["POST"])
def gradient():
    """A gradient of people is given.

    request must contain "image" in flask.request.json, containing .png in base64 format.

    Returns:
        flask.Response: image is base64, which is the gradient.
    """
    logger.debug("Gradient Is Being Calculated.")
    return flask.jsonify({"image" : cv2image_to_base64(create_gradient(get_image_file()))}), 200

#endregion 
#region Audio Services

@safe_runner("/audio", router=websocket_app.route)
def audio(ws: WebSocket):
    """A stream of audio is given and the transcribed is given back.

    Args:
        ws (WebSocket): Websocket class.
    """
    while True:
        audio_byte = ws.receive()
        ws.send(recognize_from_wav_bytes(audio_byte))

#endregion
#region Translation

@safe_runner("/translate", router=websocket_app.route)
def translate_text(ws: WebSocket):
    """it will translate to english.

    Args:
        ws (WebSocket): Websocket class.
    """
    while True:
        text = ws.receive().decode()
        ws.send(translator.translate(text, dest='en').text.encode())

#endregion

# if in debug, hot reload.
if "CMS_ACTIVE" in os.environ:
    app.run(port=8781, debug=("CMS_DEBUG" in os.environ))