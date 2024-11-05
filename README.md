# TeamSpeak Bot

TeamSpeak server query bot. This bot is mainly an example project using the [TSBot](https://github.com/jykob/TSBot) framework.

## Features

### Admin

Collection of helpful debugging commands:

- `eval <eval str>`: Evaluates given python expression.
- `exec <exec str>`: Executes given python expression. Persists any side-effects.
- `quit`: Closes the bot.
- `send <query>`: Sends a raw query to the teamspeak server and return the response data.
- `spam <#lines> <text to be spammed>` : Spams the current ctx of the message.
- `nickname <nickname>`: Changes the bot nickname. If no nickname provided, defaults to the login name.

You probably don't want anyone running these commands, so they are locked behind checks. You can configure the bot to check for specific _uids_ or server groups that have the permission to run these commands.

### AFK Mover

Checks periodically for clients that haven't been active for given amount of time.  
If such clients are found, move them to specified _AFK_ channel.

If the bot doesn't find _AFK_ channel, it will try to create one.
You can white/blacklist channels where clients can be moved from.
If you have _Jail_ plugin enabled, You might want to add your jail channel to the blacklist.

### Banned names

Kicks out any clients with configured nickname.  
You can configure a list of banned nicknames or provide a function that return a boolean telling the bot if a given nickname is allowed.

By default, the bot will only kick the default TeamSpeak nickname: `TeamSpeakUser`

### Fun

Comes with handful of fun commands:

- `coinflip`: Flips a coin, responding with heads or tails.
- `roll <size=6>`: Rolls a given sided die.

### Greeter

Greets new clients (_clients with `guest` server group_) with a configurable message.

### Jail

Jails a client for a given amount of time.
Time can be provided as a _number of seconds_ or `<int>h<int>m<int>s` meaning number of hours, minutes, and seconds respectively with out the `<>` (_no need to provide all of them_)

- `jail <nickname> <time>`: Jail misbehaving client.
- `free <nickname>`: Free jailed client. Don't use in pity.

### Jokes

Command to tell some good/bad jokes about programming:

- `joke` Tells a programming related joke

### Notify

Pokes client with a message after given amount of time.  
Time parsing works the same as in jail command.

- `notify <time> <message>`: Pokes you after given time with the provided message.

## Requirements

- Python 3.12

## Installation

You should always use virtual envs.

```shell
pip install teamspeak-bot
```

## Configuration

The bot will look for a configuration module on startup.  
You can pass a path to a config file with `-c / --config` command line argument.  
The config module must include `CONFIG` variable.

### Example config module:

```python
from teamspeak_bot import BotConfig

# BotConfig is a type safe way for you to configure
# your bot instance. If you have misconfigured your bot,
# your IDE will yell at you.

CONFIG = BotConfig(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
    plugins={},
    logging={}
)
```

## Running the bot

> **_NOTE:_** You will need provide configuration file.

```shell
teamspeak-bot
# -- OR --
python -m teamspeak_bot
```

### Command line arguments

- `-c, --config`: Path to a configuration file. Defaults to `config.py`
- `-l, --logfile`: Path to a log file. Defaults to `log.txt`
- `-v, --verbose`: Level of verbosity.
- `-h, --help`: Prints out the help message.

## Plugin configuration:

### Admin

Plugin config key: `admin`
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |
| allowed_uids | `tuple[str, ...]` | UIDs allowed to run admin commands. |
| allowed_server_groups | `tuple[str, ...]` | Server groups allowed to run admin commands. |
| strict_server_group_checking | `bool` | By default if `Admin` in allowed_server_groups, any server group with the word `Admin` is allowed to run admin commands. This flag turns on strict matching. |

### Afk Mover

Plugin config key: `afk_mover`
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |
| afk_channel | `str` | Name of the AFK channel. doesn't match strictly |
| idle_time | `float` | AFK grace period in seconds |
| channel_whitelist | `tuple[str, ...]` | Channel names where clients will be moved. |
| channel_blacklist | `tuple[str, ...]` | Channel names where clients wont be moved. |

### Banned Names

Plugin config key: `banned_names`  
`banned_names` and/or `is_banned_name` has to be defined if this plugin is enabled.
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |
| banned_names | `tuple[str, ...]` | Blacklisted names |
| is_banned_name | `Callable[[str], bool]` | Function that determines if a name is banned |
| message | `str` | Kick message |
| check_period | `float` | How often bot checks for banned names in the client list in seconds |

### Error events

Plugin config key: `error_events`
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |
| invalid_invocation_message | `str` | Message when command is invoked wrongly |
| permission_error_message | `str` | Message when an invoker doesn't have proper permissions to run the command |
| permission_error_log_message | `str` | Message logged when an invoker doesn't have proper permissions to run the command |
| command_error_message | `str` | Message when a command handler encounters user error |

### Fun

Plugin config key: `fun`
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |

### Greeter

Plugin config key: `greeter`
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |
| message | `str` | Message to new user joining the server |

### Jail

Plugin config key: `jail`
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |
| can_jail_uids | `tuple[str, ...]` | UIDs allowed to jail clients. |
| can_jail_server_groups | `tuple[str, ...]` | Server groups allowed to jail clients. |
| strict_server_group_checking | `bool` | Match server groups strictly |
| jail_channel | `str` | Name of the jail channel. |
| inmate_server_group_name | `str` | Name of the server group given to jailed clients. |

### Jokes

Plugin config key: `jokes`
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |

### Notify

Plugin config key: `notify`
| Key | Type | Explanation |
|---|---|---|
| enabled | `bool` | If the plugin is enabled |
| max_delay | `int` | The max notify time in seconds |
