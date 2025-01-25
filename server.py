import asyncio
import websockets
import signal
import logging
import json
import time

import websockets.asyncio
import websockets.asyncio.server

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Server:
    """
    WebSocket Server that listens on a specified host and port,
    manages connected clients, receives messages, and broadcasts messages.
    
    Attributes
    ----------
    host : str
        The IP address to bind the server to.
    port : int
        The port number to listen on.
    receive_queue : asyncio.Queue
        Queue for storing received messages.
    send_queue : asyncio.Queue
        Queue for messages to be broadcast to clients.
    clients : set
        A set of connected clients.
    """
    def __init__(self, host: str, port: int, receive_queue: asyncio.Queue, send_queue: asyncio.Queue):
        """
        Initializes the WebSocket server with host, port, and message queues.

        Parameters
        ----------
        host : str
            The IP address to bind the server to.
        port : int
            The port number to listen on.
        receive_queue : asyncio.Queue
            Queue for storing received messages.
        send_queue : asyncio.Queue
            Queue for messages to be broadcast to clients.
        """
        self.host = host
        self.port = port
        self.receive_queue = receive_queue
        self.send_queue = send_queue
        self.clients: dict[str,dict] = {}

    async def handler(self, websocket: websockets.ServerProtocol, path: str|None=None):
        """
        Handles incoming WebSocket connections and messages.

        Parameters
        ----------
        websocket : websockets.ServerProtocol
            The WebSocket connection.
        path : str
            The request path for the WebSocket connection.
        """
        initial_message = await websocket.recv()
        data:dict = json.loads(initial_message)
        client_id = data.get("uuid")
        client_offset = time.time() - data.get('time',0)
        if not client_id:
            logger.error("No UUID provided by client. Closing connection.")
            await websocket.close()
            return

        self.clients[client_id] = {'ws': websocket, 'time_offset': client_offset}

        logger.info(f"New connection established from {websocket.remote_address}")
        try:
            async for message in websocket:
                await self.receive_queue.put({client_id: json.loads(message)})
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.receive_queue.put({client_id: 'remove'})
            self.clients[client_id] = {'ws': None, 'time_offset': 0}

    async def broadcaster(self):
        """
        Broadcasts messages from the send queue to all connected clients.
        """
        while True:
            message = await self.send_queue.get()
            logging.info('broadcaster: sending %s', str(message))
            if message:
                await asyncio.gather(*(self.send_message(client, message) 
                                        for client in self.clients.values() 
                                        if client['ws'] is not None))

    async def send_message(self, 
                            client: dict[str,websockets.asyncio.server.ServerConnection|float], 
                            message: dict[str,dict[str,str|list[int]]]):
        """Send a message to a connected client, appending the time offset for that client and 
            removing the enrty for the client being sent the message

        Parameters
        ----------
        client : dict[str,websockets.asyncio.server.ServerConnection | float]
            Client dictionary with their websocket in [ws] and time offset in [time_offset]
        message : dict[str,dict[str,str|list[int]]]
            Message to send to the connected client
        """
        logger.debug(f'{type(client)=}')
        logger.debug(f'{type(client["ws"])=}')
        logger.debug(f'{type(client["time_offset"])=}')
        message['offset'] = client['time_offset']
        logger.info('sending: %s', json.dumps(message))
        await client['ws'].send(json.dumps(message))

    async def run(self):
        """
        Starts the WebSocket server and manages client connections.
        """
        server = await websockets.serve(self.handler, self.host, self.port)
        logger.info(f"WebSocket server started on {self.host}:{self.port}")
        
        broadcaster_task = asyncio.create_task(self.broadcaster())
        
        try:
            await server.wait_closed()
        finally:
            broadcaster_task.cancel()


async def process_messages():
    """
    Processes received messages, collects them into a dictionary,
    and adds them to the send queue periodically.
    """
    gamestate = {}
    gamestate_updated = False
    while True:
        while not receive_queue.empty():
            msg:dict = await receive_queue.get()
            logger.info(msg)
            for uuid, payload in msg.items():
                if payload == 'remove':
                    del gamestate[uuid]
                else:
                    gamestate[uuid] = payload
            logger.debug(msg)
            gamestate_updated = True
        if gamestate and gamestate_updated:
            await send_queue.put(gamestate)
            gamestate_updated = False
        
        await asyncio.sleep(1)  # Prevents busy-waiting

def shutdown_handler(*args):
    """
    Handles server shutdown on receiving SIGINT (CTRL+C).
    """
    stop_event.set()

if __name__ == "__main__":
    receive_queue = asyncio.Queue()
    send_queue = asyncio.Queue()
    server = Server("0.0.0.0", 8080, receive_queue, send_queue)

    
    loop = asyncio.get_event_loop()
    
    stop_event = asyncio.Event()
    
    signal.signal(signal.SIGINT, shutdown_handler)
    
    loop.create_task(server.run())
    loop.create_task(process_messages())
    
    loop.run_until_complete(stop_event.wait())
    logger.info("Shutting down server...")
