"""Module that implements a basic websocket server
"""
import asyncio
import signal
import json
import logging
import time
import websockets

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
    def __init__(self, host: str='localhost', port: int=8080):
        """
        Initializes the WebSocket server with host, port, and message queues.

        Parameters
        ----------
        host : str
            The IP address to bind the server to, by default localhost
        port : int
            The port number to listen on, by default 8080
        """
        self.host = host
        self.port = port
        self.receive_queue = asyncio.Queue()
        self.send_queue = asyncio.Queue()
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
        logger.debug('server.handler: %s', path)
        initial_message = await websocket.recv()
        data:dict = json.loads(initial_message)
        client_id = data.get("uuid")
        client_offset = time.time() - data.get('time',0)
        if not client_id:
            logger.error("No UUID provided by client. Closing connection.")
            await websocket.close()
            return

        self.clients[client_id] = {'ws': websocket, 'time_offset': client_offset}

        logger.info('New connection established from %s', websocket.remote_address)
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
                await asyncio.gather(*(self._send_message(client, message)
                                        for client in self.clients.values()
                                        if client['ws'] is not None))

    async def _send_message(self,
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
        logger.debug('server.sendmessage: message=%s', message)
        logger.debug('server.sendmessage: type(client)=%s', type(client))
        logger.debug('server.sendmessage: type(client[\'ws\'])=%s', type(client["ws"]))
        logger.debug('server.sendmessage: type(client[\'time_offset\'])=%s',
                        type(client["time_offset"]))
        message['offset'] = client['time_offset']
        logger.info('sending: %s', json.dumps(message))
        await client['ws'].send(json.dumps(message))

    async def send(self, message: dict):
        """Send message to the server

        Parameters
        ----------
        message : dict
            Dictionary message to send to the server

        Raises
        ------
        TypeError
            Raised when message is not of type dict
        """
        if isinstance(message, dict):
            await self.send_queue.put(message)
        else:
            raise TypeError(f'Only dicts can be sent, not {type(message)}')

    def get_messages(self) -> list:
        """Gets all current received messages in the queue.
            If the queue is empty, returns empty list

        Returns
        -------
        list
            All messages currently in the queue
        """
        ret = []
        while not self.receive_queue.empty():
            try:
                msg = self.receive_queue.get_nowait()
                logger.debug('server.get_messages: received %s', msg)
                ret.append(msg)
            except asyncio.QueueEmpty:
                pass
            self.receive_queue.task_done()
        logger.debug('server.get_messages: returning %s', ret)
        return ret

    async def run(self):
        """
        Starts the WebSocket server and manages client connections.
        """
        websocket_server = await websockets.serve(self.handler, self.host, self.port)
        logger.info('WebSocket server started on %s:%s', self.host, self.port)

        broadcaster_task = asyncio.create_task(self.broadcaster())

        try:
            await websocket_server.wait_closed()
        finally:
            broadcaster_task.cancel()


async def process_messages(message_server: Server):
    """Processes received messages, collects them into a dictionary,
        and adds them to the send queue periodically.

    Parameters
    ----------
    message_server : Server
        server to use to send and receive messages
    """
    gamestate = {}
    gamestate_updated = False
    while True:
        msgs: list[dict] = message_server.get_messages()
        for msg in msgs:
            logger.info(msg)
            for uuid, payload in msg.items():
                if payload == 'remove':
                    del gamestate[uuid]
                else:
                    gamestate[uuid] = payload
            logger.debug(msg)
            gamestate_updated = True
        if gamestate and gamestate_updated:
            await message_server.send(gamestate)
            gamestate_updated = False

        await asyncio.sleep(1)  # Prevents busy-waiting

def shutdown_handler(*args):
    """
    Handles server shutdown on receiving SIGINT (CTRL+C).
    """
    logger.debug(args)
    stop_event.set() # pylint: disable=possibly-used-before-assignment

if __name__ == "__main__":
    # server = Server("0.0.0.0", 8080)
    server = Server()

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    signal.signal(signal.SIGINT, shutdown_handler)

    loop.create_task(server.run())
    loop.create_task(process_messages(server))

    loop.run_until_complete(stop_event.wait())
    logger.info("Shutting down server...")
