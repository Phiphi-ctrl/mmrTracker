
class RLWebsocketClient:
    def get_update_state(self) -> dict:
        mess = {
          "Event": "UpdateState",
          "Data": {
            "MatchGuid": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6",
            "Players": [
              {
                "Name": "PlayerA",
                "PrimaryId": "Steam|123|0",
                "Shortcut": 1,
                "TeamNum": 0,
                "Score": 125,
                "Goals": 1,
                "Shots": 2,
                "Assists": 0,
                "Saves": 1,
                "Touches": 14,
                "CarTouches": 3,
                "Demos": 0,
              },
            {
                "Name": "PlayerB",
                "PrimaryId": "Steam|1234|0",
                "Shortcut": 1,
                "TeamNum": 0,
                "Score": 125,
                "Goals": 1,
                "Shots": 2,
                "Assists": 0,
                "Saves": 1,
                "Touches": 14,
                "CarTouches": 3,
                "Demos": 0,
            },

            ],
            "Game": {
              "Teams": [
                {
                  "Name": "Blue",
                  "TeamNum": 0,
                  "Score": 1,
                  "ColorPrimary": "0000FF",
                  "ColorSecondary": "0000AA"
                }
              ],
              "TimeSeconds": 180,
              "Frame": 120,
              "Elapsed": 50.2,
              "Ball": {
                "Speed": 850.5,
                "TeamNum": 0
              },
              "bReplay": False,
              "bHasWinner": True,
              "Winner": "Blue",
              "Arena": "Stadium_P",
              "bHasTarget": True,
              "Target": {
                "Name": "PlayerA",
                "Shortcut": 1,
                "TeamNum": 0
              }
            }
          }
        }
        return mess