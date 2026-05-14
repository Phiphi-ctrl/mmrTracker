__all__ = ['RLWebsocketClient']


def __getattr__(name):
    if name == "RLWebsocketClient":
        from rl_api.websocket_client import RLWebsocketClient

        return RLWebsocketClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
