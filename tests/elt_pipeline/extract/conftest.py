# pylint: skip-file
"""
Defines shared fixtures for the pytest test suite.
"""

import pytest


@pytest.fixture
def example_steam_api():
    """A pytest fixture that provides an example game data dictionary for testing."""
    steam_api_example = {
        "10": {
            "success": True,
            "data": {
                "type": "game",
                "name": "Counter-Strike",
                "steam_appid": 10,
                "required_age": 0,
                "is_free": False,
                "detailed_description": "Play the world's number 1 online action game. Engage in an incredibly realistic brand of terrorist warfare in this wildly popular team-based game. Ally with teammates to complete strategic missions. Take out enemy sites. Rescue hostages. Your role affects your team's success. Your team's success affects your role.",
                "about_the_game": "Play the world's number 1 online action game. Engage in an incredibly realistic brand of terrorist warfare in this wildly popular team-based game. Ally with teammates to complete strategic missions. Take out enemy sites. Rescue hostages. Your role affects your team's success. Your team's success affects your role.",
                "short_description": "Play the world's number 1 online action game. Engage in an incredibly realistic brand of terrorist warfare in this wildly popular team-based game. Ally with teammates to complete strategic missions. Take out enemy sites. Rescue hostages. Your role affects your team's success. Your team's success affects your role.",
                "supported_languages": "English\u003Cstrong\u003E*\u003C/strong\u003E, French\u003Cstrong\u003E*\u003C/strong\u003E, German\u003Cstrong\u003E*\u003C/strong\u003E, Italian\u003Cstrong\u003E*\u003C/strong\u003E, Spanish - Spain\u003Cstrong\u003E*\u003C/strong\u003E, Simplified Chinese\u003Cstrong\u003E*\u003C/strong\u003E, Traditional Chinese\u003Cstrong\u003E*\u003C/strong\u003E, Korean\u003Cstrong\u003E*\u003C/strong\u003E\u003Cbr\u003E\u003Cstrong\u003E*\u003C/strong\u003Elanguages with full audio support",
                "header_image": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/header.jpg?t=1745368572",
                "capsule_image": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/capsule_231x87.jpg?t=1745368572",
                "capsule_imagev5": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/capsule_184x69.jpg?t=1745368572",
                "website": None,
                "pc_requirements": {
                    "minimum": "\n\t\t\t\u003Cp\u003E\u003Cstrong\u003EMinimum:\u003C/strong\u003E 500 mhz processor, 96mb ram, 16mb video card, Windows XP, Mouse, Keyboard, Internet Connection\u003Cbr /\u003E\u003C/p\u003E\n\t\t\t\u003Cp\u003E\u003Cstrong\u003ERecommended:\u003C/strong\u003E 800 mhz processor, 128mb ram, 32mb+ video card, Windows XP, Mouse, Keyboard, Internet Connection\u003Cbr /\u003E\u003C/p\u003E\n\t\t\t"
                },
                "mac_requirements": {
                    "minimum": "Minimum: OS X  Snow Leopard 10.6.3, 1GB RAM, 4GB Hard Drive Space,NVIDIA GeForce 8 or higher, ATI X1600 or higher, or Intel HD 3000 or higher Mouse, Keyboard, Internet Connection"
                },
                "linux_requirements": {
                    "minimum": "Minimum: Linux Ubuntu 12.04, Dual-core from Intel or AMD at 2.8 GHz, 1GB Memory, nVidia GeForce 8600/9600GT, ATI/AMD Radeaon HD2600/3600 (Graphic Drivers: nVidia 310, AMD 12.11), OpenGL 2.1, 4GB Hard Drive Space, OpenAL Compatible Sound Card"
                },
                "developers": [
                    "Valve"
                ],
                "publishers": [
                    "Valve"
                ],
                "price_overview": {
                    "currency": "GBP",
                    "initial": 719,
                    "final": 719,
                    "discount_percent": 0,
                    "initial_formatted": "",
                    "final_formatted": "£7.19"
                },
                "packages": [574941, 7],
                "package_groups": [
                    {
                        "name": "default",
                        "title": "Buy Counter-Strike",
                        "description": "",
                        "selection_text": "Select a purchase option",
                        "save_text": "",
                        "display_type": 0,
                        "is_recurring_subscription": "false",
                        "subs": [
                            {
                                "packageid": 7,
                                "percent_savings_text": " ",
                                "percent_savings": 0,
                                "option_text": "Counter-Strike: Condition Zero - £7.19",
                                "option_description": "",
                                "can_get_free_license": "0",
                                "is_free_license": False,
                                "price_in_cents_with_discount": 719
                            },
                            {
                                "packageid": 574941,
                                "percent_savings_text": " ",
                                "percent_savings": 0,
                                "option_text": "Counter-Strike - Commercial License - £7.19",
                                "option_description": "",
                                "can_get_free_license": "0",
                                "is_free_license": False,
                                "price_in_cents_with_discount": 719
                            }
                        ]
                    }
                ],
                "platforms": {
                    "windows": True,
                    "mac": True,
                    "linux": True
                },
                "metacritic": {
                    "score": 88,
                    "url": "https://www.metacritic.com/game/pc/counter-strike?ftag=MCD-06-10aaa1f"
                },
                "categories": [
                    {
                        "id": 1,
                        "description": "Multi-player"
                    },
                    {
                        "id": 49,
                        "description": "PvP"
                    },
                    {
                        "id": 36,
                        "description": "Online PvP"
                    },
                    {
                        "id": 37,
                        "description": "Shared/Split Screen PvP"
                    },
                    {
                        "id": 66,
                        "description": "Color Alternatives"
                    },
                    {
                        "id": 68,
                        "description": "Custom Volume Controls"
                    },
                    {
                        "id": 75,
                        "description": "Keyboard Only Option"
                    },
                    {
                        "id": 69,
                        "description": "Stereo Sound"
                    },
                    {
                        "id": 8,
                        "description": "Valve Anti-Cheat enabled"
                    },
                    {
                        "id": 62,
                        "description": "Family Sharing"
                    }
                ],
                "genres": [
                    {
                        "id": "1",
                        "description": "Action"
                    }
                ],
                "screenshots": [
                    {
                        "id": 0,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000132.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000132.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 1,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000133.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000133.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 2,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000134.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000134.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 3,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000135.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000135.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 4,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000136.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000000136.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 5,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002540.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002540.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 6,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002539.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002539.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 7,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002538.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002538.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 8,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002537.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002537.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 9,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002536.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002536.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 10,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002541.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002541.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 11,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002542.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002542.1920x1080.jpg?t=1745368572"
                    },
                    {
                        "id": 12,
                        "path_thumbnail": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002543.600x338.jpg?t=1745368572",
                        "path_full": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/0000002543.1920x1080.jpg?t=1745368572"
                    }
                ],
                "recommendations": {
                    "total": 161239
                },
                "release_date": {
                    "coming_soon": False,
                    "date": "1 Nov, 2000"
                },
                "support_info": {
                    "url": "http://steamcommunity.com/app/10",
                    "email": ""
                },
                "background": "https://store.akamai.steamstatic.com/images/storepagebackground/app/10?t=1745368572",
                "background_raw": "https://store.akamai.steamstatic.com/images/storepagebackground/app/10?t=1745368572",
                "content_descriptors": {
                    "ids": [2, 5],
                    "notes": "Includes intense violence and blood."
                },
                "ratings": {
                    "usk": {
                        "rating": "16"
                    },
                    "dejus": {
                        "rating_generated": "1",
                        "rating": "14",
                        "required_age": "14",
                        "banned": "0",
                        "use_age_gate": "0",
                        "descriptors": "Violência"
                    },
                    "steam_germany": {
                        "rating_generated": "1",
                        "rating": "16",
                        "required_age": "16",
                        "banned": "0",
                        "use_age_gate": "0",
                        "descriptors": "Drastische Gewalt"
                    }
                }
            }
        }
    }
    return steam_api_example


@pytest.fixture
def example_two_games_html():
    """A pytest fixture that provides an example of 2 steam games html for testing."""
    two_games = """
    <html>
    <body>
    <a href="https://store.steampowered.com/app/10/CounterStrike/" data-ds-appid="10">
        <span class="title">Counter-Strike</span>
        <div class="col search_released responsive_secondrow">
        Nov 1, 2000
        </div>
    </a>
    <a href="https://some-other-link.com">A link to ignore</a>
    <a href="https://store.steampowered.com/app/730/CS2/" data-ds-appid="730">
        <span class="title">Counter-Strike 2</span>
        <div class="col search_released responsive_secondrow">  Aug 21, 2012   </div>
    </a>
    </body>
    </html>
    """
    return two_games


@pytest.fixture
def example_failure_html():
    """A pytest fixture that provides an example of a failure html for testing."""
    steam_failure = {
        "1": {
            "success": False
        }
    }
    return steam_failure
